"""
SmartHive Backend - FastAPI Application

Serveur principal de la plateforme SmartHive gérant :
- API REST pour réception données capteurs et détections
- WebSocket pour push temps réel vers frontend
- Client MQTT pour réception données TTN (The Things Network)
- Persistance CSV des mesures historiques

Auteur: SmartHive Team
Version: 1.0.0
"""

import asyncio
import csv
import json
import os
from datetime import datetime
from typing import List, Optional

import paho.mqtt.client as mqtt
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_TITLE = "SmartHive API"
APP_VERSION = "1.0.0"

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt.univ-cotedazur.fr")
MQTT_PORT = int(os.getenv("MQTT_PORT", "443"))
MQTT_USER = os.getenv("MQTT_USER", "fablab2122")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "2122")
MQTT_TOPIC = os.getenv(
    "MQTT_TOPIC",
    "ttn/v3/fablab2223@ttn/devices/arduino-abp-ruche-ym/up"
)

# CSV Configuration
HISTORY_FILE = os.getenv("HISTORY_FILE", "history.csv")
CSV_HEADERS = ["timestamp", "temperature", "humidity", "mass", "luminosity", "bee_count", "hornet_count"]


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LoraData(BaseModel):
    """Modèle de données pour réception payload LoRaWAN."""
    temperature: float = Field(..., description="Température en degrés Celsius", ge=-40, le=80)
    mass: float = Field(..., description="Masse de la ruche en kg", ge=0, le=200)


class YoloData(BaseModel):
    """Modèle de données pour réception statistiques YOLO."""
    bee_count: int = Field(..., description="Nombre d'abeilles détectées", ge=0)
    hornet_count: int = Field(..., description="Nombre de frelons détectés", ge=0)


class SensorState(BaseModel):
    """État complet des capteurs."""
    temperature: float = 0.0
    humidity: float = 0.0
    mass: float = 0.0
    luminosity: float = 0.0
    bee_count: int = 0
    hornet_count: int = 0


# ============================================================================
# CSV LOGGER
# ============================================================================

class CSVLogger:
    """
    Gestionnaire de persistance des mesures en format CSV.
    
    Thread-safe pour écriture append-only. Crée le fichier avec
    headers si inexistant.
    """
    
    def __init__(self, filename: str = HISTORY_FILE) -> None:
        """
        Initialise le logger CSV.
        
        Args:
            filename: Chemin du fichier CSV d'historique
        """
        self.filename = filename
        self.headers = CSV_HEADERS
        self._init_file()
    
    def _init_file(self) -> None:
        """Crée le fichier avec headers s'il n'existe pas."""
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)
    
    def log(self, state: 'SystemState') -> None:
        """
        Ajoute une ligne de données au CSV.
        
        Args:
            state: État système à persister
        """
        with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().isoformat(),
                state.temperature,
                state.humidity,
                state.mass,
                state.luminosity,
                state.bee_count,
                state.hornet_count
            ])
    
    def get_history(self, limit: Optional[int] = None) -> List[dict]:
        """
        Récupère l'historique complet ou partiel.
        
        Args:
            limit: Nombre maximum de lignes (None = tout)
            
        Returns:
            Liste de dictionnaires représentant les entrées CSV
        """
        data = []
        if os.path.exists(self.filename):
            with open(self.filename, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append({
                        "timestamp": row.get("timestamp", ""),
                        "temperature": float(row.get("temperature", 0) or 0),
                        "humidity": float(row.get("humidity", 0) or 0),
                        "mass": float(row.get("mass", 0) or 0),
                        "luminosity": float(row.get("luminosity", 0) or 0),
                        "bee_count": int(row.get("bee_count", 0) or 0),
                        "hornet_count": int(row.get("hornet_count", 0) or 0)
                    })
        
        if limit:
            data = data[-limit:]
        return data


# ============================================================================
# SYSTEM STATE
# ============================================================================

class SystemState:
    """
    État global du système en mémoire (Singleton).
    
    Maintient les dernières valeurs connues de tous les capteurs.
    Thread-safe par design (GIL Python + opérations atomiques).
    """
    
    def __init__(self) -> None:
        """Initialise l'état avec des valeurs par défaut."""
        self.temperature: float = 0.0
        self.humidity: float = 0.0
        self.mass: float = 0.0
        self.luminosity: float = 0.0
        self.bee_count: int = 0
        self.hornet_count: int = 0
    
    def to_dict(self) -> dict:
        """Convertit l'état en dictionnaire sérialisable."""
        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "mass": self.mass,
            "luminosity": self.luminosity,
            "bee_count": self.bee_count,
            "hornet_count": self.hornet_count
        }


# ============================================================================
# WEBSOCKET MANAGER
# ============================================================================

