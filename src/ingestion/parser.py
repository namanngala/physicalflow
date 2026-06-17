from config import EXPECTED_SENSORS

def parse_scenes(nusc):
    """
    Extracts scene records into a flat list of dictionaires
    Each dict has exactly the fields our database needs
    """
    scenes = []

    for scene in nusc.scene:
        scenes.append({
            'token': scene['token'],
            'name': scene['name'],
            'description': scene['description'],
            'nbr_samples': scene['nbr_samples'],
            'log_token': scene['log_token'],
            'first_sample_token': scene['first_sample_token'],
            'last_sample_token': scene['last_sample_token']

        })

    return scenes

def parse_samples(nusc):
    """
    Extracts sample records = one per keyfram moment
    """

    samples = []

    for sample in nusc.sample:
        samples.append({
            'token': sample['token'],
            'scene_token': sample['scene_token'],
            'timestamp': sample['timestamp'],
            'prev': sample['prev'],
            'next': sample['next']
        })

    return samples

def parse_sample_data(nusc):
    """
    Extracts sensor records - 12 per sample.
    Joins with sensor table to get channel name and modality
    Only keyframes (is_key_frame=True)
    """

    sensor_records = []

    for sd in nusc.sample_data:
        if not sd['is_key_frame']:
            continue

        # get sensor type for this record
        calibrated = nusc.get('calibrated_sensor', sd['calibrated_sensor_token'])
        sensor = nusc.get('sensor', calibrated['sensor_token'])

        sensor_records.append({
            'token': sd['token'],
            'sample_token': sd['sample_token'],
            'channel': sensor['channel'],
            'modality': sensor['modality'],
            'timestamp': sd['timestamp'],
            'is_key_frame': sd['is_key_frame'],
            'ego_pose_token': sd['ego_pose_token'],
            'filename': sd['filename']
        })
    return sensor_records

def parse_annotations(nusc):
    """
    Extracts annotation records
    Joints with category table to get human readbale category name
    """
    annotations = []
    for ann in nusc.sample_annotation:
        #get category name for this instance
        instance = nusc.get('instance', ann['instance_token'])
        category = nusc.get('category', instance['category_token'])

        # calculate valid_flag ourselves
        # an annotation is valid if at least one sensor confirmed it

        valid_flag = (ann['num_lidar_pts'] > 0) or (ann['num_radar_pts'] > 0)

        annotations.append({
            'token': ann['token'],
            'sample_token': ann['sample_token'],
            'instance_token': ann['instance_token'],
            'category_name': category['name'],
            'num_lidar_pts': ann['num_lidar_pts'],
            'num_radar_pts': ann['num_radar_pts'],
            'valid_flag': valid_flag,
            'visibility_token': ann['visibility_token']
        })

    return annotations
