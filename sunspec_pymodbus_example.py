#!/usr/bin/env python3
# coding: utf-8

# Example code to read SunSpec inverter information over Modbus TCP 

import struct
import time
from pymodbus.client.sync import ModbusTcpClient # for pymodbus 2.x
#from pymodbus.client import ModbusTcpClient # for pymodbus 3.x

def pymodbus_connect_tcp (host, port = 502, modbus_id = 1):
    # Connect to a SunSpec-inverter over Modbus TCP using pymodbus
    client = ModbusTcpClient(host = host, port = port, timeout = 10)
    return {'pymodbus_client': client, 'ip': host, 'port': port, 'modbus_id': modbus_id}

def read_modbus (device, reg_start, reg_vals):
    # Read modbus registers (currently this uses Modbus TCP directly, but other routes are possible)
    client = dev['pymodbus_client']
    rr = client.read_holding_registers(reg_start, reg_vals, unit=dev['modbus_id'])
    if rr.isError():
        return None
    return rr.registers

def regbytes (int_vals):
    # Convert a list of modbus register values into a block of bytes
    byteblock = bytes()
    for val in int_vals:
        short = struct.pack('!H', int(val)) # pack unsigned short int (network byte order)
        byteblock += short
    return byteblock

def bytestostr (byteblock):
    # Convert a block of bytes into a UTF-8 string
    return byteblock.split(b'\x00')[0].decode('UTF8')

def regtoint16 (val):
    # Convert an unsigned 16-bit register value into a signed 16-bit integer
    return struct.unpack('!h', struct.pack('!H', int(val)))[0]

def bytestoint16 (byteblock):
    # Convert a block of bytes into a list of signed 16-bit integers
    return struct.unpack('!h', byteblock)[0] # See: https://docs.python.org/3/library/struct.html

def bytestouint32 (byteblock):
    # Convert a block of bytes into a list of unsigned 32-bit integers
    return struct.unpack('!I', byteblock)[0] # See: https://docs.python.org/3/library/struct.html

def regstofloat32 (regs):
    # Convert a list of modbus register values into a list of 32-bit floating point values
    # We need to swap the two register values before we attempt to unpack the 32-bit float
    if len(regs) < 2:
        return None
    swapped = regs[1], regs[0]
    return struct.unpack('!f', regbytes(swapped))[0] # See: https://docs.python.org/3/library/struct.html

def sunspec_get_static (dev):

    # Read static inverter information (mostly) from the SunSpec Common Model register block
    
    static = {}
    
    # Read the header of the SunSpec Common block
    response = read_modbus(dev, 40000, 4)
    if response:
        bin_resp = regbytes(response)
        mbmap_header = bytestostr(bin_resp[:4]) # First four bytes 'SunS' uniquely identify this as a SunSpec MODBUS Map
        cmb_header = response[2] # Uniquely identifies this as a SunSpec Common Model Block, if this is 1
        cmb_len = response[3] # Length of block in 16-bit registers
    else:
        return None
        
    # Read the rest of the SunSpec Common block
    response = read_modbus(dev, 40004, cmb_len)
    if response:
        static['manufacturer'] = bytestostr(regbytes(response[:16])).strip() # The first 16 registers are C_Manufacturer
        static['model'] = bytestostr(regbytes(response[16:32])) # The next 16 registers are C_Model
        static['version'] = bytestostr(regbytes(response[40:48])) # These 8 registers are C_Version
        static['serial'] = bytestostr(regbytes(response[48:64])) # These 16 registers are C_SerialNumber
        if static['manufacturer'] == 'SolarEdge':
           # For SolarEdge, read the max. active power in W from register 0xf304 (Float32)
            response = read_modbus(dev, 0xf304, 2)
            if response:
                static['P_max'] = round(regstofloat32(response))
            
    # Read phases from the header of the device specific block
    response = read_modbus(dev, 40069, 1)
    if response:
        static['phases'] = response[0] - 100    
    
    return static


