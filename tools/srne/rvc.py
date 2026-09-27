"""RV-C (CAN, 250 kbps, 29-bit extended IDs) frame decoding.

RV-C is built on SAE J1939. The 29-bit identifier is:

  bits 26-28 priority | bit 25 reserved | bits 8-24 DGN | bits 0-7 source address

For DGNs whose high byte (bits 8-15 of the DGN) is below 0xF0 the low byte
is a destination address rather than part of the DGN (J1939 PDU1 format).

Field layouts below follow the public RV-C specification. They are marked in
docs as "spec-based": check them against real SRNE traffic before trusting
them, SRNE may only implement a subset or use proprietary DGNs.
"""

from __future__ import annotations

from dataclasses import dataclass

# DGN -> name. Decoders exist only for the ones in DECODERS below.
DGN_NAMES = {
    0x0E800: "ACKNOWLEDGMENT",
    0x0EA00: "REQUEST",
    0x0EE00: "ADDRESS_CLAIMED",
    0x0EF00: "PROPRIETARY_DGN",
    0x1EF00: "PROPRIETARY_DGN_2",
    0x1FECA: "DM_RV",
    0x1FFFF: "DATE_TIME_STATUS",
    0x1FFFD: "DC_SOURCE_STATUS_1",
    0x1FFFC: "DC_SOURCE_STATUS_2",
    0x1FFFB: "DC_SOURCE_STATUS_3",
    0x1FFD4: "INVERTER_STATUS",
    0x1FFD7: "INVERTER_AC_STATUS_1",
    0x1FFC7: "CHARGER_STATUS",
    0x1FFCA: "CHARGER_AC_STATUS_1",
    0x1FEB3: "SOLAR_CONTROLLER_STATUS",
    0x1FFB7: "TANK_STATUS",
}

NA8, NA16, NA32 = 0xFF, 0xFFFF, 0xFFFFFFFF


@dataclass
class RvcFrame:
    ts: float
    can_id: int
    data: bytes

    @property
    def priority(self) -> int:
        return (self.can_id >> 26) & 0x7

    @property
    def source(self) -> int:
        return self.can_id & 0xFF

    @property
    def dgn(self) -> int:
        dgn = (self.can_id >> 8) & 0x1FFFF
        if (dgn >> 8) & 0xFF < 0xF0:
            dgn &= 0x1FF00
        return dgn

    @property
    def destination(self) -> int | None:
        dgn = (self.can_id >> 8) & 0x1FFFF
        return dgn & 0xFF if (dgn >> 8) & 0xFF < 0xF0 else None

    @property
    def name(self) -> str:
        return DGN_NAMES.get(self.dgn, f"DGN_{self.dgn:05X}")


def _u16(d: bytes, i: int) -> int:
    return int.from_bytes(d[i:i + 2], "little")


def _u32(d: bytes, i: int) -> int:
    return int.from_bytes(d[i:i + 4], "little")


def _scaled(raw: int, na: int, scale: float, offset: float = 0.0, nd: int = 2):
    return None if raw == na else round(raw * scale + offset, nd)


def _dc_source_1(d: bytes) -> dict:
    return {
        "instance": d[0],
        "priority": d[1],
        "voltage_V": _scaled(_u16(d, 2), NA16, 0.05),
        "current_A": _scaled(_u32(d, 4), NA32, 0.001, -2_000_000, 3),
    }


def _dc_source_2(d: bytes) -> dict:
    return {
        "instance": d[0],
        "priority": d[1],
        "temperature_C": _scaled(_u16(d, 2), NA16, 0.03125, -273),
        "soc_pct": _scaled(d[4], NA8, 0.5),
        "time_remaining_min": None if _u16(d, 5) == NA16 else _u16(d, 5),
    }


CHARGER_STATES = {0: "disabled", 1: "do_not_charge", 2: "bulk", 3: "absorption",
                  4: "overcharge", 5: "equalize", 6: "float", 7: "constant_vi"}


def _charger_status(d: bytes) -> dict:
    return {
        "instance": d[0],
        "voltage_V": _scaled(_u16(d, 1), NA16, 0.05),
        "current_A": _scaled(_u16(d, 3), NA16, 0.05, -1600),
        "pct_max_current": _scaled(d[5], NA8, 0.5),
        "state": CHARGER_STATES.get(d[6], d[6]),
    }


INVERTER_STATES = {0: "disabled", 1: "invert", 2: "ac_passthru", 3: "aps_only",
                   4: "load_sense", 5: "waiting_to_invert", 6: "generator_support"}


def _inverter_status(d: bytes) -> dict:
    return {"instance": d[0], "state": INVERTER_STATES.get(d[1], d[1])}


def _tank_status(d: bytes) -> dict:
    return {
        "instance": d[0],
        "relative_level": d[1],
        "resolution": d[2],
        "absolute_level": _u16(d, 3),
        "tank_size": _u16(d, 5),
    }


DECODERS = {
    0x1FFFD: _dc_source_1,
    0x1FFFC: _dc_source_2,
    0x1FFC7: _charger_status,
    0x1FFD4: _inverter_status,
    0x1FFB7: _tank_status,
}


def decode(frame: RvcFrame) -> dict | None:
    fn = DECODERS.get(frame.dgn)
    if fn is None or len(frame.data) < 8:
        return None
    return fn(frame.data)
