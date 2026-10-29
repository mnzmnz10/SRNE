# RMA7 V1.0.16 .tft — REA bulguları (2026-10-29, Hermes Telegram oturumu)

Kurulum düzeltmesi: REA'nın firmware aracı Binwalk 3.1.x istiyor; makinede yoktu.
- rustup (kullanıcı düzeyi) + `cargo install binwalk --version 3.1.0` → `~/.cargo/bin/binwalk`
  (fontconfig-dev sudo'suz: .deb'ler scratch'e açılıp PKG_CONFIG_PATH ile derlendi; çalışma anında sistem libfontconfig kullanılır)
- `~/.hermes/config.yaml` → `mcp_servers.rea.env.REA_BINWALK_COMMAND=/home/mnzasistan/.cargo/bin/binwalk`
  (açık oturumlar REA'yı yeniden bağlayınca görür; CLI: `REA_BINWALK_COMMAND=... rea inspect-firmware-regions <yol>`)

Sonuç (`regions.json`, evidence ev_db0c8368…): 2991 aday — 2910 JPEG (~8,6 MB), 80 "gpg_signed" + 1 zlib (5–234 bayt; yanlış pozitif).
TJC kendi kapsayıcısı olduğu için Binwalk metin/font/sayfa kodunu ayrıştırmıyor; bu kısım TJC araçlarıyla yapılmalı.

- Büyük JPEG'ler 1024×608 arka planlar (ev, tekne, van, karavan, römork); üzerlerinde İngilizce yazı yok.
  Örnekler `jpeg/`, kolaj `ornek.png`. Yani arayüz yazıları resim değil, font ile çizilen metin → çevrilebilir.
- Dil menüsü var (ofset ~28,38 MB): `中文(Simplified Chinese)`, `English(English)`, `Deutsch(German)`, `Espanol(Spain)`.
  V1.0.16 çok dilli altyapı taşıyor olabilir; Türkçe için bir dil yuvası (ör. Almanca/İspanyolca) kullanılabilir mi, araştırılmalı.
- Çözülmesi gerekenler: metin tablolarının yeri, fontların Türkçe glif (ğ ş ı İ ö ü ç) içerip içermediği, CRC/başlık yeniden hesabı.
- Ekrana yükleme yok; değiştirilmiş dosya Lordum'un ayrı onayı olmadan SD karta konmaz.