class ConnectionManager:
    """
    Gestionnaire des connexions WebSocket actives.
    
    Implémente le pattern Observer pour broadcaster les mises à jour
    à tous les clients connectés.
    """
    
    def __init__(self) -> None:
        """Initialise la liste des connexions actives."""
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accepte une nouvelle connexion WebSocket.
        
        Args:
            websocket: Connexion WebSocket entrante
        """
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Supprime une connexion de la liste active.
        
        Args:
            websocket: Connexion à fermer
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str) -> None:
        """
        Envoie un message à tous les clients connectés.
        
        Les erreurs de connexion sont silencieusement ignorées
        (le client sera nettoyé lors de la prochaine erreur).
        
        Args:
            message: Message JSON à diffuser
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        # Nettoyage des connexions mortes
        for conn in disconnected:
            self.disconnect(conn)


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="API Backend SmartHive - Surveillance apicole IoT",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production: spécifier les origines exactes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
state = SystemState()
logger = CSVLogger()
manager = ConnectionManager()
main_loop: Optional[asyncio.AbstractEventLoop] = None

# MQTT Client
mqtt_client = mqtt.Client(transport="websockets")


# ============================================================================
# MQTT HANDLERS
# ============================================================================

def on_connect(client: mqtt.Client, userdata: any, flags: dict, rc: int) -> None:
    """
    Callback appelé lors de la connexion MQTT.
    
    Args:
        client: Instance client MQTT
        userdata: Données utilisateur (non utilisé)
        flags: Flags de connexion
        rc: Code de retour (0 = succès)
    """
    print(f"[MQTT] Connecté au broker avec code {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"[MQTT] Abonné au topic: {MQTT_TOPIC}")


def on_message(client: mqtt.Client, userdata: any, msg: mqtt.MQTTMessage) -> None:
    """
    Callback appelé lors de réception d'un message MQTT.
    
    Parse le payload TTN et met à jour l'état système.
    
    Args:
        client: Instance client MQTT
        userdata: Données utilisateur (non utilisé)
        msg: Message MQTT reçu
    """
    global main_loop
    try:
        payload = json.loads(msg.payload.decode())
        
        # Extraction données TTN
        if "uplink_message" in payload and "decoded_payload" in payload["uplink_message"]:
            decoded = payload["uplink_message"]["decoded_payload"]
            changed = False
            
            if "temperature1" in decoded:
                state.temperature = float(decoded["temperature1"])
                changed = True
            if "masse" in decoded:
                state.mass = float(decoded["masse"])
                changed = True
            if "humd" in decoded:
                state.humidity = float(decoded["humd"])
                changed = True
            if "lum" in decoded:
                state.luminosity = float(decoded["lum"])
                changed = True
            
            if changed:
                logger.log(state)
                
                # Broadcast via WebSocket
                if main_loop and manager.active_connections:
                    message = json.dumps({
                        "type": "sensor_update",
                        "data": {
                            "temperature": state.temperature,
                            "humidity": state.humidity,
                            "mass": state.mass,
                            "luminosity": state.luminosity
                        }
                    })
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(message), 
                        main_loop
                    )
                    
    except Exception as e:
        print(f"[MQTT] Erreur traitement message: {e}")


# Configuration MQTT
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.ws_set_options(path="/ws")
mqtt_client.tls_set()  # TLS requis pour port 443


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/api/lora-uplink", response_model=dict)
async def receive_lora(data: LoraData) -> dict:
    """
    Reçoit les données des capteurs LoRa (endpoint manuel).
    
    Alternative à MQTT pour tests ou gateways directs.
    
    Args:
        data: Données LoRa (température, masse)
        
    Returns:
        Confirmation de réception
    """
    state.temperature = data.temperature
    state.mass = data.mass
    logger.log(state)
    
    await manager.broadcast(json.dumps({
        "type": "sensor_update",
        "data": {
            "temperature": state.temperature,
            "mass": state.mass
        }
    }))
    
    return {"status": "ok", "received": data.dict()}


@app.post("/api/detections", response_model=dict)
async def receive_detections(data: YoloData) -> dict:
    """
    Reçoit les statistiques de détection YOLO.
    
    Args:
        data: Compteurs d'abeilles et frelons détectés
        
    Returns:
        Confirmation de réception
    """
    state.bee_count = data.bee_count
    state.hornet_count = data.hornet_count
    logger.log(state)
    
    await manager.broadcast(json.dumps({
        "type": "detection_update",
        "data": {
            "bee_count": state.bee_count,
            "hornet_count": state.hornet_count
        }
    }))
    
    return {"status": "ok", "received": data.dict()}


@app.get("/api/history")
async def get_history() -> List[dict]:
    """
    Récupère l'historique complet des mesures.
    
    Returns:
        Liste chronologique des entrées CSV
    """
    return logger.get_history()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Endpoint WebSocket pour communication temps réel.
    
    Envoie l'état initial à la connexion, puis maintient
    la connexion ouverte pour broadcasts futurs.
    """
    await manager.connect(websocket)
    
    # Envoi état initial
    await websocket.send_text(json.dumps({
        "type": "init",
        "data": state.to_dict()
    }))
    
    try:
        while True:
            # Maintien connexion (heartbeat optionnel ici)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# LIFECYCLE EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event() -> None:
    """Initialisation au démarrage de l'application."""
    global main_loop
    main_loop = asyncio.get_running_loop()
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"[Startup] MQTT Client démarré sur {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"[Startup] Erreur connexion MQTT: {e}")
        print("[Startup] Le serveur fonctionne sans MQTT (mode simulation)")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Nettoyage à l'arrêt de l'application."""
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("[Shutdown] MQTT Client arrêté")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=2000,
        reload=True,
        log_level="info"
    )
