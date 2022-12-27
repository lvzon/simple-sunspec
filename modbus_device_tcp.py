#!/usr/bin/env python3
# coding: utf-8

# Interact with a modbus-device over TCP using Pymodbus 2.x (the version available in e.g. Ubuntu 22.04 LTS)

from pymodbus.client.sync import ModbusTcpClient # for pymodbus 2.x

class ModbusClientTCP():
    
    def __init__ (self, host, port = 502, modbus_id = 1, timeout = 10):
        self.host = host
        self.port = port
        self.dev_id = modbus_id
        self.timeout = timeout

    def connect (self):
        self.client = ModbusTcpClient(host = self.host, port = self.port, timeout = self.timeout)
        if self.client:
            return True
        else:
            return False

    def read (self, reg_start, registers = 1):
        rr = self.client.read_holding_registers(reg_start, registers, unit = self.dev_id)
        if rr.isError():
            return None
        return rr.registers
    
    def write (self, reg_start, values):
        count = len(values)
        if count == 1:
            # Use function code 0x06 to write a single register
            wr = self.client.write_register(reg_start, values[0], unit = self.dev_id)
        elif count > 1:
            # Use function code 0x10 to write multiple registers
            wr = self.client.write_registers(reg_start, registers, unit = self.dev_id)
        else:
            return 0
            
        if wr.isError():
            return 0
            
        return count
    
    def write_single (self, reg_start, value):
        # Use function code 0x06 to write a single register
        wr = self.client.write_register(reg_start, value, unit = self.dev_id)
        if wr.isError():
            return 0
        return 1;
