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
temperature_wait_time=100 # temperature waiting time, default to 60min
flag_transillumination=False # flag for saving transillumination
channel_split=640 # system split
flag_sample_on=True # flag if sample is on
stage_tolerance=0.05 # translation tolerance in mm
flag_find_laser_power=False # flag for finding optimal laser power for channel mapping
pixel_size=117 # nm/pixel
fx=50 # FOV width in pixel
fy=80 # FOV height in pixel
flag_memory_leaking=False # flag for checking memery usage using psutil
date=str(datetime.date.today()).replace('-','')
filename='C:/Users/ONI/Desktop/'+date+'_maintenance.txt'
report=open(filename,'w')
runtime=[]
result=True




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
    
def _var(ims,w=5):
    import scipy.ndimage
    v=[]
    for i in range(len(ims)):
        mean=scipy.ndimage.uniform_filter(np.float32(ims[i]),w,mode='reflect')  # get mean
        sqr_mean=scipy.ndimage.uniform_filter(np.float32(ims[i])**2,w,mode='reflect')  # get square mean
        var=sqr_mean-mean**2 # variance trick
        v.append(var/mean)
        
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
    
def _snake(w,h):
    snakescan=True


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
    report.write('\nhint: target temperature = '+str(tar)+'C')
    if flag_temperature:
        report.write('\n      temperature waiting time = '+str(temperature_wait_time/60)+'min')
    else:
        report.write('\n      please check the temperature after 60min')

# check tranillumination
# acquire two images [dim, bright] for each color
def pm_qc60(sp=640,ex=30,save=False):
    LED=instrument.TransilluminationControl
    camera.SetTargetExposureMilliseconds(ex) # set exposure
    camera.BeginView() # view camera

    # red LED
    LED.SetRingColour([0.5,0,0]) # red-dim 50%
    time.sleep(1) # wait for LED switch
    if save==True: # save
        acquisition.Start(outpath,'LED-red-dim',1)
        _wait() # wait for acquisition
        raw=data_manager.RawImages # get the raw reference
        rd=raw.GetImage(0) # get the raw
        rd=nim_image_to_array(rd) # convert it to numpy.array
        rd=rd[:,:428] # crop the left channel
        rd=np.average(rd) # compute the average
    else: # no save
        rd=camera.GetLatestImage() # grab from buffer
        rd=rd.Channel(0) # crop the let channel
        rd=np.average(rd.Pixels) # compute the average
    
    LED.SetRingColour([0.9,0,0]) # red-bright 90%
    time.sleep(1)
    if save==True:
        acquisition.Start(outpath,'LED-red-bright',1)
        _wait()
        raw=data_manager.RawImages
        rb=raw.GetImage(0)
        rb=nim_image_to_array(rb)
        rb=rb[:,:428]
        rb=np.average(rb)
    else: # no save
        rb=camera.GetLatestImage()
        rb=rb.Channel(0)
        rb=np.average(rb.Pixels)
        
    # blue LED
    LED.SetRingColour([0,0.5,0]) # blue-dim 50%
    time.sleep(1)
    if save==True:
        acquisition.Start(outpath,'LED-blue-dim',1)
        _wait()
        raw=data_manager.RawImages
        bd=raw.GetImage(0)
        bd=nim_image_to_array(bd)
        bd=bd[:,:428]
        bd=np.average(bd)
    else:
        bd=camera.GetLatestImage()
        bd=bd.Channel(0)
        bd=np.average(bd.Pixels)
    
    LED.SetRingColour([0,0.9,0]) # blue-bright 90%
    if save==True:
        acquisition.Start(outpath,'LED-blue-bright',1)
        _wait()
        raw=data_manager.RawImages
        bb=raw.GetImage(0)
        bb=nim_image_to_array(bb)
        bb=bb[:,:428]
        bb=np.average(bb)
    else:
        bb=camera.GetLatestImage()
        bb=bb.Channel(0)
        bb=np.average(bb.Pixels)
        
    # green LED
    LED.SetRingColour([0,0,0.5]) # green-dim 50%
    time.sleep(1)
    if save==True:
        acquisition.Start(outpath,'LED-green-dim',1)
        _wait()
        raw=data_manager.RawImages
        gd=raw.GetImage(0)
        gd=nim_image_to_array(gd)
        gd=gd[:,:428]
        gd=np.average(gd)
    else:
        gd=camera.GetLatestImage()
        gd=gd.Channel(0)
        gd=np.average(gd.Pixels)
    
    LED.SetRingColour([0,0,0.9]) # green-bright 90%
    time.sleep(1)
    if save==True:
        acquisition.Start(outpath,'LED-green-bright',1)
        _wait()
        raw=data_manager.RawImages
        gb=raw.GetImage(0)
        gb=nim_image_to_array(gb)
        gb=gb[:,:428]
        gb=np.average(gb)
    else:
        gb=camera.GetLatestImage()
        gb=gb.Channel(0)
        gb=np.average(gb.Pixels)
    
    LED.Enabled=False # turn off LED
    
    if sp==640: # current observation of brightness is green > red > blue for 640-split
        if rd > rb or bd > bb or gd > gb or rd > gd or bd > rd or rb > gb or bb > rb:
            return False
        else:
            return True    

   
