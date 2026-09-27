import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from srne.modbus import StreamSplitter, Tracker, crc16, read_request, with_crc  # noqa: E402
from srne.regmap import RegisterMap  # noqa: E402


def response(addr, values, fc=3):
    data = b"".join(v.to_bytes(2, "big") for v in values)
    return with_crc(bytes([addr, fc, len(data)]) + data)


def test_crc_known_vector():
    # 01 03 00 00 00 01 -> CRC 84 0A (standard Modbus example)
    assert read_request(1, 0, 1) == bytes.fromhex("010300000001840a")
    assert crc16(b"") == 0xFFFF


def test_split_request_response_stream_in_odd_chunks():
    stream = read_request(1, 0x0100, 3) + response(1, [87, 134, 250])
    s = StreamSplitter()
    frames = []
    for i in range(0, len(stream), 3):
        frames += s.feed(stream[i:i + 3])
    assert [f.kind for f in frames] == ["request", "response"]
    assert frames[0].start == 0x0100 and frames[0].count == 3
    assert frames[1].values == [87, 134, 250]


def test_leading_garbage_is_skipped():
    s = StreamSplitter()
    frames = s.feed(b"\x00\xff\x13" + read_request(1, 0xE002, 2) + response(1, [100, 0x0C0C]))
    assert [f.kind for f in frames] == ["request", "response"]
    assert s.garbage == 3


def test_tracker_pairs_read_and_fc6_echo():
    t = Tracker()
    s = StreamSplitter()
    write = with_crc(bytes([1, 6, 0xE0, 0x04, 0x00, 0x04]))
    frames = s.feed(read_request(1, 0x0100, 2) + response(1, [55, 131]) + write + write)
    txs = [tx for f in frames if (tx := t.push(f))]
    assert (txs[0].op, txs[0].start, txs[0].values) == ("read", 0x0100, [55, 131])
    assert (txs[1].op, txs[1].start, txs[1].values) == ("write", 0xE004, [4])


def test_register_map_decoding():
    rmap = RegisterMap.load(ROOT / "registers" / "srne_mc.yaml")
    rows = rmap.decode_block(0x0100, [87, 134, 250, (25 << 8) | 0x85])
    assert rows[1] == (0x0101, "battery_voltage", "13.4 V")
    assert rows[2] == (0x0102, "charge_current", "2.5 A")
    assert rows[3][2] == "25 / -5 °C"
    # Unknown registers are still shown
    assert rmap.decode_block(0x7000, [1])[0][1] == "?0x7000"
