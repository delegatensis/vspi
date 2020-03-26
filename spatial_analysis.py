# -*- coding: utf-8 -*-
"""
Created on Mon Jan 13 10:39:39 2020

@author: galem
"""

"""
Further things to consider:
    - Integration of LFMC into analysis
    - Stratification of forest type
    - FFDI and weather variables
    - Time since fire from NPWS
    - Modelled DFMC
    - Fine-scale rainfall using ANUCLIM
    
"""

import gdal
import numpy as np
import rasterio
from scipy.io import netcdf
from netCDF4 import Dataset
import georasters as gs
import julian
import datetime

#test change

"""
Spatial analysis of fire severity as function of:
    - Fuel load indicators from LiDAR
    - Aspect, slope, elevation, topogrtaphic wetness

First, create datatable from pixels, for linear mixed-effects modelling in R.
Mask by forest==yes, burnt==yes.

"""

#import and align datasets
sitename='Wollemi'
lid_dir='C:\\UserData\\galem\\PhD\\vspi\\lidar_maps\\wollemi_maps_tif'
sev_dir='C:\\UserData\\galem\\PhD\\vspi\\data\\Wollemi\\outputs'
tsf_dir='C:\\UserData\\galem\\PhD\\vspi\\data\\Wollemi\\tsf\\FireHistory.tif'
twi_dir='C:\\UserData\\galem\\PhD\\vspi\\data\\Wollemi\\dem\\TWI.tif'
topos_dir='C:\\UserData\\galem\\PhD\\vspi\\data\\Wollemi\\dem\\TOPOS.tif'


fire_date=datetime.datetime(2019, 11, 1, 1)
j_date=julian.to_jd(fire_date)


dem_dir='C:\\UserData\\galem\\PhD\\vspi\\data\\Wollemi\\dem'
#first load DEM create slope, aspect and topographic wetness arrays
dem_fn=dem_dir+'\\DEM.tif'
slope_fn=dem_dir+'\\Slope.tif'
aspect_fn=dem_dir+'\\Aspect.tif'
#all lidar products should already be aligned...
#however they need to be projected to the same CS as vspi
#pyplot.imshow(vspi)
lcf_cf_dir=lid_dir+'\\'+'LCF_CF.tif'
lcf_ef_dir=lid_dir+'\\'+'LCF_EF.tif'

lcf_nsf_dir=lid_dir+'\\'+'LCF_NSF.tif'

vcf_dir=lid_dir+'\\'+'VCF.tif'

veh_dir=lid_dir+'\\'+'VEH.tif'

vspi_dir=sev_dir+'\\VSPI_Wollemi.tiff'

#will ignore DEM variables for now... looks like faulty z data
#assuming it doesn't affect veg variables too much....

lcf_cf_g=gdal.Open(lcf_cf_dir)
lcf_cf=np.array(lcf_cf_g.GetRasterBand(1).ReadAsArray())

lcf_ef_g=gdal.Open(lcf_ef_dir)
lcf_ef=np.array(lcf_ef_g.GetRasterBand(1).ReadAsArray())

lcf_nsf_g=gdal.Open(lcf_nsf_dir)
lcf_nsf=np.array(lcf_nsf_g.GetRasterBand(1).ReadAsArray())

vcf_g=gdal.Open(vcf_dir)
vcf=np.array(vcf_g.GetRasterBand(1).ReadAsArray())

veh_g=gdal.Open(veh_dir)
veh=np.array(veh_g.GetRasterBand(1).ReadAsArray())

if lcf_cf.shape == lcf_ef.shape == lcf_nsf.shape == vcf.shape == veh.shape:
    print("lidar array dimensions agree")
else:
    print("Error: lidar array dimensions unequal")
    
#align to vspi

(vspi_i, lcf_cf_2, GeoT_a)=gs.align_rasters(vspi_dir, lcf_cf_dir, how=np.mean)
vspi=np.array(vspi_i)

import rasterio as rio
import os

with rio.open(lcf_cf_dir) as src:
    naip_data_ras=src.read()
    naip_meta=src.profile    
naip_meta['width']=810
naip_meta['height']=810 
naip_transform=naip_meta["transform"]
naip_crs=naip_meta["crs"]
naip_transform, naip_crs
naip_meta['dtype']="float64"
vspi_out='C:\\UserData\\galem\\PhD\\vspi\data\\'+sitename+'\\outputs'
if os.path.isdir(vspi_out)==False:
    os.mkdir(vspi_out)
with rio.open(vspi_out+'\\VSPI_'+sitename+'dummy.tiff', "w", **naip_meta) as dst:
    dst.write(vspi, 1)

comm=vspi_out+'\\VSPI_'+sitename+'dummy.tiff'


#if vspi is limiting:

(vspi_i, lcf_ef_2, GeoT_a)=gs.align_rasters(vspi_dir, lcf_ef_dir, how=np.mean)

(vspi_i, lcf_nsf_2, GeoT_a)=gs.align_rasters(vspi_dir, lcf_nsf_dir, how=np.mean)

