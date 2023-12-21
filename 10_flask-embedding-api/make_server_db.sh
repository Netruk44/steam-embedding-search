#!/bin/bash

# Copy the database file and remove table that aren't neccessary
# to run the API.

# Check $1 for database file
if [ -z "$1" ]; then
  echo "Please provide a database file."
  exit 1
fi

# Create output by appending server_ to the front of the filename
output_file="server_$1"

# Copy the database file
cp "$1" "$output_file"

# Remove the unnecessary tables
echo "Removing tables..."
sqlite3 "$output_file" "DROP TABLE appdetails;"
sqlite3 "$output_file" "DROP TABLE appreviews;"
sqlite3 "$output_file" "DROP TABLE lastupdate_appdetails;"
sqlite3 "$output_file" "DROP TABLE lastupdate_appreviews;"

echo "Vacuuming database..."
sqlite3 "$output_file" "VACUUM;"

echo "Done. Database file is $output_file."