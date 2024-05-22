# Use a lightweight base image
FROM python:3.8-slim

# Install necessary system packages and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    wget \
    git \
    libopencv-dev \
    openssh-client \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

# Install necessary Python packages
RUN pip install --no-cache --upgrade polars pyarrow pandas==1.5.2 numpy scikit-learn==1.3.1 joblib flask gevent requests gunicorn category_encoders==2.6.3

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# Copy serve files to enviroment
COPY serve-files /opt/ml

# Ensure var/log/nginx directory exists
RUN mkdir -p /var/log/nginx

# Set the working directory
WORKDIR /opt/ml

# Define the entry point
ENTRYPOINT ["python3", "serve"]

