import os
import cv2
import numpy as np
from tqdm import tqdm

def detect_aruco_markers(video_path):
    """
    Détecte uniquement les marqueurs Aruco dans la vidéo et les sauvegarde dans des images.
    Les images sont sauvegardées dans le même dossier que la vidéo.
    :param video_path: Chemin de la vidéo.
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Erreur : Impossible d'ouvrir la vidéo {video_path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Obtenir le nombre total de frames
    if total_frames == 0:
        print("Erreur : La vidéo semble vide ou non lisible.")
        return

    # Créer un dossier de sortie dans le même répertoire que la vidéo
    video_dir = os.path.dirname(video_path)
    output_dir = os.path.join(video_dir, "output_aruco_markers")
    os.makedirs(output_dir, exist_ok=True)  # Créer le dossier si nécessaire

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

    frame_count = 0
    detected_any_markers = False  # Vérifier si un marqueur est détecté au moins une fois

    for _ in tqdm(range(total_frames), desc="Traitement des frames", ncols=100):
        ret, frame = cap.read()
        if not ret:
            print("Erreur : Impossible de lire la frame.")
            break

        # Convertir en niveaux de gris
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Détecter les marqueurs Aruco
        marker_corners, marker_ids, _ = detector.detectMarkers(gray)

        if marker_ids is not None and len(marker_ids) > 0:
            detected_any_markers = True  # Si des marqueurs sont détectés, on le note
            print(f"Détection des marqueurs à la frame {frame_count}. ID des marqueurs : {marker_ids}")
            # Dessiner les marqueurs Aruco détectés sur l'image
            cv2.aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)
            # Sauvegarder l'image avec les marqueurs détectés pour vérification
            cv2.imwrite(os.path.join(output_dir, f"frame_{frame_count:04d}_markers.png"), frame)
        else:
            print(f"Aucun marqueur détecté à la frame {frame_count}.")

        frame_count += 1

    cap.release()

    if not detected_any_markers:
        print("Aucun marqueur Aruco n'a été détecté dans toute la vidéo. Vérifiez les paramètres ou la qualité de la vidéo.")
    else:
        print(f"Traitement terminé. Images sauvegardées dans le dossier {output_dir}.")

# Exemple d'utilisation :
video_path = "C:/Users/fdelaplace/AppData/Local/anaconda3/envs/Pose2Sim/Lib/site-packages/Pose2Sim/Essaicalib/calibration/intrinsics/int_cam1/20240911-113831-camera01.mp4"
detect_aruco_markers(video_path)
