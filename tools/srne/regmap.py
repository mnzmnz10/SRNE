"""Register map loading and value decoding."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Register:
    address: int
    name: str
    type: str = "u16"
    scale: float = 1.0
    unit: str = ""
    desc: str = ""
    length: int = 1
    writable: bool = False
    verified: bool = False

    @property
    def width(self) -> int:
        if self.type == "u32":
            return 2
        if self.type == "str":
            return self.length
        return 1


class RegisterMap:
    def __init__(self, registers: dict[int, Register], meta: dict | None = None) -> None:
        self.registers = registers
        self.meta = meta or {}

    @classmethod
    def load(cls, path: str | Path) -> "RegisterMap":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        regs = {}
        for addr, spec in (data.get("registers") or {}).items():
            regs[int(addr)] = Register(address=int(addr), **spec)
        meta = {k: v for k, v in data.items() if k != "registers"}
        return cls(regs, meta)

    @classmethod
    def empty(cls) -> "RegisterMap":
        return cls({})

    def decode_block(self, start: int, values: list[int]) -> list[tuple[int, str, str]]:
        """Returns (address, name, formatted value) for each register in a block.

        Unknown registers are reported by address so nothing gets hidden while
        reverse engineering.
        """
        out = []
        i = 0
        while i < len(values):
            addr = start + i
            reg = self.registers.get(addr)
            if reg is None or i + reg.width > len(values):
                out.append((addr, f"?{addr:#06x}", f"{values[i]} ({values[i]:#06x})"))
                i += 1
                continue
            raw = values[i:i + reg.width]
            out.append((addr, reg.name, format_value(reg, raw)))
            i += reg.width
        return out


def _sign_magnitude(b: int) -> int:
    return -(b & 0x7F) if b & 0x80 else b


def format_value(reg: Register, raw: list[int]) -> str:
    if reg.type == "str":
        text = b"".join(v.to_bytes(2, "big") for v in raw).decode("ascii", "replace")
        return repr(text.strip("\x00 "))
    if reg.type == "temp_pair":
        hi, lo = raw[0] >> 8, raw[0] & 0xFF
        return f"{_sign_magnitude(hi)} / {_sign_magnitude(lo)} {reg.unit}".strip()
    if reg.type == "u32":
        v = (raw[0] << 16) | raw[1]
    elif reg.type == "s16":
        v = raw[0] - 0x10000 if raw[0] & 0x8000 else raw[0]
    else:
        v = raw[0]
    if reg.scale != 1:
        v = round(v * reg.scale, 3)
    return f"{v} {reg.unit}".strip()
