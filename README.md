# SRNE Karavan Enerji Sistemi — Tersine Mühendislik

SRNE RV ekosistemindeki cihazların iletişimini çözmek, ayarlarını
değiştirebilmek ve karavan için kendi akü/enerji göstergemizi yapmak.

## Cihazlar

| Cihaz | Rol | Haberleşme (kılavuzlara göre) |
|---|---|---|
| SR-CU2 Master Control | Merkez: cihazları sorgular, BT/WiFi, 6 röle, 8 sıcaklık/tank girişi | RS485 9600 + CAN 250k **RV-C**, TTL, RS232 |
| RMA7 LCD Display | 7" dokunmatik ekran, CU2 port 6 | RS485 **115200, özel protokol** |
| MC4885N25 MPPT (85A / 250V PV) | Solar şarj | Modbus RS485 (izole) / TTL 9600, CAN ([harita](registers/srne_mc.yaml)) |
| IBC12-3KW inverter/şarj | 12V 3kW inverter + şebeke şarjı | RS485 9600, RV-C (opsiyonel) |
| DCI12-1230 DC-DC | Alternatörden 30A şarj | RS485, CAN, TTL, BLE |
| BS48500 Battery Shunt | 500A akım / SOC | Modbus RS485, CAN, BLE |
| SR-DB12 | 12 kanallı DC dağıtım kutusu | RS485 9600 + RV-C, ekran portu 115200 |

Pin dizilimleri ve ayrıntılar: [docs/cihazlar.md](docs/cihazlar.md)

**Şu anki hedef:** 2 × 12.8V 310Ah akü + Bluetooth'lu JK BMS → ESP32 köprü → CU2 BMS portu → RMA7.
Plan: [docs/jk-bms-plani.md](docs/jk-bms-plani.md) · **Adım adım rehber: [docs/adim-adim-rehber.md](docs/adim-adim-rehber.md)**

**RV-C** açık bir karavan CAN standardıdır (J1939 tabanlı). CU2 ile cihazlar arasında CAN
kullanılıyorsa verilerin büyük kısmı standart DGN'lerle çözülebilir.

## Yol haritası

1. **Hangi hat aktif?** — Aynı RJ45 kablosunda hem CAN (pin 1-2) hem RS485 (pin 6-7) var.
   Lojik analizörle hangisinde trafik olduğunu bul → [rehber](docs/tersine-muhendislik.md)
2. **Pasif dinleme** — CAN ise `tools/rvc_sniff.py` + ESP32 CAN sniffer,
   RS485 ise `tools/sniff.py` + ESP32/USB-RS485. İkisi de hatta hiçbir şey göndermez.
3. **Haritayı çıkar** — Uygulamadan tek bir ayarı değiştir, hatta giden yazmayı yakala.
4. **Gösterge** — ESP32 pasif dinlemeyle veriyi alır → Home Assistant / web panel / ekran.
5. **Ayar değiştirme** — Sadece doğrulanmış register/DGN'ler, sınır kontrolüyle.

## Araçlar

```bash
pip install -r requirements.txt

# CAN / RV-C (ESP32 CAN sniffer ile)
python tools/rvc_sniff.py --esp32 /dev/ttyUSB0 --log cap.candump
python tools/rvc_sniff.py --candump cap.candump --summary   # DGN/kaynak başına değişen baytlar

# RS485 Modbus (USB-RS485 ile), ham veri de kaydedilir
python tools/sniff.py --port /dev/ttyUSB0 --baud 9600 --raw cap.bin --jsonl cap.jsonl \
    --map 1=registers/srne_mc.yaml
python tools/sniff.py --port /dev/ttyUSB0 --baud 115200 --hexdump   # RMA7 hattı (özel protokol)
python tools/analyze.py cap.jsonl --writes

# Tek cihazı doğrudan okuma (CU2'den AYIRDIKTAN sonra!) — salt okunur
python tools/probe.py --port /dev/ttyUSB0 --addr 1 --start 0x0100 --count 0x23 \
    --map registers/srne_mc.yaml

python -m pytest
```

ESP32 yazılımları: [RS485 sniffer](firmware/esp32-sniffer), [CAN sniffer](firmware/esp32-can-sniffer)

## Güvenlik

- Şarj voltajı / kesme eşiği hatalı yazılırsa akü zarar görür; lityumda yangın riski vardır.
- Eski MPPT kılavuzunda RJ45 dizilimi diğer cihazlardan farklı; kendi modelin teyit edilene kadar pinleri ölçmeden bağlama.
- CU2 port 6 ve DB12 ekran portu 13.2–13.75V, inverter portu 5V besleme veriyor.
- Modbus hattında tek master olur: CU2 bağlıyken `probe.py` çalıştırma.
- Yazma işlemleri bilerek henüz eklenmedi; doğrulanınca sınır kontrollü eklenecek.
