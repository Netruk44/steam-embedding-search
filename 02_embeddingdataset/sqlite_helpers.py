import sqlite3
import logging
from typing import List, Optional, Set, Dict
import pickle

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

def check_input_db_tables(conn: sqlite3.Connection) -> bool:
    """
    Checks if the required tables exist in the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        bool: True if the tables exist, False otherwise.
    """
    logging.debug(f"Checking if required tables exist in input SQLite database.")
    required_tables = ["appdetails", "appreviews", "gamelist"]
    
    tables_exist = [check_table(conn, table_name) for table_name in required_tables]
    
    return all(tables_exist)

def check_output_db_tables(conn: sqlite3.Connection) -> bool:
    """
    Checks if the required tables exist in the output SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        bool: True if the tables exist, False otherwise.
    """
    logging.debug(f"Checking if required tables exist in output SQLite database.")
    required_tables = ["description_embeddings", "review_embeddings"]
    
    tables_exist = [check_table(conn, table_name) for table_name in required_tables]
    
    return all(tables_exist)

def create_output_db_tables(conn: sqlite3.Connection):
    """
    Creates the tables in the output SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
    """
    logging.debug("Creating tables in output SQLite database")

    c = conn.cursor()

    c.execute('''
        CREATE TABLE description_embeddings (
            appid INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE review_embeddings (
            recommendationid INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            appid INTEGER NOT NULL
        )
    ''')

    # Add index to appid column in review_embeddings table
    c.execute('''
        CREATE INDEX review_embeddings_appid_index ON review_embeddings (appid)
    ''')

    c.close()

def get_input_appids_with_description(conn: sqlite3.Connection, only_games:bool) -> Set[int]:
    """
    Gets all appids from the input SQLite database that have a description.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        only_games (bool): If True, only return appids for games. If False, return appids for all apps.

    Returns:
        Set[int]: A set of all appids in the input SQLite database that have a description.
    """
    logging.debug("Getting all appids from input SQLite database that have a description")

    c = conn.cursor()

    if only_games:
        c.execute('''
            SELECT appid FROM appdetails WHERE type = 'game'
        ''')
    else:
        c.execute('''
            SELECT appid FROM appdetails
        ''')

    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return set(appids)

def get_output_description_appids(conn: sqlite3.Connection) -> Set[int]:
    """
    Gets all appids from the output SQLite description embedding table.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Set[int]: A set of all appids from the output SQLite description embedding table.
    """
    logging.debug("Getting all appids from output SQLite description embedding table")

    c = conn.cursor()

    c.execute('''
        SELECT appid FROM description_embeddings
    ''')

    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return set(appids)

def get_input_description_for_appid(conn: sqlite3.Connection, appid: int) -> str:
    """
    Gets the description for the given appid from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to get the description for.

    Returns:
        str: The description for the given appid from the input SQLite database.
    """
    logging.debug(f"Getting description for appid {appid} from input SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT storedescription FROM appdetails WHERE appid = ?
    ''', (appid,))
    description = c.fetchone()[0]

    c.close()

    return description

def get_input_appids_for_reviews(conn: sqlite3.Connection) -> Set[int]:
    """
    Gets all appids from the input SQLite database that have reviews.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Set[int]: A set of all appids in the input SQLite database that have reviews.
    """
    logging.debug("Getting all appids from input SQLite database that have reviews")

    c = conn.cursor()

    c.execute('''
        SELECT DISTINCT appid FROM appreviews
    ''')

    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return set(appids)

def get_input_reviews_for_appid(conn: sqlite3.Connection, appid: int) -> Dict[int,str]:
    """
    Gets all reviews for the given appid from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to get reviews for.

    Returns:
        Dict[int,str]: A dictionary of all reviews for the given appid from the input SQLite database.
    """
    logging.debug(f"Getting all reviews for appid {appid} from input SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT recommendationid, review FROM appreviews WHERE appid = ?
    ''', (appid,))
    reviews = {recommendationid: review for recommendationid, review in c.fetchall()}

    c.close()

    return reviews

def get_output_review_recommendationids(conn: sqlite3.Connection) -> Set[int]:
    """
    Gets all recommendationids from the output SQLite review embedding table.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        List[int]: A list of all recommendationids from the output SQLite review embedding table.
    """
    logging.debug("Getting all recommendationids from output SQLite review embedding table")

    c = conn.cursor()

    c.execute('''
        SELECT recommendationid FROM review_embeddings
    ''')

    recommendationids = [recommendationid[0] for recommendationid in c.fetchall()]

    c.close()

    return set(recommendationids)

def insert_description_embeddings(conn: sqlite3.Connection, appid: int, embeddings: List[List[float]]):
    """
    Inserts the description embeddings for the given appid into the output SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid to insert the description embeddings for.
        embeddings (List[List[float]]): A list of description embeddings for the given appid.
    """
    logging.debug(f"Inserting description embeddings for appid {appid} into output SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT INTO description_embeddings (appid, embedding)
        VALUES (?, ?)
    ''', (appid, pickle.dumps(embeddings)))

    conn.commit()
    c.close()

def insert_review_embeddings(conn: sqlite3.Connection, recommendationid: int, embeddings: List[List[float]], appid: int):
    """
    Inserts the review embeddings for the given recommendationid into the output SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        recommendationid (int): The recommendationid to insert the review embeddings for.
        embeddings (List[List[float]]): A list of review embeddings for the given recommendationid.
    """
    logging.debug(f"Inserting review embeddings for recommendationid {recommendationid} into output SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT INTO review_embeddings (recommendationid, embedding, appid)
        VALUES (?, ?, ?)
    ''', (recommendationid, pickle.dumps(embeddings), appid))

    conn.commit()
    c.close()

def get_game_appids_without_description_embeddings(conn: sqlite3.Connection) -> Set[int]:
    """
    Gets all appids from the input SQLite database that do not have description embeddings.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        Set[int]: A set of all appids in the input SQLite database that do not have description embeddings.
    """
    logging.debug("Getting all appids from input SQLite database that do not have description embeddings")

    c = conn.cursor()

    c.execute('''
        SELECT appid FROM appdetails 
        WHERE appid NOT IN (
            SELECT appid FROM description_embeddings
        )
        AND type = 'game'
        AND required_age < 18
    ''')

    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return set(appids)

def get_recommendationids_without_embeddings(conn):
    """
    Gets all recommendationids from the input SQLite database that do not have embeddings.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        List[int]: A list of all recommendationids in the input SQLite database that do not have embeddings.
    """
    logging.debug("Getting all recommendationids from input SQLite database that do not have embeddings")

    c = conn.cursor()

    c.execute('''
        SELECT recommendationid FROM appreviews
        JOIN appdetails USING (appid)
        WHERE recommendationid NOT IN (
            SELECT recommendationid FROM review_embeddings
        ) AND type = 'game'
        AND required_age < 18
    ''')

    recommendationids = [recommendationid[0] for recommendationid in c.fetchall()]

    c.close()

    return recommendationids

def get_review_for_recommendationid(conn: sqlite3.Connection, recommendationid: int) -> str:
    """
    Gets the review for the given recommendationid from the input SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        recommendationid (int): The recommendationid to get the review for.

    Returns:
        str: The review for the given recommendationid from the input SQLite database.
    """
    logging.debug(f"Getting review for recommendationid {recommendationid} from input SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT review FROM appreviews WHERE recommendationid = ?
    ''', (recommendationid,))
    review = c.fetchone()[0]

    c.close()

    return review

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