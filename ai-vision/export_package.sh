#!/bin/bash
# Script pour créer un package d'export avec tous les fichiers nécessaires

EXPORT_DIR="ruche_export_$(date +%Y%m%d_%H%M%S)"
echo "Création du package d'export dans: $EXPORT_DIR"

# Créer structure
mkdir -p "$EXPORT_DIR"/{models,scripts,docs,config}

# Copier le modèle NCNN (le plus performant)
echo "Copie du modèle NCNN..."
cp -r runs/detect/bee_yolo11n_robotflow/weights/best_ncnn_model "$EXPORT_DIR/models/"

# Optionnel: Copier aussi les autres modèles si besoin
echo "Copie des autres modèles (optionnel)..."
cp runs/detect/bee_yolo11n_robotflow/weights/best.pt "$EXPORT_DIR/models/" 2>/dev/null || true
cp runs/detect/bee_yolo11n_robotflow/weights/best_saved_model/best_int8.tflite "$EXPORT_DIR/models/" 2>/dev/null || true

# Copier les scripts Python
echo "Copie des scripts..."
cp ruche_detector.py "$EXPORT_DIR/scripts/"
cp pi_bench.py "$EXPORT_DIR/scripts/"
cp setup_and_run_bench.py "$EXPORT_DIR/scripts/"
cp pi_bench_optimized.py "$EXPORT_DIR/scripts/" 2>/dev/null || true

# Copier la documentation
echo "Copie de la documentation..."
cp RAPPORT_BENCHMARK_PERFORMANCE.md "$EXPORT_DIR/docs/"
cp requirements.txt "$EXPORT_DIR/"

# Copier la config dataset
echo "Copie de la configuration dataset..."
cp robotflow/data.yaml "$EXPORT_DIR/config/" 2>/dev/null || true

# Créer un README d'installation
cat > "$EXPORT_DIR/README.md" << 'EOF'
# Détection Abeilles/Frelons - Package d'export

## 📦 Contenu du package

- `models/` - Modèles YOLO optimisés (NCNN, PyTorch, TFLite)
- `scripts/` - Scripts Python pour détection et benchmark
- `docs/` - Documentation complète des performances
- `config/` - Configuration du dataset

## 🚀 Installation rapide

### 1. Installer les dépendances

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Tester la détection

```bash
# Mode démo (visualisation)
python scripts/ruche_detector.py --mode demo --source 0 --show

# Mode production (comptage 24/7)
python scripts/ruche_detector.py --mode production --source 0
```

## ⚡ Performances sur Raspberry Pi 4

| Configuration | FPS | Usage CPU | Recommandation |
|---------------|-----|-----------|----------------|
| NCNN 256px (démo) | 3.9-4.0 | 70-80% | ✅ Démos visuelles |
| NCNN 320px stride=10 | ~1.5 | 30-40% | ✅ Production 24/7 |

## 📊 Modèles disponibles

1. **best_ncnn_model/** - ⭐ RECOMMANDÉ (meilleur FPS)
   - Format: NCNN
   - Taille: 10 MB
   - FPS: 3.9-4.0

2. **best.pt** - PyTorch (baseline)
   - Format: PyTorch
   - Taille: 5.5 MB
   - FPS: 2.1-2.2

3. **best_int8.tflite** - TFLite quantifié
   - Format: TensorFlow Lite INT8
   - Taille: 2.8 MB (le plus léger)
   - FPS: 3.0

## 🎯 Optimisations possibles

### Pour augmenter FPS:
- Réduire `imgsz` (256 → 192)
- Augmenter `vid_stride` (2 → 4)
- Augmenter `conf` (0.25 → 0.35)

### Pour économiser CPU:
- Augmenter `vid_stride` (2 → 10)
- Désactiver `--show`
- Réduire `max_det` (30 → 10)

## 📝 Documentation

Voir `docs/RAPPORT_BENCHMARK_PERFORMANCE.md` pour:
- Résultats complets des benchmarks
- Comparaison détaillée des modèles
- Guide d'optimisation système
- Recommandations production

## 🔧 Configuration avancée

### Mode performance CPU (Raspberry Pi)

```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Réduire mémoire GPU

```bash
sudo nano /boot/firmware/config.txt
# Ajouter: gpu_mem=64
sudo reboot
```

## 📞 Support

Classes détectées:
- 0: frelon
- 1: abeille

Configuration: `config/data.yaml`
EOF

# Créer une archive
echo "Création de l'archive..."
tar -czf "${EXPORT_DIR}.tar.gz" "$EXPORT_DIR"

echo ""
echo "✅ Package créé avec succès!"
echo "   Dossier: $EXPORT_DIR/"
echo "   Archive: ${EXPORT_DIR}.tar.gz"
echo ""
echo "Contenu:"
du -sh "$EXPORT_DIR"
echo ""
ls -lh "${EXPORT_DIR}.tar.gz"
