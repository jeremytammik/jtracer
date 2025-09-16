#!/usr/bin/env python3
import minimalmodbus, serial, time, sys

PORT="/dev/ttyUSB0"; UNIT_ID=1; BAUDRATE=115200; TIMEOUT_S=1.2; DEBUG=True
REG_BATTERY_CAPACITY   = 36865  # 0x9001 (Ah)
REG_EQUALIZE_VOLT      = 36870  # 0x9006
REG_BOOST_VOLT         = 36871  # 0x9007
REG_FLOAT_VOLT         = 36872  # 0x9008

def init_inst():
    inst=minimalmodbus.Instrument(PORT, UNIT_ID, mode=minimalmodbus.MODE_RTU)
    inst.serial.baudrate=BAUDRATE; inst.serial.bytesize=8; inst.serial.parity=serial.PARITY_NONE
    inst.serial.stopbits=1; inst.serial.timeout=TIMEOUT_S
    inst.clear_buffers_before_each_transaction=True; inst.debug=DEBUG
    return inst

def r_u16(inst, reg): return inst.read_register(reg, 0, functioncode=3, signed=False)
def r_v(inst, reg): return r_u16(inst, reg)/100.0

def try_fc06_same(inst, reg, label, scale=1):
    try:
        cur = r_u16(inst, reg)
        print(f"Reading {label}: OK (raw={cur})")
        time.sleep(0.02)
        inst.write_register(reg, cur, 0, functioncode=6)
        time.sleep(0.5)
        rb = r_u16(inst, reg)
        print(f"FC06 write-back SAME to {label}: OK (readback={rb})")
        return True
    except Exception as e:
        print(f"FC06 write-back SAME to {label}: FAIL ({e})")
        return False

def try_fc16_same_block(inst, start_reg, labels):
    try:
        vals=[r_u16(inst, start_reg+i) for i in range(len(labels))]
        print("Reading block", labels, "OK:", vals)
        time.sleep(0.02)
        inst.write_registers(start_reg, vals)  # FC16
        time.sleep(0.5)
        rb=[r_u16(inst, start_reg+i) for i in range(len(labels))]
        print("FC16 write-back SAME block to", labels, "OK:", rb)
        return True
    except Exception as e:
        print("FC16 write-back SAME block to", labels, "FAIL:", e)
        return False

def main():
    inst=init_inst()
    print("— Diagnostic: Modbus write permissions —")

    cap_ok = try_fc06_same(inst, REG_BATTERY_CAPACITY, "Battery Capacity (0x9001)")
    fl_ok  = try_fc06_same(inst, REG_FLOAT_VOLT, "Float Voltage (0x9008)")
    blk_ok = try_fc16_same_block(inst, REG_EQUALIZE_VOLT, ["Eq(0x9006)","Boost(0x9007)","Float(0x9008)"])

    print("\nSummary:")
    print(f"  FC06 Battery Capacity same-value write: {'OK' if cap_ok else 'FAIL'}")
    print(f"  FC06 Float same-value write:           {'OK' if fl_ok else 'FAIL'}")
    print(f"  FC16 Eq/Boost/Float no-op block:       {'OK' if blk_ok else 'FAIL'}")

    if not cap_ok and not fl_ok and not blk_ok:
        print("\nConclusion: Device is rejecting parameter writes via Modbus (likely locked).")
        print("Actions:")
        print("  - Ensure no MT50/eBox or other RS-485 device is connected while running this.")
        print("  - In EPEver Solar Station Monitor, check if parameter setting is enabled for PC/COM and try changing Float there.")
        print("  - Share firmware version shown by the app; some AN firmwares require enabling PC parameter control before Modbus writes.")
    elif cap_ok and not fl_ok and not blk_ok:
        print("\nConclusion: General user params (e.g., capacity) writable, but charge setpoints blocked by firmware policy.")
        print("Actions:")
        print("  - Use the EPEver app once to change any charge setpoint; if it works, we can try to mirror that sequence.")
        print("  - If the app also fails, the firmware enforces local-only changes for voltages.")
    else:
        print("\nMixed results; please share this full debug output so we can adjust the sequence.")

if __name__=="__main__":
    main()