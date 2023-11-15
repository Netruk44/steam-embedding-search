
# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Copy sqlite database from parent directory into the container at /app
COPY ../steam_instructor-xl.db /app/steam_instructor-xl.db

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
#ENV NAME World

# Run app.py when the container launches
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=80"]

