#!/usr/bin/env python3
#
# EPEVER Tracer 3210AN Settings Utility (24V LiFePO4, staged + atomic writes @115200)
#
# Strategy:
#  - Keep baud at 115200 (your unit communicates reliably at this speed).
#  - Set battery type = USER (FC06).
#  - Probe FC16 with a no-op write on 0x9006..0x9008 to confirm block writes are allowed.
#  - Stage writes to satisfy constraints and avoid exception 04:
#      A) Raise Float to a temporary safe level (>= BR + 1.20 V, default 28.0 V).
#      B) Write Eq/Boost/Float atomically (FC16) to 28.4/28.4/<temp>.
#      C) Lower Float to final 27.60 V (>= BR + 1.20 V).
#
import minimalmodbus
import serial
import time
import sys

# ---------------- CONFIG ----------------
PORT = "/dev/ttyUSB0"
UNIT_ID = 1
BAUDRATE = 115200
TIMEOUT_S = 1.2
DEBUG = True

# Registers (decimal for EPEver A/AN)
REG_OVERVOLT_RECONNECT = 36867  # 0x9003 (read)
REG_CHARGING_LIMIT     = 36868  # 0x9004 (write FC06 if adjusted)
REG_OVERVOLT_DISCONNECT= 36869  # 0x9005 (write FC06 if adjusted)
REG_EQUALIZE_VOLT      = 36870  # 0x9006 (block write start)
REG_BOOST_VOLT         = 36871  # 0x9007
REG_FLOAT_VOLT         = 36872  # 0x9008
REG_BOOST_RECONNECT    = 36873  # 0x9009 (Charging Return) — treat read-only
REG_BATTERY_TYPE       = 36880  # 0x9010

# 24V LiFePO4 targets (constraints applied at runtime)
NEW_BATTERY_TYPE       = 3      # USER
EQ_TARGET              = 28.4   # V
BOOST_TARGET           = 28.4   # V
FLOAT_FINAL            = 27.6   # V (>= BR + 1.20)
FLOAT_TEMP_RAISE       = 28.0   # V (temporary raise for staging)
MIN_FLOAT_MARGIN_V     = 1.20   # Float >= BR + margin

PRE_WRITE_SLEEP_S      = 0.02
POST_WRITE_SLEEP_S     = 0.60
# ----------------------------------------


def init_instrument():
    inst = minimalmodbus.Instrument(PORT, UNIT_ID, mode=minimalmodbus.MODE_RTU)
    inst.serial.baudrate = BAUDRATE
    inst.serial.bytesize = 8
    inst.serial.parity   = serial.PARITY_NONE
    inst.serial.stopbits = 1
    inst.serial.timeout  = TIMEOUT_S
    inst.clear_buffers_before_each_transaction = True
    inst.debug = DEBUG
    return inst


def sleep_brief(): time.sleep(PRE_WRITE_SLEEP_S)
def sleep_settle(): time.sleep(POST_WRITE_SLEEP_S)


def r_u16(inst, reg):
    return inst.read_register(reg, 0, functioncode=3, signed=False)


def r_v(inst, reg):
    return r_u16(inst, reg) / 100.0


def w_u16_fc06(inst, reg, value):
    sleep_brief()
    inst.write_register(reg, value, 0, functioncode=6)
    sleep_settle()


def w_v_fc06(inst, reg, volts):
    w_u16_fc06(inst, reg, int(round(volts * 100)))
    return r_v(inst, reg)


def w_block_fc16(inst, start_reg, values_u16):
    sleep_brief()
    inst.write_registers(start_reg, values_u16)  # FC16
    sleep_settle()


