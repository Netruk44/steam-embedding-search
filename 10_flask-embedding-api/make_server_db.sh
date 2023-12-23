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

echo "Vacuuming database..."
sqlite3 "$1" "VACUUM;"

echo "Database ready to deploy."