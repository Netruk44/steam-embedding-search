
from flask import Flask, request
from instructor_model import InstructorModel
import sqlite_helpers
from typing import List
import logging
import numpy as np
import json
from wsgiref.simple_server import make_server
from config import database_path, instructor_model_name
import heapq
import random
import hnswlib
import time

instructor_model = None
description_index = None
review_index = None
mixed_index = None

app = Flask(__name__)

# Startup code
with app.app_context():
    logging.basicConfig(level=logging.INFO)
    logging.info('Loading instructor model...')
    instructor_model = InstructorModel(instructor_model_name)

    logging.info('Loading database...')
    conn = sqlite_helpers.create_connection(database_path)
    if sqlite_helpers.database_has_indexes_available(conn):
        logging.info('Loading indexes...')
        description_index = sqlite_helpers.load_latest_description_index(conn)
        review_index = sqlite_helpers.load_latest_review_index(conn)
        mixed_index = sqlite_helpers.load_latest_mixed_index(conn)
    else:
        logging.fatal("No indexes found, exiting...")
        exit(1)
    conn.close()


@app.route('/get_results')
def get_results():
    # Automatically route to the correct function
    # If the query is numeric, assume it's an appid
    # Otherwise, assume it's a query string
    query = request.args.get('query')
    if query is None:
        return 'No query specified', 400
    
    try:
        query = int(query)
        return get_similar_games()
    except ValueError:
        return get_query_results()

@app.route('/get_query_results')
def get_query_results():
    global instructor_model

    query = request.args.get('query')

    type = request.args.get('type')
    type = 'all' if type is None else type
    known_types = ['all', 'description', 'review', 'mixed']
    if type not in known_types:
        return 'Invalid type, must be one of: {}'.format(', '.join(known_types)), 400

    instruction = request.args.get('instruction')
    instruction = 'Represent a video game that has a description of:' if instruction is None else instruction

    num_results = request.args.get('num_results')
    num_results = 10 if num_results is None else int(num_results)
    num_results = max(0, min(num_results, 100))

    logging.info(f'Request: {request.url}')

    # Generate query embedding
    query_tokenized = instructor_model.tokenize(query)
    instructor_model.embedding_instruction = instruction

    if len(query_tokenized) > instructor_model.get_max_query_chunk_length():
        return 'Query too long, shorten query or instruction', 400
    
    query_embed = instructor_model.generate_embedding_for_query(query)

    # Query for results
    conn = sqlite_helpers.create_connection(database_path)
    search_time_begin = time.perf_counter()
    #results = search(conn, query_embed, type, max_results=num_results)
    results = index_search(conn, query_embed, type, max_results=num_results)
    search_time_end = time.perf_counter()
    logging.info(f"Search time: {search_time_end - search_time_begin}")
    conn.close()

    # Return results as JSON
    response = app.response_class(
        response=json.dumps(results),
        status=200,
        mimetype='application/json'
    )

    # TODO: Limit this to the domain of the frontend
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


