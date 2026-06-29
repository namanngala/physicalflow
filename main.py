from src.ingestion.loader import load_nuscenes
from src.ingestion.parser import (parse_scenes, parse_samples,
                                   parse_sample_data, parse_annotations)
from src.database.schema import create_schema
from src.database.loader import load_all
from src.scoring.drs import calculate_drs


def run_pipeline():
    """
    Runs the full PhysicalFlow pipeline end to end:
    load -> parse -> create schema -> load to DuckDB -> score.
    """
    print("=" * 50)
    print("PhysicalFlow Pipeline")
    print("=" * 50)

    # Step 1: Load raw nuScenes data
    nusc = load_nuscenes()

    # Step 2: Parse into clean structured records
    scenes = parse_scenes(nusc)
    samples = parse_samples(nusc)
    sensor_data = parse_sample_data(nusc)
    annotations = parse_annotations(nusc)

    # Step 3: Create database schema (idempotent)
    create_schema()

    # Step 4: Load parsed data into DuckDB (idempotent)
    load_all(scenes, samples, sensor_data, annotations)

    # Step 5: Calculate Data Readiness Scores
    drs_results = calculate_drs()

    print("\n" + "=" * 50)
    print("Data Readiness Scores (ranked)")
    print("=" * 50)

    ranked = sorted(drs_results, key=lambda x: x['drs_score'], reverse=True)
    for r in ranked:
        print(f"Scene {r['scene_token'][:8]}... | DRS: {r['drs_score']:5.1f} | "
              f"D1:{r['d1_sensor_coverage']:5.1f} D2:{r['d2_frame_completeness']:5.1f} "
              f"D3:{r['d3_timestamp_alignment']:5.1f} D4:{r['d4_annotation_validity']:5.1f} "
              f"D5:{r['d5_scene_diversity']:5.1f}")

    avg_drs = sum(r['drs_score'] for r in drs_results) / len(drs_results)
    print(f"\nAverage DRS across {len(drs_results)} scenes: {avg_drs:.1f}")
    print("\nPipeline completed successfully.")
    print("Run 'streamlit run src/dashboard/app.py' to view the interactive dashboard.")

    return drs_results


if __name__ == "__main__":
    run_pipeline()