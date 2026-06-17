from src.ingestion.loader import load_nuscenes

nusc = load_nuscenes()
print(f"\nNumber of scenes: {len(nusc.scene)}")
print(f"Number of samples: {len(nusc.sample)}")
print(f"Number of annotations: {len(nusc.sample_annotation)}")
print(f"\nFirst scene:")
print(nusc.scene[0])