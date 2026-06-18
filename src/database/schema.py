import duckdb
import os
from config import DATA_PROCESSED_DIR

def get_db_connection():
    """
    Creates or connects to our DuckDB database file
    DuckDB stores everything in a single file .db file - no server needed
    """

    db_path = os.path.join(DATA_PROCESSED_DIR, "physicalflow.db")
    return duckdb.connect(db_path)

def create_schema():
    """
    Creates all tables in DuckDB.
    Uses CREATE TABLE IF NOT EXISTS - safe to run multiple times.
    """

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scenes (
                token VARCHAR PRIMARY KEY,
                name VARCHAR,
                description VARCHAR,
                nbr_samples INTEGER,
                log_token VARCHAR,
                first_sample_token VARCHAR,
                last_sample_token VARCHAR
            )
        """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS samples (
                token VARCHAR PRIMARY KEY,
                scene_token VARCHAR,
                timestamp BIGINT,
                prev VARCHAR,
                next VARCHAR
            )
        """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
                token VARCHAR PRIMARY KEY,
                sample_token VARCHAR,
                channel VARCHAR,
                modality VARCHAR,
                timestamp BIGINT,
                is_key_frame BOOLEAN,
                ego_pose_token VARCHAR,
                filename VARCHAR
            )
        """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS annotations (
                token VARCHAR PRIMARY KEY,
                sample_token VARCHAR,
                instance_token VARCHAR,
                category_name VARCHAR,
                num_lidar_pts INTEGER,
                num_radar_pts INTEGER,
                valid_flag BOOLEAN,
                visibility_token VARCHAR
            )
        """)
    conn.close()
    print("Database schema created successfully.")