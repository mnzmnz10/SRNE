import sys; sys.path.insert(0,'.')
from fontlib import *; from trglyphs import *; from glyphcodec import decode
import numpy as np
from PIL import Image
def render_line(f,res,text):
    h=f.character_height; cols=[]
    for ch in text:
        if res and ch in res:
            r=res[ch]; w=r['width']+r['kl']+r['kr']
            a=np.frombuffer(bytes(decode(r['data'],w,h)),dtype=np.uint8).reshape(h,w)
        elif ord(ch) in f.glyphs:
            g=f.glyphs[ord(ch)]; w=g.total_width; a=np.frombuffer(bytes(decode(g.data,w,h)),dtype=np.uint8).reshape(h,w)
        else: a=np.zeros((h,6),np.uint8)
        cols.append(a)
    return np.hstack(cols)
def sheet(rows,path,scale=1):
    W=max(r.shape[1] for r in rows); H=sum(r.shape[0]+4 for r in rows)
    can=np.full((H,W+8),255,np.uint8); y=0
    for r in rows: can[y:y+r.shape[0],4:4+r.shape[1]]=255-r; y+=r.shape[0]+4
    im=Image.fromarray(can)
    if scale!=1: im=im.resize((im.width*scale,im.height*scale),Image.NEAREST)
    im.save(path); return im.size
if __name__=='__main__':
    d=open(ROOT+'/analiz/rma7_v1.0.16.tft','rb').read()
    fs=load_fonts(d); rows=[]
    for x in fs:
        f=x['font']; res=build(f,'B' in f.font_name)
        rows.append(render_line(f,res,'Parlaklık Işık süresi Şebeke Ğ Ü Ö Ç İptal çğıöşü'))
    print(sheet(rows,ROOT+'/analiz/tr_glif_onizleme.png'))
