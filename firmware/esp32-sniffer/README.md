# ESP32 pasif RS485 sniffer

Hatta asla veri göndermez: UART'ın TX pini tanımlı değil ve RS485 modülü sürekli alıcı modda.

## Bağlantı (MAX485 tipi modül)

| RS485 modülü | ESP32 |
|---|---|
| RO | GPIO16 |
| DE + RE (birbirine bağlı) | GPIO4 (LOW tutulur) |
| DI | **bağlama** |
| VCC | 3.3V (3.3V uyumlu modül) ya da 5V + RO'ya seviye dönüştürücü |
| GND | GND |
| A / B | Hattın A / B'si (splitter üzerinden) |

Hattın GND'sini de ortak bağla. Hattaki besleme pinlerini ESP32'ye doğrudan verme.

## Derleme

```bash
cd firmware/esp32-sniffer
pio run -t upload
python ../../tools/sniff.py --esp32 /dev/ttyUSB0 --jsonl cap.jsonl
```

Seri komutlar (921600): `B 19200` baud değiştirir, `G 4` frame sonu boşluğunu karakter
cinsinden ayarlar.
