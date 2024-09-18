import os
import cv2
from cv2 import aruco
import numpy as np
import toml
from tqdm import tqdm
import re  # Pour utiliser les expressions régulières

# Dictionnaire de mappage entre les noms de fichiers et les attributs d'OpenCV
ARUCO_DICT_MAPPING = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6": cv2.aruco.DICT_6X6_250,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL
}

def extract_frames(video_path, output_dir, frame_interval=20):
    """
    Extrait des frames d'une vidéo et les enregistre dans un dossier.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Ouvre la vidéo pour lire les frames
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Nombre total de frames dans la vidéo
    
    print(f"Extraction des frames de la vidéo {os.path.basename(video_path)}...")

    frame_count = 0
    saved_count = 0
    
    # Barre de progression avec tqdm pour montrer l'avancement de l'extraction
    with tqdm(total=total_frames, desc="Extraction des frames", unit="frame") as pbar:
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Sauvegarde toutes les frames selon l'intervalle défini
            if frame_count % frame_interval == 0:
                frame_filename = os.path.join(output_dir, f"frame_{saved_count:04d}.png")
                cv2.imwrite(frame_filename, frame)
                saved_count += 1

            frame_count += 1
            pbar.update(1)

    # Libération des ressources et fermeture de la vidéo
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"Extraction terminée. {saved_count} images sauvegardées dans {output_dir}.")

def get_charuco_info_from_filename(filename):
    """
    Extrait les informations de x, y, taille des carrés, taille des marqueurs et dictionnaire ArUco
    à partir du nom du fichier charuco.

    Arguments :
    filename -- nom du fichier Charuco au format charuco_xx_yy_squaresize_markersize_dict.png

    Retourne :
    x, y, taille des carrés, taille des marqueurs, dictionnaire ArUco
    """
    # Expression régulière pour extraire les valeurs
    match = re.match(r"charuco_(\d+)x(\d+)_(\d+)_(\d+)_DICT_(\d+)X(\d+)_\d+.png", filename)
    if match:
        squares_x = int(match.group(1))
        squares_y = int(match.group(2))
        square_length = float(match.group(3)) / 1000.0  # Convertir en mètres
        marker_length = float(match.group(4)) / 1000.0  # Convertir en mètres
        aruco_dict_name = f"DICT_{match.group(5)}X{match.group(6)}"
        if aruco_dict_name in ARUCO_DICT_MAPPING:
            return squares_x, squares_y, square_length, marker_length, ARUCO_DICT_MAPPING[aruco_dict_name]
        else:
            raise ValueError(f"Le dictionnaire ArUco '{aruco_dict_name}' n'est pas supporté.")
    else:
        raise ValueError(f"Le format du fichier {filename} est incorrect.")

def find_charuco_file(intrinsics_dir):
    """
    Recherche un fichier PNG commençant par 'charuco' dans le dossier intrinsics et extrait les informations nécessaires.

    Arguments :
    intrinsics_dir -- dossier où chercher le fichier charuco

    Retourne :
    Le nom du fichier et les informations extraites (x, y, taille des carrés, taille des marqueurs, dictionnaire ArUco).
    """
    for file_name in os.listdir(intrinsics_dir):
        if file_name.startswith("charuco") and file_name.endswith(".png"):
            print(f"Fichier Charuco trouvé : {file_name}")
            return get_charuco_info_from_filename(file_name)
    return None, None, None, None, None

def calibrate_and_save_parameters(frames_brut_dir, frames_annoted_dir, aruco_dict, squares_x, squares_y, square_length, marker_length, camera_name, calib_file):
    """
    Effectue la calibration intrinsèque et sauvegarde les résultats dans un fichier TOML.
    """
    # Créer le dossier pour les images annotées s'il n'existe pas
    if not os.path.exists(frames_annoted_dir):
        os.makedirs(frames_annoted_dir)

    # Conversion du dictionnaire ArUco pour être utilisé dans OpenCV
    aruco_dictionary = cv2.aruco.getPredefinedDictionary(aruco_dict)
    
    # Initialisation du plateau Charuco
    board = cv2.aruco.CharucoBoard((squares_x, squares_y), square_length, marker_length, aruco_dictionary)
    board.setLegacyPattern(True)
    params = cv2.aruco.DetectorParameters()

    # Récupère toutes les images dans frames_brut_dir
    image_files = [os.path.join(frames_brut_dir, f) for f in os.listdir(frames_brut_dir) if f.endswith(".png")]
    image_files.sort()

    print(f"Début de la calibration pour {camera_name}. Traitement des images...")

    all_charuco_corners = []
    all_charuco_ids = []

    # Barre de progression pour afficher l'avancement de la calibration
    with tqdm(total=len(image_files), desc="Calibration", unit="image") as pbar:
        for image_file in image_files:
            image = cv2.imread(image_file)
            image_copy = image.copy()
            marker_corners, marker_ids, _ = cv2.aruco.detectMarkers(image, aruco_dictionary, parameters=params)
            
            # Si au moins un marqueur ArUco est détecté
            if marker_ids is not None and len(marker_ids) > 0:
                # Dessine les marqueurs détectés
                cv2.aruco.drawDetectedMarkers(image_copy, marker_corners, marker_ids)
                # Interpolation des coins Charuco
                [charuco_retval, charuco_corners, charuco_ids] = cv2.aruco.interpolateCornersCharuco(marker_corners, marker_ids, image, board)

                # Si les coins Charuco sont détectés, on les dessine et les enregistre
                if charuco_retval and charuco_corners is not None and charuco_ids is not None:
                    cv2.aruco.drawDetectedCornersCharuco(image_copy, charuco_corners, charuco_ids)

                # Sauvegarde l'image annotée
                annotated_filename = os.path.join(frames_annoted_dir, os.path.basename(image_file))
                cv2.imwrite(annotated_filename, image_copy)

                # Ajoute les coins détectés pour la calibration
                if charuco_retval:
                    all_charuco_corners.append(charuco_corners)
                    all_charuco_ids.append(charuco_ids)

            pbar.update(1)

    # Calibration basée sur les coins Charuco détectés
    if len(all_charuco_corners) > 0 and len(all_charuco_ids) > 0:
        retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
            all_charuco_corners, all_charuco_ids, board, image.shape[:2], None, None
        )
        print(f"Calibration terminée pour {camera_name}.")
        
        # Sauvegarde les paramètres de calibration dans Calib.toml
        save_calib_parameters(calib_file, camera_name, camera_matrix, dist_coeffs, rvecs, tvecs)
    else:
        print(f"Erreur : Aucun coin ou identifiant Charuco détecté pour {camera_name}, calibration impossible.")

def save_calib_parameters(calib_file, camera_name, camera_matrix, dist_coeffs, rvecs, tvecs):
    """
    Sauvegarde les paramètres de calibration dans un fichier TOML.
    """
    if os.path.exists(calib_file):
        calib_data = toml.load(calib_file)
    else:
        calib_data = {}

    # Ajouter les données de calibration pour la caméra actuelle
    calib_data[camera_name] = {
        'name': camera_name,
        'size': [1920.0, 1080.0],  # Taille fixe pour les GoPro
        'matrix': camera_matrix.tolist(),
        'distortions': dist_coeffs.ravel().tolist(),
        'rotation': rvecs[0].ravel().tolist() if len(rvecs) > 0 else [0.0, 0.0, 0.0],
        'translation': tvecs[0].ravel().tolist() if len(tvecs) > 0 else [0.0, 0.0, 0.0],
        'fisheye': False
    }

    # Sauvegarder dans Calib.toml
    with open(calib_file, 'w') as f:
        toml.dump(calib_data, f)

    print(f"Paramètres sauvegardés pour {camera_name} dans {calib_file}.")

def process_all_videos(frame_interval=20, extract_frames_option=True):
    """
    Parcourt tous les dossiers int_cam (int_cam1, int_cam2, etc.) pour extraire les frames, 
    réaliser la calibration et sauvegarder les résultats dans Calib.toml.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Chemin dynamique où se situe le fichier
    essaicalib_dir = os.path.join(base_dir, 'Essaicalib')  # Chemin vers le dossier Essaicalib
    calibration_dir = os.path.join(essaicalib_dir, 'calibration')  # Chemin vers le dossier calibration
    intrinsics_dir = os.path.join(calibration_dir, 'intrinsics')  # Chemin vers intrinsics

    # Chemin du fichier Calib.toml dans calibration
    calib_file = os.path.join(calibration_dir, 'Calib.toml')
    
    # Recherche d'un fichier charuco dans le dossier intrinsics
    squares_x, squares_y, square_length, marker_length, aruco_dict = find_charuco_file(intrinsics_dir)
    
    # Si aucun fichier Charuco n'est trouvé, on utilise les paramètres par défaut
    if squares_x is None:
        print("Aucun fichier Charuco trouvé, utilisation des paramètres par défaut.")
        aruco_dict = ARUCO_DICT_MAPPING["DICT_6X6_250"]
        squares_x = 9
        squares_y = 6
        square_length = 0.04  # Taille des carrés en mètres
        marker_length = 0.03  # Taille des marqueurs en mètres

    # Parcours des dossiers int_cam pour traiter les vidéos et extraire les frames
    for folder_name in os.listdir(intrinsics_dir):
        folder_path = os.path.join(intrinsics_dir, folder_name)
        if os.path.isdir(folder_path) and folder_name.startswith("int_cam"):
            print(f"Traitement du dossier {folder_name}...")

            frames_brut_dir = os.path.join(folder_path, "frames_brut")
            frames_annoted_dir = os.path.join(folder_path, "frames_annoted")
            
            if extract_frames_option:
                # Extraction des frames à partir de la vidéo
                video_files = [f for f in os.listdir(folder_path) if f.endswith(".mp4")]
                if len(video_files) > 0:
                    video_path = os.path.join(folder_path, video_files[0])
                    extract_frames(video_path, frames_brut_dir, frame_interval)
                else:
                    print(f"Aucune vidéo trouvée dans {folder_path}, extraction des frames ignorée.")

            # Calibration sur les frames
            calibrate_and_save_parameters(frames_brut_dir, frames_annoted_dir, aruco_dict, squares_x, squares_y, square_length, marker_length, folder_name, calib_file)

# -------------------------------------
# Exécution du traitement (penser à mettre un charuco renommé de cette manière : charuco_9x6_40_30_DICT_6X6_250.png)
# -------------------------------------
process_all_videos(extract_frames_option=False)
