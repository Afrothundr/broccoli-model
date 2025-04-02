# Use the official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /code

# Copy the requirements file to the working directory
COPY ./requirements.txt /code/requirements.txt

RUN apt-get update
# RUN apt-get install ffmpeg libsm6 libxext6 libpq-dev postgresql-client -y
COPY ./app /code/app

# # Install the Python dependencies
# RUN pip install /code/app/en_receipt_model-0.0.1-py3-none-any.whl && pip install -r /code/requirements.txt
# Install the Python dependencies
RUN pip install -r /code/requirements.txt


# Run the FastAPI application using uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]