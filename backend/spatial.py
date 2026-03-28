def get_spatial_cue(bbox: tuple, frame_size: tuple) -> dict:
    x1, y1, x2, y2 = bbox
    w, h = frame_size
    
    cx = (x1 + x2) / 2
    
    if cx < w / 3:
        direction = "to your left"
    elif cx > 2 * w / 3:
        direction = "to your right"
    else:
        direction = "directly ahead"
        
    height_ratio = (y2 - y1) / h
    
    if height_ratio > 0.30:
        distance_label = "approximately 1 meter"
        dist_m = 1.0
    elif height_ratio > 0.15:
        distance_label = "approximately 2 meters"
        dist_m = 2.0
    elif height_ratio > 0.08:
        distance_label = "approximately 3 to 4 meters"
        dist_m = 3.5
    else:
        distance_label = "far ahead"
        dist_m = 6.0
        
    return {
        'direction': direction,
        'distance_label': distance_label,
        'distance_m': dist_m
    }
