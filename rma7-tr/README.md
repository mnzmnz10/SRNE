# SRNE RMA7 ekranı Türkçeleştirme

Hedef: `13050400010_RMA7(SRNE)_HMIMCU_05_V1.0.16_202602041130.tft` (TJC1060X570_011, 1024×600, TJC editör 1.67.1, X5 serisi).

## Bulgular
- REA bu biçimi açamıyor (`unsupported binary format`). Binwalk yok. Analiz, açık kaynak TJC/Nextion araçları (UNUF/TFTTool, YXerer668/tjc-usart-hmi-toolchain) ve kendi betiklerimizle yapıldı.
- Sağlamalar çözüldü ve yeniden üretiliyor: kaynak CRC'si (başlık 0x44), Header1 CRC'si ve dosya sonundaki CRC (`araclar/verify_crcs.py`, `araclar/tftcrc`).
- 14 font var, hepsi UTF-8 Roboto. 0–4 (16/20/24/28/32 px) doğrudan dizinli tabloya sahip, 65536 giriş, ASCII + Çince. 5–13 küçük alt kümeler (yaklaşık 90 karakter). Hiçbirinde Türkçe harf yoktu.
- Arayüz metinleri `0x1A80000` sonrasındaki nesne alanında düz UTF-8 olarak duruyor. Çoğu 3 kopya (açık/koyu tema). Yeni metin, İngilizce metnin bayt uzunluğunu aşamaz.

## Yöntem (`araclar/tr_patch.py`)
1. Türkçe harfler, fontun kendi taban harfinden + Roboto aksanından üretilir (`trglyphs.py`, `glyphcodec.py`).
2. 0–4: glif verisi, fontun sonundaki az kullanılan Çince karakterlerin yerine yazılır.
3. 5–13: font gövdesi büyütülür ve font 4'ün kuyruğuna taşınır, başlıktaki data_start/uzunluk/sayı güncellenir.
4. Metinler yerinde değiştirilir, sağlamalar yeniden hesaplanır.

## Geri dönüş
Orijinal V1.0.16 dosyası SD kartla yeniden yüklenir: `~/Stüdyo/projeler/srne-yedek/rma7-v1.0.16/`.
