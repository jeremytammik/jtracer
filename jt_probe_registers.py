#!/usr/bin/env python3
"""
Probe EPEVER Tracer registers around 0x9000–0x9010
to verify correct Modbus register addresses.
"""

import minimalmodbus
import serial
import time

PORT = "/dev/ttyUSB0"   # adjust if needed
UNIT_ID = 1
BAUDRATE = 115200       # try 9600 if 115200 fails

def init_instrument():
  inst = minimalmodbus.Instrument(PORT, UNIT_ID, mode=minimalmodbus.MODE_RTU)
  inst.serial.baudrate = BAUDRATE
  inst.serial.bytesize = 8
  inst.serial.parity   = serial.PARITY_NONE
  inst.serial.stopbits = 1
  inst.serial.timeout  = 1
  inst.clear_buffers_before_each_transaction = True
  inst.debug = False  # set True if you want raw Modbus frames
  return inst

def main():
  inst = init_instrument()

  start_reg = 36864  # 0x9000
  end_reg   = 36890  # a few past 0x9010

  print(f"Probing registers {start_reg}–{end_reg} ...\n")

  for reg in range(start_reg, end_reg + 1):
    try:
      val = inst.read_register(reg, 0, functioncode=3)
      print(f"Register {reg} (0x{reg:04X}): {val}")
      time.sleep(0.1)
    except Exception as e:
      print(f"Register {reg} (0x{reg:04X}): ERROR ({e})")

if __name__ == "__main__":
  main()