# check xy stage movement
# check stage translation if sample is not on, otherwise only read preset limits
def pm_qc70(t=0.05,sample=False):
    if sample==True: # the bead slide is on, check the preset limits
        xpos=stage.GetMaximumInMicrons(stage.Axis.X) # read positive x
        xneg=stage.GetMinimumInMicrons(stage.Axis.X) # read negative x
        xran=(xpos-xneg)/1000.0 # mm
        ypos=stage.GetMaximumInMicrons(stage.Axis.Y) # read positive y
        yneg=stage.GetMinimumInMicrons(stage.Axis.Y) # read negative y
        yran=(ypos-yneg)/1000.0
        report.write('\nhint: (preset) x-stage ['+str(xneg/1000.0)+', '+str(xpos/1000.0)+']mm')
        report.write('\n      (preset) y-stage ['+str(yneg/1000.0)+', '+str(ypos/1000.0)+']mm')
    else: # the bead slide is not on, check stage translation
        v1=stage.GetMaximumInMicrons(stage.Axis.X)
        stage.RequestMoveAbsolute(stage.Axis.X,v1)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01) # wait until stage stops
        xpos=stage.GetPositionInMicrons(stage.Axis.X)
        v2=stage.GetMinimumInMicrons(stage.Axis.X)
        stage.RequestMoveAbsolute(stage.Axis.X,v2)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
        xneg=stage.GetPositionInMicrons(stage.Axis.X)
        xran=(xpos-xneg)/1000.0
        v3=stage.GetMaximumInMicrons(stage.Axis.Y)
        stage.RequestMoveAbsolute(stage.Axis.Y,v3)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
        ypos=stage.GetPositionInMicrons(stage.Axis.Y)
        v4=stage.GetMinimumInMicrons(stage.Axis.Y)
        stage.RequestMoveAbsolute(stage.Axis.Y,v4)
        while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
            time.sleep(0.01)
        yneg=stage.GetPositionInMicrons(stage.Axis.Y)
        yran=(ypos-yneg)/1000.0
        report.write('\nhint: (preset) x-stage ['+str(v2/1000.0)+', '+str(v1/1000.0)+']mm')
        report.write('\n      (preset) y-stage ['+str(v4/1000.0)+', '+str(v3/1000.0)+']mm')
        report.write('\nhint: (actual) x-stage ['+str(xneg/1000.0)+', '+str(xpos/1000.0)+']mm')
        report.write('\n      (actual) y-stage ['+str(yneg/1000.0)+', '+str(ypos/1000.0)+']mm')
        
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
        report.write('\nhint: (preset) z-stage ['+str(zneg/1000.0)+', '+str(zpos/1000.0)+']mm')
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
        report.write('\nhint: (preset) z-stage ['+str(v2/1000.0)+', '+str(v1/1000.0)+']mm')
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
    light.GlobalOnState=False
    acquisition.Start(outpath,'hot-pixel',f)
    _wait()
    
    # _,folders,_=next(os.walk(rootpath)) # read all folders
    # template=str(datetime.date.today()).replace('-','')
    # folder=[i for i in folders if 'qc' in i.lower() and template in i.lower()] # read current folder
    # path=rootpath+'/'+folder[0]
    path=data_manager.Directory
    _,_,files=next(os.walk(path))
    file=[i for i in files if 'hot-pixel_thumbnail' in i.lower()] # read the preview png
    png=skimage.io.imread(path+'/'+file[0])
    
    m=png.max() # read maximum pixel value
    if m!=0: # hot pixel exists
        loc=np.sum(png==m)
        report.write('\nhint: '+str(loc)+' hot pixel found at 100ms exposure')
        return False
    else:
        report.write('\nhint: 0 hot pixel found at 100ms exposure')
        return True
    

