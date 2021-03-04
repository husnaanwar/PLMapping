# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 16:14:11 2020

@author: ak4jo
"""
from scipy.signal import savgol_filter

from seabreeze.spectrometers import Spectrometer
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append(r'../../')
import DataAnalysis as aj
import motorautomation as ma
import re
from matplotlib import cm
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from mpl_toolkits.axes_grid1.colorbar import colorbar
from matplotlib import gridspec
import time
import array as arr



##takes in spectra as nx2 np array, [wavelength, intensities]
##intensity should be normalized
from ColourStuff import xyz_from_xy, ColourSystem

##taken from https://scipython.com/blog/converting-a-spectrum-to-a-colour/

    

def get_starting_position(ax1,ax2, align_motors = True):
    #input("Roughly align middle of sample with collection fibre ")
    
    ##Option to move motors to align sample rather than substrate, if substrate hard to move
    if align_motors:
        while True:
            try:
                x = float(input("Please enter an x starting value "))
                y = float(input("Please enter a y starting value "))
      
            except ValueError:
                print ("Please enter numbers only! ")
                continue
            
            else:
                ax1.move_to(y)
                ax2.move_to(x)
                ans = str(input("is this the correct starting point? (y/n) "))
                if ans == 'y':
                    break
                else:
                    continue
        
##will include funtionality to pick out crystal, tray etc later-
def calculate_map(num_points):
    while True:
        measurement_type = input("What type of sample is being measured?" + "\n" +
                             "A: Default Substrate" + "\n"+
                             "B: high-throughput tray" + "\n"+
                             "C: Custom" + "\n").lower()
        print (measurement_type)
        if not re.findall('[abc]', measurement_type, flags = re.IGNORECASE):
            print("Please select A, B or C!")
            continue
        else:
            if measurement_type == 'a':
                x_points = np.linspace(-10, 10,int(np.sqrt(num_points)))
                y_points = np.linspace(-10, 10, int(np.sqrt(num_points)))
                
            elif measurement_type == 'b':
                ## Tray has 8 rows of wells and 12 columns of wells
                ## 3 rows of drops per well
                ## Spacing between rows of drops in each well is 2.5mm OC
                ## Spacing between rows of wells is 1mm
                ## Spacing between columns of drops is 8.75mm OC
                x_points = np.linspace(start=0, stop=9*11, num=12)
                y_points = [0]
                for i in range((8*3)-1):
                    if i % 3 == 2:
                        y_points.append(y_points[-1] + 3.65)
                    else:
                        y_points.append(y_points[-1] + 2.65)
                y_points = np.array(y_points)
                
            elif measurement_type == 'c':
                ##Todo: implement custom limits
                print ("Not currently supported")
            
            break
        
    return np.array([x_points.T, y_points.T])
                

def execute_mapping(mymap, ax1, ax2, save_dir, name='',save_spectra = True):
    r = xyz_from_xy(0.7347, 0.2653)
    g = xyz_from_xy(0.1152,0.88264)
    b = xyz_from_xy(0.1566,0.0177)
    w = xyz_from_xy(0.3457,0.3585)
    
    wide_gamut = ColourSystem(r,g,b,w)
    starting_x =  ax2.get_current_position()
    starting_y =  ax1.get_current_position()
    
    x_points = starting_x + mymap[0]
    y_points = starting_y + mymap[1]
    max_int = np.zeros([len(x_points), len(y_points)])
    print(x_points.shape)
    print(y_points.shape)
    print(mymap.shape)
    print(mymap[0].shape)
    print(mymap[1].shape)
    RGB = np.zeros([len(x_points),len(y_points),3])
    for ix,x in enumerate(x_points):
        if ix % 2 == 0:
            y_p = y_points
        else:
            y_p = y_points[::-1]
        
        for iy,y in enumerate(y_p):
            print ("Moving to point ({0:.2f},{1:.2f})".format(x,y))
            ax2.move_to(x)
            ax1.move_to(y)
            print ("Acquiring Spectra")
            w, i = spec.spectrum()
            s = aj.find_nearest(380,w)
            e = aj.find_nearest(780,w)
            w = w[s:e]
            i = i[s:e]
            if save_spectra:
                 np.savetxt(save_dir + name+'x_'+ str(round(x,2)) +'_y_' + str(round(y,2))+ 'spectra.npy',np.array([w,i]))
            ## move in snake-ish motion
            if iy % 2 ==0:
                ix = ix
            else:
                ix = len(x_points) - ix-1
            
            max_int[ix,iy] = np.max(i)
            #smooth data and normalize before getting RGB values
            i = savgol_filter(i, 101, 3)
            i = aj.min_max(i)
            RGB[ix,iy,:] = wide_gamut.spec_to_rgb(w,i)
            

    ax1.move_to(0)
    ax2.move_to(0)
    
    f, ax = plt.subplots(nrows = 2, ncols = 1, figsize = [10,20], sharex = True)
    f.tight_layout()
    f.subplots_adjust(hspace = 0.2, top = 0.9, bottom = 0.1, left = 0.1, right = 0.9)
    
    a1 = ax[0]
    a2 = ax[1]
    
    im = a1.imshow(RGB, extent = [np.min(x_points), np.max(x_points), np.min(y_points), np.max(y_points)], origin = 'lower',aspect = 'auto')
    #contour = a2.contourf(x_points, y_points, max_int, cmap = 'plasma')
    #c1_divider = make_axes_locatable(a1)
    #ca1 = c1_divider.append_axes("right", size="7%", pad="4%",)
    #ca1.axis('off')
    #ax2_divider = make_axes_locatable(a2)
    #cax2 = ax2_divider.append_axes("right", size="7%", pad="4%",)
    #cb2 = colorbar(contour, cax = cax2)
    
    # a2.set_aspect(1)
    # a1.set_aspect(1)
    
    # aj.figure_quality_axes(a1, '', 'YPos (mm)', 'RBG',legend  = False)
    # aj.figure_quality_axes(a2, 'XPos (mm)', 'YPos (mm)', 'PL Intensity',legend  = False)
    # aj.figure_quality_axes(cb2.ax, '', 'Intensity (A.U.)', '',legend  = False)
    
    
    np.save(save_dir + name+'Intensities', max_int)
    np.save(save_dir + name+'Colours', RGB)
    #f.savefig(save_dir+name+'Mapped.png', format = 'png', dpi= 600)
            
            


if __name__ == '__main__':
    esp = ma.ESP('COM4')
    ax1 = esp.axis(1, acc = 10)
    ax2 = esp.axis(2, acc = 10)
    spec = Spectrometer.from_first_available()
    spec.integration_time_micros(200000)
    save_dir = re.sub(r'\\',r'/',r'C:\Users\ECE\Desktop\PL_Mapping')
    get_starting_position(ax1,ax2)
    mymap = calculate_map(500)
    start = time.process_time()

    execute_mapping(mymap, ax1,ax2,save_dir, name = '200 ms int')
    
    print("Time elapsed is {0:.2f}".format(time.process_time() - start))    
    esp.close()
    
    spec.close()



