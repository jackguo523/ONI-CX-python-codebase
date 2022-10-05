# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 12:23:36 2022

@author: JACK
"""

import os
import numpy as np
import time


# current there is no "safety check"
# current progress bar is not allowed by NimOS




# compute the absolute XY positions based on request
# input: mosaic row count, mosaic column count, overlap rate [0,100], scan method [1->snake, 2->raster], order [1->X, 2->Y], z-lock engagement [True->enabled, False->Disabled]
# output: list of positions to scan
def get_scan_position(row=1,col=1,overlap=0,method=1,order=1,zlock=True):\
    pixel_size=0.117
    # pixel_size=calibration.ChannelMapping.GetLatestMapping().pixelSize_um
    w=camera.GetLatestImage().Channel(0).Dims.Width*pixel_size # read FOV width in um
    h=camera.GetLatestImage().Channel(0).Dims.Height*pixel_size # read FOV height in um
    
    if overlap<0 or overlap>=100: # cast overlap request to 0% for invalid input
        overlap=0
    
    XP=[] # initial X positions
    YP=[] # initial Y positions
    xpos=stage.GetPositionInMicrons(stage.Axis.X) # read origins in um
    ypos=stage.GetPositionInMicrons(stage.Axis.Y)
    
    if method==1: # snake scan by default
        if order==1: # X-major by default
            for j in range(col):
                f=1 # direction factor [1->forward, -1->backward]
                for i in range(row):
                    f=1 if j%2==0 else -1 # update direction factor [even row->forward, odd row->backward]
                    XP.append(xpos+i*w*((100-overlap)/100.0)*f) # add position to list
                    YP.append(ypos)
                xpos=xpos+i*w*((100-overlap)/100.0)*f # update origins
                ypos=ypos+h*((100-overlap)/100.0)
        else: # Y-major
            for i in range(row):
                f=1 # direction factor [1->forward, -1->backward]
                for j in range(col):
                    f=1 if i%2==0 else -1 # update direction factor [even column->forward, odd column->backward]
                    XP.append(xpos) # add position to list
                    YP.append(ypos+j*h*((100-overlap)/100.0)*f)
                xpos=xpos+w*((100-overlap)/100.0) # update origins
                ypos=ypos+j*h*((100-overlap)/100.0)*f
    else: # raster scan
        if order==1: # X-major
            for j in range(col):
                for i in range(row):
                    XP.append(xpos+i*w*((100-overlap)/100.0)) # add position to list
                    YP.append(ypos)
                ypos=ypos+h*((100-overlap)/100.0) # update origin
        else: # Y-major
            for i in range(row):
                for j in range(col):
                    XP.append(xpos) # add position to list
                    YP.append(ypos+j*h*((100-overlap)/100.0))
                xpos=xpos+w*((100-overlap)/100.0) # update origin
                
    return XP,YP


# read the absolute XYZ positions from file (previously saved)
# input: the position file
# output: list of positions to scan
def read_scan_position(filename):
    tbd=1
    
# compute the relative Z positions based on request
# input: relative stack top position, relative stack bottom position, number of sections, stack order [1->topward, 2->bottomward]
def get_stack_position(top=1,bot=-1,frame=10,order=1):
    zpos=stage.GetPositionInMicrons(stage.Axis.Z) # read origin in um
    
    ZP=[] # initial Z positions
    ss=(top-bot)/(frame-1) # compute the step size
    
    for i in range(frame):
        if order==1: # from bottom to top by default
            ZP.append(zpos+bot+i*ss)
        else: # from top to bottom
            ZP.append(zpos+top-i*ss)
            
    return ZP


# acquire the mosaic
# input: list of X positions, list of Y positions, z-lock engagement [True->enabled, False->disabled], wait time after stage translation in second, homing after acquistion [True->yes, False->no]
# output:
def mosaicking(XP,YP,zlock=True,wait=0,home=True):
    if zlock: # active z-lock
        if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS: # check z-lock
            autofocus.StartContinuousAutoFocus()
            time.sleep(5)
    else: # inactive z-lock
        autofocus=False # need to check if this is possible
        
    count=len(XP)
    
    
    
    