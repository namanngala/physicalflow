from src.database.schema import get_db_connection
from src.validation.quality import (check_frame_completeness,
                                    check_timestamp_alignment,
                                    check_annotation_validity)
from config import EXPECTED_SENSORS, TIMESTAMP_SYNC_THRESHOLD_MS

def calculate_d1_sensor_coverage():
    """
    D1: For each scene, what fraction of the expected sensors were present?
    Returns dict: {scene_token: d1_score}
    """
    conn = get_db_connection()

    query = """
        SELECT
            sm.scene_token,
            COUNT(DISTINCT sd.channel) AS sensors_present
        FROM sensor_data sd
        JOIN samples sm on sm.token = sd.sample_token
        GROUP BY sm.scene_token
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    scores = {}
    for scene_token, sensors_present in rows:
        scores[scene_token] = (sensors_present / EXPECTED_SENSORS) * 100

    return scores

def calculate_d2_frame_completeness():
    """
    D2: Actual vs expected sample count per scene.
    Capped at 100 - a scene can't exceed perfect completeness.
    """

    frame_data = check_frame_completeness()

    scores = {}
    for row in frame_data:
        ratio = row['actual_samples'] / row['expected_samples']
        scores[row['scene_token']] = min(ratio * 100, 100)

    return scores

def calculate_d3_timestamp_alignment():
    """
    D3: Average sync quality across all samples in a scene.
    Needs scene_token, so we join sample-level sync data back to scenes.
    """

    conn = get_db_connection()

    sync_data = check_timestamp_alignment()

    # build a lookup: sample_token -> scene_token
    rows = conn.execute("SELECT token, scene_token FROM samples").fetchall()
    conn.close()
    sample_to_scene = {token: scene_token for token, scene_token in rows}

    # group sync data by scene_token
    scene_deltas = {}
    for item in sync_data:
        scene_token = sample_to_scene.get(item['sample_token'])
        if scene_token not in scene_deltas:
            scene_deltas[scene_token] = []
        scene_deltas[scene_token].append(item['sync_delta_ms'])

    scores = {}
    for scene_token, deltas in scene_deltas.items():
        avg_delta = sum(deltas) / len(deltas)
        score = max(0, (1 - avg_delta / TIMESTAMP_SYNC_THRESHOLD_MS)) * 100
        scores[scene_token] = min(score, 100)  # Cap at 100

    return scores

def calculate_d4_annotation_validity():
    """
    D4: Valid annotation ratio, penalized by ghost ratio.
    """

    validity_data = check_annotation_validity()

    scores = {}
    for row in validity_data:
        valid_ratio = row['valid_annotations'] / row['total_annotations']
        score = valid_ratio * (1 - row['ghost_ratio']) * 100
        scores[row['scene_token']] = score

    return scores

def calculate_5_scene_diversity():
    """
    D5: How many disctinct object categories appear in each scene.
    Simple version: ration of categories present vs 23 total categories
    """

    conn = get_db_connection()
    query = """
        SELECT
            sm.scene_token,
            COUNT(DISTINCT a.category_name) AS distinct_categories
        FROM annotations a
        JOIN samples sm ON sm.token = a.sample_token
        GROUP BY sm.scene_token
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    TOTAL_CATEGORIES = 23
    scores = {}
    for scene_token, distinct_categories in rows:
        scores[scene_token] = min((distinct_categories / TOTAL_CATEGORIES) * 100, 100)
    
    return scores

def calculate_drs():
    """
    Combines all 5 dimention socres into the final Data Readiness Score.
    Weights: D1 = 25%, D2 = 25%, D3 = 20%, D4 = 20%, D5 = 10%
    """

    d1 = calculate_d1_sensor_coverage()
    d2 = calculate_d2_frame_completeness()
    d3 = calculate_d3_timestamp_alignment()
    d4 = calculate_d4_annotation_validity()
    d5 = calculate_5_scene_diversity()

    results = []

    for scene_token in d1.keys():
        d1_score = d1.get(scene_token, 0)
        d2_score = d2.get(scene_token, 0)
        d3_score = d3.get(scene_token, 0)
        d4_score = d4.get(scene_token, 0)
        d5_score = d5.get(scene_token, 0)

        drs = (d1_score * 0.25 + d2_score * 0.25 + d3_score * 0.2 +
                d4_score * 0.2 + d5_score * 0.1)
        
        results.append({
            'scene_token': scene_token,
            'd1_sensor_coverage': round(d1_score, 1),
            'd2_frame_completeness': round(d2_score, 1),
            'd3_timestamp_alignment': round(d3_score, 1),
            'd4_annotation_validity': round(d4_score, 1),
            'd5_scene_diversity': round(d5_score, 1),
            'drs_score' : round(drs, 1)
        })

    return results
