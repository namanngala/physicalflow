from src.ingestion.loader import load_nuscenes
from src.ingestion.parser import (parse_scenes, parse_samples,
                                   parse_sample_data, parse_annotations)
from src.database.schema import create_schema
from src.database.loader import load_all
from src.validation.quality import (check_frame_completeness,
                                     check_timestamp_alignment,
                                     check_annotation_validity)

nusc = load_nuscenes()

scenes = parse_scenes(nusc)
samples = parse_samples(nusc)
sensor_data = parse_sample_data(nusc)
annotations = parse_annotations(nusc)

create_schema()
load_all(scenes, samples, sensor_data, annotations)

frame_results = check_frame_completeness()
sync_results = check_timestamp_alignment()
validity_results = check_annotation_validity()

print(f"\nFrame completeness check - first scene:")
print(frame_results[0])

print(f"\nTimestamp alignment check - first sample:")
print(sync_results[0])

print(f"\nAnnotation validity check - first scene:")
print(validity_results[0])
