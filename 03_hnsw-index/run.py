import click
import sqlite_helpers
import tqdm
import logging
import hnswlib
import numpy as np
from typing import List, Optional, Set, Dict, Iterator, Tuple, Callable
import sqlite3
import os


COLOR_DARK_GREY = "\x1b[38;5;240m"
COLOR_BOLD = "\x1b[1m"
COLOR_RESET = "\x1b[0m"
LOGGING_FORMAT = COLOR_DARK_GREY + '[%(asctime)s - %(name)s]' + COLOR_RESET + COLOR_BOLD + ' %(levelname)s:' + COLOR_RESET + ' %(message)s'

@click.command()
@click.option('--db', required=True, help='Path to SQLite database')
@click.option('--index-type', type=click.Choice(['description', 'review', 'mixed', 'all']), default='all', help='Type of index to create')
@click.option('--remove-old-indexes', default=False, is_flag=True, help='Remove old indexes after creating new ones')
@click.option('--verbose', is_flag=True, help='Print verbose output')
def main(db, index_type, remove_old_indexes, verbose):
  logging.basicConfig(format = LOGGING_FORMAT, level = logging.INFO if not verbose else logging.DEBUG)

  # Load input sqlite database
  if not os.path.exists(db):
    logging.error(f"Input SQLite database {db} does not exist")
    exit(1)
  
  conn = sqlite_helpers.create_connection(db)

  # Make sure input tables exist
  input_tables = ['description_embeddings', 'review_embeddings']

  if not sqlite_helpers.check_all_tables_exist(conn, input_tables):
    logging.error(f"Input SQLite database {db} does not have the required tables")
    logging.info(f"Required tables: {input_tables}")
    exit(1)
  
  # Make sure output tables exist
  sqlite_helpers.create_output_db_tables(conn)

  # Create and insert new indexes
  # ef and M values were found through experimentation with playground.ipynb notebook
  # M value doesn't seem to affect much for these embeddings.
  if index_type == 'description' or index_type == 'all':
    logging.info("Creating new description index...")
    num_elements = sqlite_helpers.get_count_appids_with_description_embeddings(conn)
    description_index = create_index(
      conn, 
      # ~90% recall
      num_elements=num_elements, 
      ef_recall=1000,
      ef_construct=num_elements, 
      M=32, 
      get_batches=get_descriptions_by_appid_batched
    )
    sqlite_helpers.add_description_index(conn, description_index)

  if index_type == 'review' or index_type == 'all':
    logging.info("Creating new review index...")
    num_elements = sqlite_helpers.get_count_appids_with_review_embeddings(conn)
    review_index = create_index(
      conn, 
      # 90.21% recall @ double the time of brute force search :/
      num_elements=num_elements, 
      ef_recall=4000, 
      ef_construct=num_elements, 
      M=32, 
      get_batches=get_reviews_by_appid_batched
    )
    sqlite_helpers.add_review_index(conn, review_index)

  if index_type == 'mixed' or index_type == 'all':
    logging.info("Creating new mixed index...")
    num_elements = sqlite_helpers.get_count_appids_with_description_or_review_embeddings(conn)
    mixed_index = create_index(
      conn, 
      # 90.82% recall @ 70%-90% the time of brute force
      num_elements=num_elements, 
      ef_recall=1500, 
      ef_construct=num_elements, 
      M=32, 
      get_batches=get_mixed_by_appid_batched
    )
    sqlite_helpers.add_mixed_index(conn, mixed_index)

  if remove_old_indexes:
    sqlite_helpers.remove_old_indexes(conn)
    logging.info("Removed old indexes, remember to VACUUM the database to reclaim space")
  
  conn.close()


def mean_pooling(embeddings: List[List[float]]) -> List[float]:
  return np.sum(embeddings, axis=0) / len(embeddings)

def get_index_dimension(conn: sqlite3.Connection) -> int:
  return len(sqlite_helpers.get_any_description_embeddings_list(conn)[0])

