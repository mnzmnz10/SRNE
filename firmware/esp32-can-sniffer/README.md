# ESP32 pasif CAN / RV-C sniffer

TWAI denetleyicisi **listen-only** modda çalışır: hatta hiçbir bit göndermez, ACK bile vermez.

## Bağlantı (SN65HVD230 gibi 3.3V CAN transceiver)

| Transceiver | ESP32 |
|---|---|
| TXD (D) | GPIO5 |
| RXD (R) | GPIO4 |
| 3V3 | 3.3V |
| GND | GND |
| CANH / CANL | RJ45 pin 2 / pin 1 (SRNE dizilimi, splitter üzerinden) |

- RJ45 pin 5 = GND, ortak bağla.
- Sistem kapalıyken CANH–CANL arası direnci ölç: ~60Ω ise hat iki uçtan sonlandırılmış,
  modüldeki 120Ω direnci **çıkar**. ~120Ω veya açık devre ise bırak (DB12 kılavuzu dahili
  sonlandırma direnci olmadığını söylüyor, hat hiç sonlandırılmamış olabilir).

```bash
cd firmware/esp32-can-sniffer
pio run -t upload
python ../../tools/rvc_sniff.py --esp32 /dev/ttyUSB0 --log cap.candump
```
