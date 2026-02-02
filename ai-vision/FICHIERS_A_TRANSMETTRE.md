# 📦 Fichiers à transmettre pour optimisation

## ✅ Package d'export créé

**Fichier principal** : `ruche_export_20251111_214044.tar.gz` (16 MB)

**Emplacement** : `/home/fablab/Ruche/ENTRAINEMENT - Copie/ruche_export_20251111_214044.tar.gz`

---

## 📂 Contenu du package

### 1. Modèles (dossier `models/`)

| Fichier | Format | Taille | FPS | Recommandation |
|---------|--------|--------|-----|----------------|
| **best_ncnn_model/** | NCNN | 10 MB | **3.9-4.0** | ⭐ **MEILLEUR** |
| best.pt | PyTorch | 5.5 MB | 2.1-2.2 | Baseline |
| best_int8.tflite | TFLite INT8 | 2.8 MB | 3.0 | Léger |

**Modèle NCNN** (prioritaire) :
```
models/best_ncnn_model/
├── model.ncnn.bin      # Poids (10 MB)
├── model.ncnn.param    # Architecture (23 KB)
├── metadata.yaml       # Métadonnées
└── model_ncnn.py       # Wrapper Python
```

### 2. Scripts Python (dossier `scripts/`)

| Script | Description | Usage |
|--------|-------------|-------|
| **ruche_detector.py** | Script principal 2 modes | ⭐ **À utiliser** |
| pi_bench.py | Benchmark multi-modèles | Test performance |
| pi_bench_optimized.py | Benchmark configurations | Analyse |
| setup_and_run_bench.py | Setup automatique | Installation |

### 3. Documentation (dossier `docs/`)

- **RAPPORT_BENCHMARK_PERFORMANCE.md** : Analyse complète des résultats
  - Comparaison tous les modèles
  - Optimisations testées
  - Recommandations finales

### 4. Configuration (dossier `config/`)

- **data.yaml** : Configuration du dataset
  ```yaml
  nc: 2
  names: ['frelon', 'abeille']
  ```

### 5. Fichiers racine

- **README.md** : Guide d'installation et utilisation
- **requirements.txt** : Dépendances Python

---

## 🚀 Guide d'utilisation rapide

### Extraire le package

```bash
tar -xzf ruche_export_20251111_214044.tar.gz
cd ruche_export_20251111_214044
```

### Installer les dépendances

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Tester immédiatement

```bash
# Mode démo (visualisation fluide ~4 FPS)
python scripts/ruche_detector.py --mode demo --source 0 --show

# Mode production (comptage continu ~1.5 FPS, CPU faible)
python scripts/ruche_detector.py --mode production --source 0
```

---

## 🎯 Points clés pour l'optimisation

### Performances actuelles (Raspberry Pi 4)

| Configuration | FPS | CPU | Qualité |
|---------------|-----|-----|---------|
| NCNN 256px, stride=2 | 3.9-4.0 | 70% | ✅ Bon pour démo |
| NCNN 320px, stride=10 | ~1.5 | 30% | ✅ Parfait 24/7 |

### Pistes d'optimisation identifiées

1. **Utiliser NCNN natif C++** (pas via Ultralytics)
   - Gain estimé : +100% FPS (4 FPS → 8 FPS)
   - Supprimer overhead Python/Ultralytics

2. **Réduire résolution d'entrée**
   - 256px → 192px : ~+20% FPS
   - 256px → 160px : ~+50% FPS

3. **Optimisations système Pi**
   - Mode performance CPU
   - Réduire mémoire GPU (gpu_mem=64)
   - Dissipateur thermique

4. **Post-processing optimisé**
   - NMS plus rapide
   - Réduire `max_det` (30 → 10)
   - Augmenter `conf` (0.25 → 0.35)

5. **Hardware upgrade**
   - Raspberry Pi 5 : +100% CPU → ~8 FPS
   - Google Coral TPU : +500% → 20+ FPS

---

## 📊 Benchmarks détaillés

Voir `docs/RAPPORT_BENCHMARK_PERFORMANCE.md` pour :
- ✅ Tests complets 4 modèles × 8 configurations
- ✅ Comparaison NCNN vs TFLite vs PyTorch
- ✅ Impact résolution et stride
- ✅ Recommandations production vs démo

---

## 🔧 Modifications possibles du code

### 1. Optimiser le preprocessing (ruche_detector.py)

```python
# Actuel : Utilise Ultralytics avec overhead
model.predict(source, imgsz=256, ...)

# Optimisation possible : Preprocessing manuel
import cv2
frame = cv2.resize(frame, (256, 256))
# Inférence NCNN directe sans Ultralytics
```

### 2. Multithreading pour caméra

```python
# Thread 1 : Capture frames
# Thread 2 : Inférence
# Thread 3 : Comptage/logging
```

### 3. Buffer circulaire frames

```python
# Éviter reallocation mémoire
import numpy as np
buffer = np.zeros((10, 256, 256, 3), dtype=np.uint8)
```

---

## 📞 Informations techniques

**Environnement de test :**
- Hardware : Raspberry Pi 4 (ARM Cortex-A72 @ 1.5 GHz)
- OS : Raspberry Pi OS 64-bit (Bookworm)
- Python : 3.13
- Ultralytics : 8.3.227
- NCNN : 1.0.20250916

**Dataset :**
- Classes : 2 (frelon=0, abeille=1)
- Modèle : YOLO11n (nano)
- Entraînement : 2238 images Roboflow

**Classes d'objets :**
```python
class_names = {
    0: "frelon",
    1: "abeille"
}
```

---

## 📝 Checklist transmission

- [x] Modèle NCNN complet
- [x] Scripts Python fonctionnels
- [x] Documentation benchmark complète
- [x] Configuration dataset
- [x] Requirements.txt
- [x] README installation
- [x] Guide optimisation

**Fichier à envoyer** : `ruche_export_20251111_214044.tar.gz` (16 MB)

---

## 🎯 Objectifs d'optimisation suggérés

1. **Court terme** : Atteindre 5+ FPS stable
2. **Moyen terme** : Réduire CPU <50% pour mode démo
3. **Long terme** : Support temps réel 10+ FPS

**Méthode recommandée** : Utiliser NCNN C++ natif avec bindings Python optimisés.
