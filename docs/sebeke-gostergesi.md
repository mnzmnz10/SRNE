# Şebeke (AC) göstergesi — CU2 tank girişiyle

İnverterde AC IN klemensi yok ve AC şarj cihazı sadece Bluetooth'lu. Bu yüzden RMA7'deki
"AC giriş voltajı" alanı hep 0 V kalır. Çözüm: şebeke var/yok bilgisini CU2'nin boş bir
**tank girişine** direnç olarak vermek. Böylece RMA7'de "Şebeke" adlı bir tank %0 / dolu görünür.

## Malzeme

| Parça | Nereden |
|---|---|
| 12V adaptör (ADS-40FSI-12) | Elinde var (Motorobit, Şubat 2026) |
| 12V röle, **bobini doğrudan 12V ile çeken**, kontağı NO/COM/NC | Oto yedek parçacıdaki 5 pinli 12V röle (+ soket) ya da tetik girişli bir röle modülü |
| 220Ω direnç | Elinde var (Motorobit, Mayıs 2026) |
| İnce 2 damarlı kablo | Elinde var |

⚠ Elindeki "Butonlu Röle Modülü 12V 10A" butona basınca konum değiştiren (kilitlemeli) tipteyse
bu iş için **uygun değil**: röle, adaptörde 12V olduğu sürece çekili, olmadığında bırakmış olmalı.
Modülde ayrı bir tetik girişi yoksa oto yedek parçacıdan normal bir 12V röle al (yerli, ucuz).

## Bağlantı

```
Şebeke prizi (transfer şalterinden ÖNCE, sadece kamp yeri elektriği varken enerjili)
   └── 12V adaptör ──(+12V / GND)──> Röle bobini (85 / 86)

Röle kontağı (5 pinli oto rölesi):
   30  (COM) ───────────────> CU2 tank girişi DATA   (ör. CH3)
   87a (NC)  ───────────────> CU2 tank girişi GND    → şebeke yokken 0 Ω
   87  (NO)  ──[ 220 Ω ]────> CU2 tank girişi GND    → şebeke varken 220 Ω
```

- Röle kontağı tamamen kuru kontak; CU2 tarafına hiçbir voltaj verilmez.
- Adaptörün 230V tarafını karavanın şebeke tesisatını yapan elektrikçiye bağlatın.

## Ayar ve deneme

1. SRNE uygulamasında o kanalı (ör. CH3) **tank / 0–190Ω** tipine ayarla.
2. Kanalın adı değiştirilebiliyorsa **"Şebeke"** yap.
3. Şebekeyi tak/çıkar, RMA7'deki değere bak:
   - Ters gösteriyorsa (şebeke varken %0): NC ve NO uçlarını yer değiştir.
   - Şebeke varken "hata/aralık dışı" görünüyorsa: 220Ω yerine iki 220Ω'u paralel bağla (110Ω).
   - Tank tipini 240–33Ω'a çevirmek de bir seçenek; o zaman hangi direncin "dolu" olduğunu
     deneyerek bulun.

## Alternatif / ek

Waveshare kart da aynı bilgiyi (ve istenirse şebeke voltajını/akımını) okuyup telefondaki
sayfasında gösterebilir; ama RMA7'de görünmesi için yukarıdaki tank yöntemi gerekir.
