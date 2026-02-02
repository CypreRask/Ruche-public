from pathlib import Path
import yaml
import random

DATASET = Path(r"C:\ENTRAINEMENT\robotflow")

print("="*60)
print("VERIFICATION RAPIDE ROBOTFLOW")
print("="*60)

# 1. YAML
with open(DATASET / "data.yaml", 'r') as f:
    config = yaml.safe_load(f)

print(f"\n[YAML]")
print(f"  Path: {config.get('path')}")
print(f"  Classes: {config.get('names')}")

# 2. Compter fichiers
train_imgs = list((DATASET / "train" / "images").glob("*.*"))
train_lbls = list((DATASET / "train" / "labels").glob("*.txt"))
val_imgs = list((DATASET / "valid" / "images").glob("*.*"))
val_lbls = list((DATASET / "valid" / "labels").glob("*.txt"))

print(f"\n[FICHIERS]")
print(f"  Train: {len(train_imgs)} images, {len(train_lbls)} labels")
print(f"  Val: {len(val_imgs)} images, {len(val_lbls)} labels")

# 3. Vérifier 5 correspondances
print(f"\n[CORRESPONDANCES] (5 exemples)")
for img in random.sample(train_imgs, 5):
    lbl = DATASET / "train" / "labels" / f"{img.stem}.txt"
    status = "[OK]" if lbl.exists() else "[MANQUANT]"
    print(f"  {status} {img.name}")

# 4. Analyser classes
print(f"\n[CLASSES] (100 labels échantillon)")
c0, c1 = 0, 0
for lbl in random.sample(train_lbls, min(100, len(train_lbls))):
    with open(lbl, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                if int(parts[0]) == 0:
                    c0 += 1
                else:
                    c1 += 1

print(f"  Classe 0 (frelon): {c0}")
print(f"  Classe 1 (abeille): {c1}")

# 5. Exemple de label
print(f"\n[EXEMPLE LABEL]")
example = random.choice(train_lbls)
print(f"  Fichier: {example.name}")
with open(example, 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[:3]):
        parts = line.strip().split()
        cls = int(parts[0])
        name = config['names'][cls]
        print(f"    Ligne {i+1}: classe {cls} ({name})")

print("\n" + "="*60)
print("[VERDICT]")
if len(train_imgs) > 2000 and len(train_lbls) > 2000:
    print("  [OK] Dataset complet et pret !")
    print("\n  Lancez: python train_robotflow.py")
else:
    print("  [WARN] Dataset incomplet ?")
print("="*60)
