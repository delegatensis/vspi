# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 10:17:42 2020

@author: galem
"""

from sentinelhub import WcsRequest, MimeType, CRS, BBox
import datetime
import os
import gdal
from matplotlib import pyplot as plt
import numpy as np
import rasterio as rio


i_id='5dd07e12-0bb5-4308-a509-792f573dd329'

#copy and paste bucket:
t_left=[-32.903588, 150.300881]
b_right=[-33.372116, 150.808262]

#coords in format: [lon upper left, lat upper left, lon lower right, lat lower right] WGS84
coords=[t_left[1], t_left[0], b_right[1], b_right[0]]
bbox_1=BBox(bbox=coords, crs=CRS.WGS84)
#define max cloud cover:
cloud_cover=0.2

#date format for wms request: 'yyyy-mm_dd'
fire_start=datetime.date(2019, 10, 1)
fire_end=datetime.date(2020, 1, 1)
#intervals: 60 days prior to fire start, fire end : today
#^^^^^^^^change with time since fire events^^^^^^^^^^
pre_int=datetime.timedelta(days=60)
pre_start=fire_start-pre_int
pre_end=fire_start
#print(pre_start)
post_start=fire_end
post_end=datetime.date.today()
#print(post_end)

intervals=['pre-fire', 'post-fire']
site_name='Wollemi'
path_dir='C:\\UserData\\galem\\PhD\\vspi\\data'

for p in range(0, len(intervals)):
     t=intervals[p] 
     save_dir=path_dir+'\\'+site_name+'\\'+t    
     if os.path.isdir(save_dir)==False:
         os.mkdir(save_dir)
     if t=='pre-fire':
         t_start=pre_start
         t_end=pre_end
     else:
         t_start=post_start
         t_end=post_end
     wms_pre = WcsRequest(data_folder=save_dir,
                  layer='VSPI',
                  bbox=bbox_1,
                  time=(t_start, t_end),
                  resx='60m', resy='60m',
                  image_format=MimeType.TIFF,
                  maxcc=cloud_cover,
                  instance_id=i_id)

     print('Downloading '+t+' data.....')                      
     wms_pre.save_data()

#save BA bands
for p in range(0, len(intervals)):
     t=intervals[p]
     ba_save_dir=path_dir+'\\'+site_name+'\\ba\\'
     if os.path.isdir(ba_save_dir)==False:
         os.mkdir(ba_save_dir)
     if os.path.isdir(ba_save_dir+t)==False:
         os.mkdir(ba_save_dir+t)
     if t=='pre-fire':
         t_start=pre_start
         t_end=pre_end
     else:
         t_start=post_start
         t_end=post_end    
     wms_ba = WcsRequest(data_folder=ba_save_dir+t,
                layer='BA_COMPOSITE',
                bbox=bbox_1,
                time=(t_start, t_end),
                resx='60m', resy='60m',
                image_format=MimeType.TIFF,
                maxcc=cloud_cover,
                instance_id=i_id)
   
     print('Downloading '+t+' BA classification data.....')            
     wms_ba.save_data()
         

#-------------------------------------

fns=os.listdir(save_dir)

img=gdal.Open(save_dir+'\\'+fns[0])      
print(str(img.RasterCount)+' bands') 
img2=np.array(img.GetRasterBand(12).ReadAsArray())             

plt.imshow(img2)

#B11 and B12 bands of interest -- ordered at [12] and [13]

#-------------------------------------

#Project and extract b11 and b12 bands

folds=['pre-fire', 'post-fire']

for p in range(0, len(folds)):
    time=folds[p]
    save_dir2=path_dir+'\\'+site_name+'\\'+time   
    fns=os.listdir(save_dir2)
    proj_dir=path_dir+'\\'+site_name+'\\projected\\'+time 
    if os.path.isdir(path_dir+'\\'+site_name+'\\projected\\')==False:
        os.mkdir(path_dir+'\\'+site_name+'\\projected\\')
    if os.path.isdir(proj_dir)==False:
        os.mkdir(proj_dir)
    #project to zone 56 gda94 EPSG:28356
    print('Projecting rasters: '+time, end='')
    for pprj in range(0, len(fns)):
        fn=fns[pprj]
        infile=save_dir2+'\\'+fn
        outfile=proj_dir+'\\GDA94_Z56_'+fn[4:]
        gdal.Warp(outfile, infile, dstSRS='EPSG:28356')
        print('.', end='')       
    #keep most recent three files
    fns=os.listdir(proj_dir)
    for f in [1, 2, 3]:
        fn=fns[len(fns)-f]
        img=gdal.Open(proj_dir+'\\'+fn)
        #nbands=img.RasterCount
        img_b11=np.array(img.GetRasterBand(1).ReadAsArray())
        img_b12=np.array(img.GetRasterBand(2).ReadAsArray())
        if os.path.isdir(path_dir+'\\'+site_name+'\\vspi_bands')==False:
            os.mkdir(path_dir+'\\'+site_name+'\\vspi_bands')
        b_outs=path_dir+'\\'+site_name+'\\vspi_bands\\'+time
        if os.path.isdir(b_outs)==False:
            os.mkdir(b_outs)
        #info=gdal.Info(img)
        for b in [11, 12]:
            if b==11:
                img_b=img_b11
            else:
                img_b=img_b12
            b_outpath=b_outs+'\\b_'+str(b)
            if os.path.isdir(b_outpath)==False:
                os.mkdir(b_outpath)
            with rio.open(proj_dir+'\\'+fn) as src:
                data_ras=src.read()
                meta=src.profile
            meta
            transform=meta["transform"]
            crs=meta["crs"]
            transform, crs
            meta['dtype']="uint16"
            meta['count']=1
            with rio.open(b_outpath+'\\'+fn[:-5]+'_B'+str(b)+'.tif', 'w', **meta) as dst:
                dst.write(img_b, 1)

#BA composites:
bats=['post-fire', 'pre-fire']
ba_dir=path_dir+'\\'+site_name+'\\ba'
ba_outdir=path_dir+'\\'+site_name+'\\ba_projected'
if os.path.isdir(ba_outdir)==False:
    os.mkdir(ba_outdir)
for bat in range(0, len(bats)):
    ba_indir=ba_dir+'\\'+bats[bat]
    fns=os.listdir(ba_indir)
    ba_outpath=ba_outdir+'\\'+bats[bat]
    if os.path.isdir(ba_outpath)==False:
        os.mkdir(ba_outpath)
    print('Projecting rasters: BA', end='')
    for pprj in range(0, len(fns)):
        fn=fns[pprj]
        infile=ba_indir+'\\'+fn
        outfile=ba_outpath+'\\GDA94_Z56_'+fn[4:]
        gdal.Warp(outfile, infile, dstSRS='EPSG:28356')
        print('.', end='')       
    




