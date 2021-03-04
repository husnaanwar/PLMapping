# -*- coding: utf-8 -*-
"""
Created on Wed May 29 15:27:17 2019

@author: ak4jo
"""

##file containing all functions used in data extraction/generation
import numpy as np
import re
import os
import pandas as pd
import openpyxl
import csv
from sklearn.model_selection import train_test_split

def figure_quality_axes(ax, xl, yl, title, legend = True, loc = 0, fontsize = 20):
    ax.set_xlabel(xl, fontsize = fontsize, weight = 'bold')
    ax.set_ylabel(yl, fontsize = fontsize, weight = 'bold')
    ax.set_title(title, fontsize = fontsize, weight = 'bold')
    ax.tick_params(axis='x',labelsize = fontsize, width = 3,length =10)
    ax.tick_params(axis='y',labelsize = fontsize, width = 3,length =10)
    [i.set_linewidth(4) for i in ax.spines.values()]
    if legend:
        h, l = ax.get_legend_handles_labels()
        ax.legend(h,l, fontsize = 18, loc = loc)


def linear(x, C):
    return C*x

def linear_off(x,*C):
    m = C[0]
    b = C[1]
    return m*x +b

def MExp(x, *C):
    return C[0]*np.exp(-x/C[1]) + C[2]

def find_nearest(value,array):
   pos = np.argmin(np.abs(array - value))
   return pos

def return_time_wavelength_data(filename):
    with open(filename) as f:
        Data = csv.reader(f, delimiter = ',')
        data = [row for row in Data]
        my_data = np.zeros((len(data),len(data[0])))
        for i,row in enumerate(data):
            try:
                my_data[i,:] = [float(x) for x in row]
            except ValueError:
                pass
    time = my_data[0,1:]

    my_data = my_data[my_data[:,1] != 0.,:]
    my_data.shape

    wavelengths = my_data[1:,0]
    values = my_data[1:,1:]
    mask = ~np.any(np.isnan(values), axis = 1)
    wavelengths = wavelengths[mask]
    values = values[mask,:]

    return time, wavelengths, values

def get_lamp_PL(filename, sheet):
    book = openpyxl.load_workbook(filename)
    sheet = book.get_sheet_by_name(sheet)
    lastRow = sheet.dimensions[int(sheet.dimensions.find(":"))+2:]
    Wavelengths = []
    Counts = []
    cells = sheet["A1" : "B" +str(lastRow)]

    for c1,c2 in cells:
        Wavelengths.append(c1.value)
        Counts.append(c2.value)

    Wavelengths = np.array(Wavelengths)
    Counts = np.array(Counts)
    return Wavelengths, Counts

def get_absorption(filename):
    ##Returns absorption file from PerkinElmer (reads csv)
    with open(filename,'r') as csvfile:
        Data = csv.reader(csvfile,delimiter = ',')
        myList = list(Data)

    Wavelengths = np.array([float(x[0]) for x in myList[1:]])
    Counts = np.array([float(x[1])for x in myList[1:]])
    return Wavelengths, Counts

def find_nearest(value,array):
    ##Returns index of array that is closest to value
   pos = np.argmin(np.abs(array - value))
   return pos

def fit_multi_exp(n):
    ##Geneartes a nth exponential function in which the parameter inputs are [A1, tau2, A2, tau2...]
    def exp(x,*par):
        temp = 0.
        for i in range(2*n):
            if i%2 ==0:
                temp+= par[i]*np.exp(-x/par[i+1])
        return temp
    return exp


def fit_multi_exp_offset(n):
    ##Geneartes a nth exponential function y = y0 + sum(A*exp(x-x0)/tau)
    #in which the parameter inputs are [y0, x0, A1, tau2, A2, tau2...]
    def exp(x,*par):
        temp = par[0]
        for i in range(2,2*n):
            if i%2 ==0:
                temp+= par[i]*np.exp(-(x-par[1])/par[i+1])
        return temp
    return exp

