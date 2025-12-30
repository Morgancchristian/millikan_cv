import cv2
import numpy as np

def extract_video_properties(video):
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return total_frames, frame_width, frame_height

def find_slopes(peaks, troughs):
    points = sorted(peaks + troughs, key=lambda x: x[0])

    # Calculate slopes between consecutive points
    positive_slopes = []
    negative_slopes = []
    for i in range(1, len(points)):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        # Calculate slope (delta_y / delta_x)
        if x2 != x1:  # Prevent division by zero
            slope = (y2 - y1) / (x2 - x1)
            if slope > 0:
                positive_slopes.append(slope)
            else:
                negative_slopes.append(slope)
        else:
            print("Vertical line detected, slope considered as infinite.")

    # Calculate the median slopes
    neg_slope_median = np.median(negative_slopes) if negative_slopes else 0
    pos_slope_median = np.median(positive_slopes) if positive_slopes else 0

    return convert_to_mm_per_sec(neg_slope_median, pos_slope_median, 30, 414.20)

def convert_to_mm_per_sec(negative, positive, fps, calibration):
    # Convert slopes to mm/s
    negative = np.abs((negative * fps) / calibration)
    positive = np.abs((positive * fps) / calibration)
    return negative * 1e-3, positive * 1e-3  # Convert to m/s