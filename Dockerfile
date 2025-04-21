# Use a Python base image
FROM python:3.10

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies if needed (e.g., for specific libraries)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
# Consider using --no-cache-dir for smaller image size
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the application code into the container
COPY ./app ./app

# Expose the port the app runs on
EXPOSE 8006

# Command to run the application using uvicorn
# Use reload for development, but remove it for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
# Production CMD: CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]