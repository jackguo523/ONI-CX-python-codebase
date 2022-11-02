# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 07:59:34 2022

@author: JACK
"""

import argparse
import os
import time
import pandas as pd
import numpy as np


# def from_oni(filename,quiet=False): # read oni csv
#     f=open(filename)
#     data=np.genfromtxt(f,delimiter=',',names=True)
#     if not quiet:
#         print('\n    data read from {}'.format(f.name))
#     return data

# def to_thunderstorm(data,filename,quiet=False): # write thunderstorm csv from oni csv
#     if 'X_pix' not in data.dtype.names:
#         raise ValueError('colum X_pix not found in current csv file '
#                          'please check export options in NimOS Settings>UserSettings>EXPORT OPTIONS>Positions (pixels)')
    
#     thunderstorm_names=('x','y','frame','sigma','intensity','background') # thunderstorm label
#     oni_names=('X_pix','Y_pix','Frame','sigma','Photons','Background') # oni label
    
#     if 'PSF_Sigma_X_pix' in data.dtype.names and 'PSF_Sigma_Y_pix' in data.dtype.names:
#         descr=[('sigma',float)] # append a new class 'sigma'
#         tmp=np.empty(data.shape,dtype=data.dtype.descr+descr)
#         for name in data.dtype.names:
#             tmp[name]=data[name] # copy all necessary data
#         data=tmp # overwrite
#         data['sigma']=(data['PSF_Sigma_X_pix']+data['PSF_Sigma_Y_pix'])/2 # average the sigma along XY
        
#         f=open(filename,'w')
#         f.write(','.join(thunderstorm_names)+'\n') # write labels
#         result=[]
#         for name, oni_name in zip(thunderstorm_names,oni_names):
#             result.append(data[oni_name])
            
#         np.savetxt(f,np.column_stack(result),'%s',',') #save to csv
#         f.close()
        
#         if not quiet:
#             print('\n    data saved to {}'.format(f.name))


def single_filter(infile,outfile,keyword,threshold,rule='higher'): # rule can be 'higher' or 'lower'
    print('Start!')
    f=open(infile)
    df=pd.read_csv(f,delimiter=',')
    sub_df=[c for c in df.columns if keyword in c]
    for i in range(len(sub_df)):
        if rule=='higher': # filter out larger values
            df=df[df[sub_df[i]]<=threshold]
        else: # filter out smaller values
            df=df[df[sub_df[i]]>=threshold]
    df.to_csv(outfile,index=False)
    print('Done!')

def batch_filter(inpath,keyword,threshold,rule='higher'):
    print('Start batch filtering based on keyword '+keyword+'!')
    _,_,files=next(os.walk(inpath))
    files=[i for i in files if 'f_' not in i.lower()] # remove previous filtering results
    paths=[inpath+'/'+i for i in files]
    # print(paths)
    for f in range(len(paths)):
        file=open(paths[f])
        df=pd.read_csv(file,delimiter=',')
        sub_df=[c for c in df.columns if keyword in c]
        for i in range(len(sub_df)):
            if rule=='higher': # filter out larger values
                df=df[df[sub_df[i]]<=threshold]
            else: # filter out smaller values
                df=df[df[sub_df[i]]>=threshold]
        df.to_csv(inpath+'/f_'+files[f],index=False)
    print('Done batch filtering based on keyword '+keyword+'!')

def check(df):
    if 'X (pix)' not in df.dtypes:
        raise ValueError('Colume X (pix) or Y (pix) not found in current CSV, '
                          'please check the export options in NimOS Settings>User Settings>Export Options>Positions (pixels)')
    if 'PSF Sigma X (pix)' not in df.dtypes:
        raise ValueError('Colume PSF Sigma X (pix) or PSF Sigma Y (pix) not found in current CSV, '
                          'please check the export options in NimOS Settings>User Settings>Export Options>PSF sigmas')
    if 'X (nm)' not in df.dtypes:
        raise ValueError('Colume X (nm) or Y (nm) not found in current CSV, '
                          'please check the export options in NimOS Settings>User Settings>Export Options>Positions (nm)')
        
            
def convert_chunk(filename,output,dlist,total,copy=False,pixel=False,chunk=10000000,quiet=False,drop=None,split=False):
    f=open(filename)
    count=0 # initial iterator
    channel=[0,0,0,0,0,0] # initial flag for channel header
    psize=0 # initial pixel size
    if not quiet: # print process
        print('\n        dataframe read from {}'.format(f.name))
        
    for c in pd.read_csv(f,delimiter=',',chunksize=chunk):
        check(c) # check data for validation
        if not quiet: # print process
            print('\n        processing chunk #'+str(count+1)+'/'+str(total)) 
        
        if not copy: # drop some columns to compress
            for i in dlist:
                c=c.drop(columns=i,errors='ignore')
                
        if count==0:
            psize=c.at[0,'X (nm)']/c.at[0,'X (pix)'] # calculate the pixel size in nanometer
            
        if drop!=None: # drop channel
            c=c.drop(c[(c['Channel']==drop)].index,errors='ignore')
            
        c=c.rename(columns={'Channel':'channel','Frame':'frame','Photons':'intensity [photon]','Background':'background [photon]'})
        if not pixel: # diplay in nanometers
            c['sigma [nm]']=(c['PSF Sigma X (pix)']+c['PSF Sigma Y (pix)'])/2*psize # average sigmas along XY 
            c=c.rename(columns={'X (nm)':'x [nm]','Y (nm)':'y [nm]','Z (nm)':'z [nm]','X precision (nm)':'x precision [nm]','Y precision (nm)':'y precision [nm]'},errors='ignore')
            c=c.drop(columns=['X (pix)','Y (pix)','Z (pix)','X precision (pix)','Y precision (pix)','PSF Sigma X (pix)','PSF Sigma Y (pix)'],errors='ignore')
        else:
            c['sigma [px]']=(c['PSF Sigma X (pix)']+c['PSF Sigma Y (pix)'])/2 # average sigmas along XY
            c=c.rename(columns={'X (pix)':'x [px]','Y (pix)':'y [px]','Z (pix)':'z [px]','X precision (pix)':'x precision [px]','Y precision (pix)':'y precision [px]','PSF Sigma X (pix)':'sigma x [px]','PSF Sigma Y (pix)':'sigma y [px]'},errors='ignore')
            c=c.drop(columns=['X (nm)','Y (nm)','Z (nm)','X precision (nm)','Y precision (nm)'],errors='ignore')
        
        if not split: # merge channels
            if count==0: # first time, write with header
                c.to_csv(output,index=False)
            else: # append without header
                c.to_csv(output,index=False,mode='a',header=False)
        else: # split channels
            clist=(c[~c.duplicated('channel')])['channel'].values # get channel list
            group=c.groupby(c['channel'])
            for i in range(len(clist)):
                if channel[clist[i]]==0: # first time, write with header
                    tmp=group.get_group(clist[i]) # get channel information from data
                    tmp.to_csv(output[:output.index('thunderstorm')]+'C'+str(clist[i])+'_'+output[output.index('thunderstorm'):],index=False)
                    channel[clist[i]]=1
                else: # append without header
                    tmp=group.get_group(clist[i]) # get channel information from data
                    tmp.to_csv(output[:output.index('thunderstorm')]+'C'+str(clist[i])+'_'+output[output.index('thunderstorm'):],index=False,mode='a',header=False)
        count=count+1
        
    f.close()
    if not quiet:
        print('\n        dataframe saved to {}'.format(f.name))
    
    
def convert_bulk(filename,output,dlist,copy=False,pixel=False,quiet=False,drop=None,split=False):
    f=open(filename)
    df=pd.read_csv(f,delimiter=',') # read CSV as DataFrame
    f.close()
    check(df) # check data for validation
        
    if not quiet: # print process
        print('\n        dataframe read from {}'.format(f.name))
        
    if not copy: # drop some columns to compress
        for i in dlist:
            df=df.drop(columns=i,errors='ignore')
    
    psize=df.at[0,'X (nm)']/df.at[0,'X (pix)'] # calculate the pixel size in nanometer
    
    if drop!=None: # drop channel
        df=df.drop(df[(df['Channel']==drop)].index,errors='ignore')
    
    df=df.rename(columns={'Channel':'channel','Frame':'frame','Photons':'intensity [photon]','Background':'background [photon]'})
    if not pixel: # diplay in nanometers
        df['sigma [nm]']=(df['PSF Sigma X (pix)']+df['PSF Sigma Y (pix)'])/2*psize # average sigmas along XY 
        df=df.rename(columns={'X (nm)':'x [nm]','Y (nm)':'y [nm]','Z (nm)':'z [nm]','X precision (nm)':'x precision [nm]','Y precision (nm)':'y precision [nm]'},errors='ignore')
        df=df.drop(columns=['X (pix)','Y (pix)','Z (pix)','X precision (pix)','Y precision (pix)','PSF Sigma X (pix)','PSF Sigma Y (pix)'],errors='ignore')
    else:
        df['sigma [px]']=(df['PSF Sigma X (pix)']+df['PSF Sigma Y (pix)'])/2 # average sigmas along XY
        df=df.rename(columns={'X (pix)':'x [px]','Y (pix)':'y [px]','Z (pix)':'z [px]','X precision (pix)':'x precision [px]','Y precision (pix)':'y precision [px]','PSF Sigma X (pix)':'sigma x [px]','PSF Sigma Y (pix)':'sigma y [px]'},errors='ignore')
        df=df.drop(columns=['X (nm)','Y (nm)','Z (nm)','X precision (nm)','Y precision (nm)'],errors='ignore')
    
    if not split: # merge channels
        df.to_csv(output,index=False)
    else: # split channels
        clist=(df[~df.duplicated('channel')])['channel'].values # get channel list
        group=df.groupby(df['channel'])
        for i in range(len(clist)):
            tmp=group.get_group(clist[i]) # get channel information from data
            tmp.to_csv(output[:output.index('thunderstorm')]+'C'+str(clist[i])+'_'+output[output.index('thunderstorm'):],index=False)
    
    if not quiet:
        print('\n        dataframe saved to {}'.format(f.name))
    


if __name__=="__main__":
    parser=argparse.ArgumentParser(description='ONI to ThunderSTORM batch processing')
    parser.add_argument('--filepath',metavar='C:/Users/...',help='absolute input root directory')
    parser.add_argument('--output',default='result',metavar='folder',help='output folder')
    parser.add_argument('--memory',default=2,help='memory limit to bulk process')
    parser.add_argument('--chunk',default=10000000,help='processing chunk size, default to 10000000')
    parser.add_argument('--full',action='store_true',help='flag for exporting full data without compression')
    parser.add_argument('--pixel',action='store_true',help='use pixels for display rather than nanometers')
    parser.add_argument('--quiet',action='store_true',help='flag for console printing')
    parser.add_argument('--filter',type=int,metavar='[1,4]',help='filter out channel')
    parser.add_argument('--channel',action='store_true',help='flag for splitting channels')
    
    args=parser.parse_args()
          
    indir=args.filepath # input diretory
    if indir==None: # if no folder specified
        raise ValueError('No input folder specified, '
                         'please add the corresponding argument --filepath')
    outdir=args.output # output folder
    m=args.memory # memory limit
    b=args.chunk # stream chunk size
    q=args.quiet # default to False: print the progress
    c=args.full # default to False: drop some "unnessary" columns from CSV to compress, including [raw, sigma var, CRLB intensity, CRLB background, p-value]
    dlist=('X raw (pix)','Y raw (pix)','Z raw (pix)','Sigma X var','Sigma Y var','CRLB Intensity','CRLB Background','p-value','Z out of range flag')
    p=args.pixel # default to False: represent in nanometers
    d=args.filter # drop channel
    s=args.channel # split channel
    
    (_,_,files)=next(os.walk(indir)) # scan all included files
    csv=[i for i in files if '.csv' in i.lower()] # get all included csvs
    numF=len(csv) # get number of CSV
    print(str(numF)+' CSV found')
    
    outdir = indir+'/'+outdir
    if not os.path.exists(outdir): # create output folder if not exist
        os.mkdir(outdir)
    
    print('\nStart Batch Processing:')
    start=time.time()
    
    for i in range(numF): # start batch process
        f=indir+'/'+csv[i] # update absolute path
        o=outdir+'/thunderstorm_'+csv[i] # create output csv name
        
        size=os.path.getsize(f)/1024/1024/1024 # read CSV size in GB
        if size>=m: # convert in chunks
            print('\n    processing CSV #'+str(i+1)+'/'+str(numF)+' in chunks:')
            convert_chunk(f,o,dlist,int(np.ceil(s/m)),c,p,b,q,d,s)
        else: # convert in bulk
            print('\n    processing CSV #'+str(i+1)+'/'+str(numF)+' in bulk:')
            convert_bulk(f,o,dlist,c,p,q,d,s)
        
    end=time.time()
    print('\nEnd Batch Processing')
    print('\nTime to process: '+str(round(end-start,3))+'s\n')