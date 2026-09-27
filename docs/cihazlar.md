# Cihazlar, portlar ve protokoller

Kaynak: kullanıcının yüklediği resmi kılavuzlar (SR-CU2, MC4870N15 V1.03, BS48500 shunt V1.03,
IBC12-3KW V1.04, SR-DB12 V1.02, DCI datasheet V1.0) ve Skyenergi kurulum kılavuzu V2.
Kılavuzlarda yazanlar **[kılavuz]**, bizim çıkarımlarımız **[çıkarım]** olarak işaretli.

## Özet: kim hangi dili konuşuyor

| Cihaz | RS485 | CAN | Diğer | Not |
|---|---|---|---|---|
| SR-CU2 | 9600 (port 1–5, 7, 8); 115200 (port 6 = ekran) | 250k RV-C (port 1–6, 8) | TTL×2 9600, RS232, BLE, WiFi | Sistemin master'ı |
| RMA7 ekran | 115200, **özel protokol** | — | — | CU2 port 6'ya bağlı [kurulum kılavuzu] |
| MPPT (MC4885N15 / MC48100N15 ailesi?) | 9600 Modbus, izole | **kullanıcıya göre var**, dizilimi bilinmiyor | TTL 9600 Modbus, BLE | Model teyit edilecek |
| IBC12-3KW inverter | 9600 | RV-C (opsiyonel) | BLE, TTL | RJ45'te uzaktan açma (SW1/SW2) ve 5V çıkışı var |
| BS48500 shunt | 9600 Modbus | var | BLE | |
| SR-DB12 dağıtım kutusu | 9600 + ekran portu 115200 (özel) | 250k RV-C, 2.0B extended | BLE | Dahili CAN sonlandırma direnci yok |
| DCI12-1230 DC-DC | var | var | BLE, TTL | Pin dizilimi datasheet'te yok |

## RJ45 pin dizilimleri [kılavuz]

Pin numaraları kılavuz çizimlerindeki numaralardır; fiziksel yönü multimetreyle teyit et.

| Pin | CU2 RS485/CAN 1–5 | CU2 port 6 (LCD) | CU2 RS485-7 | CU2 BMS-8 | DB12 RS485/CAN | DB12 ekran | BS48500 shunt | IBC12 inverter | **MC4870N15 MPPT** |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CAN_L | CAN_L | NC | B/D- | CAN_L | NC | CAN_L | CAN_L | **İzole + besleme** |
| 2 | CAN_H | CAN_H | NC | A/D+ | CAN_H | NC | CAN_H | CAN_H | **D+** |
| 3 | NC | VCC 13.2V | NC | GND | NC | ? | NC | SW2 | **D-** |
| 4 | NC | GND | NC | CAN_H | NC | ? | NC | SW1 | **İzole GND** |
| 5 | GND | GND | GND | CAN_L | GND | GND | GND | GND | uzaktan kapama |
| 6 | B/D- | B/D- | B/D- | GND | B/D- | B/D- | D- | D- | uzaktan kapama |
| 7 | A/D+ | A/D+ | A/D+ | A/D+ | A/D+ | A/D+ | D+ | D+ | NC |
| 8 | NC | VCC 13.2V | NC | B/D- | NC | +13.75V | NC | **+5V çıkış** | NC |

> ⚠ MPPT sütunu, yüklenen **MC4860/4870** kılavuzundan. Kullanıcının kitapçığı
> **MC4885N15 / MC48100N15 / MC4885N25 / MC48100N25** ailesine ait ve cihazda CAN olduğu
> belirtildi; yeni modelin RJ45 dizilimi farklı olabilir. Kendi kitapçığındaki haberleşme
> portu sayfasına göre güncellenecek.

Sonuçlar:
- CU2, DB12, shunt ve inverter **aynı dizilimi** kullanıyor: düz RJ45 kabloyla CAN (1-2) ve
  RS485 (6-7) aynı anda taşınıyor. Hangisinin kullanıldığı hattı dinleyerek anlaşılacak.
- **MPPT (eski MC4870 kılavuzuna göre) uyumsuz**: D+/D- 2-3'te, pin 1'de izole besleme girişi var. Düz kabloyla CU2'nin
  RS485/CAN portuna takılırsa CU2'nin CAN_L'si MPPT'nin besleme pinine gelir.
  [çıkarım] MPPT büyük ihtimalle CU2'nin **TTL1/TTL2** portuna bağlanıyor (ikisi de 4 pin,
  12.8–13.2V besleme + TX/RX + GND, 9600 Modbus) ya da özel bir çevirici kablo kullanılıyor.
  → Kendi sistemindeki MPPT kablosunun hangi porta gittiğine bak.
- Port 6 (ekran) ve DB12 ekran portu **13.2–13.75V besleme** veriyor: sniffer'ı bağlarken
  bu pinleri ESP32'ye verme.
- IBC12 pin 8'de 5V/200mA çıkış var; pin 3-4 (SW1/SW2) kısa devre = inverter AÇIK.
- MPPT pin 5-6 kısa devre = şarj durur.

