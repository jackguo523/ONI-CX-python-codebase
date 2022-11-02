# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 08:19:09 2022

@author: JACK
"""

# Oxford Nanoimaging MultiAcquisition Stitching
# probably need gpu implement numba.cuda

import os
import numpy as np
import skimage.io
import tifffile

ps=116.99999868869781 # 117nm/pixel

# read both raw and localization data providing the root directory of acquisition
def imread_fromfile(path):
    (_,folders,_)=next(os.walk(path))
    numP=len(folders) # number of positions
    raw=[] # raw images
    loc=[] # loc images
    
    for p in range(numP):
        (_,_,files)=next(os.walk(path+'/'+folders[p]))
        raw_files=[path+'/'+folders[p]+'/'+i for i in files if ('combined' not in i.lower() and 'loc' not in i.lower() and 'tif' in i.lower())]
        loc_files=[path+'/'+folders[p]+'/'+i for i in files if ('png' in i.lower() and 'thumbnail' in i.lower())]
        
        for r in range(len(raw_files)): # read raws
            raw.append(tifffile.imread(raw_files[r]))
        for l in range(len(loc_files)): # read locs
            loc.append(skimage.io.imread(loc_files[l]))
            
    return raw,loc

# separate channels
def crop_channel(imgs):
    sx=imgs[0].shape[-1] # get dimension
    
    crop_sx=int(sx/2) # 1 channel dimension
    left_imgs=[] # left channel
    right_imgs=[] # right channel
    
    for i in range(len(imgs)):
        left_imgs.append(imgs[i][...,:,:crop_sx])
        right_imgs.append(imgs[i][...,:,crop_sx:])
        
    return left_imgs,right_imgs

# stitch both raw and localization data without overlap
# input: raw data, localization data, tile dimensions, scan mode [rasterXY, rasterYX, snakeXY, snakeYX]
def stitch(raw,loc,row,col,scan='rasterXY'):
    # C0,C1=crop_channel(raw)
    C0=raw
    C1=raw
    
    sx=C0[0].shape[-1] # channel dimensions
    sy=C0[0].shape[-2]
    
    fx=sx*col # final dimensions
    fy=sy*row
    
    stitch_C0=np.zeros((fy,fx),np.uint16)
    stitch_C1=np.zeros((fy,fx),np.uint16)
    stitch_L=np.zeros((fy,fx),np.uint8)
    
    px=[] # tile position lists
    py=[]
    
    for i in range(len(raw)):
        if scan=='rasterXY':
            px.append(fx-((i%col)+1)*sx)
            py.append(fy-((i//col)+1)*sy)
        elif scan=='rasterYX':
            px.append(fx-((i//row)+1)*sx)
            py.append(fy-((i%row)+1)*sy)
        elif scan=='snakeXY':
            px.append((fx-((i%col)+1)*sx,(i%col)*sx)[(i//col)%2==1])
            py.append(fy-((i//col)+1)*sy)
        elif scan=='snakeYX':
            px.append(fx-((i//row)+1)*sx)
            py.append((fy-((i%row)+1)*sy,(i%row)*sy)[(i//row)%2==1])
    
    for i in range(len(raw)):
        stitch_C0[py[i]:py[i]+sy,px[i]:px[i]+sx]=C0[i]
        stitch_C1[py[i]:py[i]+sy,px[i]:px[i]+sx]=C1[i]
        # stitch_L[py[i]:py[i]+sy,px[i]:px[i]+sx]=loc[i]
            
    return stitch_C0,stitch_C1,stitch_L
        
    
rootpath='test'
raw=[]
for i in range(4):
   raw.append(tifffile.imread(rootpath+'/{:03d}'.format(i+1)+'.tif'))
   
loc=raw
# raw,loc=imread_fromfile(rootpath)
R0,R1,L=stitch(raw,loc,2,2,'snakeXY')
tifffile.imsave(rootpath+'/stitched_C0.tif',R0)
tifffile.imsave(rootpath+'/stitched_C1.tif',R1)
tifffile.imsave(rootpath+'/stitched_loc.tif',L)

