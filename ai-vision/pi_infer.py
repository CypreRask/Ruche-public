"""
Inference minimal pour Raspberry Pi (caméra ou vidéo)

Usage exemples:
  - Caméra: python pi_infer.py --source 0 --weights best.tflite
  - Vidéo : python pi_infer.py --source ruche.mp4 --weights best.tflite --save

Par défaut optimisé Pi:
  imgsz=416, conf=0.25, iou=0.45, vid_stride=2, max_det=30
"""

import argparse
from pathlib import Path
from ultralytics import YOLO


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--weights", type=str, default="best.tflite", help="Chemin vers le modele (.tflite)")
    p.add_argument("--source", type=str, default="0", help="Source (index camera ou chemin video)")
    p.add_argument("--imgsz", type=int, default=416)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--iou", type=float, default=0.45)
    p.add_argument("--vid-stride", dest="vid_stride", type=int, default=2)
    p.add_argument("--max-det", dest="max_det", type=int, default=30)
    p.add_argument("--save", action="store_true", help="Sauver la video annotee")
    p.add_argument("--show", action="store_true", help="Afficher en direct")
    return p.parse_args()


def main():
    args = parse_args()

    weights = Path(args.weights)
    if not weights.exists():
        print(f"[ERROR] Modele introuvable: {weights}")
        return

    # Convertit "0" en 0 pour webcam
    source: object
    if str(args.source).isdigit():
        source = int(args.source)
    else:
        source = args.source

    print(f"[INFO] Chargement du modele: {weights}")
    model = YOLO(str(weights))

    print("[INFO] Demarrage inference...")
    results = model.predict(
        source=source,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        vid_stride=args.vid_stride,
        max_det=args.max_det,
        classes=[0, 1],
        save=args.save,
        show=args.show,
        stream=False,
        show_labels=True,
        show_conf=True,
        line_width=2,
        verbose=True,
    )

    # Si sauvegarde activee, Ultralytics ecrit dans runs/detect/predict/
    if args.save:
        print("[OK] Video annotee sauvee dans runs/detect/predict/")


if __name__ == "__main__":
    main()

