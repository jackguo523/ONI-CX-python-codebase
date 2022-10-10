# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 07:44:18 2022

@author: JACK
"""

import time
import numpy as np

def read_camera(c=0):
    time.sleep(0.3)
    im=camera.GetLatestImage()
    p=im.Channel(c).Pixels
    h=im.Channel(c).Dims.Height
    w=im.Channel(c).Dims.Width
    
    return np.array(p).reshape((h,w))

def read_focus_camera():
    time.sleep(0.3)
    raw=focus_cam.GetLatestImage()
    im=nim_image_to_array(raw)
    
    return im

def _var(im):
    return im.std()**2


def coarse_focus(start=100,limit=800,step=1,patience=3,eps=1):
    light.GlobalOnState=True
    light[5].Enabled=True
    camera.BeginView()
    
    move=int(limit/step)
    stage.RequestMoveAbsolute(stage.Axis.Z,start)
    while stage.IsMoving(stage.Axis.Z):
        time.sleep(0.01)
    origin=stage.GetPositionInMicrons(stage.Axis.Z)
    stop_point=0
    pcount=0
    V=[0]*patience
    
    prev=0
    curv=0
    for i in range(move):
        stage.RequestMoveAbsolute(stage.Axis.Z,origin-i*step)
        while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
        
        im=read_focus_camera()
        curv=_var(im)
        if curv<prev-eps:
            if pcount<patience:
                V[pcount]=curv
                pcount=pcount+1
            else:
                stop_point=origin-(i-patience-1)*step
                # print('found coarse focus at '+str(stop_point)+'um')
                return stop_point
        else:
            pcount=0
        #print('the current index = '+str(i)+', the current v = '+str(curv)+', the previous v = '+str(prev))
        prev=curv
        
def fine_focus(focus,limit=20,step=0.1,channel=0,laser=30):
    light.GlobalOnState=True
    light[2].Enabled=True
    light[2].PercentPower=laser
    # light[5].Enabled=True
    camera.BeginView()
    
    origin=focus+limit/2
    move=int(limit/step)
    
    stage.RequestMoveAbsolute(stage.Axis.Z,origin)
    while stage.IsMoving(stage.Axis.Z):
        time.sleep(0.01)

    V=[]
    for i in range(100):
        stage.RequestMoveAbsolute(stage.Axis.Z,origin-i*step)
        while stage.IsMoving(stage.Axis.Z):
            time.sleep(0.01)
        im=read_camera(channel)
        V.append(_var(im))
    
    idx=V.index(max(V))
    focus=origin-idx*step
    print('focus found at '+str(focus)+'um')
    
    stage.RequestMoveAbsolute(stage.Axis.Z,focus)
    light[2].Enabled=False
    
    
def channel_mapping(l1=2,l2=3,p1=30,p2=20,count=5,fov=20,point=2000,distance=5.0,radius=10.0,optimal=True):
    light.GlobalOnState=True
    light[l1].Enabled=True
    light[l2].Enabled=True
    light[l1].PercentPower=p1
    light[l2].PercentPower=p2
    camera.BeginView()
    
    result=False
    for i in range(count):
        calibration.ChannelMapping.BeginCalibration(fov,point,distance,radius,False)
        pixel_size=calibration.ChannelMapping.GetLatestMapping().pixelSize_um
        std_pixel=calibration.ChannelMapping.GetLatestMapping().stDevSingleAxisAbsoluteErrors
        std=std_pixel*pixel_size
        coverage=calibration.ChannelMapping.GetLatestMapping().proportionCoverage
        if std < 0.02 and coverage==1.0:
            print('channel mapping calibrated with standard deviation of errors = '+str(std*1000)+'nm')
            calibration.ChannelMapping.SaveLatestCalibration()
            result=True
            break
    if not result:
        print('channel mapping calibration failed')
    
    light[l1].Enabled=False
    light[l2].Enabled=False
            

def auto_tirf(channel=0,l=2,p=30,start=45,end=57,step=0.5):
    light.GlobalOnState=True
    light[l].Enabled=True
    light[l].PercentPower=p
    camera.BeginView()
    
    time.sleep(5)
    
    V=[]
    for i in np.arange(start,end,step):
       	illum_angle.RequestMoveAbsolute(i)
       	time.sleep(1)
        im=read_camera(channel)
        V.append(_var(im))
    
    angle=start+np.argmax(V)*step
    illum_angle.RequestMoveAbsolute(angle)
    print('TIRF angle found at '+str(angle)+'-degrees')
    
    light[l].Enabled=False

start=time.time()
autofocus.ClearReferencePoint()
p=coarse_focus()
fine_focus(p)
autofocus.StartReferenceCalibration()
while autofocus.CurrentStatus == autofocus.Status.CALIBRATING:
    time.sleep(1)
autofocus.StartContinuousAutoFocus()
end=time.time()
print('autofocus runtime: '+str(end-start)+'s')

start=time.time()
channel_mapping()
end=time.time()
print('channel mapping calibration runtime: '+str(end-start)+'s')


start=time.time()
auto_tirf()
end=time.time()
print('auto-TIRF runtime: '+str(end-start)+'s')