def dump_settings(inst, header="Current Charger Settings"):
    print(f"\n{header}:")
    for name, reg, is_volt in [
        ("Over-voltage Reconnect", REG_OVERVOLT_RECONNECT, True),
        ("Charging Limit Voltage", REG_CHARGING_LIMIT,     True),
        ("Over-voltage Disconnect",REG_OVERVOLT_DISCONNECT,True),
        ("Equalize Voltage",       REG_EQUALIZE_VOLT,      True),
        ("Boost Voltage",          REG_BOOST_VOLT,         True),
        ("Float Voltage",          REG_FLOAT_VOLT,         True),
        ("Boost Reconnect Voltage",REG_BOOST_RECONNECT,    True),
        ("Battery Type",           REG_BATTERY_TYPE,       False),
    ]:
        try:
            val = r_u16(inst, reg)
            if is_volt:
                print(f"  {name:25s}: {val/100:.2f} V")
            else:
                btypes = {0: "Sealed", 1: "Gel", 2: "Flooded", 3: "User"}
                print(f"  {name:25s}: {val} ({btypes.get(val,'Unknown')})")
        except Exception as e:
            print(f"  {name:25s}: ERROR ({e})")
    print()


def compute_targets(inst):
    # Read current values
    ov_reconn = r_v(inst, REG_OVERVOLT_RECONNECT)
    chg_limit = r_v(inst, REG_CHARGING_LIMIT)
    ov_disc   = r_v(inst, REG_OVERVOLT_DISCONNECT)
    eq_now    = r_v(inst, REG_EQUALIZE_VOLT)
    bo_now    = r_v(inst, REG_BOOST_VOLT)
    fl_now    = r_v(inst, REG_FLOAT_VOLT)
    br_now    = r_v(inst, REG_BOOST_RECONNECT)

    min_float_allowed = round(br_now + MIN_FLOAT_MARGIN_V, 2)

    # Stage A temp float
    fl_temp = max(FLOAT_TEMP_RAISE, min_float_allowed)

    # Stage B block targets (keep float at temp to ease constraints)
    eq_blk = max(EQ_TARGET, fl_temp)
    bo_blk = max(BOOST_TARGET, fl_temp)
    fl_blk = fl_temp

    # Stage C final float
    fl_final = max(FLOAT_FINAL, min_float_allowed)

    # Keep CL and OVD consistent and safe
    chg_limit_new = chg_limit
    if chg_limit_new < eq_blk:
        chg_limit_new = eq_blk
    ov_disc_new = ov_disc
    if ov_disc_new <= chg_limit_new:
        ov_disc_new = round(chg_limit_new + 0.30, 2)

    return {
        "ov_reconn": ov_reconn,
        "chg_limit_new": chg_limit_new,
        "ov_disc_new": ov_disc_new,
        "eq_blk": eq_blk,
        "bo_blk": bo_blk,
        "fl_blk": fl_blk,
        "fl_final": fl_final,
        "br_now": br_now,
        "min_float_allowed": min_float_allowed,
    }


