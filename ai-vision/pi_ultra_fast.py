"""
Test ULTRA-RAPIDE pour atteindre 5+ FPS sur Raspberry Pi

Optimisations extrêmes:
- imgsz 192, 160, 128
- No preprocessing overhead
- Skip frames agressif
"""

import time
from pathlib import Path
from ultralytics import YOLO


def test_ultra_fast():
    base_dir = Path(__file__).parent

    # Meilleur modèle selon les tests précédents
    model_path = base_dir / "runs/detect/bee_yolo11n_robotflow/weights/best_ncnn_model"
    video_path = base_dir / "vidéos/Bees LOVE flowers.mp4"

    print("="*60)
    print("TEST ULTRA-RAPIDE - Objectif: 5+ FPS")
    print("="*60)

    # Configurations ultra-optimisées
    configs = [
        {"imgsz": 192, "stride": 2},
        {"imgsz": 160, "stride": 2},
        {"imgsz": 192, "stride": 4},
        {"imgsz": 128, "stride": 3},
    ]

    model = YOLO(str(model_path))

    for config in configs:
        imgsz = config["imgsz"]
        stride = config["stride"]

        print(f"\n>>> Test: imgsz={imgsz}, stride={stride}")

        start = time.time()
        frame_count = 0

        results_gen = model.predict(
            source=str(video_path),
            imgsz=imgsz,
            conf=0.3,  # Un peu plus élevé pour réduire les calculs
            iou=0.5,
            vid_stride=stride,
            max_det=10,
            save=False,
            show=False,
            stream=True,
            verbose=False,
        )

        for r in results_gen:
            frame_count += 1

        elapsed = time.time() - start
        fps = frame_count / elapsed

        status = "✓ OBJECTIF ATTEINT!" if fps >= 5.0 else f"({5.0-fps:.2f} FPS restant)"
        print(f"    Résultat: {fps:.2f} FPS - {frame_count} frames en {elapsed:.2f}s {status}")


if __name__ == "__main__":
    test_ultra_fast()
