import json,sys
sys.path.insert(0,'.')
from usarthmi.zi_font import ZiFont
F='/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/analiz/rma7_v1.0.16.tft'
d=open(F,'rb').read()
info=json.load(open('/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/analiz/inspect.json'))
run=info['embedded_font_runs'][0]; base=run['base_offset']
TR='çÇğĞıİöÖşŞüÜ'
out=[]
for i,e in enumerate(run['entries']):
    hdr=d[e['offset']:e['offset']+0x2c]
    body=d[base+e['data_start']:base+e['data_start']+e['variable_data_len']]
    f=ZiFont.from_bytes(hdr+body,e['font_name'])
    cps=set(f.glyphs)
    have=''.join(c for c in TR if ord(c) in cps); miss=''.join(c for c in TR if ord(c) not in cps)
    latin=sum(1 for c in cps if 0x80<=c<0x250)
    print(i,e['font_name'],e['char_height'],'glyphs',len(cps),'latin-ext',latin,'TR var:',have,'yok:',miss)
    out.append(dict(id=i,name=e['font_name'],h=e['char_height'],n=len(cps),tr_have=have,tr_miss=miss))
json.dump(out,open('/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/analiz/font_coverage.json','w'),ensure_ascii=False,indent=1)
