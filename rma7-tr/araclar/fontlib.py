import json,sys
sys.path.insert(0,'/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/araclar/tjc-usart-hmi-toolchain')
from usarthmi.zi_font import ZiFont
ROOT='/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr'
def load_fonts(tft_bytes):
    info=json.load(open(ROOT+'/analiz/inspect.json'))
    run=info['embedded_font_runs'][0];base=run['base_offset']
    fonts=[]
    for i,e in enumerate(run['entries']):
        hdr=tft_bytes[e['offset']:e['offset']+0x2c]
        s=base+e['data_start']
        body=tft_bytes[s:s+e['variable_data_len']]
        f=ZiFont.from_bytes(hdr+body,e['font_name'])
        fonts.append(dict(id=i,entry=e,body_start=s,font=f))
    return fonts
