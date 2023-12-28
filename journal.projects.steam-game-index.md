---
id: upk1346sjovht5vd99icif4
title: Steam Game Index
desc: ''
updated: 1699844933806
created: 1699842923436
---

## Idea Overview

Search through steam games in natural language.

## Outline

### Phase 0
> *Does this work at all?*

* [X] Find API for steam game store
    * Or figure out how to use beautiful soup to scrape the store
    * Game title
    * Store description (long)
    * Maybe top 10 reviews if possible?
        * Or possibly take the top X and use the longest 10
    * **(IMPORTANT) RESULT**: API is limited to 200 requests per 5 minutes
        * Or 1 request every 1.5 seconds
    * **RESULT**: `https://store.steampowered.com/api/appdetails?appids=<app_id>`
        * Unofficial/unsupported API
        * Returns a json object with:
        * `obj[<app_id>]['data']['name']` - Name
        * `obj[<app_id>]['data']['detailed_description']` - Description
    * **RESULT**: `https://store.steampowered.com/appreviews/<app_id>?json=1[&cursor=<cursor>]`
        * [Documentation](https://partner.steamgames.com/doc/store/getreviews)
        * Returns a json object with:
        * `reviews[0]['review']` - Review text
        * `cursor` - Used for pagination
            * Will need to make multiple requests to get more than 20 reviews at a time
    * **RESULT**: `http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json` - List of all games
        * [Documentation](https://partner.steamgames.com/doc/webapi/ISteamApps#GetAppList)
        * Returns a (~10 MB) json object with:
        * `obj['applist']['apps'][<index>]['appid']` - App id
        * `obj['applist']['apps'][<index>]['name']` - Name
* [X] Process API inputs into some kind of "source truth" document
    * Basically just a reflection of what the API returned
    * Probably stored in some kind of database
    * Or possibly just a bunch of json files on disk
    * **TODO**: Extract out common data into a base class
        - Add SteamGame class
        - Maybe add ItchIoGame class?
        - And other stores.
* [X] Create embeddings for description and reviews
    * Using separate embedding instructions, embed store description and reviews
        * "Represent a video game that has a description of: "
        * "Represent a video game that has a review of: "
* [X] **Test** Query the embeddings for a game
    * "Represent a video game with the description of: "
    * Evaluate to see if I want to continue with the project

### Phase 1
> *Make it usable for literally anyone other than me*

**Idea**: Make a web app people can use to search through the dataset.

* [X] Create an Azure Function / Web App API for
    * [ ] ~~Generating an embedding for a query~~
    * [X] Querying the database for games that match a given query
* [X] Create a web interface for querying the dataset
    * Is it possible to run database search on client?
    * [X] Deploy

### Future
*Pending*
* [X] Create ~~FAISS~~ hnsw index for dataset
* [ ] Publicize
    * [X] Create blog post
    * [X] Post to some website
        * Posted, nobody cared lol
* [X] Similar games
    * Given a game, use embeddings and compare to other games to find most similar
* [ ] Specify distance algorithm
    * Cosine similarity
    * Euclidean distance
    * Dot product
* [ ] Research: Check embedding magnitudes
    * Does query length affect magnitude?
* [X] Add appid column to review_embeddings table
    * Add index
* [ ] Research: Investigate different questions
    * Which games have descriptions that most closely match their reviews?
    * Which game descriptions are least similar to their reviews?
    * Which games have the most similar reviews?
    * Which games have the most different reviews?
    * Which games have the most similar descriptions?
    * Are there any games that have a review that is more similar to another game's description than its own description?
* [ ] 10_flask_api: Replace python wget with wget from apt
    * Python version of wget is like, 8 years old and probably awfully insecure...
* [ ] 11_react_frontend: Add a "system status" indicator.
    * Have status.txt file uploaded to azure storage somwhere (Hot tier)
    * Fetch status.txt from frontend
    * Display contents of status.txt in a status indicator


### Itch.io

* Any store listing page can be made into an api call by adding `.xml?page=<page_number>`.
    * Example: `https://itch.io/games/newest.xml?page=2`
* Rate limit (according to (the go itchio library)[https://github.com/itchio/go-itchio/blob/master/rate_limiter.go]) is 8 req/s with burst of ~15.
    * Or 1 request every 125ms.