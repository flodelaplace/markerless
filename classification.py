# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 11:41:39 2024

@author: fdelaplace
"""


import shutil
import os
from pathlib import Path
import time
from datetime import datetime
import cv2
from rtmlib import BodyWithFeet, Wholebody, PoseTracker, draw_skeleton
import logging
from skelly_synchronize import skelly_synchronize as sync
from Pose2Sim import Pose2Sim
import ffmpeg
    

def classification(path=None,videoFormat = ".MP4") :
    
    """
    ***
    OBJECTIF DE LA FONCTION
    ***
    Classer toutes les vidéos d'une session d'acquisition avec la bonne 
    structure de dossier et les bons noms de dossier et de vidéos dans un 
    dossier "_traitement" qui est créé dans le dossier parent du dossier actif.
    """

    os.system("====================")
    os.system("File classification...")
    os.system("--------------------\n\n")  
    print(path)
    
    """
    1 - Initialisation
    Récupération du dossier de travail, des noms des fichiers et du 
    nombre de caméras.
    """

    # Récupérer le chemin du dossier de travail
    if path is None:
        path = os.getcwd()
    else:
        path = Path(path)
        print("OUAIIIIIS")

    # Création du dossier "_traitement" dans le dossier parent du dossier actif
    traitement_path = os.path.join(os.path.dirname(path), os.path.basename(path) + "_traitement")
    print(traitement_path)
    if not os.path.exists(traitement_path):
        os.mkdir(traitement_path)
        print(f"Création du dossier de traitement : {traitement_path}")
    """ 
    # Récupération des noms de fichiers vidéo dans le dossier actif
    filenames = [file for file in os.listdir(path) if file.endswith(videoFormat)]
    """
    #Récup nom des fichiers vidéo
    filenames =[] 
    for file in os.listdir(path):
        if file.endswith(videoFormat):
            filenames.append(file)
    
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

    
    """
    2 - Calibration path
    Création des dossiers de calibration si inexistants,
    prise en compte du fichier de calibration .toml si ancienne calibration
    à prendre en compte.
    """

    # Dossiers de calibration dans le dossier cible
    calibFolderPath = os.path.join(path,"calibration")
    calibExtFolderPath = os.path.join(path,"calibration","extrinsics")
    calibIntFolderPath = os.path.join(path,"calibration","intrinsics")
    calibVerifIntFolderPath = os.path.join(path,"intrinsics")

    # Création des dossiers de calibration si inexistants
    userCalib = False
    userCalibInt = False

    if not os.path.exists(calibFolderPath):
        print("Création du dossier calibration avec les sous-dossiers respectifs.")
        os.mkdir(calibFolderPath)
        os.mkdir(calibExtFolderPath)
        if not os.path.exists(calibVerifIntFolderPath):
            os.mkdir(calibIntFolderPath)
            for n in range(1, nbcam + 1):
                if n < 10:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam0{n}"))
                    os.mkdir(os.path.join(calibIntFolderPath, f"int_cam0{n}"))
                else:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam{n}"))
                    os.mkdir(os.path.join(calibIntFolderPath, f"int_cam{n}"))
        else:
            userCalibInt = True
            shutil.move(calibVerifIntFolderPath, calibFolderPath)
            for n in range(1, nbcam + 1):
                if n < 10:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam0{n}"))
                else:
                    os.mkdir(os.path.join(calibExtFolderPath, f"ext_cam{n}"))
    else:
        print("Un dossier calibration a été trouvé.")
        for file in os.listdir(calibFolderPath):
            if not any(s in file for s in ["calib", "Calib", "Calib_scene"]):
                print("WARNING - Aucun fichier .toml de calibration retrouvé.")
            else:
                userCalib = True

    
    """
    3 - Sort trials
    Détermination du nombre d'acquisitions réalisées.
    Si le nombre de fichier n'est pas un multiple du nombre de caméra,
    l'utilisateur est averti et la classification des vidéos n'opère pas.
    Si ok, alors chaque paquet de nbcam fichiers est déplacé dans le dossier 
    Trial_n dans le dossier "_traitement".
    """

    # Calcul du nombre d'essais
    if userCalib == False and userCalibInt == False:
        nbtrials = (nbfiles - nbcam * 2) / nbcam
    if userCalib == False and userCalibInt == True:
        nbtrials = (nbfiles - nbcam) / nbcam
    else:
        nbtrials = (nbfiles) / nbcam

    # Si le nombre de vidéos est cohérent avec le nombre de caméras...
    if nbtrials % 1 == 0:
        nbtrials = int(nbtrials)

        # Création des dossiers Trial_n et sous-dossiers videos_raw dans le dossier "_traitement"
        for trial in range(1, nbtrials + 1):
            trial_path = os.path.join(traitement_path, f"Trial_{trial}")
            if not os.path.exists(trial_path):
                os.mkdir(trial_path)
            if not os.path.exists(os.path.join(trial_path, "videos_raw")):
                os.mkdir(os.path.join(trial_path, "videos_raw"))

        # Si aucune calibration n'a été fournie par l'utilisateur...
        if userCalib == False and userCalibInt == False:
            try:
                for acq in range(0, nbtrials + 2):
                    # Classification des vidéos pour calibration intrinsèque
                    if acq == 0:
                        for cam in range(0, nbcam):
                            shutil.copy(os.path.join(path, filenames[cam]),
                                        os.path.join(calibIntFolderPath, f"int_cam{cam+1:02}", filenames[cam]))
                    # Classification des vidéos pour calibration extrinsèque
                    elif acq == 1:
                        for cam in range(0, nbcam):
                            shutil.copy(os.path.join(path, filenames[nbcam * acq + cam]),
                                        os.path.join(calibExtFolderPath, f"ext_cam{cam+1:02}", filenames[nbcam * acq + cam]))
                    # Classification des vidéos d'essai
                    else:
                        shutil.copyfile(os.path.join(path, 'Config.toml'),
                                        os.path.join(traitement_path, f"Trial_{acq - 1}", 'Config.toml'))
                        for cam in range(0, nbcam):
                            shutil.copy(os.path.join(path, filenames[nbcam * acq + cam]),
                                        os.path.join(traitement_path, f"Trial_{acq - 1}", "videos_raw", filenames[nbcam * acq + cam][0:filenames[nbcam * acq + cam].find("CAMERA") + 8] + ".MP4"))
            except Exception as e:
                logging.error(f"ERROR - unable to transfer files: {e}")

        # Si calibration intrinsèque déjà effectuée
        elif userCalib == False and userCalibInt == True:
            try:
                for acq in range(0, nbtrials + 1):
                    if acq == 0:
                        for cam in range(0, nbcam):
                            shutil.copy(os.path.join(path, filenames[nbcam * acq + cam]),
                                        os.path.join(calibExtFolderPath, f"ext_cam{cam+1:02}", filenames[nbcam * acq + cam]))
                    else:
                        shutil.copyfile(os.path.join(path, 'Config.toml'),
                                        os.path.join(traitement_path, f"Trial_{acq}", 'Config.toml'))
                        for cam in range(0, nbcam):
                            shutil.copy(os.path.join(path, filenames[nbcam * acq + cam]),
                                        os.path.join(traitement_path, f"Trial_{acq}", "videos_raw", filenames[nbcam * acq + cam][0:filenames[nbcam * acq + cam].find("CAMERA") + 8] + ".MP4"))
            except Exception as e:
                logging.error(f"ERROR - unable to transfer files: {e}")

    else:
        os.system("ERROR - Nombre de fichiers vidéo non cohérent avec le nombre de caméras.")

    # Affichage du résumé et logs
    os.system("\n\n--------------------")
    logging.info(f'Dossier de travail : {path}')
    logging.info(f'Nombre de caméras trouvées : {nbcam}')
    logging.info(f'Nombre d acquisitions classées : {nbtrials}')
    logging.info("\nClassement des enregistrements fait avec succès.")
    os.system("====================")


classification(path="C:\\Users\\fdelaplace\\AppData\\Local\\anaconda3\\envs\\Pose2Sim\\Lib\\site-packages\\Pose2Sim\\Essaiclassification", videoFormat=".MP4")

