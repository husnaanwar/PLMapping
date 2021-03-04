# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 13:51:44 2020

@author: ak4jo

Code to control newport controllers using either pyserial or newportesp
"""
import serial
from time import sleep

##this is a py3 wrapparound for the newportESP class that doesn't work with python3,
##primarily because ASCII strings are encoded differently


##decorator that will only call function if the "is_moving" property returns false
def check_previous_motion_is_done(func):
  def checked_previous_motion_is_done(*args, **kwargs):
    self = args[0]
    while self.is_moving():
      print ("Previous motion is not done! Waiting")
      sleep(self.polling_time)
      
    func(*args, **kwargs)
  return checked_previous_motion_is_done


class ESP(object):
    def __init__(self, port):
        ##initialize and open the connection with motor controller, fix baudrate to what is listed in:
        ##https://www.newport.com/medias/sys_master/images/images/hda/h3e/9117547069470/ESP301-User-s-Manual.pdf
        ##other parameters are the default in serial.Serial initialization class
        self.ser = serial.Serial(port = port, baudrate = 921600, timeout = 3)
        
        print("Found controller: " + self.get_version())
        
    def write(self, string, axis = None):
        string_to_pass = (str(axis) if axis is not None else "")+string + '\r'
        
        self.ser.write(str.encode(string_to_pass))
        
    def read(self):
        byte_response =  self.ser.readlines(1)
        
        if len(byte_response) > 0:
            return byte_response[0].decode('UTF-8').split('\r')[0]
        else:
            return 'No response'
    
    def query(self, string, axis=None):
        
        self.write(string+'?', axis = axis)
        return self.read()
     
    
    def axis (self, axis_index = 1, acc = 40, low_limit = -50, high_limit = 50, find_limits = False):
        
        return Axis(self, axis = axis_index, acc = acc, find_limits = find_limits, low_limit = low_limit, high_limit = high_limit)
        
    def close(self):
        self.ser.close()
    
    def get_version(self):
        return self.query('VE')
        
    
class Axis(object):
    def __init__(self, controller, axis = 1, acc=40, low_limit = -50, high_limit = 50, find_limits = False):
        self.axis = axis
        self.esp = controller
        self.read = self.esp.read
        self.low_limit = low_limit
        self.high_limit= high_limit
        self.polling_time = 0.1
        self.__turnon__()
        self.write('JH7')
        self.write('AC' + str(acc))
        
        
        if find_limits:
            self.get_axes_limits()
            self.move_to(0)
            
        self.home_search()
        self.define_home()
        self.current_position = 0.
        self.update_current_position()
        self.write('SL'+ str(self.low_limit))
        self.write('SR'+ str(self.high_limit))
        self.write('ZL0')
        print("Axis {} has been initialized".format(str(axis)))
    
    def get_current_position(self):
        print(self.query('TP'))
        return float(self.query('TP'))
          
    def update_current_position(self):
        self.current_position =  float(self.query('TP'))
    
    def __turnoff__(self):
        self.off()
        
    def __turnon__(self):
        self.on()
    
    def write(self, string):
        self.esp.write(string, self.axis)
        
    def query(self, string):
        return self.esp.query(string, self.axis)
        
    def off(self):
        self.write('MF')
    
    def on(self):
        self.write('MO')
    
    @check_previous_motion_is_done
    def home_search(self, wait = True):
        self.write('OR')
        if wait:
            self.wait()
    
    @check_previous_motion_is_done
    def define_home(self):
        self.write('DH')
    
    def is_moving(self):
        return False if self.query('MD')=="1" else True
    
    def wait(self):
        while self.is_moving():
            print("Currently at {0:.2f}, moving".format(self.get_current_position()))
            sleep(self.polling_time)
            
            
            
    @check_previous_motion_is_done
    def move_to(self, pos, wait = True):
        if pos > self.high_limit or pos < self.low_limit:
            print('Requested position {0:.1f} outside of limits, please enter a position within {1:.1f} and {2:.1f} '.\
                  format(pos, self.low_limit, self.high_limit))
        else:
            self.write("PA" + str(pos))
            if wait:
                self.wait()
            
        self.update_current_position()
        
            
    @check_previous_motion_is_done
    def move_by(self, amount, wait = True):
        if self.current_position + amount > self.high_limit or self.current_position+amount < self.low_limit:
            print('Requested position {0:.1f} outside of limits, please enter a position within {1:.1f} and {2:.1f} '.\
                  format(self.current_position + amount, self.low_limit, self.high_limit))
        else:
            self.write("PR" + str(amount))
            if wait:
                self.wait()
                
        self.update_current_position()
                
    @check_previous_motion_is_done
    def get_axes_limits(self):
        self.write('MT')
        self.wait()
        self.high_limit = self.get_current_position()
        self.write('MT-')
        self.wait()
        self.low_limit = self.get_current_position()
        self.move_to((self.high_limit + self.low_limit)/2.)
        self.define_home()
        
        print('Low limit is at {0:.2f} and high limit is at {1:.2f}'.format(self.low_limit, self.high_limit))
        
    
    
    
if __name__ == "__main__":

    
    esp = ESP('COM5')
    ax = esp.axis(1)
    #esp.close()
    
    
    
    