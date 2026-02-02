from ultralytics import YOLO
from pathlib import Path

# Poids par defaut (best.pt issu de ton entrainement)
BEST = Path("runs/detect/bee_yolo11n_robotflow/weights/best.pt")

# YAML du dataset pour calibrer l'INT8 (important pour la precision)
DATASET_YAML = Path("robotflow/data.yaml")

DEFAULT_IMGSZ = 416  # plus leger pour Raspberry Pi


def main():
    if not BEST.exists():
        print(f"[ERROR] Poids non trouves : {BEST}")
        return

    model = YOLO(str(BEST))

    print(f"[INFO] Export NCNN (imgsz={DEFAULT_IMGSZ})...")
    ncnn_dir = model.export(format="ncnn", imgsz=DEFAULT_IMGSZ)
    print("[OK] NCNN :", ncnn_dir)

    print(f"[INFO] Export TFLite INT8 (imgsz={DEFAULT_IMGSZ})...")
    if DATASET_YAML.exists():
        print(f"[INFO] Calibration INT8 avec: {DATASET_YAML}")
        tflite = model.export(format="tflite", int8=True, imgsz=DEFAULT_IMGSZ, data=str(DATASET_YAML))
    else:
        print("[WARN] Dataset YAML introuvable, export INT8 sans calibration explicite")
        tflite = model.export(format="tflite", int8=True, imgsz=DEFAULT_IMGSZ)
    print("[OK] TFLite INT8 :", tflite)

    print("\n[OK] Export termine !")
    print("Formats generes:")
    print("  - NCNN")
    print("  - TFLite INT8 (quantifie, leger)")


if __name__ == "__main__":
    main()
