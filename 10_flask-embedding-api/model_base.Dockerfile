
# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Install c++ build tools (required by hnswlib)
RUN apt-get update && apt-get install -y \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy prepare script and supporting files into the container at /app
COPY config.py /app
COPY instructor_model.py /app
COPY prepare.py /app

# Run prepare script
RUN python3 prepare.py

# Copy database file
COPY server_steam_instructor-xl.db /app/steam_instructor-xl.db

# Download database file
#RUN python -m wget -o /app/steam_instructor-xl.db http://netrukpub.z5.web.core.windows.net/steamvibes/server_steam_instructor-xl.db
