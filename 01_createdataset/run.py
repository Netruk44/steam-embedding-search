from steamapi import get_game_list, get_app_details, get_n_reviews
import sqlite3
import tqdm
import logging
import json
import random

COLOR_DARK_GREY = "\x1b[38;5;240m"
COLOR_BOLD = "\x1b[1m"
COLOR_RESET = "\x1b[0m"
LOGGING_FORMAT = COLOR_DARK_GREY + '[%(asctime)s - %(name)s]' + COLOR_RESET + COLOR_BOLD + ' %(levelname)s:' + COLOR_RESET + ' %(message)s'
logging.basicConfig(format = LOGGING_FORMAT, level = logging.INFO)

## SQLite functions

def create_connection(db_file = "steam.db"):
    '''
    Creates a connection to the SQLite database.

    Args:
        db_file (str): The path to the SQLite database.

    Returns:
        sqlite3.Connection: A connection to the SQLite database.
    '''
    logging.debug("Creating connection to SQLite database")
    return sqlite3.connect(db_file)

def check_tables(conn):
    '''
    Checks if the tables exist in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        bool: True if the tables exist, False otherwise.
    '''
    logging.debug("Checking if tables exist in SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='gamelist'
    ''')
    gamelist_exists = c.fetchone()[0] == 1

    c.execute('''
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='appdetails'
    ''')
    appdetails_exists = c.fetchone()[0] == 1

    c.execute('''
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='appreviews'
    ''')
    appreviews_exists = c.fetchone()[0] == 1

    c.close()

    return gamelist_exists and appdetails_exists and appreviews_exists

def create_tables(conn):
    '''
    Creates the tables in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
    '''
    logging.debug("Creating tables in SQLite database")

    c = conn.cursor()

    # Create table 'gamelist'
    c.execute('''
        CREATE TABLE IF NOT EXISTS gamelist (
            datajson TEXT,
            appid INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')

    # Create table 'appdetails'
    c.execute('''
        CREATE TABLE IF NOT EXISTS appdetails (
            datajson TEXT,
            appid INTEGER PRIMARY KEY,
            storedescription TEXT
        )
    ''')

    # Create table 'appreviews'
    c.execute('''
        CREATE TABLE IF NOT EXISTS appreviews (
            datajson TEXT,
            recommendationid INTEGER PRIMARY KEY,
            appid INTEGER,
            review TEXT,
            FOREIGN KEY(appid) REFERENCES gamelist(appid)
        )
    ''')

    conn.commit()
    c.close()

def insert_gamelist(conn, gamelist):
    '''
    Inserts a list of games into the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        gamelist (list): A list of dictionaries containing the appid and name of each game.
    '''
    logging.debug("Inserting gamelist into SQLite database")

    c = conn.cursor()

    for game in tqdm.tqdm(gamelist):
        c.execute('''
            INSERT OR IGNORE INTO gamelist (datajson, appid, name)
            VALUES (?, ?, ?)
        ''', (json.dumps(game), game["appid"], game["name"]))

    conn.commit()
    c.close()

def get_known_appids(conn):
    '''
    Returns a list of all appids in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        list: A list of all appids in the SQLite database.
    '''
    logging.debug("Getting all appids from SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT appid FROM gamelist
    ''')
    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return appids

def insert_appdetails(conn, appid, appdetails):
    '''
    Inserts a list of games into the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appdetails (list): A list of dictionaries containing the details of each game.
    '''
    logging.debug("Inserting appdetails into SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT OR IGNORE INTO appdetails (datajson, appid, storedescription)
        VALUES (?, ?, ?)
    ''', (json.dumps(appdetails), appid, appdetails["detailed_description"]))

    conn.commit()
    c.close()

def appdetails_exists(conn, appid):
    '''
    Checks if the appdetails for a game exist in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid of the game.

    Returns:
        bool: True if the appdetails exist, False otherwise.
    '''
    logging.debug("Checking if appdetails for appid " + str(appid) + " exist in SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT count(*) FROM appdetails WHERE appid = ?
    ''', (appid,))
    appdetails_exist = c.fetchone()[0] == 1

    c.close()

    return appdetails_exist

def insert_appreviews(conn, appid, appreviews):
    '''
    Inserts a list of reviews for a game into the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid of the game.
        appreviews (list): A list of dictionaries containing the reviews of the game.
    '''
    logging.debug("Inserting appreviews for appid " + str(appid) + " into SQLite database")

    c = conn.cursor()

    for review in appreviews:
        c.execute('''
            INSERT OR IGNORE INTO appreviews (datajson, recommendationid, appid, review)
            VALUES (?, ?, ?, ?)
        ''', (json.dumps(review), review["recommendationid"], appid, review["review"]))

    conn.commit()
    c.close()

def get_appreviews(conn, appid):
    '''
    Returns a list of all recommendationids for a game in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid of the game.

    Returns:
        list: A list of all recommendationids for a game in the SQLite database.
    '''
    logging.debug("Getting all recommendationids for appid " + str(appid) + " from SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT recommendationid FROM appreviews WHERE appid = ?
    ''', (appid,))
    recommendationids = [recommendationid[0] for recommendationid in c.fetchall()]

    c.close()

    return recommendationids

## Main function

def main():
    # Create SQLite database
    conn = create_connection()

    if not check_tables(conn):
        create_tables(conn)

    # Update game list
    gamelist = get_game_list()
    known_appids = set(get_known_appids(conn))
    new_gamelist = [game for game in gamelist if game["appid"] not in known_appids]
    logging.info("Found " + str(len(new_gamelist)) + " new games on Steam.")
    insert_gamelist(conn, new_gamelist)


    # Random subset
    limit = None # Do not comment out
    limit = 5000

    if limit != None:
        random.shuffle(gamelist)
        gamelist = gamelist[:limit]
    
    # Update app details
    for game in tqdm.tqdm(gamelist, desc = "Updating app details"):
        appid = game["appid"]
        if not appdetails_exists(conn, appid):
            try:
                appdetails = get_app_details(appid)
                insert_appdetails(conn, appid, appdetails)
            except KeyboardInterrupt:
                raise
            except:
                logging.warning("Failed to get app details for appid " + str(appid) + ". Skipping...")
                continue
        else:
            logging.debug("App details for appid " + str(appid) + " already exist in SQLite database. Skipping...")

    # Get app reviews
    for game in tqdm.tqdm(gamelist, desc = "Updating app reviews"):
        appid = game["appid"]
        known_reviews = set(get_appreviews(conn, appid))

        if len(known_reviews) < 100:
            appreviews = get_n_reviews(appid, n = 100)
            new_appreviews = [review for review in appreviews if int(review["recommendationid"]) not in known_reviews]
            logging.info("Found " + str(len(new_appreviews)) + " new reviews for appid " + str(appid) + ".")
            insert_appreviews(conn, appid, new_appreviews)

    conn.close()

if __name__ == "__main__":
    main()
