import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from rvc_sniff import from_candump, from_esp32_lines  # noqa: E402
from srne.rvc import RvcFrame, decode  # noqa: E402


def test_id_fields():
    f = RvcFrame(0, 0x19FFFD42, b"")
    assert (f.priority, f.dgn, f.source, f.name) == (6, 0x1FFFD, 0x42, "DC_SOURCE_STATUS_1")
    # PDU1: REQUEST to destination 0x80
    req = RvcFrame(0, 0x18EA8042, b"")
    assert (req.dgn, req.destination, req.name) == (0x0EA00, 0x80, "REQUEST")


def test_dc_source_status_1():
    volts = int(13.25 / 0.05).to_bytes(2, "little")
    amps = int((-12.5 + 2_000_000) / 0.001).to_bytes(4, "little")
    f = RvcFrame(0, 0x19FFFD42, bytes([1, 100]) + volts + amps)
    assert decode(f) == {"instance": 1, "priority": 100, "voltage_V": 13.25, "current_A": -12.5}


def test_dc_source_status_2_not_available():
    f = RvcFrame(0, 0x19FFFC42, bytes([1, 100, 0xFF, 0xFF, 170, 0xFF, 0xFF, 0xFF]))
    assert decode(f) == {"instance": 1, "priority": 100, "temperature_C": None,
                         "soc_pct": 85.0, "time_remaining_min": None}


def test_input_parsers():
    esp = list(from_esp32_lines(["C 1500 19fffd42 01 64 09 01 00 00 00 00", "# hello"]))
    assert esp[0].ts == 1.5 and esp[0].dgn == 0x1FFFD and esp[0].data[2] == 0x09
    dump = list(from_candump(["(1700000000.123456) can0 19FFFD42#0164090100000000"]))
    assert dump[0].can_id == 0x19FFFD42 and len(dump[0].data) == 8