def main():
    inst = init_instrument()

    dump_settings(inst, "Reading current settings")

    # Battery type USER via FC06 (works on your unit)
    print("Ensuring battery type = User/Custom (FC06)...")
    try:
        w_u16_fc06(inst, REG_BATTERY_TYPE, NEW_BATTERY_TYPE)
        bt = r_u16(inst, REG_BATTERY_TYPE)
        if bt != NEW_BATTERY_TYPE:
            print(f"Warning: battery type readback = {bt}, not User/Custom!")
    except Exception as e:
        print("Error setting battery type:", e)
        sys.exit(1)

    # Compute staged targets
    tg = compute_targets(inst)
    print("Plan:")
    print(f"  Stage A: raise Float to {tg['fl_blk']:.2f} V (BR={tg['br_now']:.2f}, min Float={tg['min_float_allowed']:.2f})")
    print(f"  Stage B: block write Eq/Boost/Float = {tg['eq_blk']:.2f}/{tg['bo_blk']:.2f}/{tg['fl_blk']:.2f} V")
    print(f"  Stage C: lower Float to {tg['fl_final']:.2f} V")
    print(f"  Charging Limit (>= Eq): {tg['chg_limit_new']:.2f} V; Over-voltage Disconnect (> CL): {tg['ov_disc_new']:.2f} V")

    # Quick no-op FC16 test on 0x9006..0x9008 (write current values back)
    try:
        eq_cur, bo_cur, fl_cur = r_v(inst, REG_EQUALIZE_VOLT), r_v(inst, REG_BOOST_VOLT), r_v(inst, REG_FLOAT_VOLT)
        print("FC16 no-op probe on 0x9006..0x9008...")
        w_block_fc16(inst, REG_EQUALIZE_VOLT, [int(round(x*100)) for x in (eq_cur, bo_cur, fl_cur)])
        print("  FC16 probe OK (device responded).")
    except Exception as e:
        print("  FC16 probe failed (device refused/ignored block writes):", e)
        print("  We can still proceed (falls back to FC06 where possible), but block write may be refused.")

    # Stage A: raise Float (FC06)
    try:
        print("Stage A: raising Float (FC06)...")
        fl_after = w_v_fc06(inst, REG_FLOAT_VOLT, tg["fl_blk"])
        print(f"  Float now: {fl_after:.2f} V")
    except Exception as e:
        print("Stage A failed (raising Float):", e)
        sys.exit(1)

    # Pre-adjust CL/OVD if needed (FC06)
    try:
        if abs(r_v(inst, REG_CHARGING_LIMIT) - tg["chg_limit_new"]) > 1e-3:
            print("Updating Charging Limit (FC06)...")
            w_v_fc06(inst, REG_CHARGING_LIMIT, tg["chg_limit_new"])
        if abs(r_v(inst, REG_OVERVOLT_DISCONNECT) - tg["ov_disc_new"]) > 1e-3:
            print("Updating Over-voltage Disconnect (FC06)...")
            w_v_fc06(inst, REG_OVERVOLT_DISCONNECT, tg["ov_disc_new"])
    except Exception as e:
        print("Pre-block consistency writes failed (continuing):", e)

    # Stage B: block write Eq/Boost/Float (0x9006..0x9008)
    try:
        print("Stage B: writing Eq/Boost/Float as FC16 block...")
        vals = [int(round(v * 100)) for v in [tg["eq_blk"], tg["bo_blk"], tg["fl_blk"]]]
        w_block_fc16(inst, REG_EQUALIZE_VOLT, vals)
        # Readback
        eq_r = r_v(inst, REG_EQUALIZE_VOLT)
        bo_r = r_v(inst, REG_BOOST_VOLT)
        fl_r = r_v(inst, REG_FLOAT_VOLT)
        print(f"  Readback: Eq={eq_r:.2f} V, Boost={bo_r:.2f} V, Float={fl_r:.2f} V")
    except Exception as e:
        print("Stage B block write failed:", e)
        # Fallback: FC06 singles in dependency-safe order
        try:
            print("Fallback: FC06 singles (Float→Boost→Equalize)...")
            fl_r = w_v_fc06(inst, REG_FLOAT_VOLT, tg["fl_blk"])
            bo_r = w_v_fc06(inst, REG_BOOST_VOLT, max(tg["bo_blk"], fl_r))
            eq_r = w_v_fc06(inst, REG_EQUALIZE_VOLT, max(tg["eq_blk"], bo_r))
            print(f"  Readback: Eq={eq_r:.2f} V, Boost={bo_r:.2f} V, Float={fl_r:.2f} V")
        except Exception as e2:
            print("Fallback singles failed:", e2)
            sys.exit(1)

    # Stage C: lower Float to final target (FC06)
    try:
        print("Stage C: lowering Float to final target (FC06)...")
        fl_final_r = w_v_fc06(inst, REG_FLOAT_VOLT, tg["fl_final"])
        print(f"  Float now: {fl_final_r:.2f} V")
    except Exception as e:
        print("Stage C failed (lowering Float):", e)
        print("Keeping Float at raised value.")

    dump_settings(inst, "Verifying final settings")
    print("Done.")


if __name__ == "__main__":
    main()