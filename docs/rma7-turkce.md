# RMA7 Türkçe — tersine mühendislik planı

SRNE resmi Türkçe desteği vermiyor (21.10.2026 cevabı). Mümkün olup olmadığı RMA7'nin **içindeki
ekran tipine** bağlı. Önce açmadan, sadece dinleyerek öğreniyoruz.

## Aşama A — Hattı dinle (kasayı açmadan, 10 dakika)

RMA7, CU2'nin port 6'sına bağlı: RS485, 115200 baud.

Bağlantı (RMA7 kablosunun arasına breakout/splitter ile, **sadece dinleme**):

| CU2 port 6 pini | USB-RS485 |
|---|---|
| 7 (A/D+) | A |
| 6 (B/D-) | B |
| 5 (GND) | GND |

⚠ Pin 3 ve 8'de **13.2V besleme** var, bunlara hiçbir şey bağlama.

```
python tools\sniff.py --port COM5 --baud 115200 --hexdump --raw rma7.bin > rma7.txt
```
Kayıt sürerken RMA7'de sayfalar arasında gez, bir ayara gir-çık. 2-3 dakika yeter.

**Çıktı ne anlatır:**

| Gördüğün | Ekran tipi | Türkçe yolu |
|---|---|---|
| Satırlar `5a a5 ..` ile başlıyor | **DWIN DGUS** seri HMI | Ekranın UI dosyaları (resimler, fontlar) SD kartla yüklenir. Yazılar resimlerin içindeyse resimler Türkçe hazırlanır; metin değişkeniyse font + metin değişir. |
| ASCII satırlar, sonları `ff ff ff` (`page 1`, `t0.txt="Battery"` gibi) | **TJC / Nextion** tipi HMI | Yazıları CU2 gönderiyorsa araya bir ESP32 koyup **anında çeviririz** (ekrana dokunmadan). Ekranda gömülüyse .tft dosyası yeniden yapılır. |
| `01 03 ..` gibi Modbus | Ekranın içinde kendi işlemcisi var, CU2'den sadece sayı istiyor | Yazılar ekranın firmware'inde → zor yol (Aşama C). |
| Başka, düzensiz | Özel protokol | Kayıtları inceleyip karar veririz. |

## Aşama B — Fotoğraflar (açmadan)

- RMA7'nin arkası: etiket, model, varsa SD kart yuvası / küçük kapak / USB.
- Ayarlar menüsünde dil seçeneği var mı.

## Aşama C — İçini açmak (sadece gerekirse, garanti riski)

Kartın ve çiplerin üzerindeki yazıların net fotoğrafları (ana işlemci, flash çipi, SD yuvası,
"DWIN", "T5L", "TJC", "STM32", "GD32" gibi yazılar, test noktaları).

- **DWIN / TJC kartlarda** genelde SD kart yuvası vardır; UI güncellemesi SD kartla yapılır,
  geri dönüş de aynı yoldan mümkündür.
- **Özel işlemcili kartta** firmware'i okumak (SWD) çoğu zaman kilitlidir; yazı ve Türkçe karakter
  (ş, ğ, ı, İ, ç, ö, ü) eklemek için hem metinleri hem font tablosunu yamalamak gerekir.
  Riskli: tek ekran bozulabilir. Bu durumda önerim yapmamak veya önce tam yedek almak.

## Ara yol — Çevirmen ESP32 (ekrana dokunmadan)

Ekran yazıları CU2'den metin olarak alıyorsa (TJC/Nextion tipinde sık), CU2 ile RMA7 arasına iki
RS485 portlu bir ESP32 konur: CU2'den gelen her mesajı okur, İngilizce metinleri Türkçe'yle
değiştirir, ekrana iletir. Ekran ve CU2'nin yazılımı hiç değişmez; ESP32 çıkarılınca her şey
eskisi gibi olur. Gerekli: Waveshare kartın RS485'i + elindeki RS485 modülü (ikinci port).
