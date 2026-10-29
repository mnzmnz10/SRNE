"""TJC .zi v6 glif RLE kod çözücü/kodlayıcı (bitdepth 3 = 8 seviye gri)."""
def decode(data, w, h):
    a=bytearray(w*h); p=0
    if not data: return a
    bd=data[0]
    def put(v,n):
        nonlocal p
        for _ in range(n):
            if p<len(a): a[p]=v
            p+=1
    sh=lambda s:max(0,min(255,(255//7)*s))
    for it in data[1:]:
        m=it>>6; m2=(it>>5)&1; n=it&31
        if m==0: put(255 if m2 else 0,n)
        elif m==1: put(0,n); put(255,1+m2)
        elif m==2:
            if bd==1: put(0,n); put(255,3+m2)
            else: put(0,(it>>3)&7); put(sh(it&7),1)
        else:
            if bd==1: put(0,(it>>3)&7); put(255,it&7)
            else: put(sh((it>>3)&7),1); put(sh(it&7),1)
        if p>=len(a): break
    return a

def quant(v):  # 0..255 -> 0..7
    return max(0,min(7,int(round(v*7/255))))

def encode(alpha, w, h):
    q=[quant(v) for v in alpha]; n=len(q); out=bytearray([3]); i=0
    while i<n:
        if q[i]==0:
            r=1
            while i+r<n and q[i+r]==0 and r<31: r+=1
            if r>=2 or i+1>=n:
                out.append(r); i+=r; continue
            # tek sıfır + gölge: mode2 (whites=1, shade)
            out.append(0x80|(1<<3)|q[i+1]); i+=2; continue
        if q[i]==7:
            r=1
            while i+r<n and q[i+r]==7 and r<31: r+=1
            if r>=2 or i+1>=n:
                out.append(0x20|r); i+=r; continue
        if i+1<n:
            out.append(0xC0|(q[i]<<3)|q[i+1]); i+=2
        else:
            out.append(0x80|q[i]); i+=1
    return bytes(out)
