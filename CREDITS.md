# Crédits et Bibliothèques

## 🧠 Computer Vision & Deep Learning

- **[Ultralytics YOLO](https://docs.ultralytics.com/)** - Framework de détection d'objets
  - Modèle YOLOv11n (nano) pré-entraîné sur COCO
  - API d'export : NCNN, TFLite, ONNX, OpenVINO
  - Licence : AGPL-3.0

- **[OpenCV](https://opencv.org/)** - Traitement d'image et capture vidéo
  - Lecture webcam/fichiers, encodage MJPEG, annotations
  - Licence : Apache-2.0

- **[PyTorch](https://pytorch.org/)** - Framework deep learning
  - Backend inference pour le modèle .pt
  - Licence : BSD-3-Clause

## 🌐 Backend & IoT

- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web async
  - API REST, WebSocket natif, auto-documentation OpenAPI
  - Licence : MIT

- **[Paho-MQTT](https://www.eclipse.org/paho/)** - Client MQTT Python
  - Connexion au broker The Things Network (TTN)
  - Licence : EPL-2.0

- **[Uvicorn](https://www.uvicorn.org/)** - Serveur ASGI
  - Serveur HTTP/WebSocket performant
  - Licence : BSD-3-Clause

## 🎨 Frontend

- **[SvelteKit](https://kit.svelte.dev/)** - Framework frontend
  - Compilation (pas de Virtual DOM), réactivité fine-grained
  - Licence : MIT

- **[TailwindCSS](https://tailwindcss.com/)** - Framework CSS utility-first
  - Design system cohérent, dark mode
  - Licence : MIT

- **[Chart.js](https://www.chartjs.org/)** - Bibliothèque de graphiques
  - Visualisations temporelles interactives
  - Licence : MIT

- **[Lucide](https://lucide.dev/)** - Bibliothèque d'icônes
  - Icônes modernes et légers
  - Licence : ISC

## 📊 Dataset

- **[Bee-Hornet-Detect](https://universe.roboflow.com/imgprocess-n3bpn/bee-hornet-detect)** 
  - Plateforme : Roboflow Universe
  - Fournisseur : imgprocess (Roboflow user)
  - Images : 2,238 images annotées
  - Classes : Frelon (0), Abeille (1)
  - Format : YOLOv11
  - Licence : **CC BY 4.0**
  - Pré-traitement : Auto-orientation, resize 640x640 (stretch)

## 🔧 Infrastructure

- **[The Things Network](https://www.thethingsnetwork.org/)** - Infrastructure LoRaWAN
  - Broker MQTT public pour réception des données
  - Gratuit pour usage académique/personnel

## 🙏 Remerciements

- **Encadrant académique** pour le support hardware, le firmware Arduino et la mise à disposition de l'équipement LoRaWAN
- **Communauté Ultralytics** pour la documentation détaillée et les outils d'export
- **Roboflow** pour la plateforme de datasets et l'annotation communautaire
- **Contributeurs open-source** de toutes les bibliothèques utilisées

## 📄 Licences du projet

- **Code source** : MIT License (voir fichier LICENSE)
- **Modèle entraîné** : Dérivé du dataset CC BY 4.0 + YOLO AGPL-3.0
- **Documentation** : CC BY 4.0

---

*Projet développé dans le cadre d'un Devoir de Validation en architecture IoT et systèmes embarqués.*
