# JK BMS → CU2 / RMA7 planı

**Hedef:** 2 × 12.8V (4S LiFePO4) 310Ah akü, her birinde Bluetooth'lu JK BMS (200A).
Bu aküleri RMA7 ekranında görmek.

## Mimari

```
JK BMS #1 ─┐  Bluetooth (BLE)
           ├──> ESP32 köprü ──(CU2'nin beklediği protokol)──> CU2 "BMS RS485/CAN-8" portu ──> RMA7
JK BMS #2 ─┘        │
                    └──> (opsiyonel) WiFi / Home Assistant: hücre voltajları, sıcaklıklar, dengeleme
```

- JK BMS modeli belli değil ama önemi yok: Bluetooth protokolü bütün JK nesilleri için
  çözülmüş ([syssi/esphome-jk-bms](https://github.com/syssi/esphome-jk-bms): JK02, JK02_32S, JK04).
  RS485 kablosu ya da ek modül gerekmiyor.
- Bir ESP32 aynı anda 3 BLE cihazına bağlanabilir, yani 2 BMS sorun değil.

## Adım 1: CU2'nin BMS portu hangi protokolü bekliyor? (akü gelmeden yapılabilir)

### 1a. Uygulamaya bak
SRNE uygulamasında CU2'ye bağlan. Akü veya BMS ayarlarında "BMS protocol / communication /
battery type" gibi bir seçim listesi var mı bak. Varsa listenin ekran görüntüsünü al.

### 1b. Portu dinle
BMS portunun pin dizilimi [kılavuz]:

| Pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| | B/D- | A/D+ | GND | CAN_H | CAN_L | GND | A/D+ | B/D- |

**RS485:** USB-RS485'in A'sını pin 2'ye, B'sini pin 1'e, GND'sini pin 3'e bağla (portta başka hiçbir şey takılı olmasın).
```bash
python tools/sniff.py --port /dev/ttyUSB0 --baud 9600 --hexdump   # ham bayt + ASCII
python tools/sniff.py --port /dev/ttyUSB0 --baud 9600             # Modbus olarak çöz
```
Bir şey gelmezse 19200 ve 115200'ü de dene. Neyi görürsen ne demek olduğu:

| Gördüğün | Anlamı |
|---|---|
| `~20..` ile başlayan, `\r` ile biten ASCII satırlar | **Pylontech RS485** protokolü, JK'da da var |
| `01 03 ...` gibi CRC'si geçerli Modbus istekleri | SRNE'nin Modbus tabanlı BMS protokolü: hangi register'ları istediği görünür |
| Hiçbir şey | CU2 RS485'te sorgu atmıyor → CAN'e bak, ya da uygulamada BMS kapalı |

**CAN:** ESP32 CAN sniffer'ı bağla, CANH'yi pin 4'e, CANL'yi pin 5'e.
```bash
python tools/rvc_sniff.py --esp32 /dev/ttyUSB0 --log bms-port.candump
```
Hatta başka cihaz yokken CU2'nin gönderdiği bir frame onaylanmaz. Bu yüzden aynı frame'i
sürekli tekrar ettiğini görürsün; bu normal, frame'in ID'si yine de protokolü ele verir.
Pylontech CAN 500k kullanır, CU2'nin varsayılanı 250k. Gerekirse sniffer'ı 500k'ya da alırız.

## Adım 2: köprü (protokol belli olunca)

- ESPHome + `esphome-jk-bms` ile iki BMS'i BLE üzerinden oku.
- İki paketi birleştir:
  - voltaj = ortalama (paralel bağlı oldukları için neredeyse aynı)
  - akım = toplam
  - SOC = kapasiteye göre ağırlıklı ortalama
  - kalan Ah = toplam
  - hücre min/max, sıcaklık max = iki paketin en kötüsü
  - alarmlar = VEYA
- Şarj/deşarj limitleri, CU2 bu limitlere göre şarjı yönetebileceği için:
  - şarj voltajı sınırı (CVL) = sabit ve güvenli bir değer (ör. 14.2V), BMS verisinden türetilmez
  - şarj akımı sınırı (CCL) = **çevrimiçi ve şarjı açık paket sayısı × paket başına güvenli akım**.
    Bir BMS koparsa ya da şarj MOSFET'ini kapatırsa limit o anda düşer.
  - İki BMS'ten de veri gelmezse köprü **sustur**: sahte "her şey yolunda" verisi asla gönderilmez.
- Aynı veriyi WiFi üzerinden Home Assistant'a da ver: hücre bazlı izleme RMA7'de görünmese bile telefondan görünür.

## Adım 3: doğrulama

- Önce PV ve şebeke şarjı kapalıyken bağla. RMA7'de değerleri kontrol et.
- Bir BMS'in Bluetooth'unu kes (ESP32'yi uzaklaştır). Ekranda uyarı çıkmalı ve limitler düşmeli.
- Sonra şarjı aç, akım limitlerine uyulduğunu shunt'tan izle.