@app.route('/get_similar_games')
def get_similar_games():
    global instructor_model

    appid = int(request.args.get('query'))
    num_results = request.args.get('num_results')
    num_results = 10 if num_results is None else int(num_results)
    num_results = max(0, min(num_results, 100))
    type = request.args.get('type')
    type = 'all' if type is None else type

    if type not in ['all', 'description', 'review', 'mixed']:
        return 'Invalid type, must be one of: all, description, review', 400

    logging.info(f'Request: {request.url}')

    # Query for results
    conn = sqlite_helpers.create_connection(database_path)
    
    search_time_begin = time.perf_counter()
    results = index_search_similar(conn, appid, type, max_results=num_results)
    search_time_end = time.perf_counter()
    logging.info(f"Search time: {search_time_end - search_time_begin}")

    conn.close()

    # Return results as JSON
    response = app.response_class(
        response=json.dumps(results),
        status=200,
        mimetype='application/json'
    )

    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def cosine_similarity(a: List[float], b: List[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def mean_pooling(embeddings: List[List[float]]) -> List[float]:
    return np.sum(embeddings, axis=0) / len(embeddings)

def compare_all_embeddings_take_max(embeddings: List[List[float]], query_embed: List[float]) -> float:
    similarities = [cosine_similarity(embedding, query_embed) for embedding in embeddings]
    return max(similarities)

def add_to_heap(heap: List[dict], item_to_add: dict, max_length: int):
    # Add to heap
    # Add a random number to the tuple to break ties, since you can't compare dicts
    heapq.heappush(heap, (item_to_add['score'], random.random() , item_to_add))

    # Pop if too large
    if len(heap) > max_length:
        heapq.heappop(heap)

def index_search(conn, query, query_for_type, max_results=10):
    matches = []
    logging.debug(f"Searching for {query_for_type} matches")

    # Store Description Search
    if query_for_type == 'all' or query_for_type == 'description':
        #description_index = sqlite_helpers.load_latest_description_index(conn)
        global description_index
        appids, distances = description_index.knn_query(query, k=max_results)
        
        appids = appids[0]
        distances = distances[0]

        for appid, distance in zip(appids, distances):
            appid = int(appid)
            distance = float(distance)

            name = sqlite_helpers.get_name_for_appid(conn, appid)
            matches.append({
                'appid': appid,
                'name': name,
                'match_type': 'description',
                'score': 1.0 - distance,
            })

    # Review search - Calculate average embedding for all reviews / mean pooling
    if query_for_type == 'all' or query_for_type == 'review':
        #review_index = sqlite_helpers.load_latest_review_index(conn)
        global review_index
        appids, distances = review_index.knn_query(query, k=max_results)

        appids = appids[0]
        distances = distances[0]

        for appid, distance in zip(appids, distances):
            appid = int(appid)
            distance = float(distance)

            name = sqlite_helpers.get_name_for_appid(conn, appid)
            matches.append({
                'appid': appid,
                'name': name,
                'match_type': 'review',
                'score': 1.0 - distance,
            })
    
    # Mixed search - Pool store description and review embeddings
    if query_for_type == 'all' or query_for_type == 'mixed':
        global mixed_index
        appids, distances = mixed_index.knn_query(query, k=max_results)

        appids = appids[0]
        distances = distances[0]

        for appid, distance in zip(appids, distances):
            appid = int(appid)
            distance = float(distance)

            name = sqlite_helpers.get_name_for_appid(conn, appid)
            matches.append({
                'appid': appid,
                'name': name,
                'match_type': 'mixed',
                'score': 1.0 - distance,
            })

    # Order by score
    matches = sorted(matches, key=lambda x: x['score'], reverse=True)

    # Remove duplicate appids
    # This can happen if a game has both a description and review that match the query
    appids_seen = set()
    deduped_matches = []
    for match in matches:
        if match['appid'] not in appids_seen:
            deduped_matches.append(match)
            appids_seen.add(match['appid'])

    return deduped_matches[:max_results]

def index_search_similar(conn, query_appid, query_for_type, max_results=10):
    matches = []
    logging.debug(f"Searching for similar games to {sqlite_helpers.get_name_for_appid(conn, query_appid)}")

    # Store Description Search
    if query_for_type == 'all' or query_for_type == 'description':
        #description_index = sqlite_helpers.load_latest_description_index(conn)
        global description_index
        all_description_embeddings = sqlite_helpers.get_description_embeddings_for_appid(conn, query_appid)
        query_embed = mean_pooling(all_description_embeddings)

        # Add 1 to max results to account for the query returning
        # the app we're searching for
        appids, distances = description_index.knn_query(query_embed, k=max_results + 1)
        
        appids = appids[0]
        distances = distances[0]

        for appid, distance in zip(appids, distances):
            appid = int(appid)
            distance = float(distance)

            if appid == query_appid:
                continue

            name = sqlite_helpers.get_name_for_appid(conn, appid)
            matches.append({
                'appid': appid,
                'name': name,
                'match_type': 'description',
                'score': 1.0 - distance,
            })

    # Review search - Calculate average embedding for all reviews / mean pooling
    if query_for_type == 'all' or query_for_type == 'review':
        #review_index = sqlite_helpers.load_latest_review_index(conn)
        global review_index
        
        query_review_embeddings = sqlite_helpers.get_review_embeddings_for_appid(conn, query_appid)
        logging.info(f"Basing review query on {len(query_review_embeddings)} user reviews.")
        query_flat_embeddings = [review_embedding for review_id in query_review_embeddings for review_embedding in query_review_embeddings[review_id]]
        query_embed = mean_pooling(query_flat_embeddings)

        appids, distances = review_index.knn_query(query_embed, k=max_results + 1)

        appids = appids[0]
        distances = distances[0]

        for appid, distance in zip(appids, distances):
            appid = int(appid)
            distance = float(distance)

            if appid == query_appid:
                continue

            name = sqlite_helpers.get_name_for_appid(conn, appid)
            matches.append({
                'appid': appid,
                'name': name,
                'match_type': 'review',
                'score': 1.0 - distance,
            })

    # Mixed search - Pool store description and review embeddings
    if query_for_type == 'all' or query_for_type == 'mixed':
        global mixed_index

        all_description_embeddings = sqlite_helpers.get_description_embeddings_for_appid(conn, query_appid)
        all_review_embeddings = sqlite_helpers.get_review_embeddings_for_appid(conn, query_appid)

        if len(all_review_embeddings) == 0:
            logging.info(f"No reviews found for {sqlite_helpers.get_name_for_appid(conn, query_appid)}")
            query_embed = mean_pooling(all_description_embeddings)
        elif len(all_description_embeddings) == 0:
            logging.info(f"No description found for {sqlite_helpers.get_name_for_appid(conn, query_appid)}")
            flat_embeddings = [review_embedding for review_id in all_review_embeddings for review_embedding in all_review_embeddings[review_id]]
            query_embed = mean_pooling(flat_embeddings)
        else:
            # Weighted average of description and review embeddings
            review_weight = 0.7
            description_weight = 1.0 - review_weight

            description_embed = mean_pooling(all_description_embeddings)
            flat_embeddings = [review_embedding for review_id in all_review_embeddings for review_embedding in all_review_embeddings[review_id]]
            review_embed = mean_pooling(flat_embeddings)

            query_embed = description_weight * description_embed + review_weight * review_embed

        appids, distances = mixed_index.knn_query(query_embed, k=max_results + 1)

        appids = appids[0]
        distances = distances[0]

        for appid, distance in zip(appids, distances):
            appid = int(appid)
            distance = float(distance)

            if appid == query_appid:
                continue

            name = sqlite_helpers.get_name_for_appid(conn, appid)
            matches.append({
                'appid': appid,
                'name': name,
                'match_type': 'mixed',
                'score': 1.0 - distance,
            })

    # Order by score
    matches = sorted(matches, key=lambda x: x['score'], reverse=True)

    # Remove duplicate appids
    appids_seen = set()
    deduped_matches = []
    for match in matches:
        if match['appid'] not in appids_seen:
            deduped_matches.append(match)
            appids_seen.add(match['appid'])

    return deduped_matches[:max_results]

if __name__ == '__main__':
    server = make_server('localhost', 5000, app)
    server.serve_forever()
