# -*- coding: utf-8 -*-
"""
Created on Fri May 17 15:06:21 2024

@author: admin
"""

import json
import os
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.animation
import pandas as pd


#%% INPUT

path = 'C:\\Users\\fdelaplace\\AppData\\Local\\anaconda3\\envs\\Pose2Sim\\Lib\\site-packages\\Pose2Sim\\Essai_labo_squat\\Trial_1\\pose\\synced_20240904_160813-CAMERA01_json\\'
nbMarkers = 25

#%% PROGRAM

# récupérer les json
files = os.listdir(path)
nbMaxFrames = len(files)

# initialisation vars
Data = {}
X = pd.DataFrame(0, index=np.arange(nbMaxFrames), columns=range(0,nbMarkers)) 
Y = pd.DataFrame(0, index=np.arange(nbMaxFrames), columns=range(0,nbMarkers))

for frame in range(0,nbMaxFrames) :
    file = files[frame]
    # récupérer data
    with open(path+file) as f:
        data_n1 = json.load(f)
        
    # stockage data
    try :
        for people in [0] : #in range(0,len(data_n1["people"])):
            for point in range(0,nbMarkers):   
                X.iloc[frame,point]=data_n1["people"][people]["pose_keypoints_2d"][3*point]
                Y.iloc[frame,point]=data_n1["people"][people]["pose_keypoints_2d"][3*point+1]
            

    except :
        print('frame '+str(frame)+ ' : no data.')




#%% PLOT 

def f(l):
    x=X.iloc[l][:]
    y=Y.iloc[l][:]
    return x,y

def update(l):
    x,y = f(l)
    plt.gca().cla()
    ax.set_xlim(0,Xmax)
    ax.set_ylim(0,Ymax)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.scatter(x, y, marker="o")
    ax.set_title('frame '+ str(l))

fig,ax = plt.subplots()
ax.remove()
ax=fig.add_subplot(projection='3d')

Xmax = np.max(X.max(axis=1))
Ymax = np.max(Y.max(axis=1))

Anim = matplotlib.animation.FuncAnimation(fig, update, frames=nbMaxFrames,repeat=False)
plt.show()




              


#%%




