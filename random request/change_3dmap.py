# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 12:52:24 2022

@author: JACK
"""

# batch process for NYIT on the 3dmap issue

import os
import re

rootpath='C:/users/jack/desktop/test'

(_,rootfolders,_)=next(os.walk(rootpath)) # read all folders from the rootpath
tag='pos_0'

# function to modify the 3dmap.nim file
def modify_3dmap(path):
    print('process data: '+str(path))
    f=open(path,'r+')
    T=f.read()
    crop=T[T.find('          "h": 684'):T.rfind('\n        }\n      }\n    ]\n  },\n  "Format": 4')]
    T=T.replace(crop,'          "h": 684,\n          "w": 428,\n          "x": 0,\n          "y": 0\n        }\n      },\n      {\n        "region": {\n          "h": 684,\n          "w": 428,\n          "x": 428,\n          "y": 0')
    f.seek(0)
    f.write(T)
    f.truncate()
    f.close()

# main function
if __name__ == "__main__":
    print('start batch process...')
    
    for i in range(len(rootfolders)):
        print('\nprocess folder '+str(i+1)+'/'+str(len(rootfolders)))
        (_,outfolders,files)=next(os.walk(rootpath+'/'+rootfolders[i]))
        
        if len(outfolders)==0: # normal acquisition
            files=[n for n in files if '3dmap.nim' in n.lower()]
            for j in range(len(files)):
                abspath=rootpath+'/'+rootfolders[i]+'/'+files[j]
                modify_3dmap(abspath)
        else: # multi-acquisition
            for j in range(len(outfolders)):
                if outfolders[j]==tag:
                    (_,_,files)=next(os.walk(rootpath+'/'+rootfolders[i]+'/'+outfolders[j]))
                    files=[n for n in files if '3dmap.nim' in n.lower()]
                    for o in range(len(files)):
                        abspath=rootpath+'/'+rootfolders[i]+'/'+outfolders[j]+'/'+files[o]
                        modify_3dmap(abspath)
                else:
                    (_,infolder,_)=next(os.walk(rootpath+'/'+rootfolders[i]+'/'+outfolders[j]))
                    for k in range(len(infolder)):
                        if infolder[k]==tag:
                            (_,_,files)=next(os.walk(rootpath+'/'+rootfolders[i]+'/'+outfolders[j]+'/'+infolder[k]))
                            files=[i for i in files if '3dmap.nim' in i.lower()]
                            for l in range(len(files)):
                                abspath=rootpath+'/'+rootfolders[i]+'/'+outfolders[j]+'/'+infolder[k]+'/'+files[l]
                                modify_3dmap(abspath)
            
# for i in range(len(folders)):
#     (_,_,files)=next(os.walk(rootpath+'/'+folders[i]+'/pos_0'))
#     files=[i for i in files if 'map.nim' in i.lower()]
    
#     # read the correct value from 2dmap, but it should always be [428, 0]
#     # f=open(rootpath+'/'+folders[i]+'/pos_0/'+files[1],'r')
#     # GT=f.read()
#     # f.close()
#     # crop=GT[GT.rfind('region'):GT.rfind(',"temperatureCelsius')]
#     # crop=crop[crop.find('region'):]
#     # coordinates=re.findall('\d+',crop)
#     # xs=coordinates[2]
#     # ys=coordinates[3]
    
#     # modify the corresponding value from 3dmap
#     f=open(rootpath+'/'+folders[i]+'/pos_0/'+files[0],'r+')
#     T=f.read()
    
#     crop=T[T.find('          "h": 684'):T.rfind('\n        }\n      }\n    ]\n  },\n  "Format": 4')]
#     T=T.replace(crop,'          "h": 684,\n          "w": 428,\n          "x": 0,\n          "y": 0\n        }\n      },\n      {\n        "region": {\n          "h": 684,\n          "w": 428,\n          "x": 428,\n          "y": 0')
#     f.seek(0)
#     f.write(T)
#     f.truncate()
#     f.close()

print('\ndone batch processing...')