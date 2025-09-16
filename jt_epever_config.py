#!/usr/bin/env python3
#
# ~/w/src/python/jtracer/jt_epever_config.py
#
# ChatGPT generated: 
# https://chatgpt.com/s/t_68c906f8d8a88191b3827d8d4e41ee86
#
# Copyright 2025-09-16 Jeremy Tammik
#
"""
EPEVER Tracer Settings Utility
- Connects via Modbus RTU over RS-485
- Reads current voltage settings
- Sets Battery Type to User/Custom
- Updates charging voltages safely (low → high order)
"""

import minimalmodbus
import serial
import time

# ---------------- CONFIG ----------------
PORT = "/dev/ttyUSB0"   # serial port of RS-485 adapter
UNIT_ID = 1             # Modbus slave ID (usually 1)
BAUDRATE = 115200       # try 9600 if communication fails

# Verified register addresses (decimal)
REG_OVERVOLT_RECONNECT = 36867  # 0x9003
REG_CHARGING_LIMIT     = 36868  # 0x9004
REG_EQUALIZE_VOLT      = 36870  # 0x9006
REG_BOOST_VOLT         = 36871  # 0x9007
REG_FLOAT_VOLT         = 36872  # 0x9008
REG_BATTERY_TYPE       = 36880  # 0x9010

# Desired settings (Volts)
NEW_CHARGING_LIMIT = 28.00
NEW_EQUALIZE       = 27.60
NEW_BOOST          = 27.40
NEW_FLOAT          = 27.00
NEW_BATTERY_TYPE   = 3  # User/Custom
# ----------------------------------------


def init_instrument():
  inst = minimalmodbus.Instrument(PORT, UNIT_ID, mode=minimalmodbus.MODE_RTU)
  inst.serial.baudrate = BAUDRATE
  inst.serial.bytesize = 8
  inst.serial.parity   = serial.PARITY_NONE
  inst.serial.stopbits = 1
  inst.serial.timeout  = 1
  inst.clear_buffers_before_each_transaction = True
  return inst


def read_voltage(inst, reg):
  """Read raw register and convert to volts."""
  val = inst.read_register(reg, 0, functioncode=3, signed=False)
  return val / 100.0


def write_voltage(inst, reg, volts):
  """Write volts×100 to register and verify."""
  value = int(round(volts * 100))
  inst.write_register(reg, value, 0, functioncode=16)
  time.sleep(0.2)
  return read_voltage(inst, reg)


def dump_settings(inst):
  print("\nCurrent Charger Settings:")
  for name, reg in [
    ("Over-voltage Reconnect", REG_OVERVOLT_RECONNECT),
    ("Charging Limit Voltage", REG_CHARGING_LIMIT),
    ("Equalize Voltage",       REG_EQUALIZE_VOLT),
    ("Boost Voltage",          REG_BOOST_VOLT),
    ("Float Voltage",          REG_FLOAT_VOLT),
    ("Battery Type",           REG_BATTERY_TYPE),
  ]:
    try:
      val = inst.read_register(reg, 0, functioncode=3)
      if reg == REG_BATTERY_TYPE:
        btypes = {0: "Sealed", 1: "Gel", 2: "Flooded", 3: "User"}
        print(f"  {name:25s}: {val} ({btypes.get(val,'Unknown')})")
      else:
        print(f"  {name:25s}: {val/100:.2f} V")
    except Exception as e:
      print(f"  {name:25s}: ERROR ({e})")
  print()


def main():
  inst = init_instrument()

  print("Reading current settings...")
  dump_settings(inst)

  # Step 1: Ensure battery type is User/Custom
  print("Setting battery type to User/Custom...")
  try:
    inst.write_register(REG_BATTERY_TYPE, NEW_BATTERY_TYPE, 0, functioncode=16)
    time.sleep(0.2)
    bt = inst.read_register(REG_BATTERY_TYPE, 0, functioncode=3)
    if bt == NEW_BATTERY_TYPE:
      print("Battery type successfully set to User/Custom.\n")
    else:
      print(f"Warning: battery type readback = {bt}, not User/Custom!\n")
  except Exception as e:
    print("Error setting battery type:", e)
    return

  # Step 2: Write voltages in safe order (low → high)
  print("Writing new voltage settings (safe order)...")
  try:
    flt   = write_voltage(inst, REG_FLOAT_VOLT,     NEW_FLOAT)
    #boost = write_voltage(inst, REG_BOOST_VOLT,     NEW_BOOST)
    #eq    = write_voltage(inst, REG_EQUALIZE_VOLT,  NEW_EQUALIZE)
    #cl    = write_voltage(inst, REG_CHARGING_LIMIT, NEW_CHARGING_LIMIT)

    print("New values written:")
    print(f"  Float Voltage           : {flt:.2f} V")
    print(f"  Boost Voltage           : {boost:.2f} V")
    print(f"  Equalize Voltage        : {eq:.2f} V")
    print(f"  Charging Limit Voltage  : {cl:.2f} V")
  except Exception as e:
    print("Error writing settings:", e)


if __name__ == "__main__":
  main()
