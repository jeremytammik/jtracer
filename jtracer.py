#!python3
'''
jmain.py - connect to tracer
connect to EPEver Tracer 3210AN charge controller via Serial Modbus RS485
based on
https://github.com/Charanmakkar/RS485-USB-SERIAL-READ
https://stackoverflow.com/questions/64251163/cant-connect-to-epsolar-tracer-3210an-charge-controller-from-windows-10-via-ser
https://trevorsullivan.net/2020/10/22/capture-and-analyze-solar-power-generation-metrics-with-influxdb/
EPEver PDF documentation /j/doc/hardware/manual/epever_tracer_3210an/rs485/a_or_bseriescontrollerprotocolv2.5.pdf
https://minimalmodbus.readthedocs.io/en/stable/apiminimalmodbus.html -- API for MinimalModbus
Jeremy Tammik, 2021-06-12
'''

from time import gmtime, sleep, strftime
import minimalmodbus

# Define the registers from the PDF documentation

PORT='/dev/tty.SLAB_USBtoUART' # MacOS
PORT='/dev/ttyUSB0' # Linux Mint
PV_VOLTAGE = 0x3100
PV_CURRENT = 0x3101
BATT_SOC = 0x311A # state of charge, the percentage of battery remaining capacity
BATT_VOLTAGE_MAX_DAY = 0x3302 # Maximum battery voltage today
BATT_VOLTAGE_MIN_DAY = 0x3303 # Minimum battery voltage today
KWH_CONSUMED_DAY_L = 0x3304 # Consumed energy today L
KWH_CONSUMED_DAY_H = 0x3305 # Consumed energy today H
KWH_CONSUMED_MONTH_L = 0x3306 # Consumed energy this month L
KWH_CONSUMED_MONTH_H = 0x3307 # Consumed energy this month H
KWH_CONSUMED_YEAR_L = 0x3308 # Consumed energy this year L
KWH_CONSUMED_YEAR_H = 0x3309 # Consumed energy this year H
KWH_CONSUMED_TOTAL_L = 0x330A # Total consumed energy L
KWH_CONSUMED_TOTAL_H = 0x330B # Total consumed energy H
KWH_DAY_L = 0x330C # Generated energy today L
KWH_DAY_H = 0x330D # Generated energy today H
KWH_MONTH_L = 0x330E # Generated energy this month L
KWH_MONTH_H = 0x330F # Generated energy this month H
KWH_YEAR_L = 0x3310 # Generated energy this year L
KWH_YEAR_H = 0x3311 # Generated energy this year H
KWH_TOTAL_L = 0x3312 # Total generated energy L
KWH_TOTAL_H = 0x3313 # Total generated energy H
BATT_VOLTAGE = 0x331A # Battery voltage
BATT_CURRENT_L = 0x331B # Battery current L
BATT_CURRENT_H = 0x331C # Battery current H

def setParameters( port, baudrate ):
  'set parameters for communication'
  try:
    ins = minimalmodbus.Instrument(port, 1, debug=False)

    ins.serial.baudrate = baudrate
    #ins.serial.bytesize = 8
    #ins.serial.stopbits = 1
    #ins.serial.parity = serial.PARITY_NONE
    ins.serial.timeout = 1
    #
    #ins.mode = minimalmodbus.MODE_RTU
    #ins.clear_buffers_before_each_transaction = True

    print(( 'setParameters:', ins ))
    return ins
  except:
    # if no device found
    print( 'setParameters: Device NOT connected' )

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
instrument = setParameters( PORT, baudrate )

if instrument:

  t = strftime('%Y-%m-%d %H:%M:%S', gmtime())
  
  pv_voltage = readint( PV_VOLTAGE )
  pv_current = readint( PV_CURRENT )
  batt_voltage = readint( BATT_VOLTAGE )
  batt_current_l = readint( BATT_CURRENT_L )
  batt_current_h = readint( BATT_CURRENT_H )
  batt_soc = readint( BATT_SOC )
  batt_voltage_max_day = readint( BATT_VOLTAGE_MAX_DAY )
  batt_voltage_min_day = readint( BATT_VOLTAGE_MIN_DAY )
  kwh_day_l = readint( KWH_DAY_L )
  kwh_day_h = readint( KWH_DAY_H )
  kwh_month_l = readint( KWH_MONTH_L )
  kwh_month_h = readint( KWH_MONTH_H )
  kwh_year_l = readint( KWH_YEAR_L )
  kwh_year_h = readint( KWH_YEAR_H )
  kwh_total_l = readint( KWH_TOTAL_L )
  kwh_total_h = readint( KWH_TOTAL_H )
  kwh_consumed_day_l = readint( KWH_CONSUMED_DAY_L )
  kwh_consumed_day_h = readint( KWH_CONSUMED_DAY_H )
  kwh_consumed_month_l = readint( KWH_CONSUMED_MONTH_L )
  kwh_consumed_month_h = readint( KWH_CONSUMED_MONTH_H )
  kwh_consumed_year_l = readint( KWH_CONSUMED_YEAR_L )
  kwh_consumed_year_h = readint( KWH_CONSUMED_YEAR_H )
  kwh_consumed_total_l = readint( KWH_CONSUMED_TOTAL_L )
  kwh_consumed_total_h = readint( KWH_CONSUMED_TOTAL_H )  

  print(t)
  print('PV:', pv_voltage, 'V', pv_current, 'A', pv_voltage * pv_current, 'W') 
  print('Battery:', batt_voltage, 'V', batt_current_l, 'A', batt_voltage * batt_current_l, 'W', batt_soc, '%')
  print('Day Min', batt_voltage_min_day, 'V, Max', batt_voltage_max_day, 'V')
  print('kWh day/month/year/total', kwh_day_l, kwh_month_l, kwh_year_l, kwh_total_l)
  print('Consumed kWh day/month/year/total', kwh_consumed_day_l, kwh_consumed_month_l, kwh_consumed_year_l, kwh_consumed_total_l)

  # Loop forever
  
  while (1):
    t = strftime('%Y-%m-%d %H:%M:%S', gmtime())
    
    pv_voltage = readint( PV_VOLTAGE )
    pv_current = readint( PV_CURRENT )
    batt_voltage = readint( BATT_VOLTAGE )
    batt_current_l = readint( BATT_CURRENT_L )
    #batt_current_h = readint( BATT_CURRENT_H )
    batt_soc = readint( BATT_SOC )
  
    print('%s -- PV: %5.2f V %4.2f A %6.2f W -- Battery: %5.2f V %5.2f A %6.2f W %.0f %s' % (t, pv_voltage, pv_current, pv_voltage * pv_current, batt_voltage, batt_current_l, batt_voltage * batt_current_l, 100 * batt_soc, '%'))
  
    # break
  
    # Time delay of 10 seconds after each run
    
    sleep(10)
