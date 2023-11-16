
#!/bin/bash

# Make sure $1 is set
if [ -z "$1" ]
then
    echo "Please provide a version tag as the first argument"
    exit 1
fi

# Get the version tag from the first argument
version=$1

# Build the Docker image and tag it with the version
docker build -t steamvibes-api:$version .

# Print a message indicating the build is complete
echo "Docker build complete for steamvibes-api:$version"
