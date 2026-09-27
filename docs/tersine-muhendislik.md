# Tersine mühendislik adımları

## 1. Pinleri ve fiziksel katmanı bul (sistem kapalıyken başla)

Kabloların çoğu RJ45. SRNE portlarında genelde bazı pinlerde **akü voltajı / 5V besleme**
olur (BT modülünü beslemek için). Rastgele bağlantı ESP32'yi veya adaptörü yakabilir.

1. Bir RJ45 **ara geçiş / splitter** (ya da kesip açılmış yedek kablo) hazırla; orijinal
   kabloyu bozma.
2. Sistem açık, multimetre ile her pini GND'ye göre ölç ve not al:
   - 12–14V veya 5V sabit → besleme
   - 0V → GND
   - ~2–3V civarı dalgalanan iki pin → veri hattı (A/B veya CANH/CANL)
3. Veri hattını ayırt et:
   - **RS485**: boşta A > B (ör. A ≈ 3V, B ≈ 2V). Veri anında ikisi zıt yönde oynar.
   - **CAN**: boşta ikisi de ≈ 2.5V. Veri anında CANH ≈ 3.5V'a çıkar, CANL ≈ 1.5V'a iner.
   - **TTL UART / RS232** de olabilir (RS232'de ±5–12V görürsün).

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

**CAN ise** — ESP32'nin dahili TWAI denetleyicisi + SN65HVD230 gibi bir transceiver ile
listen-only modda dinlenir (firmware ayrıca eklenecek).

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
