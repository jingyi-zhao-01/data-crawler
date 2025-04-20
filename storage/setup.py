import sqlite3


def setup_tables(db_name: str):
    """Create required tables in the database."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create gpu_models table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gpu_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gpu_model TEXT NOT NULL,
            vram TEXT NOT NULL,
            price REAL
        )
    """
    )

    # Add more table creation statements here if needed

    conn.commit()
    conn.close()


if __name__ == "__main__":
    DB_NAME = "test.db"
    setup_tables(DB_NAME)
    print(f"Tables set up in database: {DB_NAME}")
