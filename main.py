from src.ingestion.loader import load_nuscenes
from src.ingestion.parser import (parse_scenes, parse_samples,
                                   parse_sample_data, parse_annotations)
from src.database.schema import create_schema
from src.database.loader import load_all
from src.scoring.drs import calculate_drs

from src.validation.quality import check_timestamp_alignment


nusc = load_nuscenes()

scenes = parse_scenes(nusc)
samples = parse_samples(nusc)
sensor_data = parse_sample_data(nusc)
annotations = parse_annotations(nusc)

create_schema()
load_all(scenes, samples, sensor_data, annotations)

sync_check = check_timestamp_alignment()
sync_deltas = [item['sync_delta_ms'] for item in sync_check]

print(f"\nMin sync delta: {min(sync_deltas)}")
print(f"Max sync delta: {max(sync_deltas)}")
print(f"Average sync delta: {sum(sync_deltas)/len(sync_deltas)}")

drs_results = calculate_drs()

print("\n--- Data Readiness Scores ---")
for r in sorted(drs_results, key=lambda x: x['drs_score'], reverse=True):
    print(r)