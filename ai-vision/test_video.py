from ultralytics import YOLO
from pathlib import Path
import sys

BEST = Path("runs/detect/bee_yolo11n_robotflow/weights/best.pt")

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python test_video.py <chemin_video>")
        print("\nExemple:")
        print("  python test_video.py ma_video_abeilles.mp4")
        print("  python test_video.py C:\\Videos\\ruche.mp4")
        return

    video_path = sys.argv[1]
    if not Path(video_path).exists():
        print(f"❌ Vidéo non trouvée : {video_path}")
        return

    if not BEST.exists():
        print(f"❌ Modèle non trouvé : {BEST}")
        print("⚠️ Lancez d'abord l'entraînement avec: python train.py")
        return

    print(f"📦 Chargement du modèle {BEST}...")
    model = YOLO(str(BEST))

    print(f"\n🎥 Détection sur vidéo : {video_path}")
    print("⏳ Traitement en cours...")
    print("\n📊 Le modèle va:")
    print("  • Détecter les abeilles et frelons image par image")
    print("  • Dessiner des boîtes de couleur autour")
    print("  • Afficher le nom (abeille/frelon) + % de confiance")
    print("  • Sauvegarder la vidéo annotée")

    # Traitement de la vidéo
    results = model.predict(
        source=video_path,
        conf=0.10,          # Seuil BAISSE à 10% pour détecter plus
        iou=0.45,           # Seuil NMS pour éviter doublons
        imgsz=640,          # Taille utilisée pendant entraînement
        save=True,          # Sauvegarder la vidéo annotée
        show=False,         # Ne pas afficher (peut causer erreurs sur certains PC)
        stream=True,        # Traitement streaming (économise RAM)
        verbose=True,       # Afficher progression
        line_width=2,       # Épaisseur des boîtes
        show_labels=True,   # Afficher labels
        show_conf=True,     # Afficher confiance
    )

    # Compter les détections
    total_frames = 0
    total_detections = 0
    bee_count = 0
    hornet_count = 0

    print("\n🔍 Analyse frame par frame:")
    for r in results:
        total_frames += 1
        boxes = r.boxes

        if len(boxes) > 0:
            total_detections += len(boxes)
            for box in boxes:
                cls = int(box.cls[0])
                if cls == 1:  # abeille
                    bee_count += 1
                elif cls == 0:  # frelon
                    hornet_count += 1

    print(f"\n✅ Traitement terminé !")
    print(f"📁 Vidéo annotée sauvegardée dans: runs/detect/predict/")
    print(f"\n📊 Statistiques:")
    print(f"  • Frames analysées : {total_frames}")
    print(f"  • Détections totales : {total_detections}")
    print(f"  • 🐝 Abeilles détectées : {bee_count}")
    print(f"  • 🐝 Frelons détectés : {hornet_count}")
    print(f"\n💡 Ouvrez la vidéo pour voir les boîtes et labels en action !")

if __name__ == "__main__":
    main()