def pool_description_embeddings(embeddings: List[List[float]]) -> List[float]:
  # embeddings[chunk_size][embedding_dim]
  return mean_pooling(embeddings)

def pool_review_embeddings(embeddings: Dict[str, List[List[float]]]) -> List[float]:
  # embeddings[review_id][chunk_size][embedding_dim]
  flat_embeddings = [review_embedding for review_id in embeddings for review_embedding in embeddings[review_id]]
  # flat_embeddings[chunk_size][embedding_dim]
  return mean_pooling(flat_embeddings)

def get_descriptions_by_appid_batched(conn: sqlite3.Connection, page_size: int = 1000) -> Iterator[List[Tuple[int, List[float]]]]:
  for batch in sqlite_helpers.get_description_embeddings_batch(conn, page_size):
    appids, embeddings = zip(*batch)
    yield [(appid, pool_description_embeddings(embedding)) for appid, embedding in zip(appids, embeddings)]

def get_reviews_by_appid_batched(conn: sqlite3.Connection, page_size: int = 1000) -> Iterator[List[Tuple[int, List[float]]]]:
  appids = sqlite_helpers.get_appids_with_review_embeddings(conn)

  for i in range(0, len(appids), page_size):
    yield [(appid, pool_review_embeddings(sqlite_helpers.get_review_embeddings_for_appid(conn, appid))) for appid in appids[i:i+page_size]]

def get_mixed_by_appid_batched(conn: sqlite3.Connection, page_size: int = 1000, review_weight: float = 0.7) -> Iterator[List[Tuple[int, List[float]]]]:
  appids_with_description_embeddings = set(sqlite_helpers.get_appids_with_description_embeddings(conn))
  appids_with_reviews = set(sqlite_helpers.get_appids_with_review_embeddings(conn))
  appids = list(appids_with_description_embeddings.union(appids_with_reviews))

  for i in range(0, len(appids), page_size):
    page = []
    for appid in appids[i:i+page_size]:
      all_description_embeddings = sqlite_helpers.get_description_embeddings_for_appid(conn, appid)
      all_review_embeddings = sqlite_helpers.get_review_embeddings_for_appid(conn, appid)

      #if len(all_review_embeddings) == 0 and len(all_description_embeddings) == 0:
      #  raise ValueError(f"No description or review embeddings found for appid {appid}")
      
      if len(all_review_embeddings) == 0:
        #review_weight = 0.0
        description_embedding = pool_description_embeddings(all_description_embeddings)
        page.append((appid, description_embedding))
      elif len(all_description_embeddings) == 0:
        #review_weight = 1.0
        review_embedding = pool_review_embeddings(all_review_embeddings)
        page.append((appid, review_embedding))
      else:
        # Weighted average of description and review embeddings
        # Default of 0.7 was chosen mostly arbitrarily
        description_embedding = pool_description_embeddings(all_description_embeddings)
        review_embedding = pool_review_embeddings(all_review_embeddings)
        final_embedding = review_weight * review_embedding + (1.0 - review_weight) * description_embedding
        page.append((appid, final_embedding))
    yield page

def create_index(
  conn: sqlite3.Connection, 
  num_elements: int, 
  ef_recall: int, 
  ef_construct: int,
  M: int, 
  get_batches: Callable[[sqlite3.Connection, int], Iterator[List[Tuple[int, List[float]]]]]) -> hnswlib.Index:
  dim = get_index_dimension(conn)

  logging.info(f"Creating index with: {num_elements} elements, dim={dim}, ef_recall={ef_recall}, ef_construct={ef_construct}, M={M}")

  index = hnswlib.Index(space='cosine', dim=dim)
  index.init_index(max_elements=num_elements, ef_construction=ef_construct, M=M)
  index.set_ef(ef_recall)

  bar = tqdm.tqdm(total=num_elements, desc="Creating index", smoothing=0.9)

  for batch in get_batches(conn):
    appids, embeddings = zip(*batch)
    index.add_items(embeddings, appids)
    bar.update(len(batch))
  
  bar.close()

  return index

if __name__ == '__main__':
  main()