FROM python:3.12-slim-bullseye

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /ds

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the ds project files
COPY . .

# Run the script
CMD ["python", "ds_models.py"]