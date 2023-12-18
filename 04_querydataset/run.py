
import click
from instructor_model import InstructorModel
#from sqlite_helpers import * # TODO: Define functions
import sqlite_helpers
import tqdm
import logging
import os
from typing import List
import numpy as np

COLOR_DARK_GREY = "\x1b[38;5;240m"
COLOR_BOLD = "\x1b[1m"
COLOR_RESET = "\x1b[0m"
LOGGING_FORMAT = COLOR_DARK_GREY + '[%(asctime)s - %(name)s]' + COLOR_RESET + COLOR_BOLD + ' %(levelname)s:' + COLOR_RESET + ' %(message)s'

@click.command()
@click.option('--db', required=True, help='Path to SQLite database')
@click.option('--query', help='Query to search for')
@click.option('--similar-to-appid', default=None, help='AppID to search for similar games', type=int)
@click.option('--index', default=None, help='Path to index file')
@click.option('--query-for-type', default='all', help='Type of data to search for (all, description, review)')
@click.option('--embed-query', default='Represent a video game that has a description of:', help='Embedding instruction for query')
@click.option('--model-name', default='hkunlp/instructor-large', help='Name of the instructor model to use')
@click.option('--max-results', default=10, help='Maximum number of results to return')
@click.option('--verbose', is_flag=True, help='Print verbose output')
def main(db, query, similar_to_appid, index, query_for_type, embed_query, model_name, max_results, verbose):
    logging.basicConfig(format = LOGGING_FORMAT, level = logging.INFO if not verbose else logging.DEBUG)

    # Load input sqlite database
    if not os.path.exists(db):
        logging.error(f"Input SQLite database {db} does not exist")
        exit(1)
    
    conn = sqlite_helpers.create_connection(db)

    # Make sure input tables exist
    if not sqlite_helpers.check_input_db_tables(conn):
        logging.error(f"Input SQLite database {db} does not have the required tables")
        exit(1)

    # Check if query is provided
    if query is None and similar_to_appid is None:
        logging.error("No query or appid provided")
        exit(1)
    
    # Check if query and appid are both provided
    if query is not None and similar_to_appid is not None:
        logging.error("Both query and appid provided, only one is allowed at a time")
        exit(1)
    
    if query is not None:
        perform_query(conn, query, query_for_type, embed_query, model_name, max_results, verbose)
    else:
        perform_similar_to_appid(conn, similar_to_appid, query_for_type, embed_query, model_name, max_results, verbose)
    
    # Close connection
    conn.close()

def perform_query(conn, query, query_for_type, embed_query, model_name, max_results, verbose):
    # Load instructor model
    # Needs to match the model used to generate the embeddings
    instructor = InstructorModel(
        # Models:
        # - hkunlp/instructor-large : ~2.5 GB VRAM
        # - hkunlp/instructor-xl    : ~6 GB VRAM
        model_name = model_name,
    )

    # Get query embedding
    query_tokenized = instructor.tokenize(query)
    if len(query_tokenized) > instructor.get_max_query_chunk_length():
        logging.error(f"Query is too long. {len(query_tokenized)} / {instructor.get_max_query_chunk_length()} tokens are used.")
        exit(1)

    instructor.embedding_instruction = embed_query
    query_embed: List[float] = instructor.generate_embedding_for_query(query, verbose)

    # Do a linear search
    results = slow_search(conn, query_embed, query_for_type, max_results)

    # Display results
    print(f"Results for query: {query}")
    for result in results:
        print(f"  {result['appid']}: {result['name']} ({result['match_type']})")
        print(f"    Match: {result['score'] * 100.0:.2f}%")

def perform_similar_to_appid(conn, similar_to_appid, query_for_type, embed_query, model_name, max_results, verbose):
    results = slow_search_similar(conn, similar_to_appid, query_for_type, max_results)

    # Display results
    print(f"Results for similar games to {sqlite_helpers.get_name_for_appid(conn, similar_to_appid)}")
    for result in results:
        print(f"  {result['appid']}: {result['name']} ({result['match_type']})")
        print(f"    Match: {result['score'] * 100.0:.2f}%")

def cosine_similarity(a: List[float], b: List[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def mean_pooling(embeddings: List[List[float]]) -> List[float]:
    return np.sum(embeddings, axis=0) / len(embeddings)

def euclidean_distance(a: List[float], b: List[float]) -> float:
    distance = np.linalg.norm(a - b)
    return 1.0 / (1.0 + distance)

def compare_all_embeddings_take_max(embeddings: List[List[float]], query_embed: List[float]) -> float:
    similarities = [cosine_similarity(embedding, query_embed) for embedding in embeddings]
    #similarities = [euclidean_distance(embedding, query_embed) for embedding in embeddings]
    return max(similarities)

def add_to_capped_list(list_to_add_to: List[dict], item_to_add: dict, max_length: int):
    list_to_add_to.append(item_to_add)
    if len(list_to_add_to) > max_length:
        # Find the lowest score, remove it
        lowest_score = min(list_to_add_to, key=lambda x: x['score'])
        list_to_add_to.remove(lowest_score)

def slow_search(conn, query_embed, query_for_type, max_results=10):
    matches = []
    logging.debug(f"Searching for {query_for_type} matches")

    # Store Description Search
    if query_for_type == 'all' or query_for_type == 'description':
        bar = tqdm.tqdm(total=sqlite_helpers.get_count_embeddings_for_descriptions(conn), desc="Store Descriptions")

        for current_page in sqlite_helpers.get_paginated_embeddings_for_descriptions(conn, page_size=100):
            for appid, embeddings in current_page.items():
                score = compare_all_embeddings_take_max(embeddings, query_embed)
                name = sqlite_helpers.get_name_for_appid(conn, appid)

                add_to_capped_list(matches, {
                    'appid': appid,
                    'name': name,
                    'match_type': 'description',
                    'score': score,
                }, max_results)

                bar.update(1)
        
        bar.close()

    # Review search v2 - Calculate average embedding for all reviews / mean pooling
    if query_for_type == 'all' or query_for_type == 'review':
        appids_with_reviews = sqlite_helpers.get_appids_with_review_embeds(conn)

        for appid in tqdm.tqdm(appids_with_reviews, desc="Reviews"):
            all_review_embeddings = sqlite_helpers.get_review_embeddings_for_appid(conn, appid)
            flat_embeddings = []

            for review_id in all_review_embeddings:
                flat_embeddings.extend(all_review_embeddings[review_id])
            
            average_embedding = mean_pooling(flat_embeddings)
            score = cosine_similarity(average_embedding, query_embed)
            #score = euclidean_distance(average_embedding, query_embed)
            name = sqlite_helpers.get_name_for_appid(conn, appid)

            add_to_capped_list(matches, {
                'appid': appid,
                'name': name,
                'match_type': 'review',
                'score': score,
            }, max_results)

    # Review search v1 - Compare each review to the query individually
    #if query_for_type == 'all' or query_for_type == 'review':
    if False:
        bar = tqdm.tqdm(total=sqlite_helpers.get_count_embeddings_for_reviews(conn), desc="Reviews")

        for current_page in sqlite_helpers.get_paginated_embeddings_for_reviews(conn, page_size=100):
            total_score = 0
            for recommendationid, embeddings in current_page.items():
                score = compare_all_embeddings_take_max(embeddings, query_embed)
                total_score += score
                appid = sqlite_helpers.get_appid_for_recommendationid(conn, recommendationid)
                name = sqlite_helpers.get_name_for_appid(conn, appid)

                add_to_capped_list(matches, {
                    'appid': appid,
                    'name': name,
                    'match_type': 'review',
                    'score': score,
                }, max_results)

                bar.update(1)
            
            # Add average score for all reviews
            #add_to_capped_list(matches, {
            #    'appid': appid,
            #    'name': name,
            #    'match_type': 'review',
            #    'score': total_score / len(current_page),
            #}, max_results)
        
        bar.close()

    # Order by score
    matches = sorted(matches, key=lambda x: x['score'], reverse=True)

    return matches

def slow_search_similar(conn, query_appid, query_for_type, max_results=10):
    matches = []
    logging.debug(f"Searching for similar games to {sqlite_helpers.get_name_for_appid(conn, query_appid)}")

    # Store Description Search
    if query_for_type == 'all' or query_for_type == 'description':
        all_description_embeddings = sqlite_helpers.get_description_embeddings_for_appid(conn, query_appid)
        query_embed = mean_pooling(all_description_embeddings)

        bar = tqdm.tqdm(total=sqlite_helpers.get_count_embeddings_for_descriptions(conn), desc="Store Descriptions")

        for current_page in sqlite_helpers.get_paginated_embeddings_for_descriptions(conn, page_size=100):
            for current_appid, embeddings in current_page.items():
                if current_appid == query_appid:
                    continue

                score = compare_all_embeddings_take_max(embeddings, query_embed)
                name = sqlite_helpers.get_name_for_appid(conn, current_appid)

                add_to_capped_list(matches, {
                    'appid': current_appid,
                    'name': name,
                    'match_type': 'description',
                    'score': score,
                }, max_results)

                bar.update(1)
    
        bar.close()

    # Review search v2 - Calculate average embedding for all reviews / mean pooling
    if query_for_type == 'all' or query_for_type == 'review':
        query_review_embeddings = sqlite_helpers.get_review_embeddings_for_appid(conn, query_appid)
        query_flat_embeddings = [review_embedding for review_id in query_review_embeddings for review_embedding in query_review_embeddings[review_id]]
        query_embed = mean_pooling(query_flat_embeddings)

        appids_with_reviews = sqlite_helpers.get_appids_with_review_embeds(conn)

        for current_appid in tqdm.tqdm(appids_with_reviews, desc="Reviews"):
            if current_appid == query_appid:
                continue
            
            all_review_embeddings = sqlite_helpers.get_review_embeddings_for_appid(conn, current_appid)
            flat_embeddings = [review_embedding for review_id in all_review_embeddings for review_embedding in all_review_embeddings[review_id]]
            average_embedding = mean_pooling(flat_embeddings)

            score = cosine_similarity(average_embedding, query_embed)
            #score = euclidean_distance(average_embedding, query_embed)
            name = sqlite_helpers.get_name_for_appid(conn, current_appid)

            add_to_capped_list(matches, {
                'appid': current_appid,
                'name': name,
                'match_type': 'review',
                'score': score,
            }, max_results)

    # Order by score
    matches = sorted(matches, key=lambda x: x['score'], reverse=True)
    return matches

if __name__ == '__main__':
    main()