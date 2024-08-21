import sqlite3
import logging
from typing import List, Optional, Set, Dict, Iterator, Tuple
import pickle
import hnswlib

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

def check_all_tables_exist(conn: sqlite3.Connection, tables: List[str]) -> bool:
    """
    Checks if all tables exist in the SQLite database.

    Args:
        tables (List[str]): A list of table names to check for.
    
    Returns:
        bool: True if all tables exist, False otherwise.
    """
    
    return all([check_table(conn, table) for table in tables])

def create_output_db_tables(conn: sqlite3.Connection):
    """
    Creates the output tables in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
    """
    logging.debug("Creating output tables in SQLite database")

    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS description_embeddings_hnsw_index (
            index_id INTEGER PRIMARY KEY,
            creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pickle BLOB NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS review_embeddings_hnsw_index (
            index_id INTEGER PRIMARY KEY,
            creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pickle BLOB NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS mixed_embeddings_hnsw_index (
            index_id INTEGER PRIMARY KEY,
            creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pickle BLOB NOT NULL
        )
    ''')

    conn.commit()
    c.close()

def remove_old_indexes(conn: sqlite3.Connection):
    """
    Removes old indexes from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
    """
    logging.debug("Removing old indexes from SQLite database")

    c = conn.cursor()

    c.execute('''
        DELETE FROM description_embeddings_hnsw_index
        WHERE index_id NOT IN (
            SELECT index_id 
            FROM description_embeddings_hnsw_index 
            ORDER BY creation_time DESC 
            LIMIT 1
        )
    ''')
    logging.debug(f"Removed {c.rowcount} old description indexes")

    c.execute('''
        DELETE FROM review_embeddings_hnsw_index
        WHERE index_id NOT IN (
            SELECT index_id 
            FROM review_embeddings_hnsw_index 
            ORDER BY creation_time DESC 
            LIMIT 1
        )
    ''')
    logging.debug(f"Removed {c.rowcount} old review indexes")

    conn.commit()
    c.close()

def add_description_index(conn: sqlite3.Connection, index: hnswlib.Index):
    """
    Adds a description index to the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        index (hnswlib.Index): The index to add.
    """
    logging.debug("Adding description index to SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT INTO description_embeddings_hnsw_index (pickle)
        VALUES (?)
    ''', (pickle.dumps(index),))

    conn.commit()
    c.close()

def add_review_index(conn: sqlite3.Connection, index: hnswlib.Index):
    """
    Adds a review index to the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        index (hnswlib.Index): The index to add.
    """
    logging.debug("Adding review index to SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT INTO review_embeddings_hnsw_index (pickle)
        VALUES (?)
    ''', (pickle.dumps(index),))

    conn.commit()
    c.close()

def add_mixed_index(conn: sqlite3.Connection, index: hnswlib.Index):
    """
    Adds a mixed index to the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        index (hnswlib.Index): The index to add.
    """
    logging.debug("Adding mixed index to SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT INTO mixed_embeddings_hnsw_index (pickle)
        VALUES (?)
    ''', (pickle.dumps(index),))

    conn.commit()
    c.close()

def get_any_description_embeddings_list(conn: sqlite3.Connection) -> List[List[float]]:
    """
    Gets the first description embeddings list from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        List[List[float]]: The description embeddings list.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT embedding FROM description_embeddings LIMIT 1
    ''')
    results = c.fetchone()[0]

    c.close()

    return pickle.loads(results)

def get_count_appids_with_description_embeddings(conn: sqlite3.Connection) -> int:
    """
    Gets the number of appids with description embeddings from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        int: The number of appids with description embeddings.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT COUNT(DISTINCT appid) FROM description_embeddings
    ''')
    results = c.fetchone()[0]

    c.close()

    return results

def get_count_appids_with_review_embeddings(conn: sqlite3.Connection) -> int:
    """
    Gets the number of appids with review embeddings from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        int: The number of appids with review embeddings.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT COUNT(DISTINCT appid) FROM review_embeddings
    ''')
    results = c.fetchone()[0]

    c.close()

    return results

def get_count_appids_with_description_or_review_embeddings(conn: sqlite3.Connection) -> int:
    """
    Gets the number of appids with either description or review embeddings from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        int: The number of appids with either description or review embeddings.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT COUNT(DISTINCT appid) FROM (
            SELECT appid FROM description_embeddings
            UNION
            SELECT appid FROM review_embeddings
        )
    ''')

    results = c.fetchone()[0]

    c.close()

    return results

def get_description_embeddings_batch(conn: sqlite3.Connection, page_size: int = 1000) -> Iterator[List[Tuple[int, List[List[float]]]]]:
    """
    Gets a generator for description embeddings in batches.

    Args:
        page_size (int): The size of each batch.

    Returns:
        Iterator[List[Tuple[int, List[float]]]]: A generator for description embeddings in batches.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT appid, embedding FROM description_embeddings
    ''')

    while True:
        results = c.fetchmany(page_size)

        if not results:
            break

        yield [(appid, pickle.loads(embedding)) for appid, embedding in results]

    c.close()

def get_appids_with_review_embeddings(conn: sqlite3.Connection) -> List[int]:
    """
    Gets the appids with reviews from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Set[int]: The appids with reviews.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT DISTINCT appid FROM review_embeddings
    ''')
    results = c.fetchall()

    c.close()

    return [appid for appid, in results]

def get_appids_with_description_embeddings(conn: sqlite3.Connection) -> List[int]:
    """
    Gets the appids with descriptions from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Set[int]: The appids with descriptions.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT DISTINCT appid FROM description_embeddings
    ''')
    results = c.fetchall()

    c.close()

    return [appid for appid, in results]

def get_review_embeddings_for_appid(conn: sqlite3.Connection, appid: int) -> Dict[int, List[List[List[float]]]]:
    """
    Gets the review embeddings for an appid from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to get the review embeddings for.

    Returns:
        Dict[str, List[List[float]]]: The review embeddings for the appid.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT recommendationid, embedding FROM review_embeddings
        WHERE appid = ?
    ''', (appid,))
    results = c.fetchall()

    c.close()

    return {recommendationid: pickle.loads(embedding) for recommendationid, embedding in results}

def get_description_embeddings_for_appid(conn: sqlite3.Connection, appid: int) -> List[List[float]]:
    """
    Gets the description embeddings for an appid from the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to get the description embeddings for.

    Returns:
        List[List[float]]: The description embeddings for the appid.
    """

    c = conn.cursor()

    c.execute(f'''
        SELECT embedding FROM description_embeddings
        WHERE appid = ?
    ''', (appid,))
    results = c.fetchall()

    c.close()

    if len(results) == 0:
        return []
    #    raise ValueError(f'No review embeddings found for appid {appid}')

    #return [pickle.loads(embedding) for embedding, in results]
    embedding, = results[0]
    return pickle.loads(embedding)