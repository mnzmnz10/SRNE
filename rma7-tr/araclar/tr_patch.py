"""RMA7 (TJC1060X570) TFT dosyasına Türkçe glif ekler ve metinleri çevirir.
Kullanım: python tr_patch.py GIRDI.tft CIKTI.tft ceviri.json
"""
import sys, json, struct
sys.path.insert(0, '/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/araclar')
sys.path.insert(0, '/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/araclar/tjc-usart-hmi-toolchain')
from fontlib import load_fonts
from trglyphs import build, TR
from usarthmi.tft_checksum import _crc32_like, update_tft_checksum
from usarthmi.tft_images import HEADER1_RESOURCE_CRC_OFFSET, _iter_words_le
from usarthmi.tft_patch import HEADER1_CRC_OFFSET

u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]
def w32(b, o, v): struct.pack_into('<I', b, o, v)

def entry_off(e, align8):
    o = e[5] | e[6] << 8 | e[7] << 16
    return o * 8 if align8 else o

def reserve_tail(raw, fx, need):
    """Doğrudan dizinli (CJK) fontun veri sonundan `need` bayt ayırır; o alanı kullanan
    CJK girişlerini boşaltır. Döner: (tablo başına göre ofset, mutlak adres, boşaltılan giriş sayısı)."""
    f = fx['font']; tstart = fx['body_start'] + f.descriptor_len
    n = f.character_count; data_end = fx['entry']['variable_data_len'] - f.descriptor_len
    ents = []
    for cp in range(n):
        o = tstart + cp * 10; e = raw[o:o + 10]
        if e[8] | e[9]:
            ents.append((entry_off(e, True), cp, o))
    ents.sort()
    empty = bytes(raw[tstart + 0xC7 * 10: tstart + 0xC7 * 10 + 10])  # boş giriş kalıbı
    assert empty[0] == 0 and empty[1] == 0 and empty[8] == 0
    start = data_end; freed = 0
    while data_end - start < need:
        off, cp, o = ents.pop()
        assert cp >= 0x3400, f'ASCII/Latin glif ({hex(cp)}) feda edilemez'
        start = off; raw[o:o + 10] = empty; freed += 1
    start = (start + 7) // 8 * 8
    while data_end - start < need:  # hizalama sonrası tekrar kontrol
        off, cp, o = ents.pop(); assert cp >= 0x3400
        start = off; raw[o:o + 10] = empty; freed += 1
    raw[tstart + start: tstart + data_end] = bytes(data_end - start)
    return start, tstart + start, freed

