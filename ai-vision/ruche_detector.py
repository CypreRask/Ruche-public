"""
Détecteur abeilles/frelons avec 2 modes:
- MODE PRODUCTION: Comptage continu, économie CPU (1-2 FPS, stride=10)
- MODE DEMO: Visualisation fluide pour présentation (4-5 FPS, stride=2)

Usage:
    # Mode production (comptage)
    python ruche_detector.py --mode production

    # Mode démo (visualisation)
    python ruche_detector.py --mode demo --show
"""

import argparse
from pathlib import Path
import time
from datetime import datetime
from ultralytics import YOLO


class RucheDetector:
    def __init__(self, model_path: str, mode: str = "production"):
        """
        Args:
            model_path: Chemin vers le modèle NCNN
            mode: "production" ou "demo"
        """
        self.model = YOLO(model_path)
        self.mode = mode
        self.detection_count = {"abeille": 0, "frelon": 0}
        self.start_time = time.time()

        # Configuration selon le mode
        if mode == "production":
            self.config = {
                "imgsz": 320,       # Qualité suffisante
                "conf": 0.35,       # Plus strict = moins de calculs
                "iou": 0.5,
                "vid_stride": 10,   # Traite 1 frame sur 10 → ~1-2 FPS effectif
                "max_det": 10,
                "show": False,
                "save": False,
            }
            print("🐝 MODE PRODUCTION: Comptage continu, économie CPU")
        else:  # demo
            self.config = {
                "imgsz": 640,       # Meilleure résolution pour éviter l'effet "zoomé"
                "conf": 0.25,
                "iou": 0.45,
                "vid_stride": 2,    # Traite 1 frame sur 2 → ~4-5 FPS
                "max_det": 30,
                "show": True,       # Affichage visuel
                "save": False,
            }
            print("📺 MODE DEMO: Visualisation fluide pour présentation")

    def stream_detection(self, source=0):
        """
        Générateur qui yield (frame, stats, detections)
        frame: image annotée (ou non)
        stats: dict {fps, beer_count, ...}
        detections: dict détaillé
        """
        print(f"Démarrage détection sur source: {source}")
        
        # Generator from YOLO
        results_gen = self.model.predict(
            source=source,
            **self.config,
            stream=True,
            verbose=False,
        )

        frame_idx = 0
        
        try:
            for r in results_gen:
                frame_idx += 1
                
                # Compteurs instantanés pour cette frame
                current_bees = 0
                current_hornets = 0
                
                if r.boxes is not None:
                    for box in r.boxes:
                        cls = int(box.cls[0])
                        # 0=frelon, 1=abeille
                        if cls == 0:
                            current_hornets += 1
                        elif cls == 1:
                            current_bees += 1
                            
                # Mise à jour compteurs globaux
                self.detection_count["frelon"] += current_hornets
                self.detection_count["abeille"] += current_bees

                # Préparation frame annotée
                # Note: On force r.plot() pour avoir les boites, mais sans "show=True" dans config pour éviter display local
                annotated_frame = r.plot()

                # Ajouter les stats textuelles sur l'image (comme dans l'ancienne version)
                # Nécessite cv2
                import cv2
                
                # Calcul FPS
                elapsed = time.time() - self.start_time
                fps = frame_idx / elapsed if elapsed > 0 else 0

                # Dessiner les overlays
                cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Abeilles: {current_bees}", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(annotated_frame, f"Frelons: {current_hornets}", (10, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                stats = {
                    "fps": fps,
                    "frame_idx": frame_idx,
                    "bees": current_bees,
                    "hornets": current_hornets,
                    "total_bees": self.detection_count["abeille"],
                    "total_hornets": self.detection_count["frelon"]
                }
                
                yield annotated_frame, stats

        except Exception as e:
            print(f"Erreur flux détection: {e}")
            raise e

    def run(self, source=0):
        """
        Mode autonome (CLI)
        """
        print(f"\n{'='*60}")
        print(f"Démarrage détection - Mode: {self.mode.upper()}")
        print(f"Source: {source}")
        print(f"Config: imgsz={self.config['imgsz']}, stride={self.config['vid_stride']}")
        print(f"{'='*60}\n")

        last_log_time = time.time()
        frame_idx = 0

        try:
            for frame, stats in self.stream_detection(source):
                frame_idx = stats["frame_idx"]
                
                # Affichage si demandé par config (vidéo locale)
                if self.config.get("show", False):
                    import cv2
                    cv2.imshow("Ruche Detector", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # Log console en production
                current_time = time.time()
                if self.mode == "production" and (current_time - last_log_time) >= 10:
                    self._log_stats(stats)
                    last_log_time = current_time

        except KeyboardInterrupt:
            print("\n\n⚠️  Arrêt détection (Ctrl+C)")
        except Exception as e:
            print(f"Erreur d'exécution: {e}")
        finally:
            self._log_final_stats(frame_idx)

    def _log_stats(self, stats):
        """Affiche les stats intermédiaires"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stats:")
        print(f"  Frames: {stats['frame_idx']} | FPS: {stats['fps']:.2f}")
        print(f"  Abeilles: {stats['bees']} (Total: {stats['total_bees']})")
        print(f"  Frelons: {stats['hornets']} (Total: {stats['total_hornets']})")
    def _log_final_stats(self, frame_idx):
        """Affiche les stats finales"""
        elapsed = time.time() - self.start_time
        fps_effectif = frame_idx / elapsed if elapsed > 0 else 0

        print(f"\n{'='*60}")
        print("STATISTIQUES FINALES")
        print(f"{'='*60}")
        print(f"Durée totale: {elapsed:.1f}s")
        print(f"Frames traités: {frame_idx}")
        print(f"FPS effectif: {fps_effectif:.2f}")
        print(f"Détections:")
        print(f"  - Abeilles: {self.detection_count['abeille']}")
        print(f"  - Frelons: {self.detection_count['frelon']}")
        print(f"  - TOTAL: {sum(self.detection_count.values())}")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Détecteur ruche abeilles/frelons")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["production", "demo"],
        default="production",
        help="Mode de fonctionnement (production=comptage, demo=visualisation)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="runs/detect/bee_yolo11n_robotflow/weights/best_ncnn_model",
        help="Chemin vers le modèle NCNN"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="Source vidéo (0 pour webcam, chemin pour fichier)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Forcer l'affichage visuel (surcharge config mode)"
    )

    args = parser.parse_args()

    # Vérifier que le modèle existe
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ Erreur: Modèle introuvable à {model_path}")
        print(f"   Assurez-vous que le modèle NCNN est bien exporté.")
        return

    # Convertir source
    source = 0 if args.source == "0" else args.source

    # Créer détecteur
    detector = RucheDetector(str(model_path), mode=args.mode)

    # Surcharger affichage si demandé
    if args.show:
        detector.config["show"] = True

    # Lancer
    detector.run(source)


if __name__ == "__main__":
    main()
