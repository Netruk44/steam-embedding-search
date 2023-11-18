from steamapi import get_game_list, get_app_details, get_n_reviews
import sqlite_helpers
import tqdm
import logging
import click
import os

COLOR_DARK_GREY = "\x1b[38;5;240m"
COLOR_BOLD = "\x1b[1m"
COLOR_RESET = "\x1b[0m"
LOGGING_FORMAT = COLOR_DARK_GREY + '[%(asctime)s - %(name)s]' + COLOR_RESET + COLOR_BOLD + ' %(levelname)s:' + COLOR_RESET + ' %(message)s'

@click.command()
@click.option('--db', required=True, help='Path to SQLite database to open (or create with --new)')
@click.option('--new', is_flag=True, help='Create a new database instead of updating an existing one')
@click.option('--limit', default=5000, help='Limit the number of appids to update')
@click.option('--update-all', is_flag=True, help='Ignore limit, update all appids')
@click.option('--update-type', default='all', help='Type of appids to update (all, details, reviews)')
@click.option('--verbose', is_flag=True, help='Print verbose output')
def main(db, new, limit, update_all, update_type, verbose):
    logging.basicConfig(format = LOGGING_FORMAT, level = logging.INFO if not verbose else logging.DEBUG)
    
    if update_type not in ["all", "details", "reviews"]:
        logging.error("Invalid update type. Must be one of: all, details, reviews")
        exit(1)

    # Create SQLite database
    if new:
        if os.path.exists(db):
            logging.error(f"Output SQLite database {db} already exists")
            exit(1)
        conn = sqlite_helpers.create_connection(db)
        sqlite_helpers.create_tables(conn)
    else:
        if not os.path.exists(db):
            logging.error(f"Input SQLite database {db} does not exist")
            exit(1)

        conn = sqlite_helpers.create_connection(db)
        if not sqlite_helpers.check_tables(conn):
            sqlite_helpers.create_tables(conn)

    # Update game list
    gamelist = get_game_list()
    known_appids = set(sqlite_helpers.get_known_appids(conn))
    new_gamelist = [game for game in gamelist if game["appid"] not in known_appids]
    logging.info("Found " + str(len(new_gamelist)) + " new games on Steam.")
    sqlite_helpers.insert_gamelist(conn, new_gamelist)

    if update_all:
        limit = len(gamelist)

    appids_to_update_details = sqlite_helpers.get_appdetails_to_update(conn, count = limit)
    
    # Update app details
    if update_type == "all" or update_type == "details":
        bar = tqdm.tqdm(appids_to_update_details, desc = "Updating app details", smoothing = 0.0)
        for appid in bar:
            bar.set_postfix(appid=str(appid))
            try:
                appdetails = get_app_details(appid)
                sqlite_helpers.insert_appdetails(conn, appid, appdetails)
            except KeyboardInterrupt:
                raise
            except:
                logging.warning("Failed to get app details for appid " + str(appid) + ". Skipping...")
                continue
            finally:
                sqlite_helpers.mark_appdetails_updated(conn, appid)


    # Update app reviews
    if update_type == "all" or update_type == "reviews":
        appids_to_update_reviews = sqlite_helpers.get_appreviews_to_update(conn, output_count = limit)

        bar = tqdm.tqdm(appids_to_update_reviews, desc = "Getting app reviews", smoothing = 0.0)
        for appid in bar:
            bar.set_postfix(appid=str(appid))

            try:
                known_reviews = sqlite_helpers.get_appreview_recommendationids(conn, appid)
                appreviews = get_n_reviews(appid, n = 100)
                new_appreviews = [review for review in appreviews if int(review["recommendationid"]) not in known_reviews]
                logging.debug("Found " + str(len(new_appreviews)) + " new reviews for appid " + str(appid) + ".")
                sqlite_helpers.insert_appreviews(conn, appid, new_appreviews)
            finally:
                sqlite_helpers.mark_appreviews_updated(conn, appid)

    conn.close()

if __name__ == "__main__":
    main()
