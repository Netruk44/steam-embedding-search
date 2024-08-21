#!/bin/bash

# Copy the database file and remove table that aren't neccessary
# to run the API.

# Check $1 for database file
if [ -z "$1" ]; then
  echo "Please provide a database file."
  exit 1
fi

# Prompt user to confirm database file
echo "Database file: $1"
read -p "Is this the correct database file to remove tables from? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^Y$ ]]; then
  echo "Exiting..."
  exit 1
fi

# Remove the unnecessary tables
echo "Removing tables..."

echo " - appdetails..."
sqlite3 "$1" "DROP TABLE appdetails;"

echo " - appreviews..."
sqlite3 "$1" "DROP TABLE appreviews;"

echo " - lastupdate_appdetails..."
sqlite3 "$1" "DROP TABLE lastupdate_appdetails;"

echo " - lastupdate_appreviews..."
sqlite3 "$1" "DROP TABLE lastupdate_appreviews;"


# Remove unnecessary indexes
echo "Removing old hnsw indexes..."

echo " - description_embeddings_hnsw_index..."
sqlite3 "$1" "DELETE FROM description_embeddings_hnsw_index WHERE creation_time < (SELECT MAX(creation_time) FROM description_embeddings_hnsw_index);"

echo " - review_embeddings_hnsw_index..."
sqlite3 "$1" "DELETE FROM review_embeddings_hnsw_index WHERE creation_time < (SELECT MAX(creation_time) FROM review_embeddings_hnsw_index);"

echo " - mixed_embeddings_hnsw_index..."
sqlite3 "$1" "DELETE FROM mixed_embeddings_hnsw_index WHERE creation_time < (SELECT MAX(creation_time) FROM mixed_embeddings_hnsw_index);"


echo "Vacuuming database..."
sqlite3 "$1" "VACUUM;"

echo "Database ready to deploy."