# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 10:08:34 2022

@author: JACK
"""

filepath='C:/users/jack/desktop/t' # change to the folder

import os
import pandas as pd


(_,_,files)=next(os.walk(filepath)) # scan all included files
csv=[i for i in files if '.csv' in i.lower()] # get all included csvs

for i in range(len(csv)):
    df=pd.read_csv(filepath+'/'+csv[i],header=None)
    df.columns=['channel','frame','x [nm]','y [nm]','z [nm]','x precision [nm]','y precision [nm]','intensity [photon]','background [photon]','sigma [nm]'] # change this accordingly
    df.to_csv(filepath+'/'+csv[i],index=False)
