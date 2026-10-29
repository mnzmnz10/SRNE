# SRNE karavan projesi — sohbet özeti (29.10.2026)

## Sistem
- **SR-CU2 G2** (fw V3.0.8 / V3.0.2, hw 00030000) — merkez; RS485/CAN (RV-C) portları, 6 röle, 8 sıcaklık/tank girişi
- **RMA7** 7" ekran — içi **TJC1060X570_011C** (TJC X5 HMI), arayüz sürümü **Ver 1.0.14**, microSD yuvalı; CU2 port 6, RS485 115200; ekran şifresi 666666
- **MC4885N25** MPPT (85A, 250V PV), 12V 3kW inverter (**AC IN yok**), **DCI12-1230** DC-DC, **BS48500** shunt, **SR-DB12**
- Eklenecek: SRNE **AC serisi şarj cihazı** (sadece Bluetooth), ayrı **transfer şalteri**
- Aküler: **2 × 12.8V 310Ah LiFePO4** paralel, her birinde Bluetooth'lu **JK BMS 200A** (model belli değil)
- Waveshare **ESP32-S3-RS485-CAN** kartı sipariş edildi

## Varılan kararlar
1. **Akü göstergesi RMA7'de shunt ile**: kapasite 620Ah, lityum, tam dolu ~13.9V, kesme ~12.0V,
   tam dolu akımı ~10–12A. Tüm eksiler shunt'ın yük tarafına.
2. **JK BMS verisi** (akü başına, hücre voltajları, sıcaklık, alarm) → Waveshare kart Bluetooth ile
   okur, **telefon/web sayfasında Türkçe** gösterir. CU2'ye veri gönderilmez (şarj kontrolüne dokunulmaz).
3. **Şebeke göstergesi**: 12V adaptör (transfer şalterinden önce) → 12V röle → CU2 boş tank girişi
   (0Ω / 220Ω). RMA7'de "Şebeke" tankı olarak görünür. Şarj akımı shunt'tan görünür.
4. **Türkçe RMA7**: Resmi destek yok (SRNE: sadece İngilizce; yeni RMA10 çok dilli). Ekran arayüz
   dosyası (.tft) ekrandan geri okunamıyor. SRNE'den Ver 1.0.14 dosyası istendi.
   Dosya gelirse önce yedeklenecek, ekrana hiçbir şey yüklenmeden incelenecek.

## SRNE yazışması (service@ / wujue@szshuori.com — Zeno)
- 21.10: AC giriş voltajı RMA7'de görünür (bizim inverterde AC IN yok → hep 0V);
  Türkçe yok; BMS portu ve CU2/RMA7 protokolleri iç protokol, paylaşılmıyor.
- 27.10: Kurtarma amaçlı RMA7 dosyası istendi.
- 28.10: Zeno ekran sürümünü sordu, dosya arayacağını söyledi; RMA10 çok dilli dedi.
  Cevap: **Ver 1.0.14** gönderildi.
- 29.10: Zeno dosyaları WhatsApp'tan gönderdi: `RMA7 Screen Upgrade Tutorial.docx` (6,6 MB) ve
  `13050400010_RMA7(SRNE)_HMIMCU_05_V1.0.16_….tft` (31,8 MB). **Gelen sürüm V1.0.16**, ekrandaki
  1.0.14 → CU2 (V3.0.8/V3.0.2) ile uyumluluğu soruldu. SD kart kapasite sınırı var (talimatta).
  Dosyalar yedeklenecek, ekrana henüz yüklenmeyecek.

## Bekleyen işler
- [ ] Shunt ayarları + RMA7 akü sayfası fotoğrafı
- [ ] Şebeke göstergesi düzeneği (5 pinli 12V oto rölesi gerekebilir)
- [ ] Waveshare kart gelince: CU2 BMS portunu dinleme (RS485 + CAN)
- [ ] (İsteğe bağlı) CU2 port 6 / RMA7 hattını dinleme (USB-RS485, pin 7/6/5; 3 ve 8'de 13.2V)
- [ ] RMA7 V1.0.16 dosyalarını bilgisayar + Drive'a yedekle, talimatı birlikte oku; uyumluluk cevabını bekle
- [ ] Aküler gelince: JK ayarları, MAC adresleri, köprü yazılımı

## Repo
GitHub `mnzmnz10/srne`, dal `claude/blissful-babbage-l6tze7` — dokümanlar `docs/`, araçlar `tools/`,
ESP32 yazılımları `firmware/`.
