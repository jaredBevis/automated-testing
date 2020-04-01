#!/usr/bin/env python3

import pyvisa
import sys
import time

device = 'ASRL/dev/ttyUSB0::INSTR'
	
class BkTrippleSupply(object):
    """    This class creates an instance to control the BK9129B tripple output power supply.
    Reference programming manual is here: 
    https://bkpmedia.s3.amazonaws.com/downloads/programming_manuals/en-us/9129B_programming_manual.pdf"""
	
    def __init__(self):
        self.cmd_delay = 0.1    # Time in seconds to wait after sending each command
        self.rm = pyvisa.ResourceManager()
        self.ps = self.rm.open_resource(device, baud_rate=9600)
        if 'B&K Precision, 9129B' in self.ps.query("*IDN?"): # Verify expected instrument is present.
            #print('Found 9129B PSU')
            self.ps.write("*PSC ON")
            time.sleep(self.cmd_delay)
            self.ps.write("*CLS")
            time.sleep(self.cmd_delay)
            self.ps.write("*RST")
            time.sleep(self.cmd_delay)
            self.ps.write("SYST:REM")
            time.sleep(self.cmd_delay)
            
            #self.esr = self.ps.query("SYST:ERR?") # Cofirm no errors
            #print("ESR=" + self.esr)
        else:
            self.ps.close()
            sys.exit('NO SUPPORTED POWER SUPPLIES FOUND')
        
    def open(self):
        """Re-open the power supply instance."""
        self.ps = self.rm.open_resource(device, baud_rate=9600)
        self.ps.write("*CLS")
        time.sleep(self.cmd_delay)
        self.ps.write("*RST")
        time.sleep(self.cmd_delay)
        self.ps.write("SYST:REM")
        time.sleep(self.cmd_delay)
        
        #self.esr = self.ps.query("SYST:ERR?") # Cofirm no errors
        #print("ESR=" + self.esr)
            
    def set_voltage_ch1(self):
        pass
        
    def enable_output_all(self):
        """Enables all three outputs of the supply"""
        self.ps.write("OUTPut:STATe:ALL ON")
        time.sleep(self.cmd_delay)
        
    def enable_output_ch(self, chan):
        """Enables specified channel output, argument is integer for channel number"""
        self.ps.write("INSTrument:SELect CH" + str(chan))
        time.sleep(self.cmd_delay)
        self.ps.write("SOURce:CHANnel:OUTPut:STATe ON")
        time.sleep(self.cmd_delay)
        
    def disable_output_all(self):
        """Disables all three outputs of the supply"""
        self.ps.write("OUTPut:STATe:ALL OFF")
        time.sleep(self.cmd_delay)
        
    def disable_output_ch(self, chan):
        """Disables specified channel output, argument is integer for channel number"""
        self.ps.write("INSTrument:SELect CH" + str(chan))
        time.sleep(self.cmd_delay)
        self.ps.write("SOURce:CHANnel:OUTPut:STATe OFF")
        time.sleep(self.cmd_delay)
        
    def set_current_ch(self, chan, current):
        """Sets specified channel current limit, argument is integer for channel number and float for current in amps"""
        self.ps.write("INSTrument:SELect CH" + str(chan))
        time.sleep(self.cmd_delay)
        self.ps.write("CURRent " + str(current) + "A")
        time.sleep(self.cmd_delay)
        
    def set_voltage_ch(self, chan, voltage):
        """Sets specified channel voltage limit, argument is integer for channel number and float for voltage in volts"""
        self.ps.write("INSTrument:SELect CH" + str(chan))
        time.sleep(self.cmd_delay)
        self.ps.write("VOLTage " + str(voltage) + "V")
        time.sleep(self.cmd_delay)
        
    def read_voltage_ch(self, chan):
        """Returns a float of specified channel voltage output, argument is integer for channel number"""
        self.ps.write("INSTrument:SELect CH" + str(chan))
        time.sleep(self.cmd_delay)
        return float(self.ps.query("VOLTage?"))
        
    def close(self):
        """Close the power supply instance."""
        self.disable_output_all()
        self.ps.write("SYST:LOC")       # Put the power supply back into local control
        time.sleep(self.cmd_delay)
        #self.esr = self.ps.query("SYST:ERR?") # Cofirm no errors
        #print("ESR=" + self.esr)
        self.ps.close()                     # Close the COM port

