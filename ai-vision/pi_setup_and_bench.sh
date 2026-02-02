#!/usr/bin/env bash
set -euo pipefail

# Script d'installation + benchmark pour Raspberry Pi
# Usage:
#   bash pi_setup_and_bench.sh \
#     --models "models/best_saved_model/best_int8.tflite,models/best.pt,models/best_ncnn_model" \
#     --videos "videos/*.mp4" \
#     [--show] [--with-ncnn] [--with-torch]

MODELS=""
VIDEOS=""
SHOW=0
WITH_NCNN=0
WITH_TORCH=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --models)
      MODELS="$2"; shift 2;;
    --videos)
      VIDEOS="$2"; shift 2;;
    --show)
      SHOW=1; shift;;
    --with-ncnn)
      WITH_NCNN=1; shift;;
    --with-torch)
      WITH_TORCH=1; shift;;
    *)
      echo "Arg inconnu: $1"; exit 1;;
  esac
done

if [[ -z "$MODELS" ]]; then
  echo "Usage: $0 --models <m1,m2,...> [--videos \"videos/*.mp4\"] [--show] [--with-ncnn] [--with-torch]"
  echo "       (si --videos omis, pi_bench.py auto-detecte ./videos, ./Videos, ./vidéos, ~/Videos, etc.)"
  exit 1
fi

echo "[INFO] Detect arch..."
ARCH=$(uname -m)
echo "[INFO] Arch: $ARCH"

VENV_DIR="$HOME/beeenv"
PYTHON_BIN=python3

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[INFO] Create venv at $VENV_DIR"
  $PYTHON_BIN -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "[INFO] Upgrade pip"
python -m pip install -U pip setuptools wheel

echo "[INFO] Install base deps"
# Ultralytics (pin proche de ton export) + OpenCV + tflite-runtime
python -m pip install "ultralytics==8.3.227"

# OpenCV peut être lourd; on tente headless d'abord
if ! python -c "import cv2" 2>/dev/null; then
  python -m pip install opencv-python-headless || true
fi
if ! python -c "import cv2" 2>/dev/null; then
  python -m pip install opencv-python || true
fi

# TFLite runtime
if ! python -c "import tflite_runtime" 2>/dev/null; then
  python -m pip install --prefer-binary tflite-runtime || true
fi

# NCNN optionnel
if [[ $WITH_NCNN -eq 1 ]]; then
  echo "[INFO] Install ncnn (optionnel)"
  python -m pip install ncnn || true
fi

# Torch optionnel (utile pour .pt) — plutôt sur Pi 5 (aarch64)
if [[ $WITH_TORCH -eq 1 ]]; then
  echo "[INFO] Install torch CPU (optionnel)"
  python -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision || true
fi

echo "[INFO] Run bench"
SHOW_FLAG=""
if [[ $SHOW -eq 1 ]]; then SHOW_FLAG="--show"; fi

if [[ -n "$VIDEOS" ]]; then
  python pi_bench.py --models "$MODELS" --videos "$VIDEOS" --imgsz 416 --vid-stride 2 --conf 0.25 $SHOW_FLAG
else
  python pi_bench.py --models "$MODELS" --imgsz 416 --vid-stride 2 --conf 0.25 $SHOW_FLAG
fi

echo "[OK] Bench terminé"
