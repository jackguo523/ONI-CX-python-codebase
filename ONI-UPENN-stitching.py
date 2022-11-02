# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 10:49:18 2022

@author: JACK
"""

# wrote specifically for UPENN Ivan, snakeXY

import os
import tifffile
import numpy as np
import time
import glob

nrow=4 # set the number of rows
ncol=4 # set the number of columns
overlap=0.1 # set the overlap ratio
nchannel=4 # set the number of channels, which equals to the number of lasers times two
ntime=240 # set the number of time points
rootpath='D:/test' # set the root path, where all the pos_x files are stored
stack=True # if want to generate a stack

width=428 # fixed dimensions
height=684

if not os.path.exists(rootpath+'/result'):
    os.mkdir(rootpath+'/result')
for p in range(nchannel):
    if not os.path.exists(rootpath+'/result/C'+str(p)):
        os.mkdir(rootpath+'/result/C'+str(p))

_,folders,_=next(os.walk(rootpath))
folders=[i for i in folders if 'result' not in i.lower()]
folders.sort(key=lambda x: int(x[4:]))


if overlap!=0:
    M=[]
    xgrad=np.tile(np.linspace(1,0,int(width*overlap)),(height,1))
    ygrad=np.transpose(np.tile(np.linspace(1,0,int(height*overlap)),(width,1)))
    for i in range(nrow*ncol):
        mask=np.ones((height,width),np.float64)
        row=i//ncol
        col=i%ncol
        if row!=0: # except first row
            mask[-int(height*overlap):,:]=mask[-int(height*overlap):,:]*ygrad
        if row!=(nrow-1): # except last row
            mask[:int(height*overlap),:]=mask[:int(height*overlap),:]*(1-ygrad)
        if col!=0: # except first column
            mask[:,-int(width*overlap):]=mask[:,-int(width*overlap):]*xgrad
        if col!=(ncol-1): # except last column
            mask[:,:int(width*overlap)]=mask[:,:int(width*overlap)]*(1-xgrad)
        M.append(mask)
else:
    M=[np.ones((height,width),np.float64)]*nrow*ncol

start=time.time()
for i in range(ntime):
    for j in range(nchannel):
        fx=(ncol-1)*(width-int(width*overlap))+width
        fy=(nrow-1)*(height-int(height*overlap))+height
        # fx=ncol*width
        # fy=nrow*height
        mosaic=np.zeros((fy,fx),np.uint16)
        for k in range(nrow*ncol):
            _,_,files=next(os.walk(rootpath+'/'+folders[k]))
            file=[f for f in files if 't'+str(i)+'_posZ0.tif' in f]
            im=tifffile.imread(rootpath+'/'+folders[k]+'/'+file[0])
            if j%2==0:
                im=im[j//2,:,:width]
            else:
                im=im[j//2,:,width:]
            # file=[i for i in files if '0C.tif' in i]
            # im=tifffile.imread(rootpath+'/'+folders[k]+'/'+file[0])[i,j,:,:]
            mosaic[fy-((k//ncol))*(height-int(height*overlap))-height:fy-((k//ncol))*(height-int(height*overlap)),fx-((k%ncol))*(width-int(width*overlap))-width:fx-((k%ncol))*(width-int(width*overlap))]= \
                mosaic[fy-((k//ncol))*(height-int(height*overlap))-height:fy-((k//ncol))*(height-int(height*overlap)),fx-((k%ncol))*(width-int(width*overlap))-width:fx-((k%ncol))*(width-int(width*overlap))]+ \
                    im*M[k]
        tifffile.imsave(rootpath+'/result/C'+str(j)+'/t{:03d}'.format(i)+'.tif',mosaic)
            
end=time.time()
duration=end-start
print('stitch runtime: '+str(duration)+'s')

if stack==True:
    start=time.time()
    for c in range(nchannel):
        ims=glob.glob(rootpath+'/result/C'+str(c)+'/*.tif')
        with tifffile.TiffWriter(rootpath+'/result/C'+str(c)+'.tif') as stack: 
            for filename in ims: 
                stack.save(tifffile.imread(filename))
    end=time.time()
    duration=end-start
    print('stack runtime: '+str(duration)+'s')
    