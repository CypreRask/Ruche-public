"""
Détection en direct sur ESP32-CAM avec gestion robuste du stream
"""
import cv2
import time
from ultralytics import YOLO
import requests
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import cv2
import threading

# Configuration
import sys
import argparse

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--source", type=str, default="WAIT", help="Video source (URL or 0 for webcam)")
args, unknown = parser.parse_known_args()

# Handle numeric source (webcam index)
source_input = args.source
if source_input.isdigit():
    ESP32_URL = int(source_input)
else:
    ESP32_URL = source_input

MODEL_PATH = "runs/detect/bee_yolo11n_robotflow/weights/best_ncnn_model"
BACKEND_URL = "http://localhost:2000/api/detections"

# MJPEG Streaming & Control Setup
app = FastAPI()

# Enable CORS for frontend control
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

output_frame = None
lock = threading.Lock()

# Global control variables
current_source = None # Will be set during init
pending_source = None # If set, main loop will switch to this

class SourceConfig(BaseModel):
    source: str

@app.post("/set_source")
async def set_source(config: SourceConfig):
    global pending_source
    print(f"Demande de changement de source: {config.source}")
    pending_source = config.source
    return {"status": "ok", "message": f"Source changée pour: {config.source}"}

def generate_frames():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
               bytearray(encodedImage) + b'\r\n')

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")

# Start Server in background thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

print(f"✓ Serveur de streaming démarré sur http://localhost:2002/video_feed")
IMGSZ = 256
CONF = 0.25
VID_STRIDE = 2
SEND_INTERVAL = 1.0  # Envoyer les données toutes les 1 seconde

print("="*60)
print("DÉTECTION EN DIRECT - ESP32-CAM")
print("="*60)
print(f"URL: {ESP32_URL}")
print(f"Modèle: NCNN (optimisé)")
print(f"Config: imgsz={IMGSZ}, stride={VID_STRIDE}")
print("="*60)

# Charger le modèle
print("\nChargement du modèle NCNN...")
model = YOLO(MODEL_PATH)
print("✓ Modèle chargé")

# Init source logic
# Start without source until set via API
current_source = None 
pending_source = source_input if source_input != "WAIT" else None

print("\nEn attente de configuration de source...")
# cap = cv2.VideoCapture(current_source, cv2.CAP_FFMPEG) # Removed initial capture

if pending_source:
    print(f"Source initiale demandée: {pending_source}")

print("✓ Connexion établie")
print("\nDémarrage de la détection (appuyez sur 'q' pour quitter)...\n")

frame_count = 0
start_time = time.time()
detection_count = {"abeille": 0, "frelon": 0}
skip_counter = 0
last_send_time = time.time()

def send_data_to_backend(bee, hornet):
    try:
        requests.post(BACKEND_URL, json={"bee_count": bee, "hornet_count": hornet}, timeout=0.5)
    except Exception as e:
        print(f"Erreur d'envoi au backend: {e}")

try:
    cap = None
    while True:
        # Check for source change request
        if pending_source is not None:
            print(f"🔄 Changement de source en cours vers : {pending_source}")
            if cap:
                cap.release()
            
            # Handle numeric source
            if pending_source.isdigit():
                current_source = int(pending_source)
            else:
                current_source = pending_source
                
            print(f"Connexion à {current_source}...")
            try:
                cap = cv2.VideoCapture(current_source, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                pending_source = None
                print("✓ Nouvelle source connectée")
            except Exception as e:
                 print(f"Erreur de connexion: {e}")

        if cap is None or not cap.isOpened():
             time.sleep(1) # Wait for source configuration
             continue

        ret, frame = cap.read()

        if not ret:
            print("⚠️  Perte de connexion, tentative de reconnexion...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(current_source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            continue

        frame_count += 1
        skip_counter += 1

        # Traiter seulement 1 frame sur VID_STRIDE
        if skip_counter < VID_STRIDE:
            continue

        skip_counter = 0

        # Inférence YOLO
        results = model.predict(
            frame,
            imgsz=IMGSZ,
            conf=CONF,
            verbose=False,
        )

        # Réinitialiser les compteurs pour cette frame (ou garder cumulatif ?)
        # Ici on compte ce qu'on voit sur l'image courante
        current_bees = 0
        current_hornets = 0

        # Compter les détections
        if results[0].boxes is not None:
            for box in results[0].boxes:
                cls = int(box.cls[0])
                if cls == 0:
                    current_hornets += 1
                elif cls == 1:
                    current_bees += 1
        
        # Mise à jour des globaux pour l'affichage (optionnel, selon logique voulue)
        detection_count["abeille"] = current_bees
        detection_count["frelon"] = current_hornets

        # Envoi au backend périodique
        current_time = time.time()
        if current_time - last_send_time > SEND_INTERVAL:
            # Envoi dans un thread pour ne pas bloquer la vidéo
            threading.Thread(target=send_data_to_backend, args=(current_bees, current_hornets)).start()
            last_send_time = current_time

        # Afficher l'image avec détections
        try:
            annotated_frame = results[0].plot()
        except (ValueError, TypeError):
            # Si erreur d'affichage, utiliser frame original
            annotated_frame = frame.copy()

        # Ajouter infos FPS et compteur
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0

        cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Abeilles: {detection_count['abeille']}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(annotated_frame, f"Frelons: {detection_count['frelon']}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Detection Abeilles/Frelons - ESP32-CAM", annotated_frame)
        
        # Update global frame for streaming
        with lock:
            output_frame = annotated_frame.copy()

        # Log toutes les 50 frames
        if frame_count % 50 == 0:
            print(f"[{frame_count}] FPS: {fps:.2f} | Abeilles: {detection_count['abeille']} | Frelons: {detection_count['frelon']}")

        # Quitter avec 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n⚠️  Arrêt demandé par l'utilisateur")
            break

except KeyboardInterrupt:
    print("\n⚠️  Arrêt (Ctrl+C)")

finally:
    # Statistiques finales
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0

    print("\n" + "="*60)
    print("STATISTIQUES FINALES")
    print("="*60)
    print(f"Durée: {elapsed:.1f}s")
    print(f"Frames traités: {frame_count}")
    print(f"FPS moyen: {fps:.2f}")
    print(f"Détections (Dernier état):")
    print(f"  - Abeilles: {detection_count['abeille']}")
    print(f"  - Frelons: {detection_count['frelon']}")
    print("="*60)

    if cap:
        cap.release()
    cv2.destroyAllWindows()
