# Araç kurulumu

```bash
cd rma7-tr/araclar
git clone --depth 1 https://github.com/UNUF/TFTTool.git
git clone --depth 1 https://github.com/YXerer668/tjc-usart-hmi-toolchain.git
mkdir -p tjc-usart-hmi-toolchain/external && ln -s ../../TFTTool tjc-usart-hmi-toolchain/external/TFTTool
python3 -m venv .venv && .venv/bin/pip install Pillow PyYAML pyserial numpy
mkdir -p roboto && curl -L -o roboto/Roboto-var.ttf "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf"
gcc -O2 -o tftcrc tftcrc.c
```

`.tft` dosyaları depoda yok (SRNE'nin yazılımı). Orijinal V1.0.16'yı `../analiz/rma7_v1.0.16.tft` olarak koy, sonra:

```bash
cd tjc-usart-hmi-toolchain && ../.venv/bin/python -m usarthmi --json tft inspect --file ../../analiz/rma7_v1.0.16.tft > ../../analiz/inspect.json
cd .. && .venv/bin/python tr_patch.py ../analiz/rma7_v1.0.16.tft ../cikti/RMA7_TR.tft ../ceviri/poc_ekran_ayarlari.json
.venv/bin/python verify_tr.py ../cikti/RMA7_TR.tft ../analiz/onizleme.png && .venv/bin/python verify_crcs.py ../cikti/RMA7_TR.tft
```
Not: betiklerdeki mutlak yollar `/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr` kökünü varsayıyor; başka makinede `fontlib.ROOT` ve `sys.path` satırlarını düzelt.
