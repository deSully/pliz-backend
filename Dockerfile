# Use the official Python image from the Docker Hub
FROM python:3.12.6-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY Pipfile Pipfile.lock /app/
RUN pip install --upgrade pip \
    && pip install pipenv \
    && pipenv install --deploy --ignore-pipfile --verbose
# Copy project
COPY . /app/

# Expose the port the app runs on
EXPOSE 8000

# Run the Django development server
CMD ["pipenv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]