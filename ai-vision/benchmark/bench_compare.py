"""
Benchmark multi-modèles (TFLite/NCNN/PyTorch) sur Raspberry Pi.

Usage minimal (auto-détection des vidéos dans ./videos, ./Videos, ./vidéos, ~/Videos, etc.):
  python pi_bench.py --models models/best_saved_model/best_int8.tflite --show

Exemple explicite:
  python pi_bench.py --models models/best_saved_model/best_int8.tflite,models/best.pt \
                     --videos "videos/*.mp4" --imgsz 416 --vid-stride 2 --conf 0.25 --show

Notes:
  - TFLite: nécessite tflite-runtime ou tensorflow.
  - NCNN: nécessite le package Python 'ncnn' si vous voulez tester 'best_ncnn_model'.
  - PyTorch (.pt): nécessite torch CPU, recommandé sur Pi 5 (aarch64).
"""

import argparse
from pathlib import Path
import glob
from typing import List, Tuple

from ultralytics import YOLO


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--models", type=str, required=True,
                   help="Chemins des modèles séparés par des virgules (ex: a.tflite,best.pt,best_ncnn_model)")
    p.add_argument("--videos", type=str, default="",
                   help="Glob de vidéos, dossier, ou '0' pour webcam. Si omis: auto-scan dossier vidéos")
    p.add_argument("--imgsz", type=int, default=416)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--iou", type=float, default=0.45)
    p.add_argument("--vid-stride", dest="vid_stride", type=int, default=2)
    p.add_argument("--max-det", dest="max_det", type=int, default=30)
    p.add_argument("--save", action="store_true")
    p.add_argument("--show", action="store_true")
    return p.parse_args()


VIDEO_EXTS = ("*.mp4", "*.avi", "*.mov", "*.mkv", "*.m4v")


def scan_dir_for_videos(d: Path) -> List[str]:
    if not d.exists() or not d.is_dir():
        return []
    found = []
    for ext in VIDEO_EXTS:
        found.extend(sorted(str(p) for p in d.glob(ext)))
    return found


def auto_find_videos() -> List[str]:
    cwd = Path.cwd()
    home = Path.home()
    candidates = [
        cwd / "videos", cwd / "Videos", cwd / "vidéos", cwd / "Vidéos",
        home / "videos", home / "Videos", home / "vidéos", home / "Vidéos",
    ]
    for d in candidates:
        vids = scan_dir_for_videos(d)
        if vids:
            return vids
    # fallback: vidéos au cwd
    vids = []
    for ext in VIDEO_EXTS:
        vids.extend(sorted(str(p) for p in Path('.').glob(ext)))
    return vids


def expand_videos(videos_arg: str) -> List[str]:
    v = (videos_arg or "").strip()
    if not v:
        return auto_find_videos()
    if v.isdigit():
        return [v]  # webcam index
    p = Path(v)
    if p.exists() and p.is_dir():
        return scan_dir_for_videos(p)
    # otherwise treat as glob
    return sorted(glob.glob(v))


def run_bench(model_path: str, video_path: str, args) -> Tuple[int, float]:
    model = YOLO(model_path)

    if video_path.strip().isdigit():
        source = int(video_path.strip())
    else:
        source = video_path

    total_ms = 0.0
    frame_count = 0

    results_gen = model.predict(
        source=source,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        vid_stride=args.vid_stride,
        max_det=args.max_det,
        classes=None,
        save=args.save,
        show=args.show,
        stream=True,
        verbose=False,
    )

    for r in results_gen:
        sp = getattr(r, "speed", None) or {}
        ms = float(sp.get("preprocess", 0.0)) + float(sp.get("inference", 0.0)) + float(sp.get("postprocess", 0.0))
        total_ms += ms
        frame_count += 1

    avg_fps = (1000.0 / (total_ms / frame_count)) if frame_count > 0 else 0.0
    return frame_count, avg_fps


def main():
    args = parse_args()
    model_paths = [m.strip() for m in args.models.split(",") if m.strip()]
    videos = expand_videos(args.videos)

    if not model_paths:
        print("[ERROR] Aucun modele fourni")
        return
    if not videos:
        print("[ERROR] Aucune vidéo trouvée (essayé ./videos, ./Videos, ./vidéos, ~/Videos, etc.)")
        print("        Fournissez --videos ou placez vos fichiers dans un de ces dossiers.")
        return

    print("=== BENCH START ===")
    print(f"Models: {model_paths}")
    print(f"Videos: {videos}")
    print(f"Params: imgsz={args.imgsz}, conf={args.conf}, iou={args.iou}, vid_stride={args.vid_stride}, max_det={args.max_det}")

    for m in model_paths:
        mp = Path(m)
        if not (mp.exists() or m.strip().isdigit()):
            print(f"[WARN] Modele introuvable: {m} — on saute.")
            continue

        print(f"\n--- Model: {m} ---")
        total_frames = 0
        weighted_sum = 0.0  # somme(fps * frames) pour moyenne ponderee

        for v in videos:
            vp = v
            if not v.strip().isdigit() and not Path(v).exists():
                print(f"[WARN] Video introuvable: {v} — on saute.")
                continue

            print(f"[INFO] Video: {vp}")
            try:
                frames, avg_fps = run_bench(m, vp, args)
                print(f"[OK] {frames} frames, FPS moyen = {avg_fps:.2f}")
                total_frames += frames
                weighted_sum += avg_fps * max(frames, 1)
            except Exception as e:
                print(f"[ERROR] Echec bench {m} sur {vp}: {e}")

        overall_fps = (weighted_sum / total_frames) if total_frames > 0 else 0.0
        print(f"[SUMMARY] Model {m}: {total_frames} frames cumulés, FPS moyen global = {overall_fps:.2f}")

    print("\n=== BENCH END ===")


if __name__ == "__main__":
    main()
