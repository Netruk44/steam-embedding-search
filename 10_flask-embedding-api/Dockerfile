
# Use an official Python runtime as a parent image
FROM steamvibes-api-base:v0.4.1
#FROM netruk44.azurecr.io/steamvibes-api-base:latest

# Set the working directory to /app
WORKDIR /app

# Copy all the other python scripts into the container at /app
COPY *.py /app/

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV TOKENIZERS_PARALLELISM=false

# Run app.py when the container launches
#CMD ["python3", "app.py"]
#CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--log-file", "-", "--log-level", "debug", "--timeout", "120", "app:app"]
