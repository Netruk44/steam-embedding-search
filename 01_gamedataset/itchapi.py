import requests
import ratelimit
import logging
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


# Fetch page from itch.io
# Rate limit to 7 requests per second / 1 request per ~140 milliseconds
@ratelimit.sleep_and_retry
@ratelimit.limits(calls=7, period=1)
def call_api(url, params = {}):
    logging.debug("Calling API: " + url)
    logging.debug("Params: " + str(params))
    response = requests.get(url = url, params = params)
    return response.text


# Fetch games from the newest games page
def get_newest_games(page):
    '''
    Returns a list of all games on itch.io's newest games page.

    Args:
        page (int): The page number to fetch.

    Returns:
        list: A list of dictionaries containing the appid and name of each game.
    '''
    logging.debug("Getting newest games from itch.io API")
    url = "https://itch.io/games/newest.xml"
    response = call_api(url, params = {"page": page})
    soup = BeautifulSoup(response, features='lxml')
    items = soup.find_all('item')

    # Extract the following information from each item:
    # title, plainTitle, link, description, updateDate
    # and also platforms as a list
    games = []
    for item in items:
        game = {}
        game['title'] = item.find('title').text
        game['plainTitle'] = item.find('plaintitle').text
        game['link'] = item.find('link').text
        game['description'] = item.find('description').text
        game['updateDate'] = item.find('updatedate').text
        # game['platforms'] = [platform.name if platform.name is not None else 'html' for platform in item.find('platforms')]
        # not reliable, if game supports html, the platforms list will only contain html regardless of what other platforms it supports
        games.append(game)
    
    return games