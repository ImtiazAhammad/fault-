import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
from collections import deque, defaultdict
import time
import csv
import os
import datetime
import math
import requests
from io import BytesIO
import base64
import json
from PIL import Image
from threading import Thread
from queue import Queue
import asyncio
from concurrent.futures import ThreadPoolExecutor


counted_vehicles = {0: {}, 1: {}, 2: {}}  # Dictionary to track counted vehicles per lane
vehicle_classes = {0: defaultdict(int), 1: defaultdict(int), 2: defaultdict(int)}  # Class counts per lane
def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        colorsBGR = [x, y]
        print(colorsBGR)

cv2.namedWindow('AI Policing System')
cv2.setMouseCallback('AI Policing System', RGB)# Define constants
SOURCE_VIDEO_PATH = r"D:\PROJECTS\AI police\test2\data\videos\3.mp4"  # Video path
USE_WEBCAM = False  # Set True if using webcam/IP camera
CAMERA_INDEX = 0  # Webcam index or IP camera URL
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5
MODEL_NAME = "best.pt"
MODEL_RESOLUTION = 640
FPS = 30  # Frames per second
LINE_DISTANCE = 10  # meters between speed calculation lines
LINE_1_Y = 250  # First speed calculation line
LINE_2_Y = 290  # Second speed calculation line

# Lane zones and directions
# LANE_1_ZONE = np.array([[773, 250], [845, 250], [1058, 360], [977, 360]])
LANE_2_ZONE = np.array([[617, 240], [858, 240], [1079, 360], [634, 360]])
LANE_3_ZONE = np.array([[300, 240], [562, 240], [563, 360], [15, 360]])
LANE_DIRECTIONS = {0: "Gazipur", 1: "Airport", 2: "Airport"}

# Source points for perspective transform (these are example coordinates - adjust for your video)
SOURCE_POINTS = np.float32([
    [300, 240],  # Top-left
    [858, 240],  # Top-right
    [1079, 360], # Bottom-right
    [15, 360]    # Bottom-left
])

# Destination points for perspective transform (adjust based on your needs)
DEST_POINTS = np.float32([
    [0, 0],
    [500, 0],
    [500, 500],
    [0, 500]
])

# Real-world distance in meters (adjust based on your scene)
REAL_WORLD_WIDTH = 15  # meters
REAL_WORLD_HEIGHT = 30  # meters

# Calculate perspective transform matrices
transform_matrix = cv2.getPerspectiveTransform(SOURCE_POINTS, DEST_POINTS)
inverse_matrix = cv2.getPerspectiveTransform(DEST_POINTS, SOURCE_POINTS)

# Initialize model and video source
model = YOLO(MODEL_NAME)
video_info = cv2.VideoCapture(CAMERA_INDEX if USE_WEBCAM else SOURCE_VIDEO_PATH)
byte_track = sv.ByteTrack(frame_rate=FPS, track_activation_threshold=CONFIDENCE_THRESHOLD)
smoother = sv.DetectionsSmoother()

# Annotators for bounding boxes, labels, and traces
box_annotator = sv.ColorAnnotator()
label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)
trace_annotator = sv.TraceAnnotator(thickness=2, trace_length=FPS * 2)

# Lane zones
# lane_zones = [sv.PolygonZone(polygon=LANE_1_ZONE), sv.PolygonZone(polygon=LANE_2_ZONE), sv.PolygonZone(polygon=LANE_3_ZONE)]
lane_zones = [sv.PolygonZone(polygon=LANE_2_ZONE), sv.PolygonZone(polygon=LANE_3_ZONE)]

# Vehicle positions for speed calculation
vehicle_trackers = {}
lane_counters = {0: 0, 1: 0, 2: 0}

# CSV logging setup
log_file = 'vehicle_log.csv'
if not os.path.exists(log_file):
    with open(log_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'TrackID', 'Lane', 'Direction', 'Speed(km/h)', 'Violation'])

