# SRNE Karavan Enerji Sistemi — Tersine Mühendislik

SRNE RV ekosistemindeki cihazların iletişimini çözmek, ayarlarını
değiştirebilmek ve karavan için kendi akü/enerji göstergemizi yapmak.

## Cihazlar

| Cihaz | Rol | Protokol durumu |
|---|---|---|
| SR-CU2 Master Control | Merkez: cihazları sorgular, BT/WiFi uygulama, 6 röle, tank/sıcaklık girişleri | Bilinmiyor — asıl hedef |
| RMA7 LCD Display | 7" dokunmatik ekran, CU2'ye bağlı | Bilinmiyor |
| MC4870N15 MPPT (70A / 150V) | Solar şarj | SRNE ML/MC Modbus — kısmen biliniyor ([harita](registers/srne_mc.yaml)) |
| SR-IC12 3kW | 12V inverter/şarj | SRNE inverter Modbus (RS485, 9600) — harita eklenecek |
| 30A DC-DC Charger | Alternatörden şarj | Bilinmiyor |
| Battery Shunt | Akım/SOC ölçümü | Bilinmiyor |
| DB-12 Distribution Box | 4 PV girişli dağıtım kutusu | Muhtemelen pasif / basit izleme |

Ayrıntılar: [docs/cihazlar.md](docs/cihazlar.md)

## Yol haritası

1. **Fiziksel katmanı belirle** — CU2 portları RS485 mi CAN mi, hangi pinler, hangi baud.
   Lojik analizör ile → [docs/tersine-muhendislik.md](docs/tersine-muhendislik.md)
2. **Pasif dinleme** — CU2 ↔ cihaz trafiğini kaydet (`tools/sniff.py` veya ESP32 sniffer).
   Hiçbir şey göndermez, sistem bozulmaz.
3. **Register haritası çıkar** — Uygulamada bir ayarı değiştir, hatta giden yazmayı yakala;
   yükleri aç/kapa, değerlerin nasıl değiştiğine bak (`tools/analyze.py`).
4. **Gösterge** — ESP32 pasif dinlemeyle veriyi alır → Home Assistant / web panel / ekran.
5. **Ayar değiştirme** — Sadece doğrulanmış register'lar, sınır kontrolüyle, önce tek cihazda.

## Araçlar

```bash
pip install -r requirements.txt

# USB-RS485 ile pasif dinleme (ham veri de kaydedilir)
python tools/sniff.py --port /dev/ttyUSB0 --baud 9600 --raw cap.bin --jsonl cap.jsonl \
    --map 1=registers/srne_mc.yaml

# Protokol Modbus değilse: sadece ham baytlar
python tools/sniff.py --port /dev/ttyUSB0 --baud 9600 --hexdump

# Kayıt özeti: hangi register ne sıklıkla okunuyor, nasıl değişiyor, neler yazılıyor
python tools/analyze.py cap.jsonl --writes

# Tek cihazı doğrudan okuma (CU2'den AYIRDIKTAN sonra!) — salt okunur
python tools/probe.py --port /dev/ttyUSB0 --addr 1 --start 0x0100 --count 0x23 \
    --map registers/srne_mc.yaml

python -m pytest
```

ESP32 sniffer (daha doğru frame zamanlaması, karavanda kalıcı kullanılabilir):
[firmware/esp32-sniffer](firmware/esp32-sniffer)

## Güvenlik

- Şarj voltajı / kesme eşiği hatalı yazılırsa akü zarar görür; lityumda yangın riski vardır.
- Modbus hattında **tek master** olur. CU2 bağlıyken `probe.py` veya başka bir aktif sorgu
  çalıştırma — önce pasif dinle.
- Yazma işlemleri bu repoda henüz yok ve bilerek eklenmedi; register'lar gerçek cihazda
  doğrulanınca sınır kontrollü olarak eklenecek.