# check stage tilting
def pm_qc100(w=50,t=2):
    light[1].PercentPower=30
    light[1].Enabled=True
    acquisition.InitAcquisition(outpath,'tilting-left',11)
    pos=-0.5
    for i in range(11): # acquire the top-left corner
        pos=pos+1*0.1
        autofocus.FocusOffset=pos
        while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
        acquisition.ContinueFor(1)
        while acquisition.IsActiveOrCompleting:
            time.sleep(0.01)
        light[1].Enabled=True
    while data_manager.IsBusy:
        time.sleep(0.1)
        
    tl=[]
    for i in range(11):
        raw=data_manager.RawImages
        img=raw.GetImage(0)
        img=nim_image_to_array(img)
        tl.append(img[:w,:w])
    v1=_var(tl,3)
    f1=v1.index(max(v1))
    
    xs=(428-w)*pixel_size
    ys=(684-w)*pixel_size
    xpos=stage.GetPositionInMicrons(stage.Axis.X)+xs
    ypos=stage.GetPositionInMicrons(stage.Axis.Y)+ys
    stage.RequestMoveAbsolute(stage.Axis.X,xpos)
    stage.RequestMoveAbsolute(stage.Axis.Y,ypos)
    while stage.IsMoving(stage.Axis.X) or stage.IsMoving(stage.Axis.Y):
        time.sleep(0.01)
    
    pos=-0.5
    for i in range(11): # acquire the top-left corner
        pos=pos+1*0.1
        autofocus.FocusOffset=pos
        while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
        acquisition.ContinueFor(1)
        while acquisition.IsActiveOrCompleting:
            time.sleep(0.01)
        light[1].Enabled=True
    while data_manager.IsBusy:
        time.sleep(0.1)
    
    rb=[]
    for i in range(11):
        raw=data_manager.RawImages
        img=raw.GetImage(0)
        img=nim_image_to_array(img)
        tl.append(img[-w:,-w:])
    v2=_var(rb,3)
    f2=v2.index(max(v2))

    diff=math.abs(v2-v1)
    report.write('\nhint: '+str(diff*100)+'nm focus difference')
    if diff > 2:
        return False
    else:
        return True
    
   
# check z-lock
# current assume focus is set
def pm_qc110():
    focus=instrument.FocusCameraControl
    if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS:
        autofocus.StartContinuousAutoFocus()
        time.sleep(5) # wait
    
    # _,folders,_=next(os.walk(rootpath)) # read all folders
    # template=str(datetime.date.today()).replace('-','')
    # folder=[i for i in folders if 'qc' in i.lower() and template in i.lower()] # read current folder
    # path=rootpath+'/'+folder[0]
    path=data_manager.Directory
    img=focus.GetLatestImage()
    img=nim_image_to_array(img)
    skimage.io.imsave(path+'/focus-pattern.tif',img)
    print('focus pattern saved as focus-pattern.tif')
    report.write('\nhint: focus pattern saved as focus-pattern.tif')
    
    _snake(fx,fy)
    
    
