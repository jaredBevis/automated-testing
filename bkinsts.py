#!/usr/bin/env python3

import pyvisa
import sys
import time
import serial

device_default = 'COM9'
	
class BkTrippleSupply_9129B(object):
    """    This class creates an instance to control the BK9129B tripple output power supply.
    Reference programming manual is here: 
    https://bkpmedia.s3.amazonaws.com/downloads/programming_manuals/en-us/9129B_programming_manual.pdf"""
	
    def __init__(self, device=device_default, baudrate=9600):
        self.cmd_delay = 0.1    # Time in seconds to wait after sending each command, manual warns to add an unspecified delay after commands
        self.rm = pyvisa.ResourceManager()
        self.ps = self.rm.open_resource(device, baudrate=baudrate)
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
        
class BkDcLoad_8500(object):
    """    This class creates an instance to control the BK8500 DC programmable load.
    Reference programming manual is here: 
    https://bkpmedia.s3.us-west-1.amazonaws.com/downloads/manuals/en-us/85xx_manual.pdf
    TLDR; this device is dumb and is far from SCPI compliant.  All operations are byte oriented."""
    
    # Command byte definitions
    STATUS_DATA = 0x12
    SET_REMOTE = 0x20
    SET_ON_OFF = 0x21
    SET_MAX_VOLTAGE_LIMIT = 0x22
    GET_MAX_VOLTAGE_LIMIT = 0x23
    SET_MAX_CURRENT_LIMIT = 0x24
    GET_MAX_CURRENT_LIMIT = 0x25
    SET_MAX_POWER_LIMIT = 0x26
    GET_MAX_POWER_LIMIT = 0x27
    SET_OP_MODE = 0x28
    GET_OP_MODE = 0x29
    SET_CC_MODE_CURRENT = 0x2A
    GET_CC_MODE_CURRENT = 0x2B
    SET_CV_MODE_VOLTAGE = 0x2C
    GET_CV_MODE_VOLTAGE = 0x2D
    SET_CW_MODE_POWER = 0x2E
    GET_CW_MODE_POWER = 0x2F
    SET_CR_MODE_RESISTANCE = 0x30
    GET_CR_MODE_RESISTANCE = 0x31
    # Transient and List operations not implemented (0x32 - 0x4D)
    # 0x4E and 0x4F technically called battery testing, but is functionally under voltage lockout.
    SET_UVLO_VOLTAGE = 0x4E
    GET_UVLO_VOLTAGE = 0x4F
    # Load timer not implemented (0x50 - 0x53)
    # Communication address not implemented (0x54)
    # SET_LOCAL = 0x55 # Disables 'LOCAL' key on front panel, do not implement...
    # Remote sensing not implemented (0x56 - 0x57)
    # Triggering not implemented (no transient implemented) (0x58 - 0x5A)
    # Store/Recall not implemented (0x5B - 0x5C)
    # SET_FUNCTION_MODE = 0x5D # Only constant modes implemented in this library
    # GET_FUNCTION_MODE = 0x5E
    GET_VALUES = 0x5F
    # Calibration not implemented (0x60 - 0x69)
    GET_MFG_INFO = 0x6A
    # Barcode info not implemented (0x6B)
    
    # Device constants
    START_BYTE = 0xAA
    INSTRUMENT_ADDRESS = 0x00 # Unless you've changed it...
    RESERVED_BYTE = 0x00
    PACKET_LENGTH = 26 # all commands and responses are 26 bytes
    
    # Status Byte values (byte 3)
    STATUS_BAD_CHECKSUM = 0x90
    STATUS_BAD_PARAMETER = 0xA0
    STATUS_UNKNOWN_COMMAND = 0xB0
    STATUS_BAD_COMMAND = 0xC0
    STATUS_SUCCESS = 0x80
    STATUS_BAD_PACKET = 0x00 # This is mine...general catchall for malformed packet
    
    # Command Dictionaries
    cmd_remote_control = {'command': SET_REMOTE, 'command_arg': [0x01], 'arg_format': None, 'command_return': 'status_packet'}
    cmd_local_control = {'command': SET_REMOTE, 'command_arg': [0x00], 'arg_format': None, 'command_return': 'status_packet'}
    cmd_enable_load = {'command': SET_ON_OFF, 'command_arg': [0x01], 'arg_format': None, 'command_return': 'status_packet'}
    cmd_disable_load = {'command': SET_ON_OFF, 'command_arg': [0x00], 'arg_format': None, 'command_return': 'status_packet'}
    cmd_set_max_voltage_limit = {'command': SET_MAX_VOLTAGE_LIMIT, 'command_arg': [], 'arg_format': 'four_byte_1mv_units', 'command_return': 'status_packet'}       # requires pre-command to determine the argument
    cmd_get_max_voltage_limit = {'command': GET_MAX_VOLTAGE_LIMIT, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_1mv_units'}
    cmd_set_max_current_limit = {'command': SET_MAX_CURRENT_LIMIT, 'command_arg': [], 'arg_format': 'four_byte_0ma1_units', 'command_return': 'status_packet'}       # requires pre-command to determine the argument
    cmd_get_max_current_limit = {'command': GET_MAX_CURRENT_LIMIT, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_0ma1_units'}
    cmd_set_max_power_limit = {'command': SET_MAX_POWER_LIMIT, 'command_arg': [], 'arg_format': 'four_byte_1mw_units', 'command_return': 'status_packet'}       # requires pre-command to determine the argument
    cmd_get_max_power_limit = {'command': GET_MAX_POWER_LIMIT, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_1mw_units'}
    cmd_set_mode = {'command': SET_OP_MODE, 'command_arg': [], 'arg_format': 'op_mode', 'command_return': 'status_packet'}   # requires pre-command to determine the argument
    cmd_get_mode = {'command': GET_OP_MODE, 'command_arg': [], 'arg_format': None, 'command_return': 'op_mode'}
    cmd_set_cc_mode_current = {'command': SET_CC_MODE_CURRENT, 'command_arg': [], 'arg_format': 'four_byte_0ma1_units', 'command_return': 'status_packet'}   # requires pre-command to determine the argument
    cmd_get_cc_mode_current = {'command': GET_CC_MODE_CURRENT, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_0ma1_units'}
    cmd_set_cv_mode_voltage = {'command': SET_CV_MODE_VOLTAGE, 'command_arg': [], 'arg_format': 'four_byte_1mv_units', 'command_return': 'status_packet'}   # requires pre-command to determine the argument
    cmd_get_cv_mode_voltage = {'command': GET_CV_MODE_VOLTAGE, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_1mv_units'}
    cmd_set_cw_mode_power = {'command': SET_CW_MODE_POWER, 'command_arg': [], 'arg_format': 'four_byte_1mw_units', 'command_return': 'status_packet'}   # requires pre-command to determine the argument
    cmd_get_cw_mode_power = {'command': GET_CW_MODE_POWER, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_1mw_units'}
    cmd_set_cr_mode_resistance = {'command': SET_CR_MODE_RESISTANCE, 'command_arg': [], 'arg_format': 'four_byte_1mo_units', 'command_return': 'status_packet'}   # requires pre-command to determine the argument
    cmd_get_cr_mode_resistance = {'command': GET_CR_MODE_RESISTANCE, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_1mo_units'}
    cmd_set_uvlo_voltage = {'command': SET_UVLO_VOLTAGE, 'command_arg': [], 'arg_format': 'four_byte_1mv_units', 'command_return': 'status_packet'}       # requires pre-command to determine the argument
    cmd_get_uvlo_voltage = {'command': GET_UVLO_VOLTAGE, 'command_arg': [], 'arg_format': None, 'command_return': 'four_byte_1mv_units'}
    cmd_get_present_values = {'command': GET_VALUES, 'command_arg': [], 'arg_format': None, 'command_return': 'front_panel_struct'}
    cmd_get_mfg_info = {'command': GET_MFG_INFO, 'command_arg': [], 'arg_format': None, 'command_return': 'mfg_info_struct'}
    
    # All data is little endian (lower MSB first)
    
    # Buffer initialization
    rx_buff = [0x00] * PACKET_LENGTH
    tx_buff = [0x00] * PACKET_LENGTH
    
    def to_bytes_1mv_units(self, voltage):
        voltage_1mv = int(voltage * 1000)
        return list(voltage_1mv.to_bytes(4, 'little'))
        
    def from_bytes_1mv_units(self, bytes_in):
        voltage_1v = int.from_bytes(bytes(bytes_in), 'little') / 1000.0
        return voltage_1v
        
    def to_bytes_0ma1_units(self, current):
        current_0ma1 = int(current * 10000)
        return list(current_0ma1.to_bytes(4, 'little'))
        
    def from_bytes_0ma1_units(self, bytes_in):
        current_1a = int.from_bytes(bytes(bytes_in), 'little') / 10000.0
        return current_1a
        
    def to_bytes_1mw_units(self, current):
        power_1mw = int(current * 1000)
        return list(power_1mw.to_bytes(4, 'little'))
        
    def from_bytes_1mw_units(self, bytes_in):
        power_1w = int.from_bytes(bytes(bytes_in), 'little') / 1000.0
        return power_1w
        
    def to_bytes_1mo_units(self, resistance):
        resistance_1mo = int(resistance * 1000)
        return list(resistance_1mo.to_bytes(4, 'little'))
        
    def from_bytes_1mo_units(self, bytes_in):
        resistance_1o = int.from_bytes(bytes(bytes_in), 'little') / 1000.0
        return resistance_1o
        
    def convert_op_mode(self, mode):
        mode_dict = {0x00: 'CC', 'CC': [0x00], 0x01: 'CV', 'CV': [0x01], 0x02: 'CW', 'CW': [0x02], 0x03: 'CR', 'CR': [0x03]}
        return mode_dict[mode]
    
    def calc_checksum(self, packet):
        checksum = 0
        
        for val in packet[:-1]:
            checksum = checksum + (val % 256)
        checksum = checksum % 256
        return checksum
    
    def check_status(self, rx_buff):
        if rx_buff[0] != self.START_BYTE:
            return self.STATUS_BAD_PACKET
        else:
            # We are properly byte aligned with a response
            
            # Check if response packet
            if rx_buff[2] != self.STATUS_DATA:
                # Not a status packet, contains response data
                return self.STATUS_BAD_PACKET
            else:
                if rx_buff[3] == self.STATUS_BAD_CHECKSUM:
                    print('ERROR: BAD CHECKSUM')
                elif rx_buff[3] == self.STATUS_BAD_PARAMETER:
                    print('ERROR: BAD PARAMETER')
                elif rx_buff[3] == self.STATUS_UNKNOWN_COMMAND:
                    print('ERROR: UNKNOWN COMMAND')
                elif rx_buff[3] == self.STATUS_BAD_COMMAND:
                    print('ERROR: BAD COMMAND')
                elif rx_buff[3] == self.STATUS_SUCCESS:
                    # This is what we want to see...
                    return self.STATUS_SUCCESS
                else:
                    print('ERROR: UNKNOWN RESPONSE')
            
                return rx_buff[3]
        
    def send_command(self, cmd, arg=None): 
        # Start by formatting argument if applicable
        if cmd['arg_format'] == 'four_byte_1mv_units':
            cmd['command_arg'] = self.to_bytes_1mv_units(arg)
        elif cmd['arg_format'] == 'four_byte_0ma1_units':
            cmd['command_arg'] = self.to_bytes_0ma1_units(arg)
        elif cmd['arg_format'] == 'four_byte_1mw_units':
            cmd['command_arg'] = self.to_bytes_1mw_units(arg)
        elif cmd['arg_format'] == 'op_mode':
            cmd['command_arg'] = self.convert_op_mode(arg)
        else: pass
    
        self.tx_buff = []
        self.tx_buff.append(self.START_BYTE)             # Byte 0
        self.tx_buff.append(self.INSTRUMENT_ADDRESS)     # Byte 1
        self.tx_buff.append(cmd['command'])              # Byte 2
        self.tx_buff = self.tx_buff + cmd['command_arg']      # Bytes 3+
        self.tx_buff = self.tx_buff + ([self.RESERVED_BYTE] * (self.PACKET_LENGTH - 3 - len(cmd['command_arg']) - 1)) # Zero stuff unused bytes in packet
        
        self.tx_buff.append(0x00)                        # Placeholder for checksum
        
        self.tx_buff[-1] = self.calc_checksum(self.tx_buff)   # Insert checksum to end of packet
        
        # Clear UART buffers
        self.sp.reset_output_buffer()
        self.sp.reset_input_buffer()
        
        # Send the command, wait for all bytes to send
        self.sp.write(bytearray(self.tx_buff))
        self.sp.flush()
        
        # Receive response packet
        self.rx_buff = list(self.sp.read(self.PACKET_LENGTH))
        
        if cmd['command_return'] == 'status_packet':
            if self.check_status(self.rx_buff) != self.STATUS_SUCCESS:
                assert ValueError
        elif cmd['command_return'] == 'four_byte_1mv_units':
            return self.from_bytes_1mv_units(self.rx_buff[3:7])
        elif cmd['command_return'] == 'four_byte_0ma1_units':
            return self.from_bytes_0ma1_units(self.rx_buff[3:7])
        elif cmd['command_return'] == 'four_byte_1mw_units':
            return self.from_bytes_1mw_units(self.rx_buff[3:7])
        elif cmd['command_return'] == 'op_mode':
            return self.convert_op_mode(self.rx_buff[3])
        elif cmd['command_return'] == 'front_panel_struct':
            voltage = self.from_bytes_1mv_units(self.rx_buff[3:7])
            current = self.from_bytes_0ma1_units(self.rx_buff[7:11])
            power = self.from_bytes_1mw_units(self.rx_buff[11:14])
            return  {'voltage': voltage, 'current': current, 'power': power}
        elif cmd['command_return'] == 'mfg_info_struct':
            model = ''.join([chr(x) for x in self.rx_buff[3:7]])
            firmware = (int(self.rx_buff[8]) / 100.0) + int(self.rx_buff[9])
            serial = ''.join([chr(x) for x in self.rx_buff[10:20]])
            return  {'model': model, 'firmware': firmware, 'serial': serial}    
        else:
            print('ERROR: UNKNOWN RETURN DATA TYPE')
            assert ValueError
    
    # Short methods for easy control:
    
    def remote_control(self): self.send_command(self.cmd_remote_control)
    
    def local_control(self): self.send_command(self.cmd_local_control)
    
    def enable_load(self): self.send_command(self.cmd_enable_load)
    
    def disable_load(self): self.send_command(self.cmd_disable_load)
    
    def set_max_voltage_limit(self, max_voltage):
        self.send_command(self.cmd_set_max_voltage_limit, max_voltage)
        
    def get_max_voltage_limit(self):
        return self.send_command(self.cmd_get_max_voltage_limit)
        
    def set_max_current_limit(self, max_current):
        self.send_command(self.cmd_set_max_current_limit, max_current)
        
    def get_max_current_limit(self):
        return self.send_command(self.cmd_get_max_current_limit)
        
    def set_max_power_limit(self, max_power):
        self.send_command(self.cmd_set_max_power_limit, max_power)
        
    def get_max_power_limit(self):
        return self.send_command(self.cmd_get_max_power_limit)
        
    def set_mode(self, mode):
        # mode = 'CC', 'CV', 'CW', 'CR'
        self.send_command(self.cmd_set_mode, mode)
        
    def get_mode(self):
        return self.send_command(self.cmd_get_mode)
        
    def set_current_setpoint(self, current):
        self.send_command(self.cmd_set_cc_mode_current, current)
        
    def get_current_setpoint(self):
        return self.send_command(self.cmd_get_cc_mode_current)
        
    def set_voltage_setpoint(self, voltage):
        self.send_command(self.cmd_set_cv_mode_voltage, voltage)
        
    def get_voltage_setpoint(self):
        return self.send_command(self.cmd_get_cv_mode_voltage)
    
    def set_power_setpoint(self, power):
        self.send_command(self.cmd_set_cw_mode_power, power)
        
    def get_power_setpoint(self):
        return self.send_command(self.cmd_get_cw_mode_power)
     
    def set_resistance_setpoint(self, resistance):
        self.send_command(self.cmd_set_cr_mode_resistance, resistance)
        
    def get_resistance_setpoint(self):
        return self.send_command(self.cmd_get_cr_mode_resistance)
        
    def set_uvlo_setpoint(self, voltage):
        self.send_command(self.cmd_set_uvlo_voltage, voltage)
        
    def get_uvlo_setpoint(self):
        return self.send_command(self.cmd_get_uvlo_voltage)
        
    def get_present_values(self):
        return self.send_command(self.cmd_get_present_values)
        
    def get_mfg_info(self):
        return self.send_command(self.cmd_get_mfg_info)
    
    def __init__(self, device=device_default, baudrate=9600):
        # The 8500 instrument requires hardware flow control RTS and DTR signalling.
        # All packets to the 8500 are 26 bytes sent and 26 bytes received
        
        self.sp = serial.Serial(port=device, baudrate=baudrate, write_timeout=5)
