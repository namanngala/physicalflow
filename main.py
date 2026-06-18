from src.ingestion.loader import load_nuscenes
from src.ingestion.parser import (parse_scenes, parse_samples,
                                   parse_sample_data, parse_annotations)
from src.database.schema import create_schema
from src.database.loader import load_all

nusc = load_nuscenes()

scenes = parse_scenes(nusc)
samples = parse_samples(nusc)
sensor_data = parse_sample_data(nusc)
annotations = parse_annotations(nusc)

create_schema()
load_all(scenes, samples, sensor_data, annotations)