def min_max(arr):
    ##Min Max normalization
    return (arr-np.min(arr))/(np.max(arr)-np.min(arr))

def low_T_PL(filename):
    with open(filename, 'r') as f:
        Data = f.read().splitlines()
    try:
        start = Data.index(r'>>>>>Begin Processed Spectral Data<<<<<') + 1
    except ValueError:
        start = 0


    myWavelengths= np.array([float(x.split("\t")[0]) for x in Data[start:-1]])
    myCounts =np.array([float(x.split("\t")[1]) for x in Data[start:-1]])
    return myWavelengths, myCounts


def PLFromLaser(filename):
    with open(filename, 'r') as f:
        Data = f.read().splitlines()

    start = Data.index(r'{DATA} - this is a file signature, please do not edit it') + 2
    myWavelengths= np.array([float(x.split("\t")[0]) for x in Data[start:]])
    myCounts =np.array([float(x.split("\t")[1]) for x in Data[start:]])
    return myWavelengths, myCounts

def get_lifetime(filename, offset=10):
    with open(filename, 'r') as f:
        Data = f.read().splitlines()

    start = Data.index(r'Chan	Data')+1
    scale = Data[4]
    scale = scale.lstrip("Time calibration: ")
    scale = float(scale[0:scale.find("ns/ch")])

    myTime= np.array([float(x.split("\t")[0]) for x in Data[start:]])
    myCounts = np.array([float(x.split("\t")[1]) for x in Data[start:]])
    myTime = myTime[np.nonzero(myCounts)] * scale
    myCounts = myCounts[np.nonzero(myCounts)]
    offset = offset

    baseline = np.average(myCounts[np.argmax(myCounts) - 50 : np.argmax(myCounts)-10])
    print (baseline)
    myTime = myTime[np.argmax(myCounts)+offset:]
    myCounts = myCounts[np.argmax(myCounts)+offset:] - baseline
    #myCounts = (myCounts - np.min(myCounts))/(np.max(myCounts) - np.min(myCounts))
    myCounts = myCounts/np.max(myCounts)
    myTime = myTime - myTime[0]

    return myTime, myCounts

def get_Xps(filename, sheet):
    book = openpyxl.load_workbook(filename)
    sheet = book.get_sheet_by_name(sheet)
    lastRow = sheet.dimensions[int(sheet.dimensions.find(":"))+2:]
    Energy = []
    Counts = []
    Bkg = []
    cells = sheet["A1" : "C" +str(lastRow)]

    for c1,c2,c3 in cells:
        Energy.append(c1.value)
        Counts.append(c2.value)
        Bkg.append(c3.value)
    Energy = np.array(Energy)
    Counts = np.array(Counts)
    Bkg = np.array(Bkg)
    return Energy, Counts, Bkg

##For 1D diffusion analysis: takes an absorption coefficient, returns the 1D PL-Flux at the interface
## between acceptor and donor (following 10.1021/nn402197a). The first input to PL_Func is the diffusion length,
##The second is the magnitude of the entire curve--> this is necessary because the PL counts retrieved from
## the machine are arbitrary. This is a fitting parameter
def Diffusion_1D_PL(alpha):
    def PL_Func(x, Ld):
        a = alpha
        A = (-np.exp(-a*x) + np.exp(x/Ld))/(np.exp(-x/Ld) - np.exp(x/Ld))
        B = (-np.exp(-a*x) + np.exp(-x/Ld))/(np.exp(x/Ld) - np.exp(-x/Ld))
        y = abs(1./Ld * (A*np.exp(-x/Ld) - B*np.exp(x/Ld)) + a*np.exp(-a*x))
        print ("max value is" + str(np.nanmax(y)))
        return y/np.nanmax(y)
        #return y
    return PL_Func