## SR-CU2 portları [kılavuz]

| # | Port | Varsayılan |
|---|---|---|
| 1, 2 | TTL2, TTL1 (4 pin: VCC 13.2V, TX, RX, GND) | 9600 8N1 |
| 3 | RS232 (RJ12: 1 RX, 2 TX, 3-4 GND) | 9600 8N1 |
| 4–8 | RS485/CAN-1…5 | RS485 9600 / CAN 250k RV-C |
| 9 | RS485/CAN-6 — **LCD (RMA7)** | RS485 **115200** / CAN 250k |
| 10 | RS485-7 (sadece RS485) | 9600 |
| 11 | BMS RS485/CAN-8 — sadece akü BMS'i | 9600 / 250k |
| 15 | 8 kanal sıcaklık (NTC 10K 3950) / tank seviyesi (0–190Ω, 240–33Ω) | CH1-2 sıcaklık, CH3-8 tank |
| 16 | 6 röle, SPDT, 30VDC/6A | manuel veya tetik modu (APP) |

Montaj şemasında portlara bağlanan cihazlar: Battery protector, RV controller, Inverter,
Coulombmeter, LCD, DCI controller, Energy storage battery BMS.

## MPPT — MC48xxN15 ailesi

- Kullanıcının kitapçığı (sayfa 08, teknik parametreler): MC4885N15 / MC48100N15 (150V PV),
  MC4885N25 / MC48100N25 (250V PV). 12/24/36/48V, 9–64V akü, maks. PV akımı 70A,
  şarj akımı 85A veya 100A (ayarlanabilir 0–85 / 0–100A), MPPT aralığı akü+2…120V (N15).
  Haberleşme satırı: "TTL / izole RS485, 9600, 1 stop, paritesiz", BLE 4.0,
  programlanabilir röle DPST 10A. Kullanıcı cihazda CAN portu olduğunu belirtti.
- [ ] Etiketteki tam model (85A mı 100A mı?)
- [ ] Kitapçıktaki haberleşme portu / RJ45 pin sayfası
- Aşağıdaki bilgiler yüklenen MC4860/4870 kılavuzundan; aynı ailede büyük ihtimalle geçerli:
- Şarj akımı limiti register **0xE001**, 0.00–100.00A.
- Kullanıcı tanımlı (USE) modda tüm voltaj eşikleri **9–17V** aralığında (12V bazlı).
  Varsayılanlar (kapalı kurşun asit): aşırı voltaj 16.0, eşitleme 14.6, boost 14.4, float 13.8,
  boost dönüş 13.2, aşırı deşarj dönüş 12.6, düşük voltaj uyarısı 12.0, aşırı deşarj 11.1,
  deşarj kesme 10.6V, gecikme 5s, eşitleme aralığı 30 gün, boost süresi 120 dk.
- Lityum modu tanıma koşulu: eşitleme aralığı = 0, eşitleme süresi = 0, sıcaklık kompanzasyonu = 0.
- Register haritası: [registers/srne_mc.yaml](../registers/srne_mc.yaml)

## BS48500 shunt

- 500A / 60V, 12–48V. Modbus RS485 + CAN + BLE. İkinci giriş (D2) marş aküsü voltajı.
- Ayarlar: kapasite, akü tipi, tam dolu voltajı, deşarj kesme voltajı, tam dolu kesme akımı,
  tam dolu tespit süresi, mevcut SOC, sıfır akım kalibrasyonu, DOD (%5 varsayılan).
- Uygulama şifresi varsayılan **123456** (kurulum kılavuzu, tüm cihazlar için).

## IBC12-3KW inverter

- Kullanıcı listesinde "SR-IC12" olarak geçti; yüklenen kılavuz IBC12-3KW. Etiketten teyit et.
- Modlar: OFF / ON / ECO (ECO: varsayılan 30W altı yükte kapanıp 1 dk'da bir kontrol eder).
- APP/haberleşme ile değiştirilen mod, fiziksel anahtar konumundan önceliklidir (son komut geçerli).

## SR-DB12

- 12 kanallı DC dağıtım kutusu (4×30A, 2×20A, 1×10A…), sigorta atık göstergesi, uzaktan
  açma/kapama, inverter uzaktan anahtarı. Aşırı deşarj/aşırı voltaj/aşırı akım/sıcaklık durumu
  ekran veya APP üzerinden okunuyor.

## DCI12-1230 DC-DC

- 30A, 10–16V giriş, şarj modu / güç modu. Varsayılan 12.5V üstünde başlar, 12.0V altında durur.
- Haberleşme: Bluetooth, TTL, RS485, CAN. Pin dizilimi bilinmiyor → ölç.

## Açık sorular

- [ ] Senin sisteminde hangi cihaz CU2'nin hangi portuna takılı?
- [ ] MPPT kablosu CU2'de TTL portuna mı gidiyor?
- [ ] CU2 ↔ cihaz hatlarında RS485 mi CAN mi aktif (ikisi de aynı kabloda)?
- [ ] RMA7 protokolü (RS485 115200, "özel")
- [ ] Telefon uygulamasının adı
