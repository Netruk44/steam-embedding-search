
import click
from instructor_model import InstructorModel
#from sqlite_helpers import * # TODO: Define functions
import sqlite_helpers
import tqdm
import logging
import os
from typing import List

COLOR_DARK_GREY = "\x1b[38;5;240m"
COLOR_BOLD = "\x1b[1m"
COLOR_RESET = "\x1b[0m"
LOGGING_FORMAT = COLOR_DARK_GREY + '[%(asctime)s - %(name)s]' + COLOR_RESET + COLOR_BOLD + ' %(levelname)s:' + COLOR_RESET + ' %(message)s'

@click.command()
@click.option('--db', required=True, help='Path to SQLite database')
#@click.option('--output', required=True, help='Path to output database file')
@click.option('--embed-description', default='Represent a video game that has a description of:', help='Embedding instruction for game descriptions')
@click.option('--embed-review', default='Represent a video game that has a review of: ', help='Embedding instruction for game reviews')
@click.option('--model-name', default='hkunlp/instructor-large', help='Name of the instructor model to use')
@click.option('--verbose', is_flag=True, help='Print verbose output')
def main(db, embed_description, embed_review, model_name, verbose):
    logging.basicConfig(format = LOGGING_FORMAT, level = logging.INFO if not verbose else logging.DEBUG)
    # Load input sqlite database
    # Check output tables & create if necessary
    # Load instructor model
    # Update game descriptions
    #   Make set of all game app ids in output db description table
    #   Make set of all game app ids in input db
    #   For each game app id in input db that isn't in output db
    #     Generate embedding for game description
    # Update game reviews
    #   Same as above, but for reviews

    # Load input sqlite database
    if not os.path.exists(db):
        logging.error(f"Input SQLite database {db} does not exist")
        exit(1)
    
    conn = sqlite_helpers.create_connection(db)

    # Make sure input tables exist
    if not sqlite_helpers.check_input_db_tables(conn):
        logging.error(f"Input SQLite database {db} does not have the required tables")
        exit(1)
    
    # Check output tables & create if necessary
    if not sqlite_helpers.check_output_db_tables(conn):
        logging.info(f"Output SQLite database {db} does not have the required tables. Creating them now.")
        sqlite_helpers.create_output_db_tables(conn)
    
    # Load instructor model
    instructor = InstructorModel(
        # Models:
        # - hkunlp/instructor-large : ~2.5 GB VRAM
        # - hkunlp/instructor-xl    : ~6 GB VRAM
        model_name = model_name,
    )

    # Update game descriptions
    instructor.embedding_instruction = embed_description
    update_description_embeddings(conn, instructor)

    # Update game reviews
    instructor.embedding_instruction = embed_review
    update_review_embeddings(conn, instructor)

    # Close connection
    conn.close()

def generate_embeddings_for_contents(
        file_contents: str,
        instructor: InstructorModel) -> List[List[float]]:
    # Tokenize the file contents in chunks based on the model's max chunk length
    tokens = instructor.tokenize(file_contents)
    max_chunk_length = instructor.get_max_document_chunk_length()

    # Split tokens into chunks
    all_embeddings: List[List[float]] = []
    for chunk_number, i in enumerate(range(0, len(tokens), max_chunk_length)):

        chunk = tokens[i:i + max_chunk_length]
        chunk = instructor.detokenize(chunk)
        
        logging.debug(f'Chunk {chunk_number} token length: {min(max_chunk_length, len(tokens) - i)} | Chunk string length: {len(chunk)} | Max chunk length: {max_chunk_length}')
        all_embeddings.append(instructor.generate_embedding_for_document(chunk))
    
    return all_embeddings

def update_description_embeddings(conn, instructor):
    # Find app ids that have embeddings already
    output_appids = sqlite_helpers.get_output_description_appids(conn)

    # Find app ids that need embeddings
    input_appids = sqlite_helpers.get_input_appids_with_description(conn, only_games=True)
    appids_need_updating = input_appids - output_appids

    # Update embeddings
    logging.info(f"Updating {len(appids_need_updating)} description embeddings")
    for appid in tqdm.tqdm(appids_need_updating, desc = "Updating description embeddings"):
        # Get description
        description = sqlite_helpers.get_input_description_for_appid(conn, appid)
        # Generate embeddings
        embeddings = generate_embeddings_for_contents(description, instructor)
        # Insert embeddings
        sqlite_helpers.insert_description_embeddings(conn, appid, embeddings)

def update_review_embeddings(conn, instructor):
    # Find recommendation ids that have embeddings already
    output_recommendationids = sqlite_helpers.get_output_review_recommendationids(conn)

    # Find app ids that need embeddings
    input_appids = sqlite_helpers.get_input_appids_for_reviews(conn)

    # Update reviews
    bar = tqdm.tqdm(input_appids, desc = "Updating review embeddings")
    for input_appid in bar:
        # Get reviews
        all_reviews = sqlite_helpers.get_input_reviews_for_appid(conn, input_appid)
        all_review_recommendationids = set(all_reviews.keys())
        new_reviews = all_review_recommendationids - output_recommendationids

        # Update embeddings
        logging.debug(f"Updating {len(new_reviews)} review embeddings for appid {input_appid}")
        for index, recommendationid in enumerate(new_reviews):
            bar.set_postfix(appid=str(input_appid), progress=int(index / len(new_reviews) * 100))
            # Get review
            review = all_reviews[recommendationid]
            # Generate embeddings
            embeddings = generate_embeddings_for_contents(review, instructor)
            # Insert embeddings
            sqlite_helpers.insert_review_embeddings(conn, recommendationid, embeddings)

if __name__ == '__main__':
    main()
