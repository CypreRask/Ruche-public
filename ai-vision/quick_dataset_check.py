"""
Script ultra-rapide pour verifier si un dataset est BON ou MAUVAIS
Usage: python quick_dataset_check.py "chemin/vers/dataset"
"""

import sys
from pathlib import Path
import yaml
import numpy as np

if len(sys.argv) < 2:
    print("Usage: python quick_dataset_check.py <chemin_dataset>")
    print('Exemple: python quick_dataset_check.py "C:\\datasets\\mon_dataset"')
    exit(1)

DATASET = Path(sys.argv[1])

print("="*60)
print(f"ANALYSE RAPIDE: {DATASET.name}")
print("="*60)

if not DATASET.exists():
    print(f"[ERROR] Dossier non trouve: {DATASET}")
    exit(1)

# 1. Trouver YAML
yaml_files = list(DATASET.glob("*.yaml")) + list(DATASET.glob("*.yml"))
if not yaml_files:
    print("[ERROR] Aucun fichier .yaml trouve")
    exit(1)

with open(yaml_files[0], 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print(f"\nClasses: {config.get('names')}")

# 2. Compter images
train_imgs = list(DATASET.rglob("train/images/*.jpg")) + list(DATASET.rglob("train/images/*.png"))
val_imgs = list(DATASET.rglob("val*/images/*.jpg")) + list(DATASET.rglob("val*/images/*.png"))

print(f"Images train: {len(train_imgs)}")
print(f"Images val: {len(val_imgs)}")

# 3. Analyser 500 labels aleatoires (rapide)
all_labels = list(DATASET.rglob("train/labels/*.txt")) + list(DATASET.rglob("val*/labels/*.txt"))
sample_labels = np.random.choice(all_labels, min(500, len(all_labels)), replace=False)

class0_boxes = []
class1_boxes = []

for lbl in sample_labels:
    with open(lbl, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            cls = int(parts[0])
            w, h = float(parts[3]), float(parts[4])
            area = w * h

            if cls == 0:
                class0_boxes.append(area)
            elif cls == 1:
                class1_boxes.append(area)

if class0_boxes and class1_boxes:
    c0_mean = np.mean(class0_boxes)
    c1_mean = np.mean(class1_boxes)
    ratio = max(c0_mean, c1_mean) / min(c0_mean, c1_mean)

    print(f"\nClasse 0: {c0_mean*100:.2f}% image (moyenne)")
    print(f"Classe 1: {c1_mean*100:.2f}% image (moyenne)")
    print(f"\nRATIO: {ratio:.2f}x")

    print("\n" + "="*60)
    if ratio < 3:
        print("VERDICT: EXCELLENT ! Utilisez ce dataset !")
    elif ratio < 10:
        print("VERDICT: BON. Dataset utilisable.")
    elif ratio < 30:
        print("VERDICT: MOYEN. Risque de biais.")
    else:
        print("VERDICT: MAUVAIS. Trop de biais de taille.")
    print("="*60)
else:
    print("\n[ERROR] Pas assez de donnees pour analyser")
