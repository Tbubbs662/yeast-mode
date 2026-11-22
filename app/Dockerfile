FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .