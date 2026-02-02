"""
Benchmark optimisé pour Raspberry Pi - visant 5+ FPS

Optimisations:
- Taille image réduite (320, 256, 224)
- Stride augmenté
- max_det réduit
- Pas d'affichage
"""

import argparse
from pathlib import Path
import time
from ultralytics import YOLO


def run_optimized_bench(model_path: str, video_path: str, imgsz: int, vid_stride: int):
    """Benchmark optimisé"""
    print(f"\n{'='*60}")
    print(f"Model: {Path(model_path).name}")
    print(f"Video: {Path(video_path).name}")
    print(f"Config: imgsz={imgsz}, stride={vid_stride}")
    print(f"{'='*60}\n")

    model = YOLO(model_path)

    start_time = time.time()
    frame_count = 0

    results_gen = model.predict(
        source=video_path,
        imgsz=imgsz,
        conf=0.25,
        iou=0.45,
        vid_stride=vid_stride,
        max_det=10,  # Réduit de 30 à 10
        classes=None,
        save=False,
        show=False,  # Pas d'affichage
        stream=True,
        verbose=False,
    )

    for r in results_gen:
        frame_count += 1

    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0.0

    print(f"✓ {frame_count} frames en {elapsed:.2f}s → {fps:.2f} FPS\n")
    return fps


def main():
    # Chemins
    base_dir = Path(__file__).parent
    models = {
        "NCNN": base_dir / "runs/detect/bee_yolo11n_robotflow/weights/best_ncnn_model",
        "TFLite INT8": base_dir / "runs/detect/bee_yolo11n_robotflow/weights/best_saved_model/best_int8.tflite",
        "PyTorch": base_dir / "runs/detect/bee_yolo11n_robotflow/weights/best.pt",
    }

    video = base_dir / "vidéos/Bees LOVE flowers.mp4"

    # Configurations à tester
    configs = [
        {"imgsz": 320, "vid_stride": 2, "desc": "320px, stride=2 (équilibré)"},
        {"imgsz": 256, "vid_stride": 2, "desc": "256px, stride=2 (rapide)"},
        {"imgsz": 224, "vid_stride": 3, "desc": "224px, stride=3 (ultra-rapide)"},
        {"imgsz": 320, "vid_stride": 4, "desc": "320px, stride=4 (skip frames)"},
    ]

    print("="*60)
    print("BENCHMARK OPTIMISÉ POUR RASPBERRY PI")
    print("Objectif: Atteindre 5+ FPS")
    print("="*60)

    results = {}

    # Test chaque modèle avec chaque config
    for model_name, model_path in models.items():
        if not model_path.exists():
            print(f"[SKIP] {model_name}: modèle introuvable")
            continue

        results[model_name] = {}

        for config in configs:
            desc = config["desc"]
            print(f"\n>>> {model_name} - {desc}")

            try:
                fps = run_optimized_bench(
                    str(model_path),
                    str(video),
                    config["imgsz"],
                    config["vid_stride"]
                )
                results[model_name][desc] = fps
            except Exception as e:
                print(f"[ERROR] {e}")
                results[model_name][desc] = 0.0

    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES RÉSULTATS")
    print("="*60)

    for model_name, configs_results in results.items():
        print(f"\n{model_name}:")
        for desc, fps in configs_results.items():
            status = "✓ OBJECTIF ATTEINT!" if fps >= 5.0 else ""
            print(f"  {desc:40s} → {fps:6.2f} FPS {status}")

    # Meilleur résultat
    print("\n" + "="*60)
    best_fps = 0.0
    best_config = ""
    best_model = ""

    for model_name, configs_results in results.items():
        for desc, fps in configs_results.items():
            if fps > best_fps:
                best_fps = fps
                best_config = desc
                best_model = model_name

    print(f"🏆 MEILLEUR RÉSULTAT: {best_model}")
    print(f"   Configuration: {best_config}")
    print(f"   Performance: {best_fps:.2f} FPS")
    print("="*60)


if __name__ == "__main__":
    main()
