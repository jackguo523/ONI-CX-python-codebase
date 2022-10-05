# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 10:38:48 2022

@author: JackGuo
"""

import numpy as np
import skimage.io
import scipy.ndimage
import cv2
import os
from numba import cuda

# provide regitration methods for widefield/confocal
# consider using loops for batch processing

# ECC-based image registration, B->A
# for linear translation only
def ECC_align(A,B,sigma=3):
    warp_mode=cv2.MOTION_TRANSLATION # assume translation
    
    iterations=1000 # define the number of iterations
    eps=1e-6 # define the threshold of the increment in the correlation coefficient between two iterations
    
    criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,iterations,eps) # define the termination criteria
    
    # currently do not blur
    # blur_A=scipy.ndimage.filters.gaussian_filter(A,(2**5,2**5),mode='reflect')
    # blur_B=scipy.ndimage.filters.gaussian_filter(B,(2**5,2**5),mode='reflect')
    
    
    warp=np.eye(2,3,dtype=np.float32)
    (_,warp)=cv2.findTransformECC(A,B,warp,warp_mode,criteria,None,sigma)
    
    return warp

@cuda.jit
def mesh(w,h,fitX,fitY,x_mesh,y_mesh):
    tx=cuda.blockDim.x*cuda.blockIdx.x+cuda.threadIdx.x  # row
    ty=cuda.blockDim.y*cuda.blockIdx.y+cuda.threadIdx.y  # col
    
    if tx>=w or ty>=h:
        return # avoid segmentation fault

    x_mesh[ty,tx]=fitX[0]+fitX[1]*tx+fitX[2]*ty+fitX[3]*tx*ty+fitX[4]*tx*tx+fitX[5]*ty*ty
    y_mesh[ty,tx]=fitY[0]+fitY[1]*tx+fitY[2]*ty+fitY[3]*tx*ty+fitY[4]*tx*tx+fitY[5]*ty*ty
    
    cuda.syncthreads()
    
# read and apply ONI channel mapping calibration
# A=C0, B=C1, by default B->A
def ONI_align(A,B,nim,order=0,mode='cpu'):
    mapfile=open(nim)
    mapfile=mapfile.read() # read cmap.nim
    if order==0: # B->A
        forX=mapfile[mapfile.find('transToA'):mapfile.rfind('transToB')]
        forY=mapfile[mapfile.find('transToB'):mapfile.rfind('region')]  

    else: # A->B
        forX=mapfile[mapfile.find('transFromA'):mapfile.rfind('transFromB')]
        forY=mapfile[mapfile.find('transFromB'):mapfile.rfind('transToA')]
 
    import re
    fitX=[float(i) for i in re.findall('[-+]?\d+\.\d+[eE][-+]?\d+|[-+]?\d+\.\d+',forX)]
    fitY=[float(i) for i in re.findall('[-+]?\d+\.\d+[eE][-+]?\d+|[-+]?\d+\.\d+',forY)]
    w=A.shape[1] # read width and height
    h=A.shape[0]
    
    x_mesh=np.zeros((h,w),np.float32) # initiate mesh grids
    y_mesh=np.zeros((h,w),np.float32)
    if mode=='cpu': # use cpu
        for j in range(h):
            for i in range(w):
                x_mesh[j,i]=fitX[0]+fitX[1]*i+fitX[2]*j+fitX[3]*i*j+fitX[4]*i*i+fitX[5]*j*j # apply polynomial fitting
                y_mesh[j,i]=fitY[0]+fitY[1]*i+fitY[2]*j+fitY[3]*i*j+fitY[4]*i*i+fitY[5]*j*j
    else: # use gpu
        d_x_mesh=cuda.device_array((h,w),np.float32) # allocate mesh grids on gpu
        d_y_mesh=cuda.device_array((h,w),np.float32)
        d_fitX=cuda.to_device(fitX) # copy from host to device
        d_fitY=cuda.to_device(fitY)
        threadsperblock=(16,16) # 2d thread block
        blockspergrid_x=int(np.ceil(w/threadsperblock[0]))
        blockspergrid_y=int(np.ceil(h/threadsperblock[1]))
        blockspergrid=(blockspergrid_x,blockspergrid_y) # 2d block grid
        mesh[blockspergrid,threadsperblock](w,h,d_fitX,d_fitY,d_x_mesh,d_y_mesh) # run the kernel
        d_x_mesh.copy_to_host(x_mesh) # copy from device to host
        d_y_mesh.copy_to_host(y_mesh)
    
    if order==0: # B->A
        align_B=cv2.remap(B,x_mesh,y_mesh,interpolation=cv2.INTER_LINEAR) # note that intensity distribution can be slightly altered
        align_A=A
    else: # A->B
        align_B=B
        align_A=cv2.remap(A,x_mesh,y_mesh,interpolation=cv2.INTER_LINEAR)
        
    return align_A,align_B
        
              
raw=skimage.io.imread('C:/users/jack/desktop/test.tif')
# skimage.io.imsave('C:/users/jack/desktop/mtest.tif',raw)
# # raw=cv2.normalize(raw,None,.0,255,cv2.NORM_MINMAX,cv2.CV_8UC1)
C0=raw[:,:428] # crop
C0=C0.astype(np.float32)
skimage.io.imsave('C:/users/jack/desktop/C0.tif',C0)
C1=raw[:,428:]
C1=C1.astype(np.float32)
skimage.io.imsave('C:/users/jack/desktop/C1.tif',C1)
C0,C1=ONI_align(C0,C1,'C:/users/jack/desktop/test.nim',0,'gpu')
skimage.io.imsave('C:/users/jack/desktop/align_C1.tif',C1) 


    
                             