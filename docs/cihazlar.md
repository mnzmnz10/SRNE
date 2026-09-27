# Cihaz envanteri ve bilinenler

Etiket fotoğrafları ve port bilgileri geldikçe bu dosyayı güncelle.

## SR-CU2 Master Control

- SRNE cihazlarını birbirine bağlayan merkez. Uygulama için Bluetooth ve WiFi var.
- Satıcı sayfalarına göre SRNE şarj cihazları ve inverterler için **RS485 / CAN** portları,
  12V yükler için **6 × 6A röle çıkışı**, tank seviye probları ve sıcaklık sensörü girişleri var.
- RMA7 ekran ve BS serisi shunt ile birlikte çalışıyor.
- Açık sorular:
  - [ ] Her cihaz ayrı portta mı (yıldız), yoksa hepsi tek hatta mı (daisy-chain)?
  - [ ] Port etiketleri, RJ45 pin dizilimi
  - [ ] RS485 mi CAN mi, baud
  - [ ] Cihazları hangi slave adresleriyle sorguluyor
  - [ ] RMA7 ile arasındaki protokol
  - [ ] Telefon uygulamasının adı, BLE/WiFi protokolü

## RMA7 LCD Display

- 7" dokunmatik; solar girişi, AC/DC yükler, akü SOC ve tank seviyelerini gösteriyor.
- [ ] CU2'ye hangi kabloyla bağlı, master mı slave mi? (Ekran CU2'den veri mi istiyor,
      CU2 ekrana veri mi itiyor?)

## MC4870N15 MPPT

- 12/24/36/48V, 70A, 150V PV. SRNE ML/MC serisi Modbus RTU protokolü.
- Varsayılan: 9600 8N1, slave adresi 1 (CU2 farklı atamış olabilir).
- Register haritası: [registers/srne_mc.yaml](../registers/srne_mc.yaml) — tamamı doğrulanmamış.

## SR-IC12 3kW

- 12V, yüksek frekanslı saf sinüs inverter + şebeke şarjı.
- SRNE inverter RS485 Modbus protokolü: 9600 baud, 8N1, tek istekte en fazla 20 register,
  32 slave'e kadar, tekil bağlantıda "evrensel adres" ile adres atanabiliyor.
- [ ] Register haritası (SRNE "PV Inverter RS485 MODBUS Communication Protocol" PDF'inden
      çıkarılacak, sonra dinleme ile doğrulanacak)

## 30A DC-DC Charger

- [ ] Model kodu, iletişim portu var mı

## Battery Shunt

- [ ] Model (BS48500?), CU2'ye bağlantı tipi. SOC hesabını shunt mı CU2 mi yapıyor?

## DB-12 Distribution Box

- 4 PV girişi (60A), 2 çıkış. RMA7/CU2 ile "entegre" deniyor.
- [ ] İletişim portu var mı, yoksa tamamen pasif mi?

## Akü

- [ ] Kimya, kapasite, voltaj, BMS modeli ve iletişim (BT/RS485/CAN)
