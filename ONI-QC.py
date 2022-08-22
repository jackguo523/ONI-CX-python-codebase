# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 12:13:00 2022

@author: JACK
"""

# automate 
# should be run inside NimOS at this moment

# 3rd party libraries
import time
import datetime
import math
import os
import numpy as np
import skimage.io
import argparse


# global NimOS variables
global data_manager
global instrument
global acquisition
global profiles
start_time=0
end_time=0


# local user variables
temperature_wait_time=3600 # temperature waiting time, default to 60min
flag_transillumination=False # flag for saving transillumination
channel_split=640 # system split
flag_sample_on=True # flag if sample is on
stage_tolerance=0.05 # translation tolerance in mm
flag_find_laser_power=True # flag for finding optimal laser power for channel mapping
flag_overview=False # flag for saving overview scan
flag_laser_screenshot=False # flag for taking a screenshot of the laser readings
pixel_size=0.117 # um/pixel
fx=50 # FOV width in pixel
fy=80 # FOV height in pixel
flag_memory_leaking=False # flag for checking memery usage using psutil
runtime=[]
result=True
pm_qc=['TBD']*17
date=str(datetime.date.today()).replace('-','')
outfile='C:/Users/ONI/Desktop/'+date+'_QC_report.txt'
report=open(outfile,'w')
abspath='' # absolute output directory


# general helper functions
def timer_start():
    global start_time
    start_time=time.time() # read current time
    
def timer_end():
    global end_time
    end_time=time.time()
    duration=end_time-start_time # compute elapse
    runtime.append(duration)
    print('runtime: '+str(duration)+'s')
    report.write('\nruntime: '+str(duration)+'s')
    
def _var(ims):
    v=[]
    for i in range(len(ims)):
        v.append((ims[i].std()**2))
        
    return v
        

# NimOS helper functions
def find_laser_power(laser=1,photon=500):
    camera.BeginView()
    light.GlobalOnState=True
    percentage=0
    light[laser].PercentPower=percentage
    light[laser].Enabled=True
    if laser==3: # for red laser
        mean_photon=np.average(camera.GetLatestImage().Channel(1).Pixels)
    else: # for UV, blue, and green laser
        mean_photon=np.average(camera.GetLatestImage().Channel(0).Pixels)
    while mean_photon <= photon:
        percentage=percentage+0.5 # increment
        light[laser].PercentPower=percentage
        time.sleep(0.5)
        if laser==3:
            mean_photon=np.average(camera.GetLatestImage().Channel(1).Pixels)
        else:
            mean_photon=np.average(camera.GetLatestImage().Channel(0).Pixels)
    
    light[laser].Enabled=False
    
    return percentage
        
def _init():
    for i in range(4): # turn off lasers
        light[i].PercentPower=0
        light[i].Enabled=False
    light.GlobalOnState=False
    
    camera.StopView() # turn off camera
    
    autofocus.FocusOffset=0 # reset z offset
    
    angle=instrument.IlluminationAngleControl # reset angle
    angle.RequestMoveAbsolute(0)
    
    instrument.ImagingModeControl.CurrentMode=instrument.ImagingModeControl.Normal # reset normal imaging mode
    
def _wait(t=0.1):
    output=True
    while acquisition.IsActiveOrCompleting: # wait for acquisition
        if camera.NumberOfFramesWaitingInBuffer()!=0:
            output=False
        time.sleep(0.1)
    while data_manager.IsBusy: # wait for data manager
        time.sleep(0.1)
    
    return output

def _select():
    instruments=instrument.GetAvailableInstruments() # get available device
    if len(instruments) > 0:
        print('connecting to %s' % instruments[0])
        instrument.SelectInstrument(instruments[0]) # connect to the first device
        return True
    else:
        print('error: no instrument available')
        return False
    
def wait_until_stable(laser):
    light[laser].Enabled=True
    time.sleep(2)
    pre=light[laser].PowerW
    time.sleep(1)
    cur=light[laser].PowerW
    while math.fabs(pre-cur)>0.00005: # if difference larger than 0.05mW
        pre=light[laser].PowerW
        time.sleep(1)
        cur=light[laser].PowerW  
    
    return cur

def read_camera(c=0):
    time.sleep(0.2)
    im=camera.GetLatestImage()
    p=im.Channel(c).Pixels
    h=im.Channel(c).Dims.Height
    w=im.Channel(c).Dims.Width
    
    return np.array(p).reshape((h,w))

def read_data_manager(i=0,c=0):
    time.sleep(0.2)
    im=data_manager.RawImages.GetChannelImage(i,c)
    
    return nim_image_to_array(im)
    
def _snake(row=10,col=10,save=False):
    w=camera.GetLatestImage().Channel(0).Dims.Width*pixel_size # FOV width in um
    h=camera.GetLatestImage().Channel(0).Dims.Height*pixel_size # FOV height in um
    
    XP=[] # initial the x position list
    YP=[] # initial the y position list
    xpos=stage.GetPositionInMicrons(stage.Axis.X)
    ypos=stage.GetPositionInMicrons(stage.Axis.Y)
    for j in range(col): # y-height
        i=0
        f=1
        for i in range(row): # x-width
            f=1 if j%2==0 else -1
            XP.append(xpos+i*w*f)
            YP.append(ypos)
        xpos=xpos+i*w*f
        ypos=ypos+h
    
    zp=True
    I=[]
    for i in range(row*col):
        stage.RequestMoveAbsolute(stage.Axis.X,XP[i])
        stage.RequestMoveAbsolute(stage.Axis.Y,YP[i])
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS:
                zp=False
            time.sleep(0.01)
        time.sleep(0.5)
        I.append(read_camera(0))
        
    if save:
        path=abspath+'/overview'
        if not os.path.exists(path):
            os.mkdir(path)
        for i in range(len(I)):
            skimage.io.imsave(path+'/{:03d}'.format(i+1)+'.tif',I[i],check_contrast=False)    
        print('overview scan saved as overview/***.tif')
        report.write('\nhint: overview mosaics saved as overview/***.tif')
    
    return zp
  

# all qc functions based on the order defined by the maintenance report FLD-00009
# check NimOS connection
def pm_qc20():
    if not instrument.IsConnected:
        if not _select():
            print('error: failed to select instrument')
            return False
        instrument.Connect()
        if not instrument.IsConnected:
            print('error: failed to connect to instrument')
            return False
        
    acquisition.Start(outpath,'t0',1) # initial "0"
    _wait()
    global abspath
    abspath=data_manager.Directory
    return True

# check temperature control
def pm_qc50(tar=31,wait=True):
    temperature.TargetTemperatureC=tar # set target temperature
    temperature.ControlEnabled=True # enable temperature control
    # time.sleep(3600) # wait for 60 mins
    # cur=temperature.CurrentTemperatureC # read current temperature
    
    # diff=math.fabs(cur-tar)
    # if diff > 0.2:
    #     report.write('qc50: failed to control temperature, the difference is '+str(diff))
    #     return False
    # else:
    #     report.write('qc50: passed to control temperature, the difference is '+str(diff))
    #     return True
    report.write('\nparameter: target temperature = '+str(tar)+'C')
    if flag_temperature:
        report.write('\n           temperature waiting time = '+str(temperature_wait_time)+'s')
    else:
        report.write('\nhint: please manually check the temperature reading after an hour')

# check tranillumination
# acquire two images [dim, bright] for each color
def pm_qc60(sp=640,ex=30,save=False):
    LED=instrument.TransilluminationControl
    camera.SetTargetExposureMilliseconds(ex) # set exposure
    camera.BeginView() # view camera
    
    report.write('\nparameter: exposure time = '+str(ex)+'ms')

    # red LED
    LED.SetRingColour([0.5,0,0]) # red-dim 50%
    time.sleep(1) # wait for LED switch
    if sp==640:
        im=read_camera(0)
    else:
        im=read_camera(1) # read the right channel for 560-split
    rd=np.average(im) # read from camera buffer
    if save: # save
        skimage.io.imsave(abspath+'/LED-red-dim.tif',im,check_contrast=False)
        report.write('\nhint: 50% red LED saved as LED-red-dim.tif')
        
    LED.SetRingColour([0.9,0,0]) # red-bright 90%
    time.sleep(1)
    if sp==640:
        im=read_camera(0)
    else:
        im=read_camera(1)
    rb=np.average(im)
    if save:
        skimage.io.imsave(abspath+'/LED-red-bright.tif',im,check_contrast=False)
        report.write('\nhint: 90% red LED saved as LED-red-bright.tif')
        
    # blue LED
    LED.SetRingColour([0,0.5,0]) # blue-dim 50%
    time.sleep(1)
    im=read_camera(0)
    bd=np.average(im)
    if save:
        skimage.io.imsave(abspath+'/LED-blue-dim.tif',im,check_contrast=False)
        report.write('\nhint: 50% blue LED saved as LED-blue-dim.tif')
    
    LED.SetRingColour([0,0.9,0]) # blue-bright 90%
    time.sleep(1)
    im=read_camera(0)
    bb=np.average(im)
    if save:
        skimage.io.imsave(abspath+'/LED-blue-bright.tif',im,check_contrast=False)
        report.write('\nhint: 90% blue LED saved as LED-blue-bright.tif')
        
    # green LED
    LED.SetRingColour([0,0,0.5]) # green-dim 50%
    time.sleep(1)
    im=read_camera(0)
    gd=np.average(im)
    if save:
        skimage.io.imsave(abspath+'/LED-green-dim.tif',im,check_contrast=False)
        report.write('\nhint: 50% green LED saved as LED-green-dim.tif')
    
    LED.SetRingColour([0,0,0.9]) # green-bright 90%
    time.sleep(1)
    gb=np.average(im)
    if save:
        skimage.io.imsave(abspath+'/LED-green-bright.tif',im,check_contrast=False)
        report.write('\nhint: 90% green LED saved as LED-green-bright.tif')
    
    LED.Enabled=False # turn off LED
    
    if rd > rb or bd > bb or gd > gb or rd > gd or bd > rd or rb > gb or bb > rb:
        return False
    else:
        return True    

   
# check xy stage movement
# check stage translation if sample is not on, otherwise only read preset limits
def pm_qc70(t=0.05,sample=True):
    if sample==True: # the bead slide is on, check the preset limits
        xpos=stage.GetMaximumInMicrons(stage.Axis.X) # read positive x
        xneg=stage.GetMinimumInMicrons(stage.Axis.X) # read negative x
        xran=(xpos-xneg)/1000.0 # mm
        ypos=stage.GetMaximumInMicrons(stage.Axis.Y) # read positive y
        yneg=stage.GetMinimumInMicrons(stage.Axis.Y) # read negative y
        yran=(ypos-yneg)/1000.0
        report.write('\nparameter: (preset) x-stage ['+str(xneg/1000.0)+', '+str(xpos/1000.0)+']mm')
        report.write('\n           (preset) y-stage ['+str(yneg/1000.0)+', '+str(ypos/1000.0)+']mm')
    else: # the bead slide is not on, check stage translation
        v1=stage.GetMaximumInMicrons(stage.Axis.X)
        stage.RequestMoveAbsolute(stage.Axis.X,v1)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01) # wait until stage stops
        xpos=stage.GetPositionInMicrons(stage.Axis.X)/1000.0
        v2=stage.GetMinimumInMicrons(stage.Axis.X)
        stage.RequestMoveAbsolute(stage.Axis.X,v2)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
        xneg=stage.GetPositionInMicrons(stage.Axis.X)/1000.0
        xran=xpos-xneg
        v3=stage.GetMaximumInMicrons(stage.Axis.Y)
        stage.RequestMoveAbsolute(stage.Axis.Y,v3)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
        ypos=stage.GetPositionInMicrons(stage.Axis.Y)/1000.0
        v4=stage.GetMinimumInMicrons(stage.Axis.Y)
        stage.RequestMoveAbsolute(stage.Axis.Y,v4)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
        yneg=stage.GetPositionInMicrons(stage.Axis.Y)/1000.0
        yran=ypos-yneg
        report.write('\nparameter: (preset) x-stage ['+str(v2/1000.0)+', '+str(v1/1000.0)+']mm')
        report.write('\n           (preset) y-stage ['+str(v4/1000.0)+', '+str(v3/1000.0)+']mm')
        report.write('\nhint: (actual) x-stage ['+str(xneg)+', '+str(xpos)+']mm')
        report.write('\n      (actual) y-stage ['+str(yneg)+', '+str(ypos)+']mm')
        
        stage.RequestMoveAbsolute(stage.Axis.X,0) # home
        stage.RequestMoveAbsolute(stage.Axis.Y,0)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
    
    if xran >= 14.0:
        xp=True
    else:
        xp=False
    if yran >= 14.0:
        yp=True
    else:
        yp=False
    
    if not sample: # check for stage stuck
        if xneg-t >= v2:
            xp=False
            report.write('\nhint: x stage is stuck along the negative direction')
        if xpos+t <= v1:
            xp=False
            report.write('\nhint: x stage is stuck along the positive direction')
        if yneg-t >= v4:
            yp=False
            report.write('\nhint: y stage is stuck along the negative direction')
        if ypos+t <= v3:
            yp=False
            report.write('\nhint: y stage is stuck along the positive direction')
    
    return xp,yp


# check z stage
# move stage translation if sample is not on, otherwise only read preset limits
def pm_qc80(t=0.05,sample=True):
    if sample==True: # the bead slide is on, check the preset limits
        zpos=stage.GetMaximumInMicrons(stage.Axis.Z)
        zneg=stage.GetMinimumInMicrons(stage.Axis.Z)
        zran=(zpos-zneg)/1000.0 # mm
        report.write('\nparameter: (preset) z-stage ['+str(zneg/1000.0)+', '+str(zpos/1000.0)+']mm')
    else: # the bead slide is not on, check stage translation
        v1=stage.GetMaximumInMicrons(stage.Axis.Z)
        stage.RequestMoveAbsolute(stage.Axis.X,v1)
        while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
        zpos=stage.GetPositionInMicrons(stage.Axis.Z)
        v2=stage.GetMinimumInMicrons(stage.Axis.Z)
        stage.RequestMoveAbsolute(stage.Axis.Z,v2)
        while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
        zneg=stage.GetPositionInMicrons(stage.Axis.Z)
        zran=(zpos-zneg)/1000.0
        report.write('\nparameter: (preset) z-stage ['+str(v2/1000.0)+', '+str(v1/1000.0)+']mm')
        report.write('\nhint: (actual) z-stage ['+str(zneg/1000.0)+', '+str(zpos/1000.0)+']mm')
        
        stage.RequestMoveAbsolute(stage.Axis.Z,0) # home
        while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
         
    if zran >= 5.0:
        zp=True
    else:
        zp=False
        
    if not sample: # check for stage stuck
        if zneg-t >= v2:
            zp=False
            report.write('\nhint: z stage is stuck along the negative direction')
        if zpos+t <= v1:
            zp=False
            report.write('\nhint: z stage is stuck along the positive direction')
        
    return zp
            
  
# check camera calibration
def pm_qc90(ex=100,f=1000):
    camera.SetTargetExposureMilliseconds(ex)
    camera.BeginView()
    light.GlobalOnState=False
    acquisition.Start(outpath,'hot-pixel',f)
    _wait()
    
    # _,folders,_=next(os.walk(rootpath)) # read all folders
    # template=str(datetime.date.today()).replace('-','')
    # folder=[i for i in folders if 'qc' in i.lower() and template in i.lower()] # read current folder
    # path=rootpath+'/'+folder[0]
    _,_,files=next(os.walk(abspath))
    file=[abspath+'/'+i for i in files if 'thumbnail' in i.lower() and 'hot-pixel' in i.lower()] # read the preview png
    file=sorted(file,key=os.path.getmtime) # sort the file by date
    png=skimage.io.imread(file[-1]) # read the newest hot-pixel thumbnail
    
    report.write('\nparameter: exposure time = '+str(ex)+'ms')
    report.write('\n           frame = '+str(f))
    
    m=png.max() # read maximum pixel value
    if m!=0: # hot pixel exists
        loc=np.sum(png==m)
        report.write('\nhint: '+str(loc)+' hot pixel found at 100ms exposure')
        if loc > 2: # at most 2 hot pixels
            return False
        else:
            return True
    else:
        report.write('\nhint: 0 hot pixel found at 100ms exposure')
        return True
    

# check stage tilting
def pm_qc100(count=5,r=100,t=2,p=30):
    camera.BeginView()
    light.GlobalOnState=True
    light[1].Enabled=True
    light[1].PercentPower=p
    if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS:
        autofocus.StartContinuousAutoFocus()
        time.sleep(5) # wait
    
    sp=False
    diff=0
    
    for c in range(count):
        tl=[] # top-left corner
        for i in range(15):
            pos=i*0.1-0.7 # [-0.7,0.7]um
            autofocus.FocusOffset=pos # set z offset
            while stage.IsMoving(stage.Axis.Z):
                time.sleep(0.01)
            tl.append(read_camera(0)[:r,:r]) # read left channel
        var1=_var(tl)
        
        w=camera.GetLatestImage().Channel(0).Dims.Width
        h=camera.GetLatestImage().Channel(0).Dims.Height
        xs=(w-r)*pixel_size
        ys=(h-r)*pixel_size
        stage.RequestMoveAbsolute(stage.Axis.X,stage.GetPositionInMicrons(stage.Axis.X)+xs) # move the FOV
        stage.RequestMoveAbsolute(stage.Axis.Y,stage.GetPositionInMicrons(stage.Axis.Y)+ys)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
            
        br=[] # bottom-right corner
        for i in range(15):
            pos=i*0.1-0.7 # [-0.7,0.7]um
            autofocus.FocusOffset=pos # set z offset
            while stage.IsMoving(stage.Axis.Z):
                time.sleep(0.01)
            br.append(read_camera(0)[-r:,-r:]) # read left channel
        var2=_var(br)
        
        diff=abs(var2.index(max(var2))-var1.index(max(var1)))
        if diff <= 2:
            sp=True
            break
        
    autofocus.FocusOffset=0 # home
    while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
    light[1].PercentPower=0
    light[1].Enabled=False
    
    report.write('\nparameter: trial = '+str(count))
    report.write('\n           blue laser power = '+str(p)+'%')
    
    report.write('\nhint: '+str(diff*100)+'nm focus difference')
    if not sp:
        report.write('\n      please check the bead slide')
    return sp
    
   
# check z-lock
# current assume focus is set
def pm_qc110(row=10,col=10,p=30,save=False):
    camera.BeginView()
    focus=instrument.FocusCameraControl
    light[1].Enabled=True
    light[1].PercentPower=p
    xpos=stage.GetPositionInMicrons(stage.Axis.X)
    ypos=stage.GetPositionInMicrons(stage.Axis.Y)
    if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS:
        autofocus.StartContinuousAutoFocus()
        time.sleep(5) # wait
    
    report.write('\nparameter: overview scan row = '+str(row))
    report.write('\n           overview scan col = '+str(col))
    report.write('\n           blue laser power = '+str(p)+'%')
    
    # _,folders,_=next(os.walk(rootpath)) # read all folders
    # template=str(datetime.date.today()).replace('-','')
    # folder=[i for i in folders if 'qc' in i.lower() and template in i.lower()] # read current folder
    # path=rootpath+'/'+folder[0]
    raw=focus.GetLatestImage()
    im=nim_image_to_array(raw)
    skimage.io.imsave(abspath+'/focus-pattern.tif',im,check_contrast=False)
    print('focus pattern saved as focus-pattern.tif')
    report.write('\nhint: focus pattern saved as focus-pattern.tif')
    
    zp=True
    zp=_snake(row,col,save)
    
    light[1].PercentPower=0
    light[1].Enabled=False
    stage.RequestMoveAbsolute(stage.Axis.X,xpos)
    stage.RequestMoveAbsolute(stage.Axis.Y,ypos)
    while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
        time.sleep(0.01)
    
    return zp
    
    
# check channel mapping
def pm_qc120(count=5,fov=20,point=2000,distance=5.0,radius=10.0,optimal=True):
    global pixel_size
    
    if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS: # check z-lock
        autofocus.StartContinuousAutoFocus()
        time.sleep(5) # wait
    
    camera.BeginView()
    light.GlobalOnState=True
    if optimal:
        p1=find_laser_power(1,500) # find optimal blue laser power
        p2=0
    else:
        p1=30
        p2=30
    light[1].Enabled=True
    light[3].Enabled=True
    light[1].PercentPower=p1
    light[3].PercentPower=p2
    
    if optimal:
        mean1=np.average(read_camera(0))
        mean2=np.average(read_camera(1))
        while mean2 <= mean1:
            p2=p2+0.5 # increment
            light[3].PercentPower=p2
            time.sleep(0.5)
            mean2=np.average(read_camera(1))
    
    cp=False
    
    for i in range(count):
        calibration.ChannelMapping.BeginCalibration(fov,point,distance,radius,False)
        pixel_size=calibration.ChannelMapping.GetLatestMapping().pixelSize_um # read pixel size
        std_pixel=calibration.ChannelMapping.GetLatestMapping().stDevSingleAxisAbsoluteErrors
        std=std_pixel*pixel_size
        coverage=calibration.ChannelMapping.GetLatestMapping().proportionCoverage
        if std < 0.02 and coverage==1.0:
            cp=True
            calibration.ChannelMapping.SaveLatestCalibration()
            break
    
    report.write('\nparameter: blue laser power = '+str(p1)+'%')
    report.write('\n           red laser power = '+str(p2)+'%')
    report.write('\n           trial = '+str(count))
    report.write('\n           max number of FOVs = '+str(fov))
    report.write('\n           target number of points = '+str(point))
    report.write('\n           max distance between channels = '+str(distance))
    report.write('\n           exclusion radius between channels = '+str(radius))
    report.write('\nhint: standard deviation of errors = '+str(std*1000)+'nm')
    report.write('\n      point coverage = '+str(coverage*100)+'%')
    
    light[1].PercentPower=0
    light[3].PercentPower=0
    light[1].Enabled=False # turn off lasers
    light[3].Enabled=False
    
    return cp
        
    
# check 3d lens
def pm_qc130(depth=1,p=30):
    # p=find_laser_power(1,1000)
    light.GlobalOnState=True
    light[1].Enabled=True
    light[1].PercentPower=p
    time.sleep(1)
    
    if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS: # check z-lock
        autofocus.StartContinuousAutoFocus()
        time.sleep(5) # wait
    
    autofocus.FocusOffset=depth
    while stage.IsMoving(stage.Axis.Z):
        time.sleep(0.01)
    acquisition.Start(outpath,'positive-PSF-'+str(depth)+'um',1)
    _wait()
    
    light[1].Enabled=True
    time.sleep(1)
    autofocus.FocusOffset=-depth
    while stage.IsMoving(stage.Axis.Z):
        time.sleep(0.01)
    acquisition.Start(outpath,'negative-PSF-'+str(depth)+'um',1)
    _wait()
    
    instrument.ImagingModeControl.CurrentMode=instrument.ImagingModeControl.ThreeD # switch on 3d
    time.sleep(2)
    
    light[1].Enabled=True
    time.sleep(1)
    acquisition.Start(outpath,'negative-astigmatism-'+str(depth)+'um',1)
    _wait()
    
    light[1].Enabled=True
    time.sleep(1)
    autofocus.FocusOffset=depth
    while stage.IsMoving(stage.Axis.Z):
        time.sleep(0.01)
    acquisition.Start(outpath,'positive-astigmatism-'+str(depth)+'um',1)
    _wait()
    
    instrument.ImagingModeControl.CurrentMode=instrument.ImagingModeControl.Normal # switch off 3d
    time.sleep(2)
    
    autofocus.FocusOffset=0 # home
    while stage.IsMoving(stage.Axis.Z):
        time.sleep(0.01)
    
    light[1].PercentPower=0
    light[1].Enabled=False # turn off laser
    
    report.write('\nparameter: depth = '+str(depth)+'um')
    report.write('\n           blue laser power = '+str(p)+'%')
    report.write('\nhint: PSF patterns saved as ***-PSF-***.tif and ***-astigmatism-***.tif')
    report.write('\n      please check the astigmatism')


# check TIRF
# from 45 to 57
def pm_qc140(l=45,u=57,s=0.5,p=30):
    angle=instrument.IlluminationAngleControl
    
    camera.BeginView()
    light.GlobalOnState=True
    light[2].Enabled=True
    light[2].PercentPower=p
    time.sleep(5) # wait
    
    report.write('\nparamter: lower bound = '+str(l)+'-degree')
    report.write('\n          upper bound = '+str(u)+'-degree')
    report.write('\n          step size = '+str(s)+'-degree')
    report.write('\n          green laser power = '+str(p)+'%')
    
    V=[]
    for i in np.arange(l,u,s):
       	angle.RequestMoveAbsolute(i) # increase illumination angle
       	time.sleep(1)
        V.append(read_camera(1).std()) # larger std means sharper image
    
    ta=l+np.argmax(V)*s # estimate 
    if ta > 56 or ta < 50:
        tp=False
        report.write('\nhint: [bad] TIRF = '+str(ta))
    elif ta < 53.5 and ta > 51.5:
        tp=True
        report.write('\nhint: [perfect] TIRF = '+str(ta))
    else:
        tp=True
        report.write('\nhint: [normal] TIRF = '+str(ta))
        
    angle.RequestMoveAbsolute(0) # home
    light[2].PercentPower=0
    light[2].Enabled=False
    
    return tp
    
    
# check light program
def pm_qc150(ex=100):
    from NimDotNet import LightProgram
    
    lp=LightProgram([[[100,0,0,0],[0,100,0,0],[0,0,100,0],[0,0,0,100]],[[0,0,0,0]],[[0,50,0,0],[0,100,0,0],[0,0,0,50],[0,0,0,100]]]) # initial 3 steps
    lp.Step[0].Repeats=2 # first step repeats 2 times
    lp.Step[1].Repeats=8 # second step repeats 8 times
    lp.Step[2].Repeats=2 # third step repeats 2 times
    light.Program=lp # set light program
    
    camera.StopView() # stop live view
    camera.SetTargetExposureMilliseconds(ex)
    light.ProgramActive=True # activate light program
    acquisition.Start(outpath,'light-program',24)
    _wait()
    
    report.write('\nparameter: exposure time = '+str(ex)+'ms')
    report.write('\nhint: light program frames saved as light-program.tif')
    report.write('\n      please check the light program frames')
    
# check memory leaking
def pm_qc160(ex=10,frame=10000,t=80):
    camera.SetTargetExposureMilliseconds(ex) # set 10ms exposure
    acquisition.SaveTiffFiles=False # disable saving raws
    acquisition.Start(outpath,'memory-leaking',frame)
    bp=_wait()
    mp=True
    
    report.write('\nparameter: exposure time = '+str(ex)+'ms')
    report.write('\n           frame = '+str(frame))
    
    if not flag_memory_leaking:
        report.write('\nhint: please check NimOS memory usage from Windows task manager')
    else:
        try:
            import psutil
            ram=psutil.virtual_memory()[2]
            if ram > t:
                mp=False
                report.write('\nhint: (bad) current NimOS memory = '+str(ram)+'%')
            else:
                mp=True
                report.write('\nhint: (good) current NimOS memory = '+str(ram)+'%')
        except ImportError:
            report.write('\nhint: psutil is not available')
            report.write('\n      please check NimOS memory usage from Windows task manager')
    
    acquisition.SaveTiffFiles=True
    
    return bp,mp
    
# check laser power
# t=-1 means wait until stable
# current standard: UV->15mW, blue->200mW, green->200mW, red->140mW
def pm_qc170(t=30,uv=15,blue=200,green=200,red=140,save=False):
    light.GlobalOnState=True
    light[0].Enabled=True # UV
    light[0].PercentPower=100
    if t!=-1:
        time.sleep(t) # wait for 30s
        light[0].Enabled=False # Marc's note: turn off the laser one time and then turn it back on and wait for 5 seconds
        time.sleep(1)
        light[0].Enabled=True
        time.sleep(5)
        u=light[0].PowerW*1000
    else:
        u=wait_until_stable(0)*1000 # wait until stable
    if save:
        from PIL import ImageGrab
        im=ImageGrab.grab()
        im.save(abspath+'/max_uv_power.tif')
    light[0].PercentPower=0
    light[0].Enabled=False
    
    light[1].Enabled=True # blue
    light[1].PercentPower=100
    if t!=-1:
        time.sleep(t) # wait for 30s
        light[1].Enabled=False
        time.sleep(1)
        light[1].Enabled=True
        time.sleep(5)
        b=light[1].PowerW*1000
    else:
        b=wait_until_stable(1)*1000 # wait until stable
    if save:
        im=ImageGrab.grab()
        im.save(abspath+'/max_blue_power.tif')
    light[1].PercentPower=0
    light[1].Enabled=False
    
    light[2].Enabled=True # green
    light[2].PercentPower=100
    if t!=-1:
        time.sleep(t) # wait for 30s
        light[2].Enabled=False
        time.sleep(1)
        light[2].Enabled=True
        time.sleep(5)
        g=light[2].PowerW*1000
    else:
        g=wait_until_stable(2)*1000 # wait until stable
    if save:
        im=ImageGrab.grab()
        im.save(abspath+'/max_green_power.tif')
    light[2].PercentPower=0
    light[2].Enabled=False
    
    light[3].Enabled=True # red
    light[3].PercentPower=100
    if t!=-1:
        time.sleep(t) # wait for 30s
        light[3].Enabled=False
        time.sleep(1)
        light[3].Enabled=True
        time.sleep(5)
        r=light[3].PowerW*1000
    else:
        r=wait_until_stable(3)*1000 # wait until stable
    if save:
        im=ImageGrab.grab()
        im.save(abspath+'/max_red_power.tif')
    light[3].PercentPower=0
    light[3].Enabled=False
    
    report.write('\nparameter: UV laser power = '+str(uv)+'mW')
    report.write('\n           blue laser power = '+str(blue)+'mW')
    report.write('\n           green laser power = '+str(green)+'mW')
    report.write('\n           red laser power = '+str(red)+'mW')
    
    if u < uv:
        up=False
    else:
        up=True
    report.write('\nhint: (actual )UV laser power = '+str(u)+'mW')
    if b < blue:
        bp=False
    else:
        bp=True
    report.write('\n      (actual) blue laser power = '+str(b)+'mW')
    if g < green:
        gp=False
    else:
        gp=True
    report.write('\n      (actual) green laser power = '+str(g)+'mW')
    if r < red:
        rp=False
    else:
        rp=True
    report.write('\n      (actual) red laser power = '+str(r)+'mW')
    
    if u > 1000:
        report.write('\n      UV laser power too high, please check it again manually')
    if b > 1000:
        report.write('\n      blue laser power too high, please check it again manually')
    if g > 1000:
        report.write('\n      green laser power too high, please check it again manually')
    if r > 1000:
        report.write('\n      red laser power too high, please check it again manually')
        
    return up,bp,gp,rp



def pm_main():   
    # PM link: https://docs.google.com/document/d/16Kt_r53kOqY2PMRJG4U3P0g0yC6TMqmf/edit#heading=h.gjdgxs
    # start PM and write header
    report.write('*******SEMI-AUTOMATED PM*******')
    report.write('\nauthor: Jack') # author acknowledgement
    report.write('\ntester: '+str(user)) # tester
    report.write('\ndate: '+str(datetime.datetime.now())) # current time
    report.write('\nserial number: '+str(instrument.GetAvailableInstruments()[0]))
    report.write('\noutput folder: '+outpath)
    _init()
    
    global result
    
    # check microscope (in person only)
    timer_start()
    print('pm_qc10: check microscope')
    report.write('\n\npm_qc10: check microscope')
    report.write('\nhint: please check the physical condition of the Nanoimager')
    pm_qc[0]='TBD'
    timer_end()
    
    # check NimOS connection
    #### need to decide how to run the script and if it is possible to print the error message
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc20: check NimOS connection')
    report.write('\n\npm_qc20: check NimOS connection')
    if not pm_qc20():
        report.write('\noutput: failed to connect to instrument from NimOS')
        pm_qc[1]='Fail'
        report.close()
        result=False
        exit()
    else:
        report.write('\noutput: passed to connect to instrument from NimOS')
        pm_qc[1]='Pass'
    timer_end()
    
    # check interlock engagement (in person only)
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc30: check interlock')
    report.write('\n\npm_qc30: check interlock')
    report.write('\nhint: please check the interlock')
    pm_qc[2]='TBD'
    timer_end()
    
    # check sample holder (in person only)
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc40: check sample holder')
    report.write('\n\npm_qc40: check sample holder')
    report.write('\nhint: please check the sample holder')
    pm_qc[3]='TBD'
    timer_end()
    
    # start temperature control
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc50: check temperature control')
    report.write('\n\npm_qc50: check temperature control')
    temperature_timer=time.time() # start timer for temperature
    pm_qc50(target_temperature,flag_temperature)
    timer_end()
    
    # check transillumination control
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc60: check transillumination')
    report.write('\n\npm_qc60: check transillumination')
    if flag_transillumination:
        print('transillumination images saved as LED-***-***.tif')
        report.write('\nhint: transillumination images saved as LED-***-***.tif')
    if not pm_qc60(channel_split,100,flag_transillumination):
        report.write('\noutput: failed to provide correct transillumination')
        pm_qc[5]='Fail'
        result=False
    else:
        report.write('\noutput: passed to provide correcct transillumination')
        pm_qc[5]='Pass'
    timer_end()
    
    # check xy stage movement
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc70: check xy stage movement')
    report.write('\n\npm_qc70: check xy stage movement')
    xp,yp=pm_qc70(stage_tolerance,flag_sample_on)
    if not xp:
        report.write('\noutput: failed to achieve correct x stage movement')
    else:
        report.write('\noutput: passed to achieve correct x stage movement')
    if not yp:
        report.write('\noutput: failed to achieve correct y stage movement')
    else:
        report.write('\noutput: passed to achieve correct y stage movement')
    if xp and yp:
        pm_qc[6]='Pass'
    else:
        pm_qc[6]='Fail'
    timer_end()    
    
    # check z stage movement
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc80: check z stage movement')
    report.write('\n\npm_qc80: check z stage movement')
    if not pm_qc80(stage_tolerance,flag_sample_on):
        report.write('\noutput: failed to achieve correct z stage movement')
        pm_qc[7]='Fail'
        result=False
    else:
        report.write('\noutput: passed to achieve correct z stage movement')
        pm_qc[7]='Pass'
    timer_end()
    
    # check camera calibration
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc90: check camera calibration')
    report.write('\n\npm_qc90: check camera calibration')
    if not pm_qc90(100,1000):
        report.write('\noutput: failed to achieve correct camera calibration')
        pm_qc[8]='Fail'
        result=False
    else:
        report.write('\noutput: passed to achieve correct camera calibration')
        pm_qc[8]='Pass'
    timer_end()
    
    # check stage tilting
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc100: check stage tilting')
    report.write('\n\npm_qc100: check stage tilting')
    if not pm_qc100(5,100,2,30):
        report.write('\noutput: failed to achieve no stage tilting')
        pm_qc[9]='Fail'
        result=False
    else:
        report.write('\noutput: passed to achieve no stage tilting')
        pm_qc[9]='Pass'
    timer_end()
    
    # check z-lock
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc110: check z-lock')
    report.write('\n\npm_qc110: check z-lock')
    if not pm_qc110(10,10,30,flag_overview):
        report.write('\noutput: failed to achieve correct z-lock')
        pm_qc[10]='Fail'
        result=False
    else:
        report.write('\noutput: passed to achieve correct z-lock')
        pm_qc[10]='Pass'
    timer_end()
    
    # check channel mapping calibration
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc120: check channel mapping calibration')
    report.write('\n\npm_qc120: check channel mapping calibration')
    if not pm_qc120(5,20,2000,5.0,10.0,flag_find_laser_power):
        report.write('\noutput: failed to achieve correct channel mapping calibration')
        pm_qc[11]='Fail'
        result=False
    else:
        report.write('\noutput: passed to achieve correct channel mapping calibration')
        pm_qc[11]='Pass'
    timer_end()
    
    # check 3d lens
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc130: check 3d lens')
    report.write('\n\npm_qc130: check 3d lens')
    pm_qc130(1,30)
    pm_qc[12]='TBD'
    timer_end()
    
    # check TIRF
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc140: check TIRF')
    report.write('\n\npm_qc140: check TIRF')
    if not pm_qc140(45,57,0.5,30):
        report.write('\noutput: failed to achieve correct TIRF angle')
        pm_qc[13]='Fail'
        result=False
    else:
        report.write('\noutput: passed to achieve correct TIRF angle')
        pm_qc[13]='Pass'
    timer_end()
    
    # check light program
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc150: check light program')
    report.write('\n\npm_qc150: check light program')
    pm_qc150(100)
    pm_qc[14]='TBD'
    timer_end()
    
    # check memory leaking
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc160: check memory leaking')
    report.write('\n\npm_qc160: check memory leaking')
    bp,mp=pm_qc160(10,10000,80)
    if not bp:
        report.write('\noutput: failed to achieve no frame skipping')
        result=False
    else:
        report.write('\noutput: passed to achieve no frame skipping')
    if not mp:
        report.write('\n        failed to achieve no memory leaking')
        result=False
    else:
        report.write('\n        passed to achieve no memory leaking')
    if bp and mp:
        pm_qc[15]='Pass'
    else:
        pm_qc[15]='Fail'
    timer_end()
    
    # check laser power
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc170: check laser power')
    report.write('\n\npm_qc170: check laser power')
    up,bp,gp,rp=pm_qc170(30,15,200,200,140,flag_laser_screenshot)
    if not up:
        report.write('\noutput: failed to achieve standard UV laser power')
        result=False
    if not bp:
        report.write('\noutput: failed to achieve standard blue laser power')
        result=False
    if not gp:
        report.write('\noutput: failed to achieve standard green laser power')
        result=False
    if not rp:
        report.write('\noutput: failed to achieve standard red laser power')
        result=False
    if up and bp and gp and rp:
        report.write('\noutput: passed to achieve standard laser powers')
        pm_qc[16]='Pass'
    else:
        pm_qc[16]='Fail'
    timer_end()
    
    # check temperature control
    if flag_temperature:
        while (time.time()-temperature_timer) < temperature_wait_time: # wait
            time.sleep(0.01)
        current_temperature=temperature.CurrentTemperatureC # read current temperature
        diff=math.fabs(current_temperature-target_temperature)
        report.write('\n\npm_qc50: continue temperature control')
        report.write('\nhint: measured temperature = '+str(current_temperature)+'C')
        report.write('\n      temperature difference = '+str(diff)+'C')
        if diff > 0.2:
            report.write('\noutput: failed to achieve correct temperature control')
            pm_qc[4]='Fail'
            result=False
        else:
            report.write('\noutput: passed to achieve correct temperature control')
            pm_qc[4]='Pass'

def pm_analysis():
    report.write('\n\n*******PM FINISHED*******')
    report.write('\nOutcome = '+str(result))
    report.write('\nTotal Runtime = '+str(sum(runtime))+'s')
    report.write('\nSummary:')
    report.write('\n         qc10: tbd, please manually check the overall condition of the Nanoimager')
    report.write('\n         qc20: ')
    if pm_qc[1]=='Fail':
        report.write('*fail, please manually check the NimOS connection')
    else:
        report.write('pass')
    report.write('\n         qc30: tbd, please manually check the interlock')
    report.write('\n         qc40: tbd, please manually check the sample stage')
    report.write('\n         qc50: ')
    if pm_qc[4]=='Fail':
        report.write('*fail, please manually check the temperature curves and rerun the thermistor calibration')
    else:
        report.write('pass')
    report.write('\n         qc60: ')
    if pm_qc[5]=='Fail':
        report.write('*fail, please manually check the LEDs and their connections on the enclosure')
    else:
        report.write('pass')
    report.write('\n         qc70: ')
    if pm_qc[6]=='Fail':
        report.write('*fail, please manually check the XY stage translation and the stage settings in the IDF')
    else:
        report.write('pass')
    report.write('\n         qc80: ')
    if pm_qc[7]=='Fail':
        report.write('*fail, please manually check the Z stage translation and the stage settings in the IDF')
    else:
        report.write('pass')
    report.write('\n         qc90: ')
    if pm_qc[8]=='Fail':
        report.write('*fail, please rerun the camera calibration')
    else:
        report.write('pass')
    report.write('\n         qc100: ')
    if pm_qc[9]=='Fail':
        report.write('*fail, please manually check the stage tilting and adjust the stage screws if needed')
    else:
        report.write('pass')
    report.write('\n         qc110: ')
    if pm_qc[10]=='Fail':
        report.write('*fail, please manually check the z-lock preferably with another bead slide')
    else:
        report.write('pass')
    report.write('\n         qc120: ')
    if pm_qc[11]=='Fail':
        report.write('*fail, please manually rerun the channel mapping calibration preferably with another bead slide')
    else:
        report.write('pass')
    report.write('\n         qc130: tbd, please manually check the acquired PSF images (in total 4 images)')
    report.write('\n         qc140: ')
    if pm_qc[13]=='Fail':
        report.write('*fail, please manually check the TIRF angle preferably with another bead slide')
    else:
        report.write('pass')
    report.write('\n         qc150: tbd, please manually check the acquired light program images (in total 24 frames)')
    report.write('\n         qc160: tbd, please manually check the memory usage of NimOS from Windows task manager')
    report.write('\n         qc170: ')
    if pm_qc[16]=='Fail':
        report.write('*fail, please manually re-check the lasers')
    else:
        report.write('pass')
        
    report.write('\n\nOnce additional manual-inspection is carried out, please complete the copy of the FLD-00009 maintenance report')
    report.close()
    
        
def iqoq_main():
    a=1
    
    
if __name__ == "__main__":
    
    parser=argparse.ArgumentParser(description='automated quality control') # add arguments and parse it to an object
    parser.add_argument('--purpose',metavar='PM/IQOQ/FIQA',default='PM',help='the purpose of the quality control (not case sensitive)')
    parser.add_argument('--user',metavar='xxxx',default='Jack',help='the tester')
    parser.add_argument('--outpath',metavar='xx',default='QC',help='relative output diretory, padded with date')
    parser.add_argument('--temperature',type=int,default=35,help='the target temperature in celsius')
    parser.add_argument('--wait',action='store_false',help='flag for waiting temperature control')
    args=parser.parse_args()
    
    purpose=args.purpose
    user=args.user
    outpath=args.outpath
    target_temperature=args.temperature
    flag_temperature=args.wait
    
    try:
        camera.NumberOfFramesWaitingInBuffer() # this function is only available in the development mode
    except NameError:
        print('[WARNING] please start NimOS in the development build')
        report.write('please start NimOS in the development build (--development-build)')
        report.close()
    else:
        print('running NimOS in development build')
    
    done=False
    if not autofocus.HasReferencePoint:
        print('[WARNING] please set the focus reference first')
        report.write('please set the focus reference first')
        report.close()
    else:
        print('The focus reference has been set')
        print('AUTOMATED '+purpose.upper()+' STARTS...')
        if purpose.lower()=='pm':
            pm_main()
            done=True
        elif purpose.lower()=='iqoq':
            iqoq_main()
            done=False
        elif purpose.lower()=='fiqa':
            print('[WARNING] currently do not support automated FIQA, please contact CX.Jack for more information')
        else:
            print('[ERROR] no such a purpose')
    
    if done:
        if not result:
            print('QC FAILED, please check the final report for more details')
        else:
            print('QC PASSED, please go and have fun :D')
        pm_analysis()
        
    # import NimSetup
    # NimYSetup.cleanup()
    
    
    
    