def log_vehicle(timestamp, track_id, lane, direction, speed, violation):
    with open(log_file, 'a', newline='', encoding= 'utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, track_id, lane, direction, speed, violation])

# Add this class for vehicle tracking and speed estimation
class VehicleTracker:
    def __init__(self, max_history=30):
        self.positions = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)
        self.speeds = deque(maxlen=5)
        
    def update(self, position, timestamp):
        transformed_point = cv2.perspectiveTransform(
            np.array([[position]], dtype=np.float32),
            transform_matrix
        )[0][0]
        self.positions.append(transformed_point)
        self.timestamps.append(timestamp)
        
    def calculate_speed(self):
        if len(self.positions) < 15:  # Need minimum points for reliable speed
            return None
            
        # Calculate distance in transformed space
        start_pos = self.positions[0]
        end_pos = self.positions[-1]
        pixel_distance = math.sqrt(
            (end_pos[0] - start_pos[0])**2 + 
            (end_pos[1] - start_pos[1])**2
        )
        
        # Convert pixel distance to real-world distance
        real_distance = (pixel_distance / 500) * REAL_WORLD_HEIGHT  # Using height as reference
        
        # Calculate time difference
        time_diff = self.timestamps[-1] - self.timestamps[0]
        if time_diff == 0:
            return None
            
        # Calculate speed in km/h
        speed = (real_distance / time_diff) * 3.6
        self.speeds.append(speed)
        
        # Return average of recent speeds for smoothing
        return sum(self.speeds) / len(self.speeds) if self.speeds else None

# Replace the existing vehicle_positions dictionary with a tracker dictionary
vehicle_positions = {}

# Replace the calculate_speed function with this updated version
def calculate_speed(track_id, detection, frame_time):
    if track_id not in vehicle_trackers:
        vehicle_trackers[track_id] = VehicleTracker()
    
    # Get bottom center point of bounding box
    bbox = detection[0]
    bottom_center = np.array([
        (bbox[0] + bbox[2]) / 2,  # x coordinate
        bbox[3]                    # y coordinate (bottom)
    ])
    
    # Update tracker and calculate speed
    vehicle_trackers[track_id].update(bottom_center, frame_time)
    return vehicle_trackers[track_id].calculate_speed()

# Lane detection
def determine_lane(detection, lane_zones):
    detection_box = sv.Detections(xyxy=np.array([detection[0]]))
    for lane_index, lane_zone in enumerate(lane_zones):
        mask = lane_zone.trigger(detections=detection_box)
        if np.any(mask):
            return lane_index, False  # No violation
    return -1, True  # Violation

# Add these constants after the existing ones
API_ENDPOINT = "http://localhost:8000/vehicle-detection"  # Adjust URL as needed

# Add this function to capture and prepare vehicle snapshot
def get_vehicle_snapshot(frame, detection):
    xyxy = detection[0]
    x1, y1, x2, y2 = map(int, xyxy)
    # Add padding around the vehicle
    padding = 10
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(frame.shape[1], x2 + padding)
    y2 = min(frame.shape[0], y2 + padding)
    
    vehicle_crop = frame[y1:y2, x1:x2]
    cv2.imshow("crope",vehicle_crop)
    
    # Convert to base64
    success, encoded_img = cv2.imencode('.jpg', vehicle_crop)
    if success:
        return base64.b64encode(encoded_img.tobytes()).decode('utf-8')
    return None