(vspi_i, vcf_2, GeoT_a)=gs.align_rasters(vspi_dir, vcf_dir, how=np.mean)

(vspi_i, veh_2, GeoT_a)=gs.align_rasters(vspi_dir, veh_dir, how=np.mean)

#dem vars:
(comm2, dem, GeoT_a)=gs.align_rasters(comm, dem_fn, how=np.mean)
(comm2, aspect, GeoT_a)=gs.align_rasters(comm, aspect_fn, how=np.mean)
(comm2, slope, GeoT_a)=gs.align_rasters(comm, slope_fn, how=np.mean)
(comm2, twi, GeoT_a)=gs.align_rasters(comm, twi_dir, how=np.mean)
(comm2, topo2, GeoT_a)=gs.align_rasters(comm, topos_dir, how=np.mean)

#tsf:
(comm2, tsf, GeoT_a)=gs.align_rasters(comm, tsf_dir, how=np.mean)

#vars: dem, aspect, slope, tsf, lcfs
#check

lcf_cf_2.shape == lcf_ef_2.shape == lcf_nsf_2.shape == vcf_2.shape == veh_2.shape == dem.shape == aspect.shape == slope.shape == tsf.shape == vspi_i.shape

#create data table of 6 vars (for now...)
dtable=np.empty([0,12], dtype=float)
percent=-1
for x in range(0, lcf_cf_2.shape[1]):
    for y in range(0, lcf_cf_2.shape[0]):
        #dtable arranged as: vspi, lcf_cf, lcf_ef, lcf_nsf, vcf, veh
        if  lcf_cf_2[y, x] >= 0  and lcf_ef_2[y, x] >= 0 and lcf_nsf_2[y, x] >= 0 and vcf_2[y, x] >= 0 and veh_2[y, x] >= 0 and (vspi[y, x]==vspi[y, x]) and tsf[y, x] >=0 and dem[y, x] >=0 and aspect[y,x] >=0 and slope[y,x] >=0 and twi[y,x]>=0 and topo2[y,x]>=0:
            d=np.array([[vspi_i[y, x], lcf_cf_2[y, x], lcf_ef_2[y, x], lcf_nsf_2[y, x], vcf_2[y, x], veh_2[y, x], (j_date-tsf[y, x]), dem[y,x], aspect[y,x], slope[y,x], twi[y,x], topo2[y,x]]])
            dtable=np.append(dtable, d, 0)
            count=percent
            percent=int((x/lcf_cf.shape[1])*100)
            if count!=percent:
                print((str(percent))+"%")

np.savetxt('C:\\UserData\\galem\\PhD\\vspi\\dtable.csv', dtable, delimiter=",")          
            
from numpy.polynomial.polynomial import polyfit     
import matplotlib.pyplot as plt   
import numpy as np
import statistics
import math
from scipy.stats import gaussian_kde

var=11

xa=dtable[:,var]
ya=dtable[:,0]

intv=0.005

x=np.arange(0, max(dtable[:,var]), intv).tolist()

fit3=np.polyfit(xa, ya, 3)

y=[]
ci_h=[]
ci_l=[]
for i in range(0, len(x)):
    result=(fit3[0]*(x[i]**3))+(fit3[1]*(x[i]**2))+(fit3[2]*x[i])+fit3[3]
    y.append(result)
    #mean vspi of vh 0 to 1 for eg.
    # temp=[]
    # st=x[i]
    # en=st+intv
    # for t in range(0, len(xa)):
    #     if xa[t]>=st and xa[t]<en:
    #         temp.append(xa[t])
    # if len(temp)>2:
    #     mn=sum(temp)/len(temp)
    #     Z=1.96
    #     sd=statistics.stdev(temp)
    #     n=len(temp)
    #     upper=result+(Z*(sd/(math.sqrt(n))))
    #     lower=result-(Z*(sd/(math.sqrt(n))))
    #     ci_h.append(upper)
    #     ci_l.append(lower)
    # else:
    #     ci_h.append(1)
    #     ci_l.append(1)
        
plt.close()
plt.plot(xa, ya, '.', color='lightslategrey')
plt.plot(x, y, '-', color='black')
plt.ylim(-1000, 5500)
# plt.plot(x, ci_l)
# plt.plot(x, ci_h)
#plt.fill_between(x, y-ci_l, y+ci_h)
xy=np.vstack([xa, ya])
z=gaussian_kde(xy)(xy)
plt.show()

fig, ax = plt.subplots()
ax.scatter(xa, ya, c=z, s=100, edgecolor='')
plt.show()





x=list(range(0, max(dtable[:,1])))

fit3 = np.polyfit(xa, ya, 3)
fit3_fn=np.poly1d(fit3)


plt.plot(x, y, '.', fit3_fn, 'r')
plt.plot(699.742*3+-1827.1*2+1173* )



for vi in range(0, len(vars)):
    var=vars[vi]