# check channel mapping
def pm_qc120(count=5,fov=20,point=2000,distance=5.0,radius=10.0):
    global pixel_size
    pixel_size=calibration.ChannelMapping.GetLatestMapping().pixelSize_um # read pixel size
    
    if autofocus.CurrentStatus is not autofocus.Status.FOCUSING_CONTINUOUS: # check z-lock
        autofocus.StartContinuousAutoFocus()
        time.sleep(5) # wait
    
    camera.BeginView()
    light.GlobalOnState=True
    p1=find_laser_power(1,500) # find optimal blue laser power
    p2=0
    light[1].PercentPower=p1
    light[1].Enabled=True
    light[3].PercentPower=p2
    light[3].Enabled=True
    mean1=np.average(camera.GetLatestImage().Channel(0).Pixels)
    mean2=np.average(camera.GetLatestImage().Channel(1).Pixels)
    while mean2 <= mean1:
        p2=p2+0.5 # increment
        light[3].PercentPower=p2
        time.sleep(0.5)
        mean2=np.average(camera.GetLatestImage().Channel(1).Pixels)
    
    cp=False
    
    for i in range(count):
        calibration.ChannelMapping.BeginCalibration(fov,point,distance,radius,False)
        std_pixel=calibration.ChannelMapping.GetLatestMapping().stDevSingleAxisAbsoluteErrors
        std=std_pixel*pixel_size
        coverage=calibration.ChannelMapping.GetLatestMapping().proportionCoverage
        if std < 0.02 and coverage==1.0:
            cp=True
            calibration.ChannelMapping.SaveLatestCalibration()
            break
    
    report.write('\nhint: blue laser = '+str(p1)+'% and red laser = '+str(p2)+'%')
    report.write('\n      max number of FOVs = '+str(fov))
    report.write('\n      target number of points = '+str(point))
    report.write('\n      max distance between channels = '+str(distance))
    report.write('\n      exclusion radius between channels = '+str(radius))
    report.write('\nhint: standard deviation of errors = '+str(std*1000)+'nm')
    report.write('\n      point coverage = '+str(coverage*100)+'%')
    
    light[1].Enabled=False # turn off lasers
    light[3].Enabled=False
    
    return cp
        
    
# check 3d lens
# current use blue laser
def pm_qc130(depth=1):
    # p=find_laser_power(1,1000)
    p=30
    light[1].PercentPower=p
    light[1].Enabled=True
    light.GlobalOnState=True
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
    
    light[1].Enabled=False # turn off laser
        
    report.write('\nhint: PSF pattern saved as ***-PSF-***.tif and ***-astigmatism-***.tif')
    report.write('\n      please check the astigmatism')


# check TIRF
# from 45 to 57
def pm_qc140(lower=45,upper=57,step=0.5,p=30):
    angle=instrument.IlluminationAngleControl
    
    camera.BeginView()
    light[2].PercentPower=p
    light[2].Enabled=True
    light.GlobalOnState=True
    time.sleep(5) # wait
    
    V=[]
    for i in np.arange(lower,upper,step):
       	angle.RequestMoveAbsolute(i) # increase illumination angle
       	time.sleep(1)
       	img=camera.GetLatestImage()
       	img=img.Channel(1)
       	V.append(np.std(img.Pixels)) # larger std means sharper image
    
    a=lower+np.argmax(V)*step # estimate 
    if a > 56 or a < 50:
        tp=False
        report.write('\nhint: [bad] TIRF = '+str(a))
    elif a < 53.5 or a > 51.5:
        tp=True
        report.write('\nhint: [perfect] TIRF = '+str(a))
    else:
        tp=True
        report.write('\nhint: [normal] TIRF = '+str(a))
        
    angle.RequestMoveAbsolute(0) # home
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
    
    camera.SetTargetExposureMilliseconds(ex)
    camera.StopView() # stop live view
    light.ProgramActive=True # activate light program
    acquisition.Start(outpath,'light-program',24)
    _wait()
    
    report.write('\nhint: frames saved as light-program.tif')
    report.write('\n      please check the light program frames')
    
