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
            storedescription TEXT,
            type TEXT
        )
    ''')

    # Add index to 'appdetails' for type
    c.execute('''
        CREATE INDEX IF NOT EXISTS appdetails_type_index ON appdetails(type)
    ''')

    # Create table 'lastupdate_appdetails'
    c.execute('''
        CREATE TABLE IF NOT EXISTS lastupdate_appdetails (
            appid INTEGER PRIMARY KEY,
            lastupdate INTEGER
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

    # Add index to 'appreviews' for appid
    c.execute('''
        CREATE INDEX IF NOT EXISTS appreviews_appid_index ON appreviews(appid)
    ''')

    # Create table 'lastupdate_appreviews'
    c.execute('''
        CREATE TABLE IF NOT EXISTS lastupdate_appreviews (
            appid INTEGER PRIMARY KEY,
            lastupdate INTEGER
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

def get_appids_with_appdetails(conn):
    '''
    Returns a list of all appids with app details in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        list: A list of all appids with app details in the SQLite database.
    '''
    logging.debug("Getting all appids with app details from SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT appid FROM appdetails
    ''')
    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return appids

def get_appids_with_reviews(conn):
    '''
    Returns a list of all appids with reviews in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.

    Returns:
        list: A list of all appids with reviews in the SQLite database.
    '''
    logging.debug("Getting all appids with reviews from SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT DISTINCT appid FROM appreviews
    ''')
    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return appids

def get_appids_with_low_number_of_reviews(conn, min_reviews = 100):
    '''
    Returns a list of all appids with less than a certain number of reviews in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        min_reviews (int): The minimum number of reviews.

    Returns:
        list: A list of all appids with less than a certain number of reviews in the SQLite database.
    '''
    logging.debug("Getting all appids with less than " + str(min_reviews) + " reviews from SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT appdetails.appid, count(appreviews.appid) as review_count
        FROM appdetails
        LEFT JOIN appreviews ON appdetails.appid = appreviews.appid
        GROUP BY appdetails.appid
        HAVING review_count < ?
    ''', (min_reviews,))
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
        INSERT OR IGNORE INTO appdetails (datajson, appid, storedescription, type)
        VALUES (?, ?, ?, ?)
    ''', (json.dumps(appdetails), appid, appdetails["detailed_description"], appdetails["type"]))

    conn.commit()
    c.close()

def mark_appdetails_updated(conn, appid):
    '''
    Marks the appdetails for a game as updated in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid of the game.
    '''
    logging.debug("Marking appdetails for appid " + str(appid) + " as updated in SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT OR IGNORE INTO lastupdate_appdetails (appid, lastupdate)
        VALUES (?, NULL)
    ''', (appid,))

    c.execute('''
        UPDATE lastupdate_appdetails
        SET lastupdate = CAST(strftime('%s', 'now') AS INTEGER)
        WHERE appid = ?
    ''', (appid,))

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

def mark_appreviews_updated(conn, appid):
    '''
    Marks the appreviews for a game as updated in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        appid (int): The appid of the game.
    '''
    logging.debug("Marking appreviews for appid " + str(appid) + " as updated in SQLite database")

    c = conn.cursor()

    c.execute('''
        INSERT OR IGNORE INTO lastupdate_appreviews (appid, lastupdate)
        VALUES (?, NULL)
    ''', (appid,))

    c.execute('''
        UPDATE lastupdate_appreviews
        SET lastupdate = CAST(strftime('%s', 'now') AS INTEGER)
        WHERE appid = ?
    ''', (appid,))

    conn.commit()
    c.close()

def get_appreview_recommendationids(conn, appid):
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

def get_appdetails_to_update(conn, count=100):
    '''
    Returns a list of appids that need updating in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        count (int): The number of appids to return.

    Returns:
        list: A list of appids that do not exist in appdetails, ordered by least recently updated.
    '''
    logging.debug("Getting " + str(count) + " appids to update from SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT gamelist.appid 
        FROM gamelist
        LEFT JOIN lastupdate_appdetails ON gamelist.appid = lastupdate_appdetails.appid
        LEFT JOIN appdetails ON gamelist.appid = appdetails.appid
        WHERE appdetails.appid IS NULL              -- appdetails do not exist in the DB
        ORDER BY IFNULL(lastupdate, 0) ASC,         -- order by least recently updated
                random() ASC                        -- randomize order of appids that have not been updated
        LIMIT ?
    ''', (count,))
    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return appids

def get_appreviews_to_update(conn, minimum_review_count = 100, output_count=100):
    '''
    Returns a list of appids that need updating in the SQLite database.

    Args:
        conn (sqlite3.Connection): A connection to the SQLite database.
        count (int): The number of appids to return.

    Returns:
        list: A list of appids that do not exist in appreviews, ordered by least recently updated.
    '''
    logging.debug("Getting " + str(output_count) + " appids to update from SQLite database")

    c = conn.cursor()

    c.execute('''
        SELECT gamelist.appid 
        FROM gamelist
        LEFT JOIN lastupdate_appreviews ON gamelist.appid = lastupdate_appreviews.appid
        LEFT JOIN (
            SELECT appid, count(appid) as review_count
            FROM appreviews
            GROUP BY appid
        ) AS review_count ON gamelist.appid = review_count.appid
        WHERE IFNULL(review_count.review_count, 0) < ?      -- app has less than minimum_review_count reviews
        ORDER BY IFNULL(lastupdate, 0) ASC,                 -- order by least recently updated
              random() ASC                                  -- randomize order of appids that have not been updated
        LIMIT ?
    ''', (minimum_review_count, output_count))
    appids = [appid[0] for appid in c.fetchall()]

    c.close()

    return appids

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

    # Take subset
    limit = None # Do not comment out
    limit = 5000

    appids_to_update_details = get_appdetails_to_update(conn, count = limit)
    
    # Update app details
    bar = tqdm.tqdm(appids_to_update_details, desc = "Updating app details", smoothing = 0.0)
    for appid in bar:
        bar.set_postfix(appid=str(appid))
        try:
            appdetails = get_app_details(appid)
            insert_appdetails(conn, appid, appdetails)
        except KeyboardInterrupt:
            raise
        except:
            logging.warning("Failed to get app details for appid " + str(appid) + ". Skipping...")
            continue
        finally:
            mark_appdetails_updated(conn, appid)


    # Update app reviews
    appids_to_update_reviews = get_appreviews_to_update(conn, output_count = limit)

    bar = tqdm.tqdm(appids_to_update_reviews, desc = "Getting app reviews", smoothing = 0.0)
    for appid in bar:
        bar.set_postfix(appid=str(appid))

        try:
            appreviews = get_n_reviews(appid, n = 100)
            new_appreviews = [review for review in appreviews if int(review["recommendationid"]) not in known_reviews]
            logging.debug("Found " + str(len(new_appreviews)) + " new reviews for appid " + str(appid) + ".")
            insert_appreviews(conn, appid, new_appreviews)
        finally:
            mark_appreviews_updated(conn, appid)

    conn.close()

if __name__ == "__main__":
    main()