def Diffusion_1D_PL_fit_alpha(x, *Ldd):
    a=Ldd[2]
    #C=Ldd[1]
    C=-1
    Ld = Ldd[0]
    A = C*(-np.exp(-a*x) + np.exp(x/Ld))/(np.exp(-x/Ld) - np.exp(x/Ld))
    B = C*(-np.exp(-a*x) + np.exp(-x/Ld))/(np.exp(x/Ld) - np.exp(-x/Ld))
    y = 1./Ld * (A*np.exp(-x/Ld) - B*np.exp(x/Ld)) + C*a*np.exp(-a*x)
    #y = np.abs((A*np.exp(-x/Ld) - B*np.exp(x/Ld)) + C*a*np.exp(-a*x))

    print ("max value is" + str(np.nanmax(y)))
    print (y/np.nanmax(y))
    if np.nanmax(y) < 0:
        return y/np.nanmin(y)
    else:
        return y/np.nanmax(y)
    #return y

def get_XRD(filename, errors='ignore'):
    with open(filename, 'rb') as f:
        Data = f.read().splitlines()

    start = [idx for idx, line in enumerate(Data) if line ==b'*RAS_INT_START'][0]
    end = [idx for idx, line in enumerate(Data) if line ==b'*RAS_INT_END'][0]
    print (start, end)
    theta = np.array([float(re.split(r'\s+', x.decode('utf-8'))[0]) for x in Data[start+1:end-1]])
    counts = np.array([float(re.split(r'\s+', x.decode('utf-8'))[1]) for x in Data[start+1:end-1]])

    return theta, counts


def Diffusion_1D_PL_glass(alpha):
    def dummy_func(x, Ld):
        a = alpha
        L = Ld
        A = (-a*L*np.exp(x/L) - np.exp(-a*x))/(np.exp(-x/L) + np.exp(x/L))
        B = (a*L*np.exp(-x/L) - np.exp(-a*x))/(np.exp(-x/L) + np.exp(x/L))

        y = np.abs(1./L * (-A*np.exp(-x/L) + B*np.exp(x/L)) - a*np.exp(-a*x))
        #print np.nanmax(y)

        return y/np.nanmax(y)
    return dummy_func

def Carrier_Profile_glass(x, alpha, Ld):
    a = alpha
    L = Ld
    A = (-a*L*np.exp(x[-1]/L) - np.exp(-a*x[-1]))/(np.exp(-x[-1]/L) + np.exp(x[-1]/L))
    B = (a*L*np.exp(-x[-1]/L) - np.exp(-a*x[-1]))/(np.exp(-x[-1]/L) + np.exp(x[-1]/L))

    y = A*np.exp(-x/L) + B*np.exp(x/Ld) + np.exp(-a*x)
    return np.abs(y)

def Carrier_Profile_1D(x, alpha, Ld):
    a = alpha
    L = Ld
    A = (-np.exp(-a*x[-1]) + np.exp(x[-1]/Ld))/(np.exp(-x[-1]/Ld) - np.exp(x[-1]/Ld))
    B = (-np.exp(-a*x[-1]) + np.exp(-x[-1]/Ld))/(np.exp(x[-1]/Ld) - np.exp(-x[-1]/Ld))
    y = A*np.exp(-x/L) + B*np.exp(x/Ld) + np.exp(-a*x)
    return np.abs(y)

def line(x, *C):
    return x*C[0]+C[1]

#def figure_aesthetics(f,ax):
#    try:
#        len(ax)
#    except TypeError:
#        ax.tick_params(axis='y',labelsize = 20, width = 3,length =10)
#        ax.tick_params(axis='x',labelsize = 20, width = 3,length =10)
#        [i.set_linewidth(4) for i in ax.spines.itervalues()]
#    else:
#        for a in ax:
#            a.tick_params(axis='y',labelsize = 20, width = 3,length =10)
#            a.tick_params(axis='x',labelsize = 20, width = 3,length =10)
#            [i.set_linewidth(4) for i in a.spines.itervalues()]
#
#    return f, ax
