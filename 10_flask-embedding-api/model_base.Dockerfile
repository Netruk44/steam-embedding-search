
# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

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
# COPY steam_instructor-xl.db /app

# Download database file
RUN python -m wget -o /app/steam_instructor-xl.db https://netrukpub.blob.core.windows.net/$web/steamvibes/server_steam_instructor-xl.db
