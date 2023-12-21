import sqlite3
import logging
from typing import List, Optional, Set, Dict, Generator
import pickle
import hnswlib

## Init

def create_connection(db_file: str = "steam.db") -> sqlite3.Connection:
    """
    Creates a connection to the SQLite database.

    Args:
        db_file (str): The path to the SQLite database.

    Returns:
        sqlite3.Connection: A connection to the SQLite database.
    """
    logging.debug("Creating connection to SQLite database")
    return sqlite3.connect(db_file)


## Validation

def check_table(conn: sqlite3.Connection, table_name: str) -> bool:
    """
    Checks if the table exists in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        table_name (str): The name of the table to check for.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    c = conn.cursor()

    c.execute(f'''
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'
    ''')
    table_exists = c.fetchone()[0] == 1

    c.close()

    logging.debug(f"Table {table_name} exists: {table_exists}")

    return table_exists

def check_input_db_tables(conn: sqlite3.Connection) -> bool:
    """
    Checks if the required tables exist in the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        bool: True if the tables exist, False otherwise.
    """
    logging.debug(f"Checking if required tables exist in input SQLite database.")
    #required_tables = ["description_embeddings", "review_embeddings", "gamelist"]
    # Updated for hack
    required_tables = ["description_embeddings", "review_embeddings", "gamelist"]
    
    tables_exist = [check_table(conn, table_name) for table_name in required_tables]
    
    return all(tables_exist)


## Data retrieval

def get_description_embeddings_for_appid(conn: sqlite3.Connection, appid: int) -> List[List[float]]:
    """
    Gets the description embeddings for the given appid from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to get the description embeddings for.

    Returns:
        List[List[float]]: The embedding for the game description.
    """
    logging.debug(f"Getting description embeddings for appid {appid} from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT embedding FROM description_embeddings WHERE appid = ?
    ''', (appid,))
    results = c.fetchone()[0]

    c.close()

    return pickle.loads(results)

def get_all_embeddings_for_descriptions(conn: sqlite3.Connection) -> Dict[int,List[List[float]]]:
    """
    Gets all the embeddings for store descriptions from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Dict[int, List[List[float]]]: A dictionary mapping appid to the embedding for the game description.
    """
    logging.debug(f"Getting all game description embeddings from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT appid, embedding FROM description_embeddings
    ''')
    results = c.fetchall()

    c.close()

    return {appid: pickle.loads(embedding) for appid, embedding in results}

def get_count_embeddings_for_descriptions(conn: sqlite3.Connection) -> int:
    """
    Gets the number of embeddings for store descriptions from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        int: The number of embeddings for game descriptions.
    """
    logging.debug(f"Getting count of game description embeddings from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT count(*) FROM description_embeddings
    ''')
    results = c.fetchone()[0]

    c.close()

    return results

def get_paginated_embeddings_for_descriptions(conn: sqlite3.Connection, page_size = 100) -> Generator[Dict[int,List[List[float]]], None, None]:
    """
    Gets all the embeddings for store descriptions from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Dict[int, List[List[float]]]: A dictionary mapping appid to the embedding for the game description.
    """
    logging.debug(f"Getting all game description embeddings from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT appid, embedding FROM description_embeddings
    ''')

    while True:
        results = c.fetchmany(page_size)
        if not results:
            break
        yield {appid: pickle.loads(embedding) for appid, embedding in results}

    c.close()

def get_count_embeddings_for_reviews(conn: sqlite3.Connection) -> int:
    """
    Gets the number of embeddings for reviews from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        int: The number of embeddings for reviews.
    """
    logging.debug(f"Getting count of review embeddings from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT count(*) FROM review_embeddings
    ''')
    results = c.fetchone()[0]

    c.close()

    return results


def get_paginated_embeddings_for_reviews(conn: sqlite3.Connection, page_size = 100) -> Generator[Dict[int,List[List[float]]], None, None]:
    """
    Gets all the embeddings for reviews from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Dict[int, List[List[float]]]: A dictionary mapping recommendationid to the embedding for the review.
    """
    logging.debug(f"Getting all review embeddings from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT recommendationid, embedding FROM review_embeddings
    ''')

    while True:
        results = c.fetchmany(page_size)
        if not results:
            break
        yield {recommendationid: pickle.loads(embedding) for recommendationid, embedding in results}

    c.close()


def get_appid_for_recommendationid(conn: sqlite3.Connection, recommendationid: int) -> int:
    """
    Gets the appid for the given recommendationid from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        recommendationid (int): The recommendationid to get the appid for.

    Returns:
        int: The appid for the given recommendationid.
    """
    logging.debug(f"Getting appid for recommendationid {recommendationid} from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT appid FROM review_embeddings WHERE recommendationid = ?
    ''', (recommendationid,))
    results = c.fetchone()[0]

    c.close()

    return results

def get_name_for_appid(conn: sqlite3.Connection, appid: int) -> str:
    """
    Gets the name for the given appid from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to get the name for.

    Returns:
        str: The name for the given appid.
    """
    logging.debug(f"Getting name for appid {appid} from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT name FROM gamelist WHERE appid = ?
    ''', (appid,))
    results = c.fetchone()[0]

    c.close()

    return results

def get_appids_with_review_embeds(conn: sqlite3.Connection) -> Set[int]:
    """
    Gets all the review app ids from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Set[int]: A set of appids for reviews.
    """
    logging.debug(f"Getting all appids for reviews from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT DISTINCT appid
        FROM review_embeddings
    ''')
    results = c.fetchall()

    c.close()

    return set([appid for appid, in results])

def get_review_embeddings_for_appid(conn: sqlite3.Connection, appid: int) -> Dict[int,List[List[float]]]:
    """
    Gets all the review embeddings for the given appid from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to get the review embeddings for.

    Returns:
        Dict[int, List[List[float]]]: A dictionary mapping recommendationid to the embedding for the review.
    """
    logging.debug(f"Getting all review embeddings for appid {appid} from input SQLite database.")
    c = conn.cursor()

    c.execute(f'''
        SELECT recommendationid, embedding
        FROM review_embeddings
        WHERE appid = ?
    ''', (appid,))
    results = c.fetchall()

    c.close()

    return {recommendationid: pickle.loads(embedding) for recommendationid, embedding in results}

def database_has_indexes_available(conn: sqlite3.Connection) -> bool:
    """
    Checks if the database has both description and review indexes available.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        bool: True if the database has both indexes available, False otherwise.
    """
    logging.debug(f"Checking if database has an index available.")

    required_tables = ['description_embeddings_hnsw_index', 'review_embeddings_hnsw_index']
    tables_exist = [check_table(conn, table_name) for table_name in required_tables]
    if not all(tables_exist):
        return False

    # Check if at least one index has been created in each table
    c = conn.cursor()
    
    c.execute(f'''
        SELECT count(*) FROM description_embeddings_hnsw_index
    ''')
    description_index_count = c.fetchone()[0]

    c.execute(f'''
        SELECT count(*) FROM review_embeddings_hnsw_index
    ''')
    review_index_count = c.fetchone()[0]

    return description_index_count > 0 and review_index_count > 0

def load_latest_description_index(conn: sqlite3.Connection) -> hnswlib.Index:
    """
    Loads the latest description index from the database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        hnswlib.Index: The description index.
    """
    logging.debug(f"Loading latest description index from database.")

    c = conn.cursor()
    
    c.execute(f'''
        SELECT pickle
        FROM description_embeddings_hnsw_index
        ORDER BY creation_time DESC
        LIMIT 1
    ''')
    description_index_pickle = c.fetchone()[0]

    c.close()

    return pickle.loads(description_index_pickle)

def load_latest_review_index(conn: sqlite3.Connection) -> hnswlib.Index:
    """
    Loads the latest review index from the database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        hnswlib.Index: The review index.
    """
    logging.debug(f"Loading latest review index from database.")

    c = conn.cursor()
    
    c.execute(f'''
        SELECT pickle
        FROM review_embeddings_hnsw_index
        ORDER BY creation_time DESC
        LIMIT 1
    ''')
    review_index_pickle = c.fetchone()[0]

    c.close()

    return pickle.loads(review_index_pickle)