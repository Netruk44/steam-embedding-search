import sqlite3
import logging
from typing import List, Optional, Set, Dict, Generator
import pickle

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
    required_tables = ["description_embeddings", "review_embeddings", "gamelist", "appreviews"]
    
    tables_exist = [check_table(conn, table_name) for table_name in required_tables]
    
    return all(tables_exist)


## Data retrieval

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
        SELECT appid FROM appreviews WHERE recommendationid = ?
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

def get_review_appids(conn: sqlite3.Connection) -> Set[int]:
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
        SELECT appid FROM appreviews
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

    ## HACK: Using external table (appreviews) to get appid
    c.execute(f'''
        SELECT review_embeddings.recommendationid, embedding FROM review_embeddings INNER JOIN appreviews USING (recommendationid) WHERE appid = ?
    ''', (appid,))
    results = c.fetchall()

    c.close()

    return {recommendationid: pickle.loads(embedding) for recommendationid, embedding in results}