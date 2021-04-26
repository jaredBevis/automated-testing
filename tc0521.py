import serial.tools.list_ports as serial_ports  # From official package 'pyserial'
import serial   # From official package 'pyserial'
from time import sleep

command_K_modelnum = b'\x02\x4B\x00\x00\x00\x00\x03'
response_K_modelnum = b'\x02#\xc4\x91#\xc4\x91#\xc4\x91#\xc4\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff521\xff\xff\xff\xff\xff\x03'

command_A_status = b'\x02\x41\x00\x00\x00\x00\x03'      # status request
command_B_backlight = b'\x02\x42\x00\x00\x00\x00\x03'   # backlight button
command_C_units = b'\x02\x43\x00\x00\x00\x00\x03'       # deg C - deg F button
command_E_record = b'\x02\x45\x00\x00\x00\x00\x03'      # REC button
command_H_hold = b'\x02\x48\x00\x00\x00\x00\x03'        # HOLD button
command_M_minmaxavg = b'\x02\x4d\x00\x00\x00\x00\x03'   # MIN/MAX/AVG button
command_N_xminmaxavg = b'\x02\x4e\x00\x00\x00\x00\x03'  # exit MIN/MAX/AVG model
command_P_load = b'\x02\x50\x00\x00\x00\x00\x03'        # recall (load) data.

# Generic bitmask values:
bit0 = (1 << 0)
bit1 = (1 << 1)
bit2 = (1 << 2)
bit3 = (1 << 3)
bit4 = (1 << 4)
bit5 = (1 << 5)
bit6 = (1 << 6)
bit7 = (1 << 7)

# Command A status report bitmasking for byte 2 data:
bitmask_T1T2mode    = bit0
bitmask_recallmode  = bit1
bitmask_T1range     = bit2
bitmask_T2range     = bit3
bitmask_T3range     = bit4
bitmask_T4range     = bit5
bitmask_T1T2range   = bit6
bitmask_units       = bit7

# Command A status report bitmasking for byte 3 data:
bitmask_alarm       = bit0
bitmask_overtemp    = bit1
bitmask_undertemp   = bit2
bitmask_recording   = bit3
bitmask_memfull     = bit4
bitmask_holdmode    = bit5
bitmask_maxminmode  = bit6
bitmask_btenabled   = bit7

# Command A status report bitmasking for byte 4 data:
bitmask_maxmode     = bit0
bitmask_minmode     = bit1
bitmask_avgmode     = bit2
bitmask_maxminavgmode   = bit3

# Command A status report bitmasking for byte 5 data:
bitmask_tc_k        = bit0
bitmask_tc_j        = bit1
bitmask_tc_e        = bit2
bitmask_tc_t        = bit3

# Command A status report bitmasking for byte 6 data:
bitmask_t1_ol       = bit0
bitmask_t2_ol       = bit1
bitmask_t3_ol       = bit2
bitmask_t4_ol       = bit3
bitmask_t1_unplug   = bit4
bitmask_t2_unplug   = bit5
bitmask_t3_unplug   = bit6
bitmask_t4_unplug   = bit7

