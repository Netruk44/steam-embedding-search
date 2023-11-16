
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
RUN python -m wget -o /app/steam_instructor-xl.db http://netrukpub.z5.web.core.windows.net/steamvibes/steam_instructor-xl.db

# Copy all the other python scripts into the container at /app
COPY *.py /app/

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV TOKENIZERS_PARALLELISM=false

# Run app.py when the container launches
#CMD ["python3", "app.py"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
