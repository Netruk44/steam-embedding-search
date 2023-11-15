import requests
import ratelimit
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import time

# Rate limit the API calls to 200 per 5 minutes / 1 call per 1.5 seconds
@ratelimit.sleep_and_retry
@ratelimit.limits(calls=200, period=300)
def call_api(url, params = {}):
    logging.debug("Calling API: " + url)
    logging.debug("Params: " + str(params))
    time.sleep(1.5) # Sleep for 1.5 seconds to avoid rate limiting
    response = requests.get(url = url, params = params)
    return response.json()

def get_game_list():
    '''
    Returns a list of all games on Steam.

    Returns:
        list: A list of dictionaries containing the appid and name of each game.
    '''
    logging.debug("Getting game list from Steam API")
    url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    response = call_api(url, params = {"format": "json"})
    app_list = response["applist"]["apps"]
    logging.info("Found " + str(len(app_list)) + " games in steam app list.")
    return app_list


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_app_details(appid):
    '''
    Returns a dictionary containing the details of a game on Steam.

    Args:
        appid (int): The appid of the game.

    Returns:
        dict: A dictionary containing the details of the game.
    '''
    logging.debug("Getting details for appid " + str(appid))
    url = "https://store.steampowered.com/api/appdetails"
    response = call_api(url, params = {"appids": appid})
    game_details = response[str(appid)]

    if game_details["success"]:
        return game_details["data"]
    else:
        logging.debug("Failed to get details for appid " + str(appid) + ". Retrying...")
        raise Exception("Failed to get details for appid " + str(appid))

# Source: https://andrew-muller.medium.com/scraping-steam-user-reviews-9a43f9e38c92
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_reviews(appid, params={'json':1}):
    url = f'https://store.steampowered.com/appreviews/{appid}'
    response = call_api(url, params)
    
    if response['success'] == 1:
        return response
    else:
        logging.warning("Failed to get reviews for appid " + str(appid) + ". Retrying...")
        raise Exception("Failed to get reviews for appid " + str(appid))

def get_n_reviews(appid, n=100):
    logging.debug("Getting reviews for appid " + str(appid))
    reviews = []
    cursor = '*'
    params = {
            'json' : 1,
            'filter' : 'all',
            'language' : 'english',
            'review_type' : 'all',
            'purchase_type' : 'all'
            }

    while n > 0:
        params['cursor'] = cursor.encode()
        params['num_per_page'] = min(100, n)
        n -= 100

        response = get_reviews(appid, params)
        cursor = response['cursor']
        reviews += response['reviews']

        if len(response['reviews']) < 100: break

    logging.debug("Found " + str(len(reviews)) + " reviews for appid " + str(appid))
    return reviews