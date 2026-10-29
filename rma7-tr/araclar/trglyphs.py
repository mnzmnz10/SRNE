"""Türkçe harfleri mevcut TJC font glifleri + Roboto aksanlarından üretir."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from glyphcodec import decode, encode, quant
ROBOTO='/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/araclar/roboto/Roboto-var.ttf'
TR={'ç':'c','Ç':'C','ğ':'g','Ğ':'G','ö':'o','Ö':'O','ş':'s','Ş':'S','ü':'u','Ü':'U','ı':'i','İ':'I'}

def tjc_mask(font,ch):
    g=font.glyphs[ord(ch)]; w=g.total_width; h=font.character_height
    return np.frombuffer(bytes(decode(g.data,w,h)),dtype=np.uint8).reshape(h,w).astype(np.int32), g

def bbox(m,thr=60):
    ys,xs=np.where(m>thr)
    if len(ys)==0: return None
    return xs.min(),ys.min(),xs.max(),ys.max()

def pil_render(ch,size,bold):
    f=ImageFont.truetype(ROBOTO,size); f.set_variation_by_axes([700 if bold else 400,100])
    im=Image.new('L',(size*3,size*3),0); ImageDraw.Draw(im).text((size,size*2),ch,font=f,fill=255,anchor='ls')
    return np.array(im).astype(np.int32)

def calibrate(font,base,bold):
    m,_=tjc_mask(font,base); b=bbox(m); th=b[3]-b[1]+1
    best=None
    for s in range(6,120):
        pb=bbox(pil_render(base,s,bold)); ph=pb[3]-pb[1]+1
        if best is None or abs(ph-th)<best[0]: best=(abs(ph-th),s)
    return best[1]

def make(font,ch,bold):
    base=TR[ch]
    m,g=tjc_mask(font,base); h,w=m.shape
    out=m.copy()
    if ch=='ı':
        rows=[(m[y]>60).any() for y in range(h)]
        b=bbox(m); y=b[1]
        while y<h and rows[y]: y+=1   # nokta
        out[:y,:]=0
        return out,g
    s=calibrate(font,base,bold)
    pb=pil_render(base,s,bold); pt=pil_render(ch,s,bold)
    mark=np.clip(pt-pb,0,255)
    # ince taban farklarını at
    mark[mark<40]=0
    mb=bbox(mark,10)
    if mb is None: return out,g
    bb_p=bbox(pb); bb_t=bbox(m)
    # taban harf kutusunu hizala (sol-alt değil: sol-üst + yükseklik eşleşmesi)
    dx=bb_t[0]-bb_p[0]; dy=bb_t[3]-bb_p[3]
    ys,xs=np.where(mark>0)
    clipped=0
    for y,x in zip(ys,xs):
        ty,tx=y+dy,x+dx
        if 0<=ty<h and 0<=tx<w: out[ty,tx]=max(out[ty,tx],mark[y,x])
        else: clipped+=1
    return out,g

def build(font,bold):
    res={}
    for ch in TR:
        r=make(font,ch,bold)
        arr,g=r[0],r[1]
        h,w=arr.shape
        data=encode(arr.astype(np.uint8).flatten().tolist(),w,h)
        res[ch]=dict(data=data,width=g.width,kl=g.kerning_left,kr=g.kerning_right,mask=arr)
    return res