# check memory leaking
def pm_qc160(ex=10,frame=10000,t=80):
    camera.SetTargetExposureMilliseconds(ex) # set 10ms exposure
    acquisition.SaveTiffFiles=False # disable saving raws
    acquisition.Start(outpath,'memory-leaking',frame)
    bp=_wait()
    mp=True
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
# default wait for 30s
# -1 means wait until stable
# current standard: UV->15mW, blue->200mW, green->200mW, red->140mW
def pm_qc170(t=30,uv=15,blue=200,green=200,red=140):
    light.GlobalOnState=True
    light[0].PercentPower=100 # UV
    light[0].Enabled=True
    if t!=-1:
        time.sleep(t) # wait for 30s
        u=light[0].PowerW*1000
    else:
        u=wait_until_stable(0)*1000 # wait until stable
    light[0].PercentPower=0
    light[0].Enabled=False
    
    light[1].PercentPower=100 # blue
    light[1].Enabled=True
    if t!=-1:
        time.sleep(t) # wait for 30s
        b=light[1].PowerW*1000
    else:
        b=wait_until_stable(1)*1000 # wait until stable
    light[1].PercentPower=0
    light[1].Enabled=False
    
    light[2].PercentPower=100 # green
    light[2].Enabled=True
    if t!=-1:
        time.sleep(t) # wait for 30s
        g=light[2].PowerW*1000
    else:
        g=wait_until_stable(2)*1000 # wait until stable
    light[2].PercentPower=0
    light[2].Enabled=False
    
    light[3].PercentPower=100 # UV
    light[3].Enabled=True
    if t!=-1:
        time.sleep(t) # wait for 30s
        r=light[3].PowerW*1000
    else:
        r=wait_until_stable(3)*1000 # wait until stable
    light[3].PercentPower=0
    light[3].Enabled=False
    
    if u < uv:
        up=False
    else:
        up=True
    report.write('\nhint: UV laser power = '+str(u)+'mW')
    if b < blue:
        bp=False
    else:
        bp=True
    report.write('\n      blue laser power = '+str(b)+'mW')
    if g < green:
        gp=False
    else:
        gp=True
    report.write('\n      green laser power = '+str(g)+'mW')
    if r < red:
        rp=False
    else:
        rp=True
    report.write('\n      red laser power = '+str(r)+'mW')
    
    return up,bp,gp,rp

def pm_main():   
    # PM link: https://docs.google.com/document/d/16Kt_r53kOqY2PMRJG4U3P0g0yC6TMqmf/edit#heading=h.gjdgxs
    # start PM and write header
    report.write('SEMI-AUTOMATED PM')
    report.write('\nauthor: Jack') # author acknowledgement
    report.write('\ntester: '+str(user)) # tester
    report.write('\ndate: '+str(datetime.datetime.now())) # current time
    report.write('\nserial number: '+str(instrument.GetAvailableInstruments()[0]))
    report.write('\noutput folder: '+str(data_manager.Directory))
    _init()
    
    global result
    
    # check microscope (in person only)
    timer_start()
    print('pm_qc10: check microscope')
    report.write('\n\npm_qc10: check microscope')
    report.write('\nhint: please check the physical condition of the Nanoimager')
    timer_end()
    
    # check NimOS connection
    #### need to decide how to run the script and if it is possible to print the error message
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc20: check NimOS connection')
    report.write('\n\npm_qc20: check NimOS connection')
    if not pm_qc20():
        report.write('\noutput: failed to connect to instrument from NimOS')
        report.close()
        result=False
        exit()
    else:
        report.write('\noutput: passed to connect to instrument from NimOS')
    timer_end()
    
    # check interlock engagement (in person only)
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc30: check interlock')
    report.write('\n\npm_qc30: check interlock')
    report.write('\nhint: please check the interlock')
    timer_end()
    
    # check sample holder (in person only)
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc40: check sample holder')
    report.write('\n\npm_qc40: check sample holder')
    report.write('\nhint: please check the sample holder')
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
    if not pm_qc60(channel_split,flag_transillumination):
        report.write('\noutput: failed to provide correct transillumination')
        result=False
    else:
        report.write('\noutput: passed to provide correcct transillumination')
    timer_end()
    
    # check xy stage movement
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc70: check xy stage movement')
    report.write('\n\npm_qc70: check xy stage movement')
    xp,yp=pm_qc70(stage_tolerance,flag_sample_on)
    if not xp:
        report.write('\noutput: failed to achieve correct x stage movement')
        result=False
    else:
        report.write('\noutput: passed to achieve correct x stage movement')
    if not yp:
        report.write('\noutput: failed to achieve correct y stage movement')
        result=False
    else:
        report.write('\noutput: passed to achieve correct y stage movement')
    timer_end()    
    
    # check z stage movement
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc80: check z stage movement')
    report.write('\n\npm_qc80: check z stage movement')
    if not pm_qc80(stage_tolerance,flag_sample_on):
        report.write('\noutput: failed to achieve correct z stage movement')
        result=False
    else:
        report.write('\noutput: passed to achieve correct z stage movement')
    timer_end()
    
    # check camera calibration
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc90: check camera calibration')
    report.write('\n\npm_qc90: check camera calibration')
    if not pm_qc90(100,1000):
        report.write('\noutput: failed to achieve correct camera calibration')
        result=False
    else:
        report.write('\noutput: passed to achieve correct camera calibration')
    timer_end()
    
    # check stage tilting
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc100: check stage tilting')
    report.write('\n\npm_qc100: check stage tilting')
    if not pm_qc100(50,2):
        report.write('\noutput: failed to achieve no stage tilting')
        result=False
    else:
        report.write('\noutput: passed to achieve no stage tilting')
    timer_end()
    
    # check z-lock
    
    
    # check channel mapping calibration
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc120: check channel mapping calibration')
    report.write('\n\npm_qc120: check channel mapping calibration')
    if not pm_qc120(5,20,2000,5.0,10.0):
        report.write('\noutput: failed to achieve correct channel mapping calibration')
        result=False
    else:
        report.write('\noutput: passed to achieve correct channel mapping calibration')
    timer_end()
    
    # check 3d lens
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc130: check 3d lens')
    report.write('\n\npm_qc130: check 3d lens')
    pm_qc130(1)
    timer_end()
    
    # check TIRF
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc140: check TIRF')
    report.write('\n\npm_qc140: check TIRF')
    if not pm_qc140(45,57,0.5,30):
        report.write('\noutput: failed to achieve correct TIRF angle')
        result=False
    else:
        report.write('\noutput: passed to achieve correct TIRF angle')
    timer_end()
    
    # check light program
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc150: check light program')
    report.write('\n\npm_qc150: check light program')
    pm_qc150()
    timer_end()
    
    # check memory leaking
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc160: check memory leaking')
    report.write('\n\npm_qc160: check memory leaking')
    bp,mp=pm_qc160()
    if not bp:
        report.write('\noutput: failed to achieve no frame skipping')
        result=False
    else:
        report.write('\noutput: passed to achieve no frame skipping')
    if not mp:
        report.write('\noutput: failed to achieve no memory leaking')
        result=False
    else:
        report.write('\noutput: passed to achieve no memory leaking')
    timer_end()
    
    # check laser power
    time.sleep(1) # hold for 1s between checkpoints
    timer_start()
    print('pm_qc170: check laser power')
    report.write('\n\npm_qc170: check laser power')
    up,bp,gp,rp=pm_qc170(30,15,200,200,140)
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
    timer_end()
    
    # check temperature control
    if flag_temperature:
        while (time.time()-temperature_timer) < temperature_wait_time: # wait
            time.sleep(0.01)
        current_temperature=temperature.CurrentTemperatureC # read current temperature
        diff=math.fabs(current_temperature-target_temperature)
        report.write('\n      measured temperature = '+str(current_temperature)+'C')
        report.write('\n      temperature difference = '+str(diff)+'C')
        if diff > 0.2:
            report.write('\noutput: failed to achieve correct temperature control')
            result=False
        else:
            report.write('\noutput: passed to achieve correct temperature control')
        
