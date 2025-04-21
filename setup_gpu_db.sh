#!/bin/bash

# Script to set up the GPU prices database

# Start the PostgreSQL container
echo "Starting PostgreSQL container..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Install required Python package if not already installed
pip install psycopg2-binary

# Set up the database tables
echo "Setting up database tables..."
python setup_db.py --with-mock-data

echo "Database setup complete!"
echo "You can now query the database using: python query_gpu_prices.py"