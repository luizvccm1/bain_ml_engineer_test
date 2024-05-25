# Use a lightweight base image
FROM python:3.8-slim

# Install nginx
RUN apt-get update && apt-get install -y nginx

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case.
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE

# Copy serve files, requirements and configuration.json to enviroment
COPY serve-files /api
COPY requirements.txt .
# COPY ../../aws_cloudformation/configuration.json /api

# List files in the /app directory
RUN echo "Listing files after copying requirements.txt:" && ls -la /api

# Install necessary Python packages
RUN pip install --verbose --no-cache-dir -r requirements.txt

# Verify that the packages are installed correctly
RUN pip list

# Set the working directory
WORKDIR /api

# Expose th api port
EXPOSE 4200

# Define the entry point
ENTRYPOINT ["python", "serve"]