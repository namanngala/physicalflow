import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


import streamlit as st
import pandas as pd
import plotly.express as px

from src.scoring.drs import calculate_drs
from src.database.schema import get_db_connection

st.set_page_config(page_title="PhysicalFlow - DRS Dashboard", layout="wide")

st.title("PhysicalFlow")
st.subheader("Data Readiness Scoring for World Model Training")

# Calcuate DRS for all scenes
drs_results = calculate_drs()
df = pd.DataFrame(drs_results)

# Get scene names for display
conn = get_db_connection()
scene_names = conn.execute("SELECT token, name, description FROM scenes").fetchall()
conn.close()

name_lookup = {token: name for token, name, desc in scene_names}
desc_lookup = {token: desc for token, name, desc in scene_names}

df['scene_name'] = df['scene_token'].map(name_lookup)
df['description'] = df['scene_token'].map(desc_lookup)
df = df.sort_values('drs_score', ascending = False)

def get_band(score):
    if score >= 90:
        return "Excellent"
    elif score >= 76:
        return "Good"
    elif score >= 61:
        return "Marginal"
    elif score >= 41:
        return "Needs Repair"
    else:
        return "Reject"
    
df['readiness_band'] = df['drs_score'].apply(get_band)

# --- SECTION 1: Leaderboard ---
st.header("DRS Leaderboard")

leaderboard_df = df[['scene_name', 'description', 'drs_score', 'readiness_band']]
st.dataframe(leaderboard_df, use_container_width = True, hide_index=True)

# --- SECTION 2: Sub-score breakdown ---
st.header('Sub-score Breakdown')

selected_scene = st.selectbox("Select a scene", df['scene_name'].to_list())
scene_row = df[df['scene_name'] == selected_scene].iloc[0]

dimensions = ['d1_sensor_coverage', 'd2_frame_completeness',
              'd3_timestamp_alignment', 'd4_annotation_validity',
              'd5_scene_diversity']
dimension_labels = ['Sensor Coverage', 'Frame Completeness', 
                    "Timestamp Alignment", "Annotation Validity",
                    "scene Diversity"]

chart_df = pd.DataFrame({
    'Dimension': dimension_labels,
    'Score' : [scene_row[d] for d in dimensions]
})

fig = px.bar(chart_df, x = 'Dimension', y = 'Score', range_y = [0, 100],
             title = f"{selected_scene} - Sub-Scores")
st.plotly_chart(fig, use_container_width=True)

# --- SECTION 3: Dataset-wide Statistics ---
st.header("Dataset Overview")

col1, col2, col3 = st.columns(3)
col1.metric("Average DRS", f"{df['drs_score'].mean():.1f}")
col2.metric("Total Scenes", len(df))
col3.metric("Score Range", f"{df['drs_score'].min():.1f} - {df['drs_score'].max():.1f}")

score_spread = df['drs_score'].max() - df['drs_score'].min()
if score_spread < 10:
    st.info(f" Scene scores cluster tightly within a {score_spread:.1f}-point range. "
            f" This suggests the mini dataset is consistent in quality, with no scenes "
            f"clearly excellent or clearly poor for training.")
    
# --- SECTION 4: Annotation quality table ---
st.header("Annotation Quality by Scene")
st.dataframe(df[['scene_name', 'd4_annotation_validity', 'd5_scene_diversity']],
            use_container_width=True, hide_index=True)