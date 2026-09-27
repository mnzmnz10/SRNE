# Tersine mühendislik adımları

## 1. Hangi hat aktif? (pin dizilimi artık biliniyor)

Kılavuzlara göre CU2, DB12, shunt ve inverter aynı RJ45 dizilimini kullanıyor
([tablo](cihazlar.md#rj45-pin-dizilimleri-kılavuz)): **pin 1 CAN_L, 2 CAN_H, 5 GND, 6 B/D-, 7 A/D+**.
Aynı kabloda iki hat birden var, hangisinin kullanıldığını bulmak gerekiyor.
**MPPT**: eski MC4870 kılavuzunda 1 izole +, 2 D+, 3 D-, 4 izole GND; senin modelinde (MC4885/48100, CAN'lı) farklı olabilir → önce ölç.

1. Orijinal kabloyu bozma; bir RJ45 **splitter / ara geçiş** kullan.
2. Sistem açıkken multimetreyle, GND = pin 5 alarak:
   - pin 1 ve 2 ikisi de ≈ 2.5V ve dalgalanıyorsa → **CAN aktif**
     (veri anında CAN_H ≈ 3.5V, CAN_L ≈ 1.5V)
   - pin 6-7 arası boşta birkaç yüz mV (A > B) ve dalgalanıyorsa → **RS485 aktif**
   - Pin 1-2 ≈ 0V veya sabit ise CAN kullanılmıyor.
3. CU2'nin her portunu (özellikle MPPT'nin bağlı olduğu, TTL olabilir) ayrı kontrol et.
4. Sistem kapalıyken CAN_H–CAN_L arası direnç: ~60Ω iki uçtan sonlandırılmış,
   ~120Ω tek uç, açık devre sonlandırma yok.

## 2. Lojik analizör ile baud ve protokol

Lojik analizör girişleri diferansiyel hattı doğrudan okuyamaz ve çoğu 5V toleranslıdır.
En güvenli yol: RS485 modülünün alıcı tarafını hatta bağla (A→A, B→B, GND ortak),
modülün **RO** çıkışını analizöre ver. CAN ise bir CAN transceiver'ın RX çıkışını kullan.

PulseView / sigrok:
- Örnekleme: en az 1 MHz.
- Önce `UART` dekoderi, baud'u en kısa bit genişliğinden hesapla (104 µs → 9600, 52 µs → 19200).
- UART temizse üstüne `Modbus` dekoderi (RTU) ekle.
- CAN ise `CAN` dekoderi; bit hızı genelde 250k veya 500k.

Komut satırı örneği:

```bash
sigrok-cli -d fx2lafw --config samplerate=1m --time 5s \
  -P uart:baudrate=9600:rx=D0 -A uart=rx-data
```

## 3. Pasif dinleme

**RS485 ise** — USB-RS485 adaptörünü splitter üzerinden hatta paralel bağla, sadece A, B, GND.
```bash
python tools/sniff.py --port /dev/ttyUSB0 --baud 9600 --raw cu2-mppt.bin --jsonl cu2-mppt.jsonl
```
- Sadece `bad-crc`/çöp görüyorsan: baud yanlış, A/B ters veya protokol Modbus değil →
  `--hexdump` ile ham baytlara bak, tekrar eden başlık baytı ara.
- Her CU2 portunu ayrı ayrı kaydet (portlar ayrı hatlar olabilir).
- USB adaptörlerde zamanlama kaba olduğu için sniffer frame'leri CRC ile ayırır. Daha doğru
  zaman damgası için ESP32 sniffer'ı kullan.

**CAN ise** — ESP32 + SN65HVD230 ile [CAN sniffer](../firmware/esp32-can-sniffer) (listen-only):
```bash
python tools/rvc_sniff.py --esp32 /dev/ttyUSB0 --log cu2-port1.candump
python tools/rvc_sniff.py --candump cu2-port1.candump --summary
```
Standart RV-C DGN'leri (DC_SOURCE_STATUS_1/2, CHARGER_STATUS, INVERTER_STATUS, TANK_STATUS)
otomatik çözülür. `PROPRIETARY_DGN` (0xEF00/0x1EF00) mesajları SRNE'ye özel olabilir;
ayar değişiklikleri büyük ihtimalle bunlarla veya standart *_COMMAND DGN'leriyle gider.
Linux'ta bir USB-CAN adaptörün varsa `--socketcan can0` da kullanılabilir.

**RMA7 hattı (CU2 port 6)** — RS485 **115200**, SRNE'ye özel protokol. Önce `--hexdump`:
```bash
python tools/sniff.py --port /dev/ttyUSB0 --baud 115200 --hexdump
```
Bu porttaki pin 3 ve 8'de 13.2V var; USB-RS485'e sadece 6, 7 ve 5'i (GND) bağla.

## 4. Anlamı çıkar: kontrollü deneyler

Kayıt açıkken her seferinde **tek bir şeyi** değiştir, zamanını not al:

| Deney | Beklenen |
|---|---|
| Uygulamada/RMA7'de bir ayarı değiştir (ör. float voltajı 13.5 → 13.6) | Hatta fc6/fc16 yazma: hangi register, hangi ölçek |
| Bir yükü aç / kapat | Yük akımı / güç register'ı değişir |
| Panelleri kapat (gölge) | PV voltaj/akım register'ları düşer |
| Motoru çalıştır | DC-DC akımı görünür |
| Şebekeye bağla | SR-IC giriş/şarj register'ları değişir |
| CU2 rölesini uygulamadan aç | CU2'nin kendi iç komutu (varsa hatta) |

Sonra:
```bash
python tools/analyze.py cu2-mppt.jsonl --writes
```
Bulunan her register'ı ilgili `registers/*.yaml` dosyasına ekle, doğrulananları `verified: true` yap.

## 5. Kaydedilecekler

Ham kayıtları (`*.bin`, `*.jsonl`) `captures/` altına **cihaz-port-deney** adıyla koy ve
ne yaptığını kısa bir `.md` notuyla yaz; ileride tekrar çözümlemek için ham veri altın değerinde.
