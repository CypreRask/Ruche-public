#!/usr/bin/env python3
"""
Script automatique pour:
1. Créer un environnement virtuel
2. Installer les dépendances nécessaires
3. Lancer le benchmark visuel avec les vidéos

Usage:
    python3 setup_and_run_bench.py
"""

import subprocess
import sys
import os
from pathlib import Path

# Configuration
VENV_DIR = Path.home() / "beeenv"
PROJECT_DIR = Path(__file__).parent.absolute()

def run_cmd(cmd, cwd=None, check=True):
    """Exécute une commande et affiche la sortie en temps réel"""
    print(f"\n{'='*60}")
    print(f"Exécution: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*60}")

    if isinstance(cmd, str):
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check)
    else:
        result = subprocess.run(cmd, cwd=cwd, check=check)

    return result

def create_venv():
    """Crée l'environnement virtuel"""
    print(f"\n[1/4] Création de l'environnement virtuel dans {VENV_DIR}...")

    if VENV_DIR.exists():
        print(f"    -> L'environnement existe déjà, on le réutilise")
        return

    run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])
    print("    ✓ Environnement virtuel créé")

def get_pip_path():
    """Retourne le chemin vers pip dans le venv"""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    else:
        return VENV_DIR / "bin" / "pip"

def get_python_path():
    """Retourne le chemin vers python dans le venv"""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"

def install_dependencies():
    """Installe les dépendances"""
    print("\n[2/4] Installation des dépendances...")

    pip_path = get_pip_path()

    # Mise à jour de pip
    print("\n    -> Mise à jour de pip...")
    run_cmd([str(pip_path), "install", "-U", "pip", "setuptools", "wheel"])

    # Installation d'ultralytics (YOLO)
    print("\n    -> Installation d'ultralytics...")
    run_cmd([str(pip_path), "install", "ultralytics==8.3.227"])

    # Installation d'OpenCV
    print("\n    -> Installation d'OpenCV...")
    try:
        run_cmd([str(pip_path), "install", "opencv-python-headless"], check=False)
    except:
        print("    -> Essai avec opencv-python...")
        run_cmd([str(pip_path), "install", "opencv-python"])

    # Installation de tflite-runtime (optionnel)
    print("\n    -> Installation de tflite-runtime (optionnel)...")
    try:
        run_cmd([str(pip_path), "install", "--prefer-binary", "tflite-runtime"], check=False)
    except:
        print("    -> tflite-runtime non disponible, continuons sans...")

    print("\n    ✓ Toutes les dépendances sont installées")

def find_best_model():
    """Trouve le meilleur modèle disponible"""
    model_candidates = [
        PROJECT_DIR / "runs/detect/bee_yolo11n_robotflow/weights/best_saved_model/best_int8.tflite",
        PROJECT_DIR / "runs/detect/bee_yolo11n_robotflow/weights/best.pt",
        PROJECT_DIR / "runs/detect/bee_yolo11n_robotflow/weights/best.onnx",
    ]

    for model in model_candidates:
        if model.exists():
            return str(model)

    return None

def find_videos():
    """Trouve les vidéos de test"""
    video_dirs = [
        PROJECT_DIR / "vidéos",
        PROJECT_DIR / "videos",
        PROJECT_DIR / "Videos",
    ]

    for vdir in video_dirs:
        if vdir.exists() and vdir.is_dir():
            videos = list(vdir.glob("*.mp4")) + list(vdir.glob("*.avi")) + list(vdir.glob("*.mov"))
            if videos:
                return str(vdir / "*.mp4")

    return ""

def run_benchmark():
    """Lance le benchmark"""
    print("\n[3/4] Préparation du benchmark...")

    model_path = find_best_model()
    if not model_path:
        print("    ✗ Aucun modèle trouvé!")
        return False

    print(f"    -> Modèle sélectionné: {model_path}")

    videos = find_videos()
    if not videos:
        print("    ! Aucune vidéo spécifique trouvée, auto-détection...")
    else:
        print(f"    -> Vidéos: {videos}")

    print("\n[4/4] Lancement du benchmark visuel...")
    print("\n" + "="*60)
    print("BENCHMARK EN COURS - Appuyez sur 'q' pour quitter")
    print("="*60 + "\n")

    python_path = get_python_path()
    bench_script = PROJECT_DIR / "pi_bench.py"

    cmd = [
        str(python_path),
        str(bench_script),
        "--models", model_path,
        "--show",  # Mode visuel
        "--imgsz", "416",
        "--conf", "0.25",
        "--vid-stride", "2",
    ]

    if videos:
        cmd.extend(["--videos", videos])

    try:
        run_cmd(cmd, cwd=PROJECT_DIR)
        print("\n    ✓ Benchmark terminé avec succès!")
        return True
    except KeyboardInterrupt:
        print("\n    ! Benchmark interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(f"\n    ✗ Erreur pendant le benchmark: {e}")
        return False

def main():
    print("="*60)
    print("SETUP ET BENCHMARK AUTOMATIQUE - DÉTECTION ABEILLES/FRELONS")
    print("="*60)

    try:
        # Étape 1: Créer venv
        create_venv()

        # Étape 2: Installer dépendances
        install_dependencies()

        # Étape 3 & 4: Lancer benchmark
        success = run_benchmark()

        if success:
            print("\n" + "="*60)
            print("✓ TOUT EST TERMINÉ AVEC SUCCÈS!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("! Le benchmark s'est terminé avec des avertissements")
            print("="*60)

    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
