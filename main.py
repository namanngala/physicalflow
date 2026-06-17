from src.ingestion.loader import load_nuscenes
from src.ingestion.parser import (parse_scenes, parse_samples,
                                   parse_sample_data, parse_annotations)

nusc = load_nuscenes()

scenes = parse_scenes(nusc)
samples = parse_samples(nusc)
sensor_data = parse_sample_data(nusc)
annotations = parse_annotations(nusc)

print(f"Scenes parsed: {len(scenes)}")
print(f"Samples parsed: {len(samples)}")
print(f"Sensor records parsed: {len(sensor_data)}")
print(f"Annotations parsed: {len(annotations)}")

print(f"\nFirst scene: {scenes[0]}")
print(f"\nFirst sensor record: {sensor_data[0]}")
print(f"\nFirst annotation: {annotations[0]}")