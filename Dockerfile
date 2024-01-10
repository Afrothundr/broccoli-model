# Use the official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /code

# Copy the requirements file to the working directory
COPY ./requirements.txt /code/requirements.txt

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

# Install the Python dependencies
RUN pip install -r /code/requirements.txt

COPY ./app /code/app

# Run the FastAPI application using uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]