def patch_fonts(raw, log):
    fonts = load_fonts(bytes(raw))
    run_base = fonts[0]['body_start'] - fonts[0]['entry']['data_start']
    glyphs = {fx['id']: build(fx['font'], 'B' in fx['font'].font_name) for fx in fonts}
    # küçük alt küme fontlarının yeni gövdeleri
    small_bodies = {}
    for fx in fonts[5:]:
        f = fx['font']; g = glyphs[fx['id']]
        old = bytes(raw[fx['body_start']: fx['body_start'] + fx['entry']['variable_data_len']])
        dl = f.descriptor_len; n = f.character_count
        table = [old[dl + i * 10: dl + i * 10 + 10] for i in range(n)]
        data = old[dl + n * 10:]
        add = len(TR) * 10
        newtab = []
        for e in table:
            e = bytearray(e); o = entry_off(e, False) + add
            e[5:8] = o.to_bytes(3, 'little'); newtab.append(bytes(e))
        cur = (n + len(TR)) * 10 + len(data); extra = b''
        for ch in TR:
            r = g[ch]; e = bytearray(10)
            e[0:2] = ord(ch).to_bytes(2, 'little'); e[2] = r['width']; e[3] = r['kl']; e[4] = r['kr']
            e[5:8] = cur.to_bytes(3, 'little'); e[8:10] = len(r['data']).to_bytes(2, 'little')
            newtab.append(bytes(e)); extra += r['data']; cur += len(r['data'])
        newtab.sort(key=lambda e: e[0] | e[1] << 8)
        body = old[:dl] + b''.join(newtab) + data + extra
        assert len(body) < 1 << 24
        small_bodies[fx['id']] = body
    # büyük CJK fontlar: Türkçe glifler kendi kuyruklarına; küçük fontlar font 4'ün kuyruğuna
    for fx in fonts[:5]:
        f = fx['font']; g = glyphs[fx['id']]
        blobs = []
        for ch in TR:
            d = g[ch]['data']; blobs.append(d + bytes((-len(d)) % 8))
        need = sum(map(len, blobs))
        if fx['id'] == 4:
            need += sum(len(b) + 8 for b in small_bodies.values())
        rel, absaddr, freed = reserve_tail(raw, fx, need)
        tstart = fx['body_start'] + f.descriptor_len
        cur = rel
        for ch, blob in zip(TR, blobs):
            r = g[ch]; e = bytearray(10)
            e[0:2] = ord(ch).to_bytes(2, 'little'); e[2] = r['width']; e[3] = r['kl']; e[4] = r['kr']
            e[5:8] = (cur // 8).to_bytes(3, 'little'); e[8:10] = len(r['data']).to_bytes(2, 'little')
            raw[tstart + ord(ch) * 10: tstart + ord(ch) * 10 + 10] = e
            raw[tstart + cur: tstart + cur + len(blob)] = blob; cur += len(blob)
        hdr = fx['entry']['offset']
        w32(raw, hdr + 0x24, u32(raw, hdr + 0x24) - freed + len(TR))
        log.append(f"font {fx['id']} {f.font_name}: +{len(TR)} Türkçe glif, {freed} CJK glif feda edildi")
        if fx['id'] == 4:
            for sid, body in small_bodies.items():
                a = tstart + cur
                raw[a:a + len(body)] = body
                sfx = fonts[sid]; h = sfx['entry']['offset']
                w32(raw, h + 0x0C, sfx['font'].character_count + len(TR))
                w32(raw, h + 0x24, u32(raw, h + 0x24) + len(TR))
                w32(raw, h + 0x14, len(body))
                w32(raw, h + 0x18, a - run_base)
                log.append(f"font {sid} {sfx['font'].font_name}: {len(body)} bayt, 0x{a:X} adresine taşındı (+{len(TR)} glif)")
                cur += len(body) + 8

def patch_texts(raw, pairs, start, log):
    total = 0
    for en, tr in pairs:
        eb, tb = en.encode(), tr.encode()
        if len(tb) > len(eb):
            raise SystemExit(f'Çeviri uzun: {en!r}({len(eb)}) -> {tr!r}({len(tb)})')
        pat = eb + b'\x00'; i = start; n = 0
        while True:
            i = raw.find(pat, i)
            if i < 0: break
            raw[i:i + len(eb)] = tb + bytes(len(eb) - len(tb)); n += 1; i += len(eb)
        total += n; log.append(f'{en!r} -> {tr!r}: {n} yer')
    return total

def refresh_checksums(raw):
    ra = u32(raw, 0x38) and 0x20000
    rs = u32(raw, 0x40)
    res = _crc32_like(list(_iter_words_le(raw[0x20000:0x20000 + rs])))
    raw[HEADER1_RESOURCE_CRC_OFFSET:HEADER1_RESOURCE_CRC_OFFSET + 4] = res.to_bytes(4, 'little')
    raw[HEADER1_CRC_OFFSET:HEADER1_CRC_OFFSET + 4] = _crc32_like(list(raw[:HEADER1_CRC_OFFSET])).to_bytes(4, 'little')
    raw[:] = update_tft_checksum(bytes(raw), series=3)

if __name__ == '__main__':
    src, dst, tr_json = sys.argv[1:4]
    raw = bytearray(open(src, 'rb').read()); n0 = len(raw); log = []
    patch_fonts(raw, log)
    cfg = json.load(open(tr_json))
    patch_texts(raw, cfg['metinler'], 0x1A80000, log)
    assert len(raw) == n0
    refresh_checksums(raw)
    open(dst, 'wb').write(raw)
    print('\n'.join(log))