def sunspec_get_vars (dev):

    # Read dynamic inverter variables from the SunSpec device specific register block
    
    var = {}
    
    # Read header of device specific block
    response = read_modbus(dev, 40069, 2)
    if response:
        phases = response[0] - 100
        dsb_len = response[1]
    else:
        return None
        
    # Read rest of device specific block
    response = read_modbus(dev, 40071, dsb_len)
    
    if response:
        
        # Decode variables
        
        sf_I = (10 ** regtoint16(response[4])) # I_AC_Current_SF
        var['I_AC'] = int(response[0]) * sf_I
        var['I_L1'] = int(response[1]) * sf_I
        if phases >= 2:
            var['I_L2'] = int(response[2]) * sf_I
        if phases >= 3:
            var['I_L3'] = int(response[3]) * sf_I
        
        sf_U = (10 ** regtoint16(response[11])) # I_AC_Voltage_SF
        if phases == 1:
            var['U_L1_N'] = int(response[5]) * sf_U
        else:
            var['U_L1_L2'] = int(response[5]) * sf_U
            var['U_L2_L3'] = int(response[6]) * sf_U
            var['U_L3_L1'] = int(response[7]) * sf_U
            var['U_L1_N'] = int(response[8]) * sf_U
            var['U_L2_N'] = int(response[9]) * sf_U
            var['U_L3_N'] = int(response[10]) * sf_U
        
        sf_P = (10 ** regtoint16(response[13])) # I_AC_Power_SF
        var['P_AC'] = int(response[12]) * sf_P
        
        sf_F = (10 ** regtoint16(response[15])) # I_AC_Frequency_SF
        var['F'] = int(response[14]) * sf_F
        
        sf_VA = (10 ** regtoint16(response[17])) # I_AC_VA_SF
        var['VA'] = int(response[16]) * sf_VA
        
        sf_VAR = (10 ** regtoint16(response[19])) # I_AC_VAR_SF
        var['VAR'] = int(response[18]) * sf_VAR
        
        sf_PF = (10 ** regtoint16(response[21])) # I_AC_PF_SF
        var['pf'] = int(response[20]) * sf_PF
        
        sf_E = (10 ** regtoint16(response[24])) # I_AC_Energy_WH_SF
        var['E_Wh'] = bytestouint32(regbytes(response[22:24])) * sf_E
        
        sf_I_DC = (10 ** regtoint16(response[26])) # I_DC_Current_SF
        var['I_DC'] = int(response[25]) * sf_I_DC
        
        sf_U_DC = (10 ** regtoint16(response[28])) # I_DC_Voltage_SF
        var['U_DC'] = int(response[27]) * sf_U_DC
        
        sf_P_DC = (10 ** regtoint16(response[30])) # I_DC_Power_SF
        var['P_DC'] = int(response[29]) * sf_P_DC
        
        sf_T = (10 ** regtoint16(response[35])) # I_Temp_SF
        var['T'] = int(response[32]) * sf_T
        
        status = int(response[36])
        var['status'] = status
        status_map = {1: 'I_STATUS_OFF', 2: 'I_STATUS_SLEEPING', 3:'I_STATUS_STARTING', 4: 'I_STATUS_MPPT', 5: 'I_STATUS_THROTTLED', 6: 'I_STATUS_SHUTTING_DOWN', 7: 'I_STATUS_FAULT', 8: 'I_STATUS_STANDBY'}
        var['status_string'] = status_map[status]
        
        var['status_vendor'] = int(response[37])

    return var


# Make sure you enable Modbus TCP on your inverter (for SolarEdge in SetApp: Site Communication -> Modbus TCP -> Enable)

# Change these to the IP-address and modbus-TCP-port of your inverter

host = '10.0.10.71'
port = 502  # Is usually 502, but tends to be 1502 for newer SolarEdge-inverters

# Connect to the inverter

dev = pymodbus_connect_tcp(host, port = port)

# Read and print static information

for k, v in sunspec_get_static(dev).items():
    print(k + ':', v)

# Read and print dynamic variables in a loop, every 10 seconds

while True:
    
    for k, v in sunspec_get_vars(dev).items():
        print(k + ':', v)
    
    time.sleep(10)
    
