from src.database.schema import get_db_connection
from config import TIMESTAMP_SYNC_THRESHOLD_MS, CAPTURE_FREQUENCY_HZ

def check_frame_completeness():
    """
    For each scene, compares actual sample count to expected count
    Excpected = scene duration in seconds * capture frequency (2Hz)
    Returns a list of dicts, one per scene
    """

    conn = get_db_connection()
    query = """
        SELECT
            s.token AS scene_token,
            s.nbr_samples AS actual_samples,
            MIN(sm.timestamp) AS start_time,
            MAX(sm.timestamp) AS end_time
        FROM scenes s
        JOIN samples sm ON sm.scene_token = s.token
        GROUP BY s.token, s.nbr_samples
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    results = []
    for scene_token, actual_samples, start_time, end_time in rows:
        duration_seconds = (end_time - start_time) / 1_000_000  # Convert microseconds to seconds
        expected_samples = duration_seconds * CAPTURE_FREQUENCY_HZ
        results.append({
            'scene_token': scene_token,
            'actual_samples': actual_samples,
            'expected_samples': expected_samples,
            'duration_seconds': duration_seconds
        })

    return results

"""
This is the old function - we had to change the way we calculate sync quality because the old method was not 
accurate enough. The new method calculates the spread between the camera and lidar timestamps for each sample.
def check_timestamp_alignment():
    
    For each sample, measures spread between  and latest
    sensor timestamp. A wide spread means sensors fired out of sync.
    Returns a list of dicts, one per sample
    

    conn = get_db_connection()

    query = 
        SELECT
            sample_token,
            MIN(timestamp) AS min_ts,
            MAX(timestamp) AS max_ts
        FROM sensor_data
        GROUP BY sample_token
    

    rows = conn.execute(query).fetchall()
    conn.close()

    results = []
    for sample_token, min_ts, max_ts in rows:
        sync_delta_ms = (max_ts - min_ts) / 1000

        results.append({
            'sample_token': sample_token,
            'sync_delta_ms': sync_delta_ms,
            'within_threshold': sync_delta_ms <= TIMESTAMP_SYNC_THRESHOLD_MS
        })

    return results

"""

def check_timestamp_alignment():
    """
    For each sample, measures the raw timestamp delta between camera 
    and LiDAR sensor_data records.
    
    NOTE: This is a simplified proxy metric, not the true sync offset.
    Camera timestamp = exposure trigger time. LiDAR timestamp = full 
    rotation completion time. These are structurally different clock 
    references, so this delta partially reflects LiDAR rotation timing 
    behavior, not pure sync error. The actual nuScenes team uses a 
    more sophisticated method (median-offset correction) to isolate 
    true sync error, which is out of scope for this pipeline.
    
    Threshold is set empirically from observed data range (40-48ms)
    rather than a theoretical physical motion calculation.
    """
    conn = get_db_connection()

    query = """
        SELECT
            sample_token, 
            MIN(timestamp) as min_ts,
            MAX(timestamp) as max_ts,
        FROM sensor_data
        WHERE modality in ('camera', 'lidar')
        GROUP BY sample_token
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    results = []
    for sample_token, min_ts, max_ts in rows:
        sync_delta_ms = (max_ts - min_ts) / 1000

        results.append({
            'sample_token': sample_token,
            'sync_delta_ms': sync_delta_ms,
            "within_threshold": sync_delta_ms <= TIMESTAMP_SYNC_THRESHOLD_MS
        })

    return results
    


def check_annotation_validity():
    """
    For each scene, calculates valid vs ghost annotation counts.
    Ghost = num_lidar_pts is 0 and num_radar_pts is 0.
    Returns a list of dicts, one per scene
    """

    conn = get_db_connection()

    query = """
        SELECT
            sm.scene_token,
            COUNT(*) AS total_annotations,
            SUM(CASE WHEN a.valid_flag THEN 1 ELSE 0 END) AS valid_annotations,
            SUM(CASE WHEN a.num_lidar_pts = 0 AND a.num_radar_pts = 0 
            THEN 1 ELSE 0 END) AS ghost_annotations
        FROM annotations a
        JOIN samples sm ON sm.token = a.sample_token
        GROUP BY sm.scene_token
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    results = []
    for scene_token, total, valid, ghost in rows:
        results.append({
            'scene_token': scene_token,
            'total_annotations': total,
            'valid_annotations': valid,
            'ghost_annotations': ghost,
            'ghost_ratio': ghost / total if total > 0 else 0
        })
    return results