'''
jmain.py - connect to tracer
connect to EPEver Tracer 3210AN charge controller via Serial Modbus RS485
based on
https://github.com/Charanmakkar/RS485-USB-SERIAL-READ
https://stackoverflow.com/questions/64251163/cant-connect-to-epsolar-tracer-3210an-charge-controller-from-windows-10-via-ser
https://trevorsullivan.net/2020/10/22/capture-and-analyze-solar-power-generation-metrics-with-influxdb/
EPEver PDF documentation /j/doc/hardware/manual/epever_tracer_3210an/rs485/a_or_bseriescontrollerprotocolv2.5.pdf
Jeremy Tammik, 2021-06-12
'''

from time import gmtime, sleep, strftime
import minimalmodbus # , serial, time

# Define the registers from the PDF documentation

PV_VOLTAGE = 0x3100
PV_CURRENT = 0x3101
BATT_SOC = 0x311A # state of charge, the percentage of battery remaining capacity
BATT_VOLTAGE_MAX_DAY = 0x3302 # Maximum battery voltage today
BATT_VOLTAGE_MIN_DAY = 0x3303 # Minimum battery voltage today
x = 0x3304 # Consumed energy today L
x = 0x3305 # Consumed energy today H
x = 0x3306 # Consumed energy this month L
x = 0x3307 # Consumed energy this month H
x = 0x3308 # Consumed energy this year L
x = 0x3309 # Consumed energy this year H
x = 0x330A # Total consumed energy L
x = 0x330B # Total consumed energy H
x = 0x330C # Generated energy today L
x = 0x330D # Generated energy today H
x = 0x330E # Generated energy this month L
x = 0x330F # Generated energy this month H
x = 0x3310 # Generated energy this year L
x = 0x3311 # Generated energy this year H
x = 0x3312 # Total generated energy L
x = 0x3313 # Total generated energy H
BATT_VOLTAGE = 0x331A # Battery voltage
BATT_CURRENT_L = 0x331B # Battery current L
BATT_CURRENT_H = 0x331C # Battery current H

def setParameters(x,b):
  'set parameters for communication'
  try:
    ins = minimalmodbus.Instrument(x, 1, debug=False)

    ins.serial.baudrate = b
    #ins.serial.bytesize = 8
    #ins.serial.stopbits = 1
    #ins.serial.parity = serial.PARITY_NONE
    ins.serial.timeout = 1
    #
    #ins.mode = minimalmodbus.MODE_RTU
    #ins.clear_buffers_before_each_transaction = True

    print 'setParameters:', ins
    return ins
  except:
    # if no device found
    print 'setParameters: Device NOT connected'

def readint(r):
  'read data from RS485 connnection at a specific register'
  try:
    #data = instrument.read_register(a,10,3)
    #data = instrument.read_register(a)
    x = instrument.read_register(r, 2, 4, False) 
    return x
  except IOError:
    return 'Failed to read register from instrument: ' + hex(r)

# Set RS485 communication parameters

baudrate = 115200

#instrument = setParameters('COM port name', Baud rate, Slave Address)
#instrument = setParameters('COM21', 19200, 111)
instrument = setParameters( '/dev/tty.SLAB_USBtoUART', baudrate )

if instrument:

  # Loop forever
  
  while (1):
    t = strftime('%Y-%m-%d %H:%M:%S', gmtime())
    print t, 'PV Voltage', readint( PV_VOLTAGE )
    print t, 'PV Current', readint( PV_CURRENT )
    print t, 'Battery Voltage', readint( BATT_VOLTAGE ), 'V'
    print t, 'Battery Current', readint( BATT_CURRENT_L ), 'A'
    #print t, 'Battery Current H', readint( BATT_CURRENT_H )
    print t, 'Percent charged', readint( BATT_SOC ), '%'
    print t, 'Day Voltage Min', readint( BATT_VOLTAGE_MIN_DAY ), 'V'
    print t, 'Day Voltage Max', readint( BATT_VOLTAGE_MAX_DAY ), 'V'
  
    break
  
    # Time delay of 10 seconds after each run
    
    sleep(10)
