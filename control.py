import json
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.constants import Endian
import time
import struct
import datetime 
import paho.mqtt.client as mqtt
import threading

meter_ip = '192.168.100.2'
meter_addr = 0
power_address = 40084
control_adress = 40295
num_of_inv = 6
upper_limit = 5
normal = 3
lower_limit = 1.5
power_grid = 0
inv_active = []
power_inv = []

def value_decode(registers, typeString, size):
	decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder= Endian.Big, wordorder=Endian.Big)
	if (typeString == "int16"):
		value = decoder.decode_16bit_int()
	elif (typeString == "uint16"):
		value = decoder.decode_16bit_uint()
	elif (typeString == "int32"):
		value = decoder.decode_32bit_int()
	elif (typeString == "uint32"):
		value = decoder.decode_32bit_uint()
	elif (typeString == "float16"):
		value = decoder.decode_16bit_float()
	elif (typeString == "float32"):
		value = decoder.decode_32bit_float()
	elif (typeString == "string"):
		value = decoder.decode_string(size).decode()
	else:
		value = "Invalid type"

	return value

def read_data():
    global power_grid, power_inv, inv_active
    try:    # đọc giá trị đồng hồ
        client = ModbusTcpClient(meter_ip, port=502, timeout=1)
        client.connect
        data = client.read_holding_registers(meter_addr, 1, unit=1)
        power_grid = value_decode(data,"float32",1)*1000
    except:
        print("The process of reading the Selec meter value is experiencing an error")   
    # for i  in range(1, num_of_inv):
        # ip = '192.168.100.' + str(10+i)
    for i  in range(1, 1):
        ip = '192.168.100.18'
        client1 = ModbusTcpClient(ip, port=502, timeout=1)
        client1.connect
        data1 = client.read_holding_registers(power_address, 1, unit=1)
        power_inv.append(round(value_decode(data1, "int16", 1))/10)
        print(power_inv)
        inv_active.append(ip)
    print("The number of inverters that can be controlled is ",len(power_inv))


def zero_export_logic():
    # inverter_check(num_of_inv)
    global power_grid, inv_active
    read_data()
    # inv_active = len(power_inv)
    try:    
        if power_grid <= lower_limit:
            power_control = (normal - power_grid)/num_of_inv
            # power_control = (normal - power_grid)/len(inv_active)
            for ip,value in zip(inv_active,power_inv):
                try:
           
                    client = ModbusTcpClient(ip, port=502, timeout=1)
                    client.connect()
                    if value + power_control >= 0 or value + power_control <= 100000:
                        response = client.write_register(control_adress, value + power_control, unit=1)  
                    if value + power_control < 0:
                        response = client.write_register(control_adress, 0, unit=1)  
                    if value + power_control > 100000:
                        response = client.write_register(control_adress,100000, unit=1) 
                    print("Setup completed successfully ",ip)
                except:
                    inv_active.append(ip)
                    power_grid.append(value)

        if power_grid >= upper_limit:
            power_control = (normal - power_grid)/num_of_inv
            # power_control = (power_grid - normal)/len(inv_active)
            for ip,value in zip(inv_active,power_inv):
                try:
                    client = ModbusTcpClient(ip, port=502, timeout=1)
                    client.connect()
                    if value + power_control >= 0 or value + power_control <= 100000:
                        response = client.write_register(control_adress, value - power_control, unit=1)  
                    if value + power_control < 0:
                        response = client.write_register(control_adress, 0, unit=1)  
                    if value + power_control > 100000:
                        response = client.write_register(control_adress,100000, unit=1) 
                    print("Setup completed successfully ",ip)
                except:
                    inv_active.append(ip)
                    power_grid.append(value)    
    except:
        print('Controller function error')
    
        

if __name__ == "__main__":
    while True:
        zero_export_logic()
        time.sleep(10)  
