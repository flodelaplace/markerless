# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 11:41:39 2024

@author: fdelaplace
"""

import shutil
import os
from pathlib import Path
from datetime import datetime
import logging
from tqdm import tqdm  # Pour ajouter des barres de chargement


def classification(path=None, videoFormat=".MP4"):
    """
    ***
    OBJECTIF DE LA FONCTION
    ***
    Classer toutes les vidéos d'une session d'acquisition avec la bonne 
    structure de dossier et les bons noms de dossier et de vidéos dans un 
    dossier "_traitement" qui est créé dans le dossier parent du dossier actif.
    
    ORGANISATION DES FICHIERS DANS LE DOSSIER A TRAITER
    ***
        - Placez toutes vos vidéos brutes dans le dossier et un fichier Config.toml
        - Dans le cas où vous gardez la même calibration intrinsèque, placez le dossier intrinsics et le fichier Calib.toml
        - Dans le cas où vous gardez la même calibration (intrinsèque et extrinsèque), placez le dossier calibration 
            contenant les sous-dossiers intrinsics et extrinsics et le fichier Calib.toml
    
    """
    print("====================")
    print("File classification...")
    print("--------------------\n\n")  

    if path is None:
        path = os.getcwd()
    else:
        path = Path(path)

    # Création du dossier "_traitement" dans le dossier parent du dossier actif
    traitement_path = os.path.join(os.path.dirname(path), os.path.basename(path) + "_traitement")
    if not os.path.exists(traitement_path):
        os.mkdir(traitement_path)
        print(f"Création du dossier de traitement : {traitement_path}")
    
    # Récupération des noms de fichiers vidéo dans le dossier actif
    filenames = [file for file in os.listdir(path) if file.endswith(videoFormat)]
    
    # Tri des vidéos par date (sans secondes) et par nom de caméra dans l'ordre croissant
    filenames = sorted(filenames, key=lambda x: (
        datetime.strptime(x[:13], "%Y%m%d_%H%M"),  # On prend en compte l'heure et minute
        x[x.find("CAMERA"):x.find("CAMERA")+8]  # On trie par numéro de caméra
    ))

    # Récupérer le nombre total de fichiers et le nombre de caméras uniques
    nbfiles = len(filenames)
    camList = [filenames[file][filenames[file].find("CAMERA"):filenames[file].find("CAMERA")+8] for file in range(nbfiles)]
    camNames = list(set(camList))  # Caméras uniques
    nbcam = len(camNames)

    print(f"Nombre total de fichiers : {nbfiles}")
    print(f"Nombre de caméras uniques : {nbcam}")

    # Vérification de la présence du fichier Config.toml et copie dans le dossier traitement
    config_file = os.path.join(path, 'Config.toml')
    if os.path.exists(config_file):
        shutil.copy(config_file, os.path.join(traitement_path, 'Config.toml'))
        print("Le fichier Config.toml a été copié dans le dossier de traitement.")
    else:
        print("ATTENTION : Aucun fichier 'Config.toml' trouvé dans le dossier actif.")

    """
    2 - Vérification des dossiers calibration et intrinsics
    Si un dossier calibration ou intrinsics est trouvé dans le dossier actif,
    il est pris en compte pour la suite du traitement.
    """

    # Chemins des dossiers calibration et intrinsics dans le dossier actif
    calibFolderPath = os.path.join(path, "calibration")
    calibVerifIntFolderPath = os.path.join(path, "intrinsics")

    # Variables pour indiquer si calibration ou intrinsics a été trouvé
    userCalib = False
    userCalibInt = False

    # Vérification si un dossier calibration existe dans le dossier actif
    if os.path.exists(calibFolderPath):
        print("Un dossier calibration a été trouvé.")
        userCalib = True  # On utilise ce dossier calibration

    # Vérification si un dossier intrinsics existe dans le dossier actif
    elif os.path.exists(calibVerifIntFolderPath):
        userCalibInt = True  # On utilise ce dossier intrinsics
        print("Un dossier intrinsics a été trouvé.")

    # Vérification de la présence des fichiers de calibration (à reporter en partie 3)
    calib_files = ['Calib.toml', 'Calib_scene.toml', 'calib.toml']
    found_calib_file = None
    for calib_file in calib_files:
        if os.path.exists(os.path.join(path, calib_file)):
            found_calib_file = calib_file
            print(f"Le fichier {calib_file} a été trouvé dans le dossier actif.")
            break

    """
    3 - Sort trials
    Détermination du nombre d'acquisitions réalisées et copie des vidéos et des dossiers
    dans le dossier traitement.
    """

    # Calcul du nombre d'essais
    if userCalib == False and userCalibInt == False:
        nbtrials = (nbfiles - nbcam * 2) / nbcam
    elif userCalib == False and userCalibInt == True:
        nbtrials = (nbfiles - nbcam) / nbcam
    else:
        nbtrials = (nbfiles) / nbcam

    # Si le nombre de vidéos est cohérent avec le nombre de caméras...
    if nbtrials % 1 == 0:
        nbtrials = int(nbtrials)
        print(f"Nombre d'essais (trials) trouvés : {nbtrials}")

        # Création des dossiers Trial_n et sous-dossiers videos_raw dans le dossier "_traitement"
        print("Création des dossiers Trial...")
        for trial in tqdm(range(1, nbtrials + 1), desc="Création des dossiers Trial"):
            trial_path = os.path.join(traitement_path, f"Trial_{trial}")
            if not os.path.exists(trial_path):
                os.mkdir(trial_path)
            if not os.path.exists(os.path.join(trial_path, "videos_raw")):
                os.mkdir(os.path.join(trial_path, "videos_raw"))

            # Copie du fichier Config.toml dans chaque dossier Trial
            if os.path.exists(config_file):
                shutil.copy(config_file, os.path.join(trial_path, 'Config.toml'))

        # Si le dossier calibration a été trouvé
        if userCalib:
            print("Le dossier calibration existe déjà, pas de copie nécessaire.")
            print("Classement des vidéos dans les dossiers Trial.")
            for acq in tqdm(range(nbtrials), desc="Classification des essais"):
                for cam in range(nbcam):
                    shutil.copy(os.path.join(path, filenames[nbcam * acq + cam]),
                                os.path.join(traitement_path, f"Trial_{acq + 1}", "videos_raw", filenames[nbcam * acq + cam]))

            # Copie du fichier de calibration dans le dossier traitement s'il n'est pas déjà présent
            if found_calib_file and not os.path.exists(os.path.join(calibFolderPath, found_calib_file)):
                shutil.copy(os.path.join(path, found_calib_file), os.path.join(traitement_path, "calibration", found_calib_file))
                print(f"Le fichier {found_calib_file} a été copié dans le dossier calibration du traitement.")

        # Si le dossier intrinsics a été trouvé mais pas le dossier calibration
        elif userCalibInt:
            print("Le dossier intrinsics a été trouvé. Création des extrinsics et gestion des trials.")
            new_calib_folder = os.path.join(traitement_path, "calibration")
            if not os.path.exists(new_calib_folder):
                os.mkdir(new_calib_folder)
            shutil.copytree(calibVerifIntFolderPath, os.path.join(new_calib_folder, "intrinsics"))

            # Création des sous-dossiers extrinsèques dans le dossier calibration
            print("Création des sous-dossiers extrinsèques...")
            calibExtFolderPath = os.path.join(new_calib_folder, "extrinsics")
            if not os.path.exists(calibExtFolderPath):
                os.mkdir(calibExtFolderPath)
            for n in tqdm(range(1, nbcam + 1), desc="Création des sous-dossiers extrinsèques"):
                if n < 10:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam0{n}"))
                else:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam{n}"))

            # Copie des vidéos dans extrinsics puis dans trials
            print("Classement des vidéos dans extrinsics et trials.")
            for cam in tqdm(range(nbcam), desc="Classification des vidéos extrinsèques"):
                shutil.copy(os.path.join(path, filenames[cam]),
                            os.path.join(traitement_path, "calibration", "extrinsics", f"ext_cam{cam+1:02}", filenames[cam]))

            for acq in tqdm(range(nbtrials), desc="Classification des essais"):
                for cam in range(nbcam):
                    shutil.copy(os.path.join(path, filenames[nbcam * acq + nbcam]),
                                os.path.join(traitement_path, f"Trial_{acq + 1}", "videos_raw", filenames[nbcam * acq + cam]))

            # Copie du fichier de calibration après la création du dossier calibration
            if found_calib_file:
                shutil.copy(os.path.join(path, found_calib_file), os.path.join(traitement_path, "calibration", found_calib_file))
                print(f"Le fichier {found_calib_file} a été copié dans le dossier calibration du traitement.")

        # Si aucune calibration n'est faite
        else:
            print("Aucune calibration trouvée. Gestion complète des vidéos (intrinsics, extrinsics, trials).")
            
            # Création des dossiers calibration, intrinsics et extrinsics
            new_calib_folder = os.path.join(traitement_path, "calibration")
            os.mkdir(new_calib_folder)
            
            # Création des sous-dossiers intrinsics
            calibIntFolderPath = os.path.join(new_calib_folder, "intrinsics")
            if not os.path.exists(calibIntFolderPath):
                os.mkdir(calibIntFolderPath)
            for n in tqdm(range(1, nbcam + 1), desc="Création des sous-dossiers intrinsics"):
                if n < 10:
                    os.mkdir(os.path.join(calibIntFolderPath, f"int_cam0{n}"))
                else:
                    os.mkdir(os.path.join(calibIntFolderPath, f"int_cam{n}"))

            # Création des sous-dossiers extrinsèques
            calibExtFolderPath = os.path.join(new_calib_folder, "extrinsics")
            if not os.path.exists(calibExtFolderPath):
                os.mkdir(calibExtFolderPath)
            for n in tqdm(range(1, nbcam + 1), desc="Création des sous-dossiers extrinsics"):
                if n < 10:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam0{n}"))
                else:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam{n}"))

            # Classement dans intrinsics
            for cam in tqdm(range(nbcam), desc="Classification des vidéos intrinsics"):
                shutil.copy(os.path.join(path, filenames[cam]),
                            os.path.join(new_calib_folder, "intrinsics", f"int_cam{cam+1:02}", filenames[cam]))

            # Classement dans extrinsics
            for cam in tqdm(range(nbcam), desc="Classification des vidéos extrinsics"):
                shutil.copy(os.path.join(path, filenames[nbcam + cam]),
                            os.path.join(new_calib_folder, "extrinsics", f"ext_cam{cam+1:02}", filenames[nbcam + cam]))

            # Classement dans trials
            for acq in tqdm(range(nbtrials), desc="Classification des essais"):
                for cam in range(nbcam):
                    shutil.copy(os.path.join(path, filenames[nbcam * acq + nbcam * 2]),
                                os.path.join(traitement_path, f"Trial_{acq + 1}", "videos_raw", filenames[nbcam * acq + cam]))

            # Copie du fichier de calibration après la création du dossier calibration
            if found_calib_file:
                shutil.copy(os.path.join(path, found_calib_file), os.path.join(traitement_path, "calibration", found_calib_file))
                print(f"Le fichier {found_calib_file} a été copié dans le dossier calibration du traitement.")

    else:
        print("ERROR - Nombre de fichiers vidéo non cohérent avec le nombre de caméras.")

    # Affichage du résumé et logs
    print("\n\n--------------------")
    logging.info(f'Dossier de travail : {path}')
    logging.info(f'Nombre de caméras trouvées : {nbcam}')
    logging.info(f'Nombre dacquisitions classées : {nbtrials}')
    print("\nClassification des enregistrements fait avec succès.")
    print("====================")

# Appel de la fonction avec le chemin
classification(path="C:\\Users\\fdelaplace\\AppData\\Local\\anaconda3\\envs\\Pose2Sim\\Lib\\site-packages\\Pose2Sim\\Essaiclassification", videoFormat=".MP4")
