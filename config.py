import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# nuScenes
NUSCENES_VERSION = "v1.0-mini"
NUSCENES_DATAROOT = os.path.join(BASE_DIR, "data", "raw")

# Quality thresholds
TIMESTAMP_SYNC_THRESHOLD_MS = 50
MIN_LIDAR_POINTS_VALID = 1
EXPECTED_SENSORS = 12
CAPTURE_FREQUENCY_HZ = 2