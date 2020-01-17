# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 13:32:13 2020

@author: galem
"""

import os
from matplotlib import pyplot
import numpy as np
import georasters as gs
import gdal

sitename='Wollemi'

datadir='C:\\UserData\\galem\\PhD\\vspi\\data\\'+sitename+'\\vspi_bands'

#create file lists, using B11 (assuming naming coventions are same between B11/B12)
pre_list_b11=[]
for file in os.listdir(datadir+'\\pre-fire\\b_11\\'):
    pre_list_b11.append(file)
        
pre_list_b12=[]
for file in os.listdir(datadir+'\\pre-fire\\b_12\\'):
    pre_list_b12.append(file)

post_list_b11=[]
for file in os.listdir(datadir+'\\post-fire\\b_11'):
    post_list_b11.append(file)   
    
post_list_b12=[]
for file in os.listdir(datadir+'\\post-fire\\b_12'):
    post_list_b12.append(file)
    
for_mask_i='C:\\UserData\\galem\\PhD\\vspi\\data\\Wollemi\\s5hgps_60m_P2.tif'
#first re-project
# outfile="C:\\UserData\\galem\\PhD\\vspi\\data\\misc\\s5hgps_60m_P.tif"
# gdal.Warp(outfile, for_mask_i, dstSRS='EPSG:28356')
ba_mask_i="C:\\UserData\\galem\\PhD\\vspi\\data\\Wollemi\\ba_wollemi2.tif"

print("Aligning BA and s5 rasters...")
(for_mask, tod, GeoT_a)=gs.align_rasters(for_mask_i, (datadir+'\\pre-fire\\b_11\\'+pre_list_b11[0]), how=np.mean)
(ba_mask, tod2, GeoT_a)=gs.align_rasters(ba_mask_i, (datadir+'\\pre-fire\\b_11\\'+pre_list_b11[0]), how=np.mean)

# os.path.isfile(datadir+'\\pre-fire\\b_11\\'+pre_list_b11[0])
# os.path.isfile(for_mask_i)

bands=["b_11", "b_12"]
        
"""
Align rasters and mask reflectances by forest == yes and burnt area == yes.

"""
       
#for time being use the first pre-fire raster/
#should add functionality for rasters of a pre-fire time period
fi=0
ref_b11_i=datadir+"\\pre-fire\\"+str(bands[0])+"\\"+pre_list_b11[fi]
ref_b12_i=datadir+"\\pre-fire\\"+str(bands[1])+"\\"+pre_list_b12[fi]
#align forest mask to sample sen2
if os.path.isfile(ref_b11_i) and os.path.exists(ref_b12_i) and os.path.exists(for_mask_i) and os.path.exists(ba_mask_i):
    #should be aligned, but just in case:
    (ref_b11, ref_b12, GeoT_a)=gs.align_rasters(ref_b11_i, ref_b12_i, how=np.mean)
    if ba_mask.shape!=for_mask.shape or ba_mask.shape!=ref_b11.shape or ref_b11.shape!=ref_b12.shape:
        print("Error: input rasters of unequal dimensions")
    else:
        #raster calc the masks to have masked b11 and b12 reflectances
        ref_m12=np.empty(ref_b11.shape, dtype=float)
        ref_m11=np.empty(ref_b11.shape, dtype=float)
        print("Masking B11 / B12 reflectance rasters...")
        percent=-1
        # x=cols, y=rows
        for x in range(0, ref_m11.shape[1]):
            for y in range(0, ref_m11.shape[0]):
                #assuming BA is represented by 1
                if ba_mask[y, x]==1 and for_mask[y, x]==1 and ref_b11[y, x]!=0 and ref_b12[y, x]!=0:
                    ref_m11[y, x]=ref_b11[y, x]
                    ref_m12[y, x]=ref_b12[y, x]
                else:
                    ref_m11[y, x]=np.nan
                    ref_m12[y, x]=np.nan
                    count=percent
                    percent=int((x/ref_m11.shape[1])*100)
                    if count!=percent and count%5==0:
                            print((str(percent))+"% ",end='')
                                
#pyplot.imshow(ref_m11)
#pyplot.imshow(ref_m12)     
                                
"""
Derive pre-fire veg line

