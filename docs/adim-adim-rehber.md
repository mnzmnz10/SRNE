# Adım adım rehber: JK BMS verisini RMA7 ekranında göstermek

Hedef: 2 × 12.8V 310Ah akü + 2 × Bluetooth'lu JK BMS → Waveshare ESP32-S3-RS485-CAN köprü
→ CU2 BMS portu → RMA7 ekran.

Aşamalar:

| Aşama | Ne zaman | Kim |
|---|---|---|
| 0. Bilgisayarı hazırla | Hemen | Sen |
| 1. Uygulama/ekranı incele, BMS portunu RS485 ile dinle | Malzeme beklerken | Sen |
| 2. Kartla CAN tarafını dinle | Kart gelince | Sen (yazılımı ben hazırlarım) |
| 3. Köprü yazılımı + sahte veriyle ekran testi | Protokol belli olunca | Ben yazarım, sen yüklersin |
| 4. JK BMS'leri bağla, gerçek test | Aküler gelince | Birlikte |

Her aşamanın sonunda bana gönderilecekler **📤** ile işaretli.

---

## Aşama 0 — Bilgisayarı hazırla (bir kerelik)

Windows'a göre anlatıyorum; Mac/Linux'ta da aynı mantık.

### 0.1 Python
1. https://www.python.org/downloads/ → en güncel Python 3'ü indir.
2. Kurulumun ilk ekranında **"Add python.exe to PATH"** kutusunu işaretle → Install.
3. Kontrol: Başlat → `cmd` → `python --version` yaz → `Python 3.x.x` görmelisin.

### 0.2 Proje dosyaları
1. https://github.com/mnzmnz10/srne adresine git.
2. Dal (branch) seçiminden **`claude/blissful-babbage-l6tze7`** dalını seç.
3. Yeşil **Code** → **Download ZIP** → ör. `C:\srne` klasörüne çıkar.
4. `cmd`'de:
   ```
   cd C:\srne
   pip install -r requirements.txt
   ```

