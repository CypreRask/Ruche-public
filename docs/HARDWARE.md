# Partie Hardware - Ruche Connectée

Le système complet comprend une **ruche physique instrumentée** qui communique avec notre backend via LoRaWAN.

## Architecture Hardware

```
┌─────────────────────────────────────────┐
│  RUCHE PHYSIQUE                         │
│  ┌─────────────────────────────────┐   │
│  │  Arduino + Shield LoRaWAN       │   │
│  │                                 │   │
│  │  Capteurs connectés :           │   │
│  │  • HX711      → Poids (0.1g)    │   │
│  │  • DS18B20    → Temp interne    │   │
│  │  • Si7021     → Temp/Hum externe│   │
│  │  • TSL2591    → Luminosité (lux)│   │
│  └──────────┬──────────────────────┘   │
└─────────────┼───────────────────────────┘
              │ LoRaWAN 868 MHz (ABP)
              ▼
       ┌──────────────┐
       │  Gateway TTN │  (The Things Network)
       └──────┬───────┘
              │ MQTT over WSS (port 443)
              ▼
       ┌──────────────┐
       │  Backend API │  ← CE REPO (Python/FastAPI)
       │  (ce repo)   │
       └──────────────┘
```

## Firmware Arduino

Le firmware Arduino (C++/Arduino framework) gère :

### 1. Acquisition
- **Lecture capteurs** via I2C (Si7021, TSL2591), OneWire (DS18B20), GPIO (HX711)
- **Calibration** du capteur de poids (tare et facteur de calibration)
- **Fréquence** : Lecture et envoi toutes les 20 secondes

### 2. Encodage
- Conversion des 5 valeurs float (4 bytes chacune) en payload de 20 bytes
- Utilisation d'une `union` C pour le casting byte-to-float

### 3. Transmission LoRaWAN
- **Protocole** : ABP (Activation By Personalization)
- **Fréquence** : 868 MHz (bande européenne)
- **SF** : SF7 (Spreading Factor 7) pour débit élevé
- **Duty cycle** : Respect de la réglementation (1%)

### Payload (20 bytes)
```c
struct Payload {
  float temperature1;  // DS18B20 (interne)
  float masse;         // HX711 (poids ruche)
  float temp3;         // Si7021 (externe)
  float humidity;      // Si7021 (%)
  float luminosity;    // TSL2591 (lux)
};
```

## Intégration Backend

Le backend reçoit les données via MQTT :
- **Broker** : `mqtt.univ-cotedazur.fr:443` (WSS/TLS)
- **Topic** : `ttn/v3/{application}@ttn/devices/{device}/up`
- **Format** : JSON avec `uplink_message.decoded_payload`

Exemple de message reçu :
```json
{
  "uplink_message": {
    "decoded_payload": {
      "temperature1": 24.5,
      "masse": 45.2,
      "humd": 65.0,
      "lum": 320.5
    }
  }
}
```

## Note

Ce firmware a été développé par mon encadrant académique dans le cadre du projet. 
Il n'est pas inclus dans ce repository qui se concentre sur la **stack logicielle et l'intelligence artificielle** que j'ai développées.
