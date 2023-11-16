
# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run prepare script
RUN python3 prepare.py

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV TOKENIZERS_PARALLELISM=false

# Run app.py when the container launches
CMD ["python3", "app.py"]
