from ultralytics import YOLO
from pathlib import Path

DATASET_YAML = Path(r"C:\ENTRAINEMENT\robotflow\data.yaml")
MODEL_SIZE = "yolo11n"
PROJECT_NAME = "bee_yolo11n_robotflow"

def main():
    if not DATASET_YAML.exists():
        print("[ERROR] Dataset non trouve")
        return

    print(f"[INFO] Chargement modele {MODEL_SIZE}.pt...")
    model = YOLO(f"{MODEL_SIZE}.pt")

    print(f"[INFO] Entrainement dataset ROBOTFLOW")
    print(f"[INFO] Ratio 7.09x - BIEN MEILLEUR que les precedents !")
    print(f"[INFO] 2119 images train, ratio equilibre")
    print(f"[INFO] Config: cache=False pour eviter crash RAM")

    results = model.train(
        data=str(DATASET_YAML),
        epochs=100,
        imgsz=640,
        batch=48,
        name=PROJECT_NAME,
        patience=20,
        device=0,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=3,
        cos_lr=True,
        close_mosaic=10,
        amp=True,
        val=True,
        plots=True,
        save=True,
        save_period=10,
        cache=False,  # Desactive pour eviter crash RAM
        workers=4,    # Reduit de 8 a 4
    )

    print("\n[OK] Entrainement termine !")
    print(f"Poids: runs/detect/{PROJECT_NAME}/weights/best.pt")
    print(f"\nCe modele devrait BIEN fonctionner car ratio equilibre !")
    print(f"\nTestez avec:")
    print(f'  python test_video.py "Hallway Entrance for bee hives..mp4"')

if __name__ == "__main__":
    main()
