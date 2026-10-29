import sys; sys.path.insert(0,'/home/mnzasistan/Stüdyo/projeler/srne-rma7-tr/araclar/tjc-usart-hmi-toolchain')
from usarthmi.tft_checksum import _crc32_like, calculate_tft_checksum
from usarthmi.tft_images import HEADER1_RESOURCE_CRC_OFFSET, _iter_words_le
from usarthmi.tft_patch import HEADER1_CRC_OFFSET
raw=open(sys.argv[1],'rb').read()
ra,rs=0x20000,int.from_bytes(raw[0x40:0x44],'little')
res=_crc32_like(list(_iter_words_le(raw[ra:ra+rs])))
st=int.from_bytes(raw[HEADER1_RESOURCE_CRC_OFFSET:HEADER1_RESOURCE_CRC_OFFSET+4],'little')
h=_crc32_like(list(raw[:HEADER1_CRC_OFFSET])); hs=int.from_bytes(raw[HEADER1_CRC_OFFSET:HEADER1_CRC_OFFSET+4],'little')
f=calculate_tft_checksum(raw,series=3); fs=int.from_bytes(raw[-4:],'little')
print(f'resource {res:08X}/{st:08X} {res==st}  header1 {h:08X}/{hs:08X} {h==hs}  file {f:08X}/{fs:08X} {f==fs}')