"""

pair_list=np.empty(shape=(0,2))
percent=-1
#first pre-fire file for now...
#for i in range(0, len(pre_list)):
    #create pair table
i=0
for x in range(0, ref_m11.shape[1]):
    for y in range(0, ref_m12.shape[0]):
        #NaN is represented by np.nan
        b11_val=ref_m11[y, x]
        b12_val=ref_m12[y, x]
        vals=[b11_val, b12_val]
        #check for NaN:
        if ~np.isnan(b11_val) and ~np.isnan(b12_val):
            pair_list=np.append(pair_list, np.array([[b11_val,b12_val]]), axis=0)
            count=percent
            percent=int((x/ref_m11.shape[1])*100)
            if count!=percent:
                print("Scene "+(str(i+1))+" of "+(str(len(pre_list_b11)))+". Complete: "+(str(percent))+"%")
                

fig=pyplot.figure()
ax=fig.add_subplot(1,1,1)
xaxis=pair_list[:,0]
yaxis=pair_list[:,1]
ax.scatter(xaxis, yaxis)
pyplot.show()

#find equation of line, using basic linear regression
#x should be b11, y should be b12
x=pair_list[:, 0]
y=pair_list[:, 1]
m = (len(x) * np.sum(x*y) - np.sum(x) * np.sum(y)) / (len(x)*np.sum(x*x) - np.sum(x) ** 2)
b = (np.sum(y) - m *np.sum(x)) / len(x)
print("Veg line equation: y = "+str(m)+"x + "+str(b))

#check above - remove first and last 5th percentiles of data?

"""
Calculate VSPI for post-fire scene

"""

#align post-fire scenes to pre-fire scene
pb11=os.listdir(datadir+'\\post-fire\\b_11\\')
pb12=os.listdir(datadir+'\\post-fire\\b_12\\')
post_b11_i=datadir+'\\post-fire\\b_11\\'+pb11[1]
post_b12_i=datadir+'\\post-fire\\b_12\\'+pb12[1]
(ref_b11, post_b11, GeoT_a)=gs.align_rasters(ref_b11_i, post_b11_i, how=np.mean)
(ref_b11, post_b12, GeoT_a)=gs.align_rasters(ref_b11_i, post_b12_i, how=np.mean)
if post_b11.shape!=post_b12.shape:
   print("Error: post-fire input rasters of unequal dimensions")
else:
    #apply masks
    post_m12=np.empty(post_b11.shape, dtype=float)
    post_m11=np.empty(post_b11.shape, dtype=float)
    percent=-1
    print("Masking B11 / B12 post-fire reflectance rasters...")
    for x in range(0, post_m11.shape[1]):
        for y in range(0, post_m11.shape[0]):
            if ba_mask[y, x]==1 and for_mask[y, x]==1 and ref_b11[y, x]!=0 and ref_b12[y, x]!=0:
                post_m11[y, x]=post_b11[y, x]
                post_m12[y, x]=post_b12[y, x]
            else:
                post_m11[y, x]=np.nan
                post_m12[y, x]=np.nan
                count=percent
                percent=int((x/post_m11.shape[1])*100)
                if count!=percent and count%5==0:
                    print((str(percent))+"% ",end='')
#pyplot.close()
#pyplot.imshow(post_m11)
#pyplot.imshow(post_m12)  
                    
#create new vspi grid
vspi=np.empty(post_b11.shape, dtype=float) 
percent=-1
print("Calculating VSPI...")
for x in range(0, vspi.shape[1]):
    for y in range(0, vspi.shape[0]):        
        if ~np.isnan(post_m11[y, x]) and ~np.isnan(post_m12[y, x]):
            #NaN is represented by np.nan
            post_b11_val=post_m11[y, x]
            post_b12_val=post_b12[y, x]
            #yA is b12 ref, xA is b11 ref
            vspi_val=(1/(np.sqrt((m**2)+1)))*(post_b12_val-(m*post_b11_val)-b)
            vspi[y, x]=vspi_val
        else:
            vspi[y, x]=np.nan
        count=percent
        percent=int((x/post_m11.shape[1])*100)
        if count!=percent:
            print((str(percent))+"% ", end='')
            
#pyplot.imshow(vspi)
            
"""
Export to geotiff

"""
        
import rasterio as rio

with rio.open(datadir+'\\post-fire\\b_11\\'+pb11[1]) as src:
    naip_data_ras=src.read()
    naip_meta=src.profile
    
naip_meta
naip_transform=naip_meta["transform"]
naip_crs=naip_meta["crs"]
naip_transform, naip_crs
naip_meta['dtype']="float64"

vspi_out='C:\\UserData\\galem\\PhD\\vspi\data\\'+sitename+'\\outputs'
if os.path.isdir(vspi_out)==False:
    os.mkdir(vspi_out)
    
with rio.open(vspi_out+'\\VSPI_'+sitename+'.tiff', "w", **naip_meta) as dst:
    dst.write(vspi, 1)