class Tc0521(object):
    '''Device handler for PerfectPrime TC0521 thermocouple meter.  
    PerfectPrime admits to bugs when changing settings remoetely and are
    unwilling to make corrections in the firmware.  Pre-set your meter before
    connecting to have settings correctly reflected in reported data.'''
    
    def __init__(self, com_port=None):
        '''Connects to TC0521 meter give input COM port.  
        COM port should use OS specifi naming.'''
        
        # Command A byte 1 battery data:
        self.battery = None     # Battery fuel gauge level
        
        # Command A byte 2 temperature operating modes data:
        self.t1t2_mode = None        # In T1-T2 mode (boolean)
        self.t1_range_hi = None    # If amplitude is xxx.x or xxxx (<= 999.9 or >= 1000) for T1
        self.t2_range_hi = None    # If amplitude is xxx.x or xxxx (<= 999.9 or >= 1000) for T2
        self.t3_range_hi = None    # If amplitude is xxx.x or xxxx (<= 999.9 or >= 1000) for T3
        self.t4_range_hi = None    # If amplitude is xxx.x or xxxx (<= 999.9 or >= 1000) for T4
        self.t1t2_range_hi = None  # If amplitude is xxx.x or xxxx (<= 999.9 or >= 1000) for T1-T2
        self.units = None       # Units of C or F
        
        # Command A byte 3 system data
        self.alarm_en = None    # Is the alarm enabled?
        self.overtemp = None    # Is there a reading exceeding alarm value?
        self.undertemp = None   # Is there a reading under alarm value?
        self.recording = None   # Is recording active?
        self.memfull = None     # Is internal storage memory full?
        self.holdmode = None    # Is unit holding current frozen value?
        self.maxminmode = None  # Is unit operating in max/min mode?
        self.btactive = None    # Is bluetooth enabled?
        
        # Command A byte 4 min/max/avg current operating mode
        self.maxminmodetype = None  # Which of min, max, avg, or min/max/avg mode are we operating in?
        
        # Command A byte 5 probe type
        self.probe_type = None
        
        # Command A byte 6 Over limit or unplugged
        self.t1_ol = None
        self.t2_ol = None
        self.t3_ol = None
        self.t4_ol = None
        self.t1_unplug = None
        self.t2_unplug = None
        self.t3_unplug = None
        self.t4_unplug = None
        
        # Probe temperatures
        self.t1 = None
        self.t2 = None
        self.t3 = None
        self.t4 = None
        self.t1t2 = None
        
        if com_port == None:
            # Scan through the ports to see if TC0521 is connected.
            
            # Determine the available system ports
            available_ports = serial_ports.comports()
        
            # Loop through all system ports to find one with responsive TC0521 unit.
            for port_info in available_ports:
                try:
                    print("trying port " + port_info.device)
                    self.port = serial.Serial(port=port_info.device, timeout=1)
                    
                    self.port.flush()
                    
                    # Send query for model number
                    self.port.write(command_K_modelnum)
                    
                    # Check response for correct value indicating right port selected
                    #self.port_read = self.port.read(size=32)
                    
                    if self.raw_data == response_K_modelnum:
                        print('Successfully connected to TC0521.')
                    else:
                        raise NameError('TC0521 NOT ON SPECIFIED PORT.')
                        self.port.close()
                        del(self.port)
                    
                except:
                    pass # Port cannot be opened, probably already in use.  Try next one.
        else:
            # COM port specified
            try:
                self.port = serial.Serial(port=com_port, timeout=1)
            except:
                raise NameError('PORT UNAVAILABLE OR ALREADY IN USE.')
                
            self.port.flush()
                
            # Send query for model number to verify correct port specified.
            self.port.write(command_K_modelnum)
            
            # Check response for correct value indicating right port selected
            self.raw_data = self.port.read(size=32)
            
            if self.raw_data == response_K_modelnum:
                print('Successfully connected to TC0521.')
            else:
                raise NameError('TC0521 NOT ON SPECIFIED PORT.')
                self.port.close()
                del(self.port)
        
                    
    def close(self):
        '''Close the serial port the TC0521 is on.'''
        self.port.close()
        
    def open(self):
        '''Reopen the serial port the TC0521 is on.'''
        self.port.open()
        
        self.port.flush()
        
    def send_command(self, command):
        '''Send the specified command (button press).'''
        
        self.port.flush()
        
        self.port.write(command)
        
    def identify(self):
        '''Blink the connected meter for 15 seconds.'''
        
        for i in range(30):
            self.send_command(command_B_backlight)
            sleep(0.5)
        
    def get_status(self):
        '''Query the current operating status and temperature values.  
        Returns True if checksum mismatch.'''
        
        self.port.flush()
        
        self.port.write(command_A_status)
        
        self.raw_data = self.port.read(size=64)
        
        # print(self.raw_data)
        
        # Parse out binary data from string:
        
        # Byte 0 is always 0x02
        
        # Byte 1 is battery level
        self.battery = self.raw_data[1] * 33
        
        # Byte 2 is boolean information about current configuration
        if self.raw_data[2] & bitmask_T1T2mode:
            self.t1t2_mode = True
        else:
            self.t1t2 = False
        if self.raw_data[2] & bitmask_recallmode:
            pass # not sure what to do here...
        if self.raw_data[2] & bitmask_T1range:
            self.t1_range_hi = True
        else:
            self.t1_range_hi = False
        if self.raw_data[2] & bitmask_T2range:
            self.t2_range_hi = True
        else:
            self.t2_range_hi = False
        if self.raw_data[2] & bitmask_T3range:
            self.t3_range_hi = True
        else:
            self.t3_range_hi = False
        if self.raw_data[2] & bitmask_T4range:
            self.t4_range_hi = True
        else:
            self.t4_range_hi = False
        if self.raw_data[2] & bitmask_T1T2range:
            self.t1t2_range_hi = True
        else:
            self.t1t2_range_hi = False
        if self.raw_data[2] & bitmask_units:
            self.units = 'C'
        else:
            self.units = 'F'
            
        # Byte 3 is more status information
        if self.raw_data[3] & bitmask_alarm:
            self.alarm_en = True
        else:
            self.alarm_en = False
        if self.raw_data[3] & bitmask_overtemp:
            self.overtemp = True
        else:
            self.overtemp = False
        if self.raw_data[3] & bitmask_undertemp:
            self.undertemp = True
        else:
            self.undertemp = False
        if self.raw_data[3] & bitmask_recording:
            self.recording = True
        else:
            self.recording = False
        if self.raw_data[3] & bitmask_memfull:
            self.memfull = True
        else:
            self.memfull = False
        if self.raw_data[3] & bitmask_holdmode:
            self.holdmode = True
        else:
            self.holdmode = False
        if self.raw_data[3] & bitmask_maxminmode:
            self.maxminmode = True
        else:
            self.maxminmode = False
        if self.raw_data[3] & bitmask_btenabled:
            self.btactive = True
        else:
            self.btactive = False
        
        # Byte 4 is min max current mode
        if self.maxminmode:
            if self.raw_data[4] & bitmask_maxmode:
                self.maxminmodetype = 'MAX'
            elif self.raw_data[4] & bitmask_minmode:
                self.maxminmodetype = 'MIN'
            elif self.raw_data[4] & bitmask_avgmode:
                self.maxminmodetype = 'AVG'
            elif self.raw_data[4] & bitmask_maxminavgmode:
                self.maxminmodetype = 'MINMAXAVG'
            else:
                self.maxminmodetype = None
        else:
            self.maxminmodetype = None
        
        # Byte 5 probe type
        if self.raw_data[5] & bitmask_tc_k:
            self.probe_type = 'K'
        elif self.raw_data[5] & bitmask_tc_j:
            self.probe_type = 'J'
        elif self.raw_data[5] & bitmask_tc_e:
            self.probe_type = 'E'
        elif self.raw_data[5] & bitmask_tc_t:
            self.probe_type = 'T'
        else:
            self.probe_type = None
            
        # Byte 6 is probe over/under load
        if self.raw_data[6] & bitmask_t1_ol:
            self.t1_ol = True
        else:
            self.t1_ol = False
        if self.raw_data[6] & bitmask_t2_ol:
            self.t2_ol = True
        else:
            self.t2_ol = False
        if self.raw_data[6] & bitmask_t3_ol:
            self.t3_ol = True
        else:
            self.t3_ol = False
        if self.raw_data[6] & bitmask_t4_ol:
            self.t4_ol = True
        else:
            self.t4_ol = False
        if self.raw_data[6] & bitmask_t1_unplug:
            self.t1_unplug = True
        else:
            self.t1_unplug = False
        if self.raw_data[6] & bitmask_t2_unplug:
            self.t2_unplug = True
        else:
            self.t2_unplug = False
        if self.raw_data[6] & bitmask_t3_unplug:
            self.t3_unplug = True
        else:
            self.t3_unplug = False
        if self.raw_data[6] & bitmask_t4_unplug:
            self.t4_unplug = True
        else:
            self.t4_unplug = False
        
        # Probe Temperatures
        if self.t1_ol | self.t1_unplug:
            self.t1 = None
        else:
            self.t1 = int((self.raw_data[9] << 8) | self.raw_data[10])
            if ~self.t1_range_hi:
                self.t1 = self.t1 / 10.0
        if self.t2_ol | self.t2_unplug:
            self.t2 = None
        else:
            self.t2 = int((self.raw_data[11] << 8) | self.raw_data[12])
            if ~self.t2_range_hi:
                self.t2 = self.t2 / 10.0
        if self.t3_ol | self.t3_unplug | (self.t1t2_mode == True):
            self.t3 = None
        else:
            self.t3 = int((self.raw_data[13] << 8) | self.raw_data[14])
            if ~self.t3_range_hi:
                self.t3 = self.t3 / 10.0
        if self.t4_ol | self.t4_unplug | (self.t1t2_mode == True):
            self.t4 = None
        else:
            self.t4 = int((self.raw_data[15] << 8) | self.raw_data[16])
            if ~self.t4_range_hi:
                self.t4 = self.t4 / 10.0
        if self.t1t2_mode:
            self.t1t2 = int((self.raw_data[17] << 8) | self.raw_data[18])
            if ~self.t1t2_range_hi:
                self.t1t2 = self.t1t2 / 10.0
        else:
            self.t1t2 = None

        # Run Checksum
        sum = 0
        for i in range(1,62):
            sum += self.raw_data[i]
            
        if (sum & 255) ^ self.raw_data[62]:
            print("WARNING: CHECKSUM MISMATCH, NULLIFYING ALL DATA.  RETRY READ.")
            return True
        else:
            return False