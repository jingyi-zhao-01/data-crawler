# GPU Prices Database Setup

This document explains how to set up and use the PostgreSQL database for storing GPU price data.

## Prerequisites

- Docker and Docker Compose
- Python 3.6+
- psycopg2 Python package

## Installation

Install the required Python package:

```bash
pip install psycopg2-binary
```

## Starting the Database

To start the PostgreSQL database using Docker Compose:

```bash
docker-compose up -d
```

This will start a PostgreSQL instance with the following configuration:
- Host: localhost
- Port: 5432
- Database: gpu_prices
- Username: postgres
- Password: postgres

## Setting Up the Database

To create the necessary tables:

```bash
python setup_db.py
```

To create tables and populate with mock data:

```bash
python setup_db.py --with-mock-data
```

## Configuration

The database connection is configurable through environment variables:

### Development (Docker Compose)

No configuration needed - defaults will connect to the local Docker container.

### Custom Configuration

You can customize individual connection parameters:

```bash
export DB_HOST=custom-host
export DB_PORT=5432
export DB_NAME=custom-db-name
export DB_USER=custom-user
export DB_PASSWORD=custom-password
python setup_db.py
```

### Production

For production, set the `POSTGRES_URL` environment variable:

```bash
export POSTGRES_URL=postgresql://user:password@hostname:port/database
python setup_db.py
```

## Using in Your Application

Import the configuration module to get connection details:

```python
from db_config import get_connection_string

# Get connection string based on environment
conn_string = get_connection_string()

# Use with psycopg2
import psycopg2
conn = psycopg2.connect(conn_string)
```

## Database Schema

The database contains the following table:

### gpu_prices

| Column      | Type           | Description                    |
|-------------|----------------|--------------------------------|
| id          | SERIAL         | Primary key                    |
| gpu_model   | VARCHAR(100)   | GPU model name                 |
| vram_gb     | VARCHAR(10)    | VRAM size in GB                |
| price_usd   | NUMERIC(10, 2) | Price in USD (can be NULL)     |
| created_at  | TIMESTAMP      | Record creation timestamp      |