def iqoq_main():
    a=1
    
    
if __name__ == "__main__":
    
    parser=argparse.ArgumentParser(description='automated quality control') # add arguments and parse it to an object
    parser.add_argument('--purpose',metavar='PM/IQOQ/FIQA',default='PM',help='the purpose of the quality control (not case sensitive)')
    parser.add_argument('--user',metavar='xxxx',default='Jack',help='the tester')
    parser.add_argument('--outpath',metavar='xx',default='QC',help='relative output diretory, padded with date')
    parser.add_argument('--temperature',type=int,default=31,help='the target temperature in celsius')
    parser.add_argument('--wait',action='store_false',help='flag for waiting temperature control')
    args=parser.parse_args()
    
    purpose=args.purpose
    user=args.user
    outpath=args.outpath
    target_temperature=args.temperature
    flag_temperature=args.wait
    
    print('AUTOMATED '+purpose.upper()+' STARTS...')
    if purpose.lower()=='pm':
        pm_main()
    elif purpose.lower()=='iqoq':
        iqoq_main()
    elif purpose.lower()=='fiqa':
        print('[WARNING] currently do not support automated FIQA, please contact CX.Jack for more information')
    else:
        print('[ERROR] no such a purpose')
        exit(0)
    
    if not result:
        print('QC failed')
        report.write('\n\nQC failed')
    else:
        print('QC passed')
        report.write('\n\nQC passed')
        
    report.write('\ntotal runtime: '+str(sum(runtime))+'s')
    report.close()
    
    # import NimSetup
    # NimYSetup.cleanup()
    
    
    
    