# Modify the send_to_api function to be synchronous
def send_to_api(detection_data, snapshot):
    try:
        payload = {
            "detection_data": detection_data,
            "snapshot": snapshot,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Add error handling and timeout
        try:
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=1  # 1 second timeout
            )
            
            if response.status_code == 200:
                print(f"Successfully sent detection data for vehicle {detection_data['track_id']}")
                return True
            else:
                print(f"API Error: Status code {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"API timeout for vehicle {detection_data['track_id']}")
            return False
        except requests.exceptions.ConnectionError:
            print("API server not running or unreachable")
            return False
            
    except Exception as e:
        print(f"Error preparing/sending detection data: {str(e)}")
        return False

# Add this function to save data locally when API fails
def save_locally(detection_data, snapshot):
    try:
        # Create directories if they don't exist
        os.makedirs('failed_uploads/images', exist_ok=True)
        os.makedirs('failed_uploads/data', exist_ok=True)
        
        # Save snapshot
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = f'failed_uploads/images/vehicle_{detection_data["track_id"]}_{timestamp}.jpg'
        data_path = f'failed_uploads/data/vehicle_{detection_data["track_id"]}_{timestamp}.json'
        
        # Save image
        img_data = base64.b64decode(snapshot)
        with open(image_path, 'wb') as f:
            f.write(img_data)
            
        # Save detection data
        with open(data_path, 'w') as f:
            json.dump(detection_data, f, indent=4)
            
        print(f"Data saved locally for vehicle {detection_data['track_id']}")
        return True
    except Exception as e:
        print(f"Error saving data locally: {str(e)}")
        return False

# Add these constants after your existing lane definitions
# Define sweet spots for each lane (adjust coordinates based on your camera view)
SWEET_SPOTS = {
    0: np.array([[650, 280], [750, 280], [750, 320], [650, 320]]),  # Lane 1 sweet spot
    1: np.array([[400, 280], [500, 280], [500, 320], [400, 320]])   # Lane 2 sweet spot
}

# Add sweet spot zones after your lane_zones initialization
sweet_spot_zones = [
    sv.PolygonZone(polygon=SWEET_SPOTS[0]),
    sv.PolygonZone(polygon=SWEET_SPOTS[1])
]

# Add this dictionary to track if we've already captured a vehicle's best frame
vehicle_captures = {}

# Add this class for handling API communications in background
class AsyncAPIHandler:
    def __init__(self):
        self.queue = Queue()
        self.thread = Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        self.executor = ThreadPoolExecutor(max_workers=4)  # Adjust number of workers as needed
    
    def _process_queue(self):
        while True:
            try:
                detection_data, snapshot = self.queue.get()
                self.executor.submit(self._send_data, detection_data, snapshot)
            except Exception as e:
                print(f"Error in queue processing: {str(e)}")
            finally:
                self.queue.task_done()
    
    def _send_data(self, detection_data, snapshot):
        try:
            if not send_to_api(detection_data, snapshot):
                save_locally(detection_data, snapshot)
        except Exception as e:
            print(f"Error in sending data: {str(e)}")
            save_locally(detection_data, snapshot)
    
    def send_async(self, detection_data, snapshot):
        self.queue.put((detection_data, snapshot))

# Initialize the async handler at the start of your script
api_handler = AsyncAPIHandler()

# Modify the process_detections function to use async handler
def process_detections(frame_time, tracked_detections, frame):
    labels = []
    for detection in tracked_detections:
        track_id = int(detection[4])
        xyxy = detection[0]
        class_name = detection[5]['class_name']
        bottom_y = int(xyxy[3])
        
        lane_index, is_violation = determine_lane(detection, lane_zones)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if lane_index != -1:  # Vehicle in valid lane
            lane = f"Lane {lane_index + 1}"
            direction = LANE_DIRECTIONS[lane_index]
            speed = calculate_speed(track_id, detection, frame_time)
            
            # Check if vehicle is in sweet spot
            detection_box = sv.Detections(xyxy=np.array([detection[0]]))
            if track_id not in vehicle_captures and sweet_spot_zones[lane_index].trigger(detections=detection_box)[0]:
                snapshot = get_vehicle_snapshot(frame, detection)
                if snapshot:
                    vehicle_captures[track_id] = True
                    detection_data = {
                        "track_id": int(track_id),
                        "class_name": str(class_name),
                        "lane": str(lane),
                        "direction": str(direction),
                        "speed": float(speed) if speed else "N/A",
                        "violation": "No",
                        "bbox": [float(x) for x in xyxy.tolist()],
                        "confidence": float(detection[2])
                    }
                    # Use async handler instead of direct API call
                    api_handler.send_async(detection_data, snapshot)
            
            # Continue with normal vehicle counting and labeling
            if track_id not in counted_vehicles[lane_index]:
                counted_vehicles[lane_index][track_id] = True
                vehicle_classes[lane_index][class_name] += 1
                lane_counters[lane_index] += 1

            label = f"ID:{track_id}|{class_name}|{lane}({direction})|Speed: {speed:.2f} km/h" if speed else f"ID:{track_id}|{class_name}|{lane}({direction})"
            violation = 'No'
            log_vehicle(timestamp, track_id, lane, direction, speed if speed else 'N/A', violation)
            
        else:  # Vehicle in violation
            # Handle violation case with converted types
            detection_data = {
                "track_id": int(track_id),
                "class_name": str(class_name),
                "lane": "None",
                "direction": "Unknown",
                "speed": "N/A",
                "violation": "Yes",
                "bbox": [float(x) for x in xyxy.tolist()],  # Convert numpy values to float
                "confidence": float(detection[2])
            }
            
            # Capture violation snapshot if not already captured
            if track_id not in vehicle_captures:
                snapshot = get_vehicle_snapshot(frame, detection)
                if snapshot:
                    vehicle_captures[track_id] = True
                    # Use async handler for violations too
                    api_handler.send_async(detection_data, snapshot)
            
            lane = 'None'
            direction = 'Unknown'
            speed = 'N/A'
            violation = 'Yes'
            label = f"ID:{track_id}|Lane Violation"
            log_vehicle(timestamp, track_id, lane, direction, speed, violation)
        
        labels.append(label)
    return labels

# Main loop
while video_info.isOpened():
    ret, frame = video_info.read()
    if not ret:
        break

    frame_time = time.time()
    frame = cv2.resize(frame, (1080, 540))
    result = model(frame, imgsz=MODEL_RESOLUTION, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(result)
    
    lane_masks = [lane.trigger(detections=detections) for lane in lane_zones]
    combined_mask = np.any(lane_masks, axis=0)
    detections = detections[combined_mask]
    # detections  = detections[detections.class_id !=0]
    
    detections = detections[detections.confidence > CONFIDENCE_THRESHOLD]
    tracked_detections = byte_track.update_with_detections(detections=detections)
    tracked_detections = smoother.update_with_detections(tracked_detections)
    
    labels = process_detections(frame_time, tracked_detections, frame)
    
    annotated_frame = frame.copy()
    annotated_frame = trace_annotator.annotate(scene=annotated_frame, detections=tracked_detections)
    annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=tracked_detections)

    # cv2.line(annotated_frame, (0, LINE_1_Y), (annotated_frame.shape[1], LINE_1_Y), (0, 255, 0), 1)
    # cv2.line(annotated_frame, (0, LINE_2_Y), (annotated_frame.shape[1], LINE_2_Y), (0, 0, 255), 1)
    
    # text_anchor = sv.Point(x=50, y=50)
    # sv.draw_text(scene=annotated_frame, text=f"Lane Counters: {lane_counters}", text_anchor=text_anchor, text_color=sv.Color.WHITE, background_color=sv.Color.GREEN)
    
    for zone in lane_zones:
        sv.draw_polygon(annotated_frame, zone.polygon, color=sv.Color.WHITE, thickness=1)

            # Display lane counters on the frame
    lane_1_count = lane_counters[0]  # Count for Lane 1
    lane_2_count = lane_counters[1]  # Count for Lane 2

    # Draw text for each lane counter
    text_anchor_1 = sv.Point(x=50, y=50)  # Position for Lane 1 count
    sv.draw_text(scene=annotated_frame, 
                 text=f"Lane 1: {lane_1_count}", 
                 text_anchor=text_anchor_1, 
                 text_color=sv.Color.WHITE, 
                 background_color=sv.Color.BLACK)

    text_anchor_2 = sv.Point(x=50, y=100)  # Position for Lane 2 count
    sv.draw_text(scene=annotated_frame, 
                 text=f"Lane 2: {lane_2_count}", 
                 text_anchor=text_anchor_2, 
                 text_color=sv.Color.WHITE, 
                 background_color=sv.Color.BLACK)

    
    annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=tracked_detections, labels=labels)

    # Optional: Visualize transform points
    for point in SOURCE_POINTS:
        cv2.circle(annotated_frame, tuple(point.astype(int)), 5, (0, 255, 0), -1)

    # Visualize sweet spots
    for sweet_spot in SWEET_SPOTS.values():
        sv.draw_polygon(annotated_frame, sweet_spot, color=sv.Color.RED, thickness=2)

    cv2.imshow('AI Policing System', annotated_frame)

    if cv2.waitKey(0) & 0xFF == ord('q'):
        break

video_info.release()
cv2.destroyAllWindows()

