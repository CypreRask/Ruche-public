import cv2
import uvicorn
import asyncio
import threading
import time
import requests
import queue
import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union
from ruche_detector import RucheDetector

# Configuration
BACKEND_URL = "http://localhost:2000/api/detections"
# Utilisation du modèle .pt (PyTorch) pour une détection stable sur PC
MODEL_PATH = "runs/detect/bee_yolo11n_robotflow/weights/best.pt"
VIDEO_DIR = r"D:\SmartHive-main\videostest"

app = FastAPI(title="Ruche Video Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class VideoState:
    def __init__(self):
        self.source = 0  # Default to webinar 0
        self.running = True
        self.lock = threading.Lock()
        self.current_frame = None
        self.detector = None
        self.needs_restart = False
        self.last_detection = {"bees": 0, "hornets": 0}

state = VideoState()
state.detector = RucheDetector(MODEL_PATH, mode="demo")
# Disable internal show, we manually plot in stream_detection
state.detector.config["show"] = False

class SourceConfig(BaseModel):
    source: Union[str, int]

def scan_cameras(max_cameras=5):
    available_cameras = []
    print("Scanning for cameras...")
    for i in range(max_cameras):
        try:
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) # CAP_DSHOW is faster on Windows
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(i)
                cap.release()
        except Exception:
            pass
    print(f"Cameras found: {available_cameras}")
    return available_cameras

def scan_video_files():
    if not os.path.exists(VIDEO_DIR):
        try:
            os.makedirs(VIDEO_DIR)
        except:
            return []
    
    files = []
    types = ('*.mp4', '*.avi', '*.mov', '*.mkv', '*.webm')
    for t in types:
        files.extend(glob.glob(os.path.join(VIDEO_DIR, t)))
    
    # Trier par nom pour avoir l'ordre 1, 2, 3...
    files.sort()
    
    # Return just filenames to the frontend
    return [os.path.basename(f) for f in files]

@app.get("/scan_devices")
async def get_devices():
    cams = scan_cameras()
    files = scan_video_files()
    return {
        "cameras": cams,
        "files": files
    }

@app.post("/set_source")
async def set_source(config: SourceConfig):
    new_source = config.source
    
    # Logic to interpret source
    final_source = new_source

    if isinstance(new_source, str):
        # Check if it's a digit (webcam string representation)
        if new_source.isdigit():
            final_source = int(new_source)
        # Check if it's a known file in our demo folder
        elif os.path.exists(os.path.join(VIDEO_DIR, new_source)):
            final_source = os.path.join(VIDEO_DIR, new_source)
        # Otherwise, assume it's a URL or absolute path provided by user
        else:
            final_source = new_source
    
    print(f"Switching source to: {final_source}")
    with state.lock:
        state.source = final_source
        state.needs_restart = True
    
    return {"status": "ok", "source": str(final_source)}

def detection_loop():
    """Main background loop handling video and detection"""
    while state.running:
        current_source = state.source
        
        try:
            print(f"Starting detection loop on {current_source}")
            # Get generator
            gen = state.detector.stream_detection(source=current_source)
            
            # Loop over frames from generator
            for frame, stats in gen:
                # Check for source change request
                if state.needs_restart:
                    print("Restarting detector due to source change...")
                    state.needs_restart = False
                    break # Break inner loop to restart with new source
                
                # Update frame for MJPEG stream
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    with state.lock:
                        state.current_frame = buffer.tobytes()
                        state.last_detection = {"bees": stats["bees"], "hornets": stats["hornets"]}
                
                # Send stats to main backend periodically
                # (Simple throttling can be added if needed, main.py handles high freq okay?)
                # Let's throttle slightly to 2Hz
                if stats["frame_idx"] % 5 == 0:
                    try:
                        requests.post(BACKEND_URL, json={
                            "bee_count": stats["bees"],
                            "hornet_count": stats["hornets"]
                        }, timeout=0.1)
                    except:
                        pass # Ignore network errors to keep video smooth
            
            # If generator finishes (end of video file), go to next video
            if not state.needs_restart:
                print("Video ended, switching to next...")
                # Get list of videos
                videos = scan_video_files()
                if len(videos) > 1:
                    # Find current index and go to next
                    current_name = os.path.basename(str(current_source))
                    try:
                        current_idx = videos.index(current_name)
                        next_idx = (current_idx + 1) % len(videos)
                        next_video = videos[next_idx]
                        print(f"Switching to next video: {next_video}")
                        with state.lock:
                            state.source = os.path.join(VIDEO_DIR, next_video)
                            state.needs_restart = True
                    except ValueError:
                        # Current video not in list, restart same
                        time.sleep(0.5)
                else:
                    # Only one video, loop it
                    print("Looping same video...")
                    time.sleep(0.5)

        except Exception as e:
            print(f"Error in detection loop: {e}")
            time.sleep(2) # Prevent rapid crash loops

def generate_mjpeg():
    """Generator for MJPEG stream"""
    while True:
        with state.lock:
            frame_data = state.current_frame
        
        if frame_data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        
        time.sleep(0.04) # ~25 FPS max

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_mjpeg(), media_type="multipart/x-mixed-replace;boundary=frame")

@app.on_event("startup")
def startup_event():
    # Start detection in background thread
    t = threading.Thread(target=detection_loop, daemon=True)
    t.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2002)
