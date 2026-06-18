import duckdb
from src.database.schema import get_db_connection

def load_scenes(scenes):
    """
    Inserts parsed scene records into DuckDB
    Uses INSERT OR REPLACE for idempotecy
    """
    conn = get_db_connection()

    for scene in scenes:
        conn.execute("""
            INSERT OR REPLACE INTO scenes VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            scene['token'],
            scene['name'],
            scene['description'],
            scene['nbr_samples'],
            scene['log_token'],
            scene['first_sample_token'],
            scene['last_sample_token']
        ])

    conn.close()
    print(f"Inserted {len(scenes)} scenes into database")

def load_samples(samples):
    """
    Inserts parsed sample records into DuckDB
    Uses INSERT OR REPLACE for idempotecy
    """
    conn = get_db_connection()

    for sample in samples:
        conn.execute("""
            INSERT OR REPLACE INTO samples VALUES (?, ?, ?, ?, ?)
        """, [
            sample['token'],
            sample['scene_token'],
            sample['timestamp'],
            sample['prev'],
            sample['next']
        ])

    conn.close()
    print(f"Inserted {len(samples)} samples into database")

def load_sensor_data(sensor_data):
    """
    Inserts parsed sensor records into DuckDB
    Uses INSERT OR REPLACE for idempotecy
    """
    conn = get_db_connection()

    for sd in sensor_data:
        conn.execute("""
            INSERT OR REPLACE INTO sensor_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            sd['token'],
            sd['sample_token'],
            sd['channel'],
            sd['modality'],
            sd['timestamp'],
            sd['is_key_frame'],
            sd['ego_pose_token'],
            sd['filename']
        ])

    conn.close()
    print(f"Inserted {len(sensor_data)} sensor records into database")

def load_annotations(annotations):
    """
    Inserts parsed annotation records into DuckDB
    Uses INSERT OR REPLACE for idempotecy
    """
    conn = get_db_connection()

    for ann in annotations:
        conn.execute("""
            INSERT OR REPLACE INTO annotations VALUES (?, ?, ?, ?, ?, ?, ?, ?,)
        """, [
            ann['token'],
            ann['sample_token'],
            ann['instance_token'],
            ann['category_name'],
            ann['num_lidar_pts'],
            ann['num_radar_pts'],
            ann['valid_flag'],
            ann['visibility_token'],
        ])

    conn.close()
    print(f"Inserted {len(annotations)} annotations into database")

def load_all(scenes, samples, sensor_data, annotations):
    """
    Runs all four loaders in the correct order.
    Order matters — samples reference scenes, so scenes must exist first.
    """
    print("\nLoading data into DuckDB..")
    load_scenes(scenes)
    load_samples(samples)
    load_sensor_data(sensor_data)
    load_annotations(annotations)

    print("All data loaded successfully!")