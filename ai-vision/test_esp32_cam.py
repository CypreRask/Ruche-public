"""
Test rapide de connexion à l'ESP32-CAM
"""
import cv2
import sys

# URLs communes pour ESP32-CAM
urls_to_test = [
    "http://192.168.X.X/stream",
    "http://192.168.X.X:81/stream",
    "http://192.168.X.X/cam-hi.jpg",
    "http://your_esp32_ip",
]

print("Test de connexion ESP32-CAM...")
print("="*60)

for url in urls_to_test:
    print(f"\nTest: {url}")
    try:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✓ SUCCÈS! Résolution: {frame.shape[1]}x{frame.shape[0]}")
                print(f"URL fonctionnelle: {url}")
                cap.release()
                sys.exit(0)
            else:
                print("  → Connexion OK mais pas de frame")
        else:
            print("  → Impossible d'ouvrir")
        cap.release()
    except Exception as e:
        print(f"  → Erreur: {e}")

print("\n❌ Aucune URL ne fonctionne")
print("\nVérifiez:")
print("  1. L'ESP32-CAM est allumé et connecté au réseau")
print("  2. L'adresse IP est correcte (192.168.1.84)")
print("  3. Le firmware ESP32-CAM utilise bien un stream HTTP")
