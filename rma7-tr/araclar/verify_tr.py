"""Yamalı TFT'yi bağımsız olarak doğrular: font başlıklarını dosyadan okur, Türkçe metni
yamalı fontlarla çizer, sağlamaları kontrol eder."""
import sys, struct
sys.path.insert(0,'/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/araclar')
sys.path.insert(0,'/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/araclar/tjc-usart-hmi-toolchain')
from usarthmi.zi_font import ZiFont
from preview_tr import render_line, sheet
RUN=0x768ED3; N=14
def fonts_from_file(d):
    out=[]
    for i in range(N):
        h=d[RUN+i*0x2c:RUN+(i+1)*0x2c]; assert h[:4]==b'\x04\xff\x00\x0a'
        ln=struct.unpack_from('<I',h,0x14)[0]; ds=struct.unpack_from('<I',h,0x18)[0]
        out.append(ZiFont.from_bytes(h+d[RUN+ds:RUN+ds+ln],f'font{i}'))
    return out
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); fs=fonts_from_file(d); rows=[]
    TRS='çÇğĞıİöÖşŞüÜ'
    for i,f in enumerate(fs):
        miss=[c for c in TRS if ord(c) not in f.glyphs]
        asc=sum(1 for c in f.glyphs if c<0x80)
        print(i,f.font_name,'glif',len(f.glyphs),'ascii',asc,'eksik TR:',''.join(miss) or 'yok')
        rows.append(render_line(f,None,'Ayarlar/Ekran Parlaklık Işık süresi Açık/Koyu İnvertör düğmesi ŞĞÜÖÇ'))
    print(sheet(rows,sys.argv[2]))
