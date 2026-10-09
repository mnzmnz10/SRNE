# JK BMS → CU2 / RMA7 planı

**Hedef:** 2 × 12.8V (4S LiFePO4) 310Ah akü, her birinde Bluetooth'lu JK BMS (200A).
Bu aküleri RMA7 ekranında görmek.

## Önce: SRNE shunt ile hazır gösterge (ek donanım gerekmez)

BS48500 shunt bir SRNE cihazı. CU2 onu zaten tanıyor (montaj şemasında "Coulombmeter" portu var),
RMA7 de verisini gösteriyor. Shunt doğru ayarlanınca **toplam akü bankası** için SOC, voltaj,
akım, kalan süre ve marş aküsü voltajı köprüye hiç gerek kalmadan ekranda görünür.

Shunt ayarları (SRNE uygulaması, varsayılan şifre 123456):

| Ayar | Değer |
|---|---|
| Battery capacity | **620Ah** (2 × 310Ah paralel) |
| Battery type | Lithium (ya da custom) |
| System voltage | 12V |
| Full voltage | Şarj voltajı − 0.2…0.3V (örnek: 14.2V şarjda ~13.9V). Lityum preset'i de olur |
| Discharge cut-off voltage | Düşük voltaj uyarısı + 0.2…0.3V (örnek: ~12.0V) |
| Full cut-off current | ~10–12A (~%2 × 620Ah; şarj akımı bunun altına düşünce "tam dolu" sayılır) |
| Full detection time | Varsayılan |
| Current SOC | Aküler tam dolduktan sonra %100 yap |
| Zero current calibration | Yük eksi ucu sökülüyken bir kez yap |
| Discharge depth (DOD) | %5 (varsayılan) |

Kablolama kuralı: akülerin eksisinden çıkan **tek** kablo shunt'ın akü tarafına gider. Diğer bütün eksiler
(inverter, MPPT, DC-DC, DB12, şasi) shunt'ın yük tarafına bağlanır. Aksi halde ölçüm eksik olur.

**Shunt'ın gösteremedikleri** (köprünün getireceği ek değer): akü başına ayrı veri, hücre voltajları,
hücre farkı/dengeleme, hücre sıcaklıkları, BMS alarmları ve bir BMS'in aküyü devreden çıkarması.
Bunlar RMA7'de yeri olmayabileceği için en kolay yol köprünün **sadece telefon/web sayfasında**
göstermesidir. Bu durumda CU2'ye hiç veri gönderilmez, şarj kontrolüne de dokunulmaz.

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
