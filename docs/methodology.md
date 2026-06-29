# Data Readiness Score (DRS) — Methodology

This document explains the reasoning, data sources, and engineering decisions behind PhysicalFlow's Data Readiness Score. It is written to be fully auditable — every formula traces to a real nuScenes schema field, and every threshold is either physically reasoned or empirically calibrated against observed data.

---

## 1. What problem this solves

World models for physical AI (autonomous vehicles, robotics) require large volumes of high-quality multi-modal sensor data. No standard automated framework exists to score whether a given batch of sensor data is "ready" for this kind of training. DRS is an original attempt at that framework, built and validated against the nuScenes v1.0-mini dataset.

---

## 2. Where the approach comes from

DRS is a **weighted linear combination** of five data quality dimensions — a scoring method with a long history, not an invented technique. Wang & Strong (1996) and earlier work by Ballou & Pazer (1985) established completeness, consistency, accuracy, and timeliness as core data quality dimensions, explicitly recommending weighted composite scores tailored to a specific use case. DRS applies this 40-year-old methodology to a new domain: physical AI sensor data.

What is novel: mapping these dimensions onto the specific nuScenes schema, deriving domain-justified weights and thresholds, and combining them into a single training-readiness metric. That specific combination does not exist as a published standard.

---

## 3. The five dimensions

### D1 — Sensor Coverage (weight: 25%)

**Question:** How many of the expected 12 sensor channels (6 cameras, 1 LiDAR, 5 RADAR) actually produced data for this scene?

**Fields used:** `sensor_data.channel`, joined to `samples.scene_token`

**Formula:**
```
D1 = (distinct sensor channels present / 12) * 100
```

**Why 25% weight:** Missing a sensor entirely is a hard blocker — a world model cannot learn physics it never observed. This is treated as equally critical to frame completeness.

**Result on mini dataset:** All 10 scenes scored 100.0 — every scene had complete 12-channel coverage. This was verified directly via SQL query before scoring logic was even built (`COUNT(*) GROUP BY channel` returned exactly 404 records per channel, matching the 404 total samples).

---

### D2 — Frame Completeness (weight: 25%)

**Question:** Did this scene capture the expected number of frames given its duration?

**Fields used:** `scenes.nbr_samples`, `samples.timestamp` (min/max per scene)

**Formula:**
```
duration_seconds = (max_timestamp - min_timestamp) / 1,000,000
expected_samples = duration_seconds * 2 Hz (nuScenes keyframe capture rate)
D2 = min((actual_samples / expected_samples) * 100, 100)
```

**Why capped at 100:** Real scenes occasionally captured marginally more frames than the strict 2Hz rate predicts (e.g. 41 actual vs 39.8 expected) due to natural timing variance. Without the cap, this would produce nonsensical scores above 100.

**Why 25% weight:** Same reasoning as D1 — missing frames mean missing moments in time the model never sees.

**Result on mini dataset:** All 10 scenes scored 100.0.

---

### D3 — Timestamp Alignment (weight: 20%)

**Question:** How well synchronized are the camera and LiDAR sensors within each sample?

**Fields used:** `sensor_data.timestamp`, filtered to `modality IN ('camera', 'lidar')`, grouped by `sample_token`

**Formula:**
```
sync_delta_ms = (max_timestamp - min_timestamp across camera+lidar records) / 1000
score_per_sample = max(0, (1 - sync_delta_ms / threshold_ms)) * 100
D3 = average(score_per_sample across all samples in scene)
```

**Engineering history — why this dimension changed during development:**

The original design measured sync delta across all 12 sensors using a 50ms threshold, derived from physical motion reasoning (a vehicle at 50km/h travels ~0.7m in 50ms — roughly the tolerance for bounding box accuracy). When implemented, every scene scored D3 = 0.

Investigation revealed the actual average sync delta across all 12 sensors was 67.8ms — already exceeding the 50ms threshold for every sample. Restricting the measurement to only camera and LiDAR (the actual fusion-critical sensor pair in AV perception — RADAR has independent firing schedules and lower spatial resolution, making its exact timing far less critical to model training) reduced the observed range to 40.9–48.3ms.

Cross-referencing against the actual nuScenes research paper revealed a further nuance: <br>**"To achieve good cross-modality data alignment between the lidar and the cameras, the exposure of a camera is triggered when the top lidar sweeps across the center of the camera's FOV. The timestamp of the image is the exposure trigger time; and the timestamp of the lidar scan is the time when the full rotation of the current lidar frame is achieved."** (nuScenes paper, Caesar et al.)

This means camera and LiDAR timestamps are measuring two structurally different events — exposure trigger vs. rotation completion — not a single shared clock. The true sync offset the nuScenes team measures (via median-offset correction per camera) is within -6ms to +7ms. PhysicalFlow's raw MAX-MIN delta is a simplified proxy that partially reflects this structural timing difference, not pure synchronization error.

