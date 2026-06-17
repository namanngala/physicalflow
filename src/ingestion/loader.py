from nuscenes.nuscenes import NuScenes
from config import NUSCENES_VERSION, NUSCENES_DATAROOT

def load_nuscenes():
    """
    Loads the nuscenes data intto python memory.
    Returns a nuscenes object we can query through the pipeline.
    """
    print(f"Loading nuscenes {NUSCENES_VERSION} from {NUSCENES_DATAROOT}")

    nusc = NuScenes(
        version = NUSCENES_VERSION,
        dataroot = NUSCENES_DATAROOT,
        verbose =  True
    )

    print(f"Loaded successfully")
    return nusc