### 0.3 USB-RS485 sürücüsü ve COM portu
1. USB-RS485'i tak.
2. Başlat'a sağ tık → **Aygıt Yöneticisi** → **Bağlantı noktaları (COM ve LPT)**.
3. `USB-SERIAL CH340 (COM5)` gibi bir satır görmelisin. **COM numarasını not al.**
4. Görünmüyorsa veya sarı ünlem varsa sürücü eksik: çipi genelde **CH340**'tır
   ("CH340 driver" diye arat, WCH'nin sitesinden kur). FTDI veya CP210x de olabilir.

### 0.4 Yardımcı programlar

| Program | Ne için | Zorunlu mu |
|---|---|---|
| Python + bu repodaki `tools/sniff.py` | Hattı dinleyip çözmek (ana araç) | Evet |
| **CoolTerm** (ücretsiz) | Seri portu gözle görmek, hex görünüm | Önerilir, yedek araç |
| **PulseView** (sigrok, ücretsiz) | Lojik analizörle sinyal görmek | Sadece sorun olursa |
| Esptool web: https://espressif.github.io/esptool-js/ veya ESPHome Web: https://web.esphome.io | Karta yazılım yüklemek (tarayıcıdan, Chrome/Edge) | Aşama 2'de |
| **nRF Connect** (telefon uygulaması) | JK BMS'lerin Bluetooth MAC adresini bulmak | Aşama 4'te |

---

## Aşama 1 — Malzeme beklerken

### 1.1 Uygulamayı ve ekranı belgele (15 dk, en değerli iş)

1. SRNE uygulamasında CU2'ye bağlan. Tüm ayar menülerini gez. Akü/BMS ile ilgili her ekranın
   ekran görüntüsünü al. Özellikle şunları ara:
   - "BMS", "Battery communication", "Protocol", "Lithium", "Battery type"
   - Varsa protokol listesi (PYL, SRNE, JK, Pylontech, CAN, 485 gibi seçenekler)
2. RMA7'de **her sayfanın** fotoğrafını çek, özellikle akü sayfasının. Neyin gösterilebildiğini
   (SOC, voltaj, akım, sıcaklık, hücre voltajları, kalan süre, alarm) böyle anlarız.

📤 Ekran görüntüleri ve fotoğraflar.

### 1.2 Dinleme kablosunu hazırla

Bir patch kablonun bir ucunu kes, dış kılıfı ~5 cm soy, 8 teli ayır.
Standart (T568B) renkler ve CU2 **BMS portu** (port 11, "BMS RS485/CAN-8") anlamları:

| Pin | Tel rengi (T568B) | BMS portunda |
|---|---|---|
| 1 | Beyaz-turuncu | RS485 B/D- |
| 2 | Turuncu | RS485 A/D+ |
| 3 | Beyaz-yeşil | GND |
| 4 | Mavi | CAN_H |
| 5 | Beyaz-mavi | CAN_L |
| 6 | Yeşil | GND |
| 7 | Beyaz-kahve | RS485 A/D+ |
| 8 | Kahve | RS485 B/D- |

⚠ Kablo T568A ile yapılmış olabilir. **Renge güvenme**: multimetreyi süreklilik (bip) moduna al,
sağlam uçtaki her pini tek tek kesik uçtaki tellerle eşleştir ve not al. Telleri bantla etiketle
(1, 2, 3, 4, 5).

### 1.3 Portta tehlikeli voltaj var mı? (bağlamadan önce mutlaka)

1. Sistem açıkken kablonun sağlam ucunu CU2'nin **BMS portuna** tak. Kesik uçtaki teller
   birbirine değmesin.
2. Multimetre DC voltajda, siyah uç **pin 3**'te (GND). Kırmızı uçla her pini ölç ve yaz.
3. Beklenen: hepsi 0–5V arası. Kılavuza göre BMS portunda besleme pini yok.
   **Herhangi bir pin 5V'un üstündeyse dur, hiçbir şey bağlama, bana yaz.**

📤 8 pinin voltaj tablosu.

### 1.4 RS485 tarafını dinle

**Bağlantı** (portta başka hiçbir şey takılı değil):

| USB-RS485 | Kablo teli |
|---|---|
| A / A+ / D+ | pin 2 (turuncu) |
| B / B- / D- | pin 1 (beyaz-turuncu) |
| GND (varsa) | pin 3 (beyaz-yeşil) |

**Dinle:**
```
cd C:\srne
python tools\sniff.py --port COM5 --baud 9600 --hexdump --raw bms-9600.bin > bms-9600.txt
```
(COM5 yerine kendi port numaranı yaz. Komut çalışırken ekrana bir şey yazmaz, çıktı dosyaya gider.)

Komut çalışırken şunları yap:
1. **2 dakika** bekle.
2. CU2'yi **kapatıp aç** (besleme sigortası veya fişi ile). Bazı cihazlar BMS'i sadece açılışta arar.
3. Uygulamada akü/BMS ayarına girip çık, varsa protokol seçimini değiştir.
4. 1 dakika daha bekle, sonra `Ctrl+C` ile durdur.

Aynısını **19200** ve **115200** için tekrarla (dosya adlarını değiştir: `bms-19200.txt` vb.).

**Sonucu yorumlama:** `bms-9600.txt` dosyasını Not Defteri ile aç.

| Dosyada gördüğün | Anlamı | Sonraki adım |
|---|---|---|
| Satırlarda `\|~20...\|` gibi okunabilir metin | **Pylontech RS485** protokolü | En kolay senaryo, JK bunu destekliyor |
| `01 03 00 ...` gibi düzenli tekrar eden baytlar | Modbus: CU2 bir BMS'i sorguluyor | Aynı komutu `--hexdump` olmadan çalıştır, çözülmüş halini de gönder |
| Anlamsız, düzensiz baytlar | Baud yanlış ya da A/B ters | A ile B'yi yer değiştirip tekrar dene |
| Dosya boş, hiçbir baudda bir şey yok | CU2 RS485'ten BMS aramıyor | Büyük ihtimalle CAN kullanıyor → Aşama 2 |

**Alternatif (Python'la uğraşmak istemezsen): CoolTerm**
Options → Serial Port: COM5, 9600, 8, None, 1 → Connect. Görünüm düğmesinden **Hex** görünüme
geç. Veri akıyor mu gözle görürsün. Kaydetmek için Connection → Capture to Text File.

📤 `bms-*.txt` dosyaları (boş olsalar bile "boş" diye bildir).

### 1.5 (İsteğe bağlı) Diğer portları da dinle

Aynı yöntemle, **sadece dinleyerek** (tek yönlü, bir şey gönderilmez), çalışan bir cihazın hattını da
kaydedebilirsin. Örneğin shunt ile CU2 arasına splitter veya breakout koyarak. Bu, SRNE'nin kendi
cihazlarıyla nasıl konuştuğunu gösterir. İlk öncelik BMS portu.

---

## Aşama 2 — Waveshare kart gelince

### 2.1 Kartı tanı
1. Kartı sadece USB-C ile bilgisayara tak (12V'a henüz bağlama). Işıklar yanmalı.
2. Aygıt Yöneticisi'nde yeni bir COM portu çıkmalı (ESP32-S3 kendi USB'siyle görünür).
3. Karttaki klemenslerin üzerindeki yazıların fotoğrafını çek (CANH, CANL, A, B, GND, V+, V-),
   varsa DIP switch veya jumper'ları da çek (120Ω sonlandırma ayarı).

📤 Kart fotoğrafları.

### 2.2 Dinleme yazılımını yükle
Karta özel dinleme yazılımını ben hazırlayıp repoya koyacağım (pin atamalarını kartın belgesinden
alacağım). Yazılım hem CAN'i (listen-only, hatta hiçbir şey göndermez) hem RS485'i dinler.
Yükleme tarayıcıdan yapılacak: https://web.esphome.io → **Connect** → portu seç →
**Install** → verdiğim `.bin` dosyasını seç. Ayrıntılı adımları yazılımla birlikte vereceğim.

### 2.3 Kartı BMS portuna bağla

| Kart klemensi | Kablo teli |
|---|---|
| CAN H | pin 4 (mavi) |
| CAN L | pin 5 (beyaz-mavi) |
| RS485 A | pin 2 (turuncu) |
| RS485 B | pin 1 (beyaz-turuncu) |
| GND | pin 3 (beyaz-yeşil) |

Kart ilk dinleme sırasında USB'den beslensin, 12V gerekmez.

### 2.4 CAN'i dinle
```
python tools\rvc_sniff.py --esp32 COM7 --log bms-can.candump
```
Yine 2 dakika bekle, CU2'yi kapatıp aç, uygulamadan BMS ayarlarına gir. Sonra:
```
python tools\rvc_sniff.py --candump bms-can.candump --summary > bms-can-ozet.txt
```
Not: Portta cevap veren bir cihaz olmadığı için CU2 aynı CAN mesajını sürekli tekrarlayabilir.
Bu normal, mesajın ID'si bize protokolü söyler. 250k'da bir şey yoksa 500k'yı deneriz
(yazılımda seri komutla değiştirilebilecek).

📤 `bms-can.candump` ve `bms-can-ozet.txt`.

### 2.5 Protokolü belirleme (bunu ben yapacağım)

| Bulgu | Köprü ne konuşacak |
|---|---|
| RS485'te `~20...` | Pylontech RS485 |
| RS485'te Modbus sorguları | SRNE BMS Modbus protokolü (istenen register'lara cevap) |
| CAN'de 0x351/0x355/0x356/0x359 aralığında ID'ler veya bunları bekleyen istekler | Pylontech CAN |
| CAN'de 29-bit RV-C mesajları | RV-C (DC_SOURCE_STATUS vb.) |
| Hiçbir şey | CU2 pasif dinliyor: yaygın protokolleri sırayla deneriz (Aşama 3'teki sahte veri testiyle) |

---

## Aşama 3 — Köprü yazılımı ve sahte veriyle ekran testi

Protokol belli olunca köprü yazılımını ben yazacağım (ESPHome tabanlı).

### 3.1 Sahte veri testi (aküler gelmeden ekran yolunu kanıtlar)
Yazılımın bir **simülasyon modu** olacak: JK yerine sabit değerler gönderir. Örnek değerler:
SOC %55, 13.20V, −5A, 22°C.

Güvenlik: bu test sırasında CU2 bu veriyi şarj kontrolü için kullanabilir. O yüzden:
1. MPPT'nin PV girişini (DB12/panel sigortası) ve şebeke şarjını **kapat**, DC-DC'yi motor
   çalışmıyorken test et.
2. Simülasyondaki şarj limitleri güvenli ve düşük tutulacak (ör. 13.8V / 10A).
3. Kartı BMS portuna tak, 12V'u 1A sigortayla ver.
4. RMA7'de akü sayfasına bak: SOC %55 görünüyor mu?

Görünüyorsa ekran yolu çalışıyor demektir. Geriye sadece gerçek JK verisini bağlamak kalır.

### 3.2 Kalıcı besleme
Kartın V+/V− klemensine: karavan 12V → **1A cam sigorta** (elindeki 5x20 sigorta yuvası) →
kart V+. Eksi → kart V−. Sürekli besleme olan bir hat seç (DB12'de sabit çıkış). Böylece
anahtar kapalıyken de akü görünür. Kart çok az akım çeker.

---

## Aşama 4 — Aküler ve JK BMS'ler gelince

### 4.1 JK BMS ayarları (JK uygulamasıyla, her BMS için)
- Hücre sayısı: **4**, kapasite: **310Ah**, kimya: LiFePO4.
- Koruma değerleri LiFePO4 için muhafazakâr seçilmeli (örnek, hücre başına):
  aşırı şarj koruması 3.65V, şarj/dengeleme bitişi 3.45–3.50V, düşük voltaj koruması 2.80V.
  Kendi hücrelerinin datasheet'ini esas al.
- BMS'lere ayırt edici isim ver (ör. `AKU-1`, `AKU-2`).

### 4.2 Aküleri paralel bağlamadan önce
- İki aküyü **ayrı ayrı tam doldur** (voltajları birbirine 0.05V yakın olsun), sonra paralelle.
- Akülerden ana baraya giden kablolar **aynı uzunlukta ve kesitte** olsun. Akım dengeli paylaşılır.
- SRNE shunt kapasitesini **620Ah** yap (uygulamadan).

### 4.3 MAC adreslerini bul
Telefonda **nRF Connect** → Scan → `JK-...` veya verdiğin isimle görünen cihazların MAC
adreslerini (`C8:47:8C:xx:xx:xx` gibi) not al. Taramadan önce JK uygulamasını kapat, yoksa BMS
meşgul görünür.

📤 İki MAC adresi ve BMS modeli (JK uygulamasının "About/Hakkında" ekranından).

### 4.4 Köprüyü gerçek moda al
Sana vereceğim ayar dosyasına (`secrets.yaml`) MAC adreslerini ve WiFi bilgini yazacaksın,
web.esphome.io'dan tekrar yükleyeceksin. Sonra:
1. Kartın web sayfasında (`http://jk-kopru.local` veya IP adresi) iki BMS'in de
   **"bağlı"** göründüğünü, voltaj ve SOC'lerin JK uygulamasıyla aynı olduğunu kontrol et.
2. RMA7'de akü değerlerini kontrol et.

### 4.5 Güvenlik testleri (sırayla)
1. **Bir BMS'i kapat** (ya da Bluetooth menzilinden çıkar). Ekranda uyarı çıkmalı, şarj akımı
   limiti tek akü seviyesine düşmeli.
2. **Kartın 12V'unu kes.** CU2 BMS'i kaybettiğini göstermeli ve kendi ayarlarına dönmeli.
   Şarj durmamalı veya kontrolsüz artmamalı.
3. PV'yi aç, shunt'tan şarj akımını izle. Limitlerin üstüne çıkmamalı.
4. İlk birkaç gün şarj sırasında hücre voltajlarını (JK uygulaması veya kartın web sayfası) izle.

### 4.6 SRNE cihazlarının kendi ayarları
Köprü çalışsa da MPPT, inverter ve DC-DC'nin akü ayarlarını da uygulamadan **lityum / kullanıcı
tanımlı** yapıp JK ile uyumlu değerlere çek (ör. boost 14.2V, float 13.5V, düşük voltaj kesme
~12.0V). Köprü koparsa sistem bu güvenli ayarlarla çalışmaya devam eder.

---

## Ekranda neler görünecek?

- **RMA7:** CU2 BMS verisini kabul edince, RMA7'nin akü sayfasında desteklediği alanlar kendiliğinden
  dolar (SOC, voltaj, akım, sıcaklık; RMA7 destekliyorsa alarmlar ve hücre bilgileri).
  RMA7'ye yeni bir sayfa eklenemez, sadece var olan alanlar dolar.
- **Telefon:** Kartın kendi web sayfası her iki akünün tüm ayrıntılarını gösterir: hücre voltajları,
  dengeleme, sıcaklıklar, döngü sayısı. İstersen Home Assistant'a da bağlanır.
- **RMA7 bazı alanları göstermezse** (ör. hücre voltajları): ikinci küçük bir ekran eklenebilir
  (elindeki düz ESP32 + ekran modülü).

---

## Sorun giderme

| Sorun | Olası neden / çözüm |
|---|---|
| COM portu görünmüyor | Sürücü eksik (CH340/CP210x) ya da USB kablosu sadece şarj kablosu |
| `sniff.py` "could not open port" | Port numarası yanlış ya da CoolTerm gibi başka bir program portu kullanıyor |
| Sürekli anlamsız bayt | Baud yanlış veya A/B ters |
| CAN'de hiç mesaj yok | CANH/CANL ters, GND bağlı değil, baud 250k/500k farkı ya da CU2 CAN'i kullanmıyor |
| CAN mesajları kesik kesik veya hata | Sonlandırma: sistem kapalıyken CANH–CANL arası ~60Ω olmalı. Açık devreyse kartın 120Ω'unu aç |
| Köprü JK'ya bağlanamıyor | JK uygulaması telefonda açık (BMS tek bağlantı kabul eder), MAC yanlış ya da mesafe fazla |
| RMA7'de değer yok ama kart veri gönderiyor | Protokol ya da ID uymuyor → kartın loglarını ve CU2 ayar ekranını gönder |