**Decision made:** Keep the simplified proxy metric (replicating the nuScenes team's exact correction methodology was out of scope for this project), but:
1. Restrict measurement to the camera-LiDAR pair only
2. Recalibrate the threshold to 60ms, grounded in the actual observed data range (40.9–48.3ms) rather than a theoretical estimate
3. Document the limitation explicitly, here and in code docstrings

**Why this matters:** This is a transparent, documented engineering tradeoff — not a hidden simplification. A more rigorous version of D3 would implement the nuScenes team's median-offset correction method; that is a clearly scoped potential future improvement.

**Result on mini dataset:** Scores ranged 24.9–28.7 after recalibration — meaningful differentiation between scenes, properly bounded.

---

### D4 — Annotation Validity (weight: 20%)

**Question:** Are labeled objects actually confirmed by sensor data, or are they "ghost" annotations?

**Fields used:** `sample_annotation.num_lidar_pts`, `sample_annotation.num_radar_pts`

**Note on valid_flag:** Earlier versions of the nuScenes schema included an explicit `valid_flag` field. The version used in this project does not include it as a stored field, so it is calculated directly:
```python
valid_flag = (num_lidar_pts > 0) or (num_radar_pts > 0)
```
This matches Motional's own documented definition: an annotation is only considered valid if at least one LiDAR or RADAR point physically confirms the object's presence.

**Formula:**
```
valid_ratio = valid_annotations / total_annotations
ghost_ratio = annotations_with_zero_lidar_and_zero_radar / total_annotations
D4 = valid_ratio * (1 - ghost_ratio) * 100
```

**Why multiply by both ratios:** A scene needs to perform well on both measures — being multiplicative makes this a stricter combination than averaging, penalizing scenes that look fine on one metric but poor on the other.

**Why 20% weight:** Ghost annotations directly teach a model to expect objects where no sensor detected anything — a serious but not absolute blocker (unlike missing sensors/frames entirely).

**Result on mini dataset:** Scores ranged 52.6–89.7 — the most differentiating dimension across scenes, alongside D5.

---

### D5 — Scene Diversity (weight: 10%)

**Question:** How many distinct object categories appear in this scene?

**Fields used:** `sample_annotation.category_name` (via `instance.category_token` → `category.name`), distinct count per scene

**Formula:**
```
D5 = min((distinct_categories_present / 23 total categories) * 100, 100)
```

**Known simplification:** This version counts distinct categories with equal weight. The original design intent included weighting rare categories (e.g. construction vehicles, emergency vehicles) higher than common ones (cars, trucks) since rare-category scenes carry more training value under the distributional coverage principle in ML theory. This rarity-weighted version was scoped out for the initial build and is a documented potential extension.

**Why lowest weight (10%):** Diversity improves training value but its absence doesn't disqualify a scene the way missing sensors or fabricated annotations would.

**Result on mini dataset:** Scores ranged 17.4–52.2 — the widest spread of any dimension, reflecting genuine variation in scene content (e.g. a busy intersection vs. an empty parking lot).

---

## 4. The composite formula

```
DRS = 0.25(D1) + 0.25(D2) + 0.20(D3) + 0.20(D4) + 0.10(D5)
```

**Weight justification:** D1 and D2 (sensor coverage, frame completeness) are weighted highest because they represent hard, binary blockers — a world model cannot learn from physical reality it never observed at all. D3 and D4 (timestamp alignment, annotation validity) degrade quality but don't void a scene's usefulness entirely. D5 (diversity) is weighted lowest as a value-add rather than a requirement.

**These weights are documented assumptions, not statistically fitted values.** They are configurable in `config.py` — a team with different priorities could justify and apply different weights without changing the underlying measurement logic.

---

## 5. How this was verified

1. **Bounds checking:** every sub-score formula is mathematically bounded to 0–100 by construction (ratios capped, floors applied via `max(0, ...)`)
2. **Sanity testing against real output:** initial D3 implementation produced a suspicious uniform 0 across all scenes — investigated rather than accepted, leading to the redesign documented above
3. **Cross-referencing published research:** D3's threshold and scope were corrected after comparing against the actual nuScenes paper's documented synchronization methodology
4. **Direct SQL verification:** D1's near-universal 100.0 score was independently confirmed via a standalone query before being trusted in the scoring pipeline

---

## 6. Known limitations

- D3 is a simplified proxy for true camera-LiDAR sync error, not an exact replication of nuScenes' own median-offset correction method
- D5 currently treats all object categories as equally valuable; rarity-weighting was scoped out of the initial build
- DRS has not been validated against actual downstream model training outcomes (e.g. "do scenes with DRS > 80 produce measurably better trained models") — this would require training infrastructure beyond this project's scope, and is the logical next validation step
- Band thresholds (Reject/Marginal/Good/Excellent) are fixed, absolute values chosen for cross-dataset comparability — they are not relative to any single dataset's score distribution, which is why all 10 mini-dataset scenes cluster in the Marginal-to-Good range rather than spanning the full scale

---

## 7. Potential extensions

- Implement true median-offset sync correction matching nuScenes' own methodology for D3
- Add rarity-weighting to D5 based on category frequency across the full (non-mini) dataset
- Validate DRS against actual model training performance given access to training infrastructure
- Extend scoring to RADAR-specific quality dimensions, given its role in all-weather backup sensing
