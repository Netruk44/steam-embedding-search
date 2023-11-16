
from flask import Flask, request
from instructor_model import InstructorModel
import sqlite_helpers
from typing import List
import logging
import numpy as np
import json
from wsgiref.simple_server import make_server
from config import database_path, instructor_model_name

instructor_model = None

app = Flask(__name__)

# Startup code
with app.app_context():
    logging.basicConfig(level=logging.INFO)
    print('Loading instructor model...')
    instructor_model = InstructorModel(instructor_model_name)


@app.route('/get_results')
def get_results():
    global instructor_model

    query = request.args.get('query')

    type = request.args.get('type')
    type = 'all' if type is None else type
    known_types = ['all', 'description', 'review']
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
    results = search(conn, query_embed, type, max_results=num_results)
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



def cosine_similarity(a: List[float], b: List[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def compare_all_embeddings_take_max(embeddings: List[List[float]], query_embed: List[float]) -> float:
    similarities = [cosine_similarity(embedding, query_embed) for embedding in embeddings]
    return max(similarities)

def add_to_capped_list(list_to_add_to: List[dict], item_to_add: dict, max_length: int):
    list_to_add_to.append(item_to_add)
    if len(list_to_add_to) > max_length:
        # Find the lowest score, remove it
        lowest_score = min(list_to_add_to, key=lambda x: x['score'])
        list_to_add_to.remove(lowest_score)



def search(conn, query_embed, query_for_type, max_results=10):
    matches = []
    logging.debug(f"Searching for {query_for_type} matches")

    # Store Description Search
    if query_for_type == 'all' or query_for_type == 'description':
        for current_page in sqlite_helpers.get_paginated_embeddings_for_descriptions(conn, page_size=100):
            for appid, embeddings in current_page.items():
                score = compare_all_embeddings_take_max(embeddings, query_embed)
                name = sqlite_helpers.get_name_for_appid(conn, appid)

                add_to_capped_list(matches, {
                    'appid': appid,
                    'name': name,
                    'match_type': 'description',
                    'score': float(score),
                }, max_results)
    
    # Review Search
    if query_for_type == 'all' or query_for_type == 'review':
        appids_with_reviews = sqlite_helpers.get_appids_with_review_embeds(conn)

        for appid in appids_with_reviews:
            all_review_embeddings = sqlite_helpers.get_review_embeddings_for_appid(conn, appid)
            flat_embeddings = []

            for review_id in all_review_embeddings:
                flat_embeddings.extend(all_review_embeddings[review_id])
            
            average_embedding = np.sum(flat_embeddings, axis=0) / len(flat_embeddings)
            score = cosine_similarity(average_embedding, query_embed)
            name = sqlite_helpers.get_name_for_appid(conn, appid)

            add_to_capped_list(matches, {
                'appid': appid,
                'name': name,
                'match_type': 'review',
                'score': float(score),
            }, max_results)
    
    # Sort by score
    matches.sort(key=lambda x: x['score'], reverse=True)

    return matches


if __name__ == '__main__':
    server = make_server('localhost', 5000, app)
    server.serve_forever()
