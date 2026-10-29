#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static uint32_t tn[256], tr[256];
void init(){for(uint32_t i=0;i<256;i++){uint32_t c=i<<24;for(int k=0;k<8;k++)c=(c&0x80000000)?(c<<1)^0x04C11DB7:c<<1;tn[i]=c;
 uint32_t r=i;for(int k=0;k<8;k++)r=(r&1)?(r>>1)^0xEDB88320:r>>1;tr[i]=r;}}
uint32_t crcn(const uint8_t*p,size_t n,uint32_t c){for(size_t i=0;i<n;i++)c=(c<<8)^tn[(c>>24)^p[i]];return c;}
uint32_t crcr(const uint8_t*p,size_t n,uint32_t c){for(size_t i=0;i<n;i++)c=(c>>8)^tr[(c^p[i])&0xff];return c;}
uint32_t stm(const uint8_t*p,size_t n,uint32_t c){for(size_t i=0;i+4<=n;i+=4){uint8_t b[4]={p[i+3],p[i+2],p[i+1],p[i]};c=crcn(b,4,c);}return c;}
int main(int argc,char**argv){FILE*f=fopen(argv[1],"rb");fseek(f,0,2);long n=ftell(f);rewind(f);uint8_t*d=malloc(n);fread(d,1,n,f);init();
 uint32_t tl=d[n-4]|d[n-3]<<8|d[n-2]<<16|(uint32_t)d[n-1]<<24, tb=__builtin_bswap32(tl);
 long starts[]={0,0x2c,0x30,0x34,0x50,0x60,0x80,0x100,0x200,0x400,0x1000};
 for(int s=0;s<11;s++){long st=starts[s];size_t len=n-4-st;
  uint32_t v[8]={crcn(d+st,len,0),crcn(d+st,len,0xffffffff),crcr(d+st,len,0),crcr(d+st,len,0xffffffff),stm(d+st,len,0xffffffff),stm(d+st,len,0),0,0};
  for(int k=0;k<6;k++){uint32_t a=v[k],b=~v[k];if(a==tl||a==tb||b==tl||b==tb)printf("HIT start=%lx variant=%d val=%08x\n",st,k,a);}}
 printf("tail %08x\n",tl);
 // header crc candidates over first 0x2c / 0x2e bytes
 for(int L=0x20;L<=0x30;L++){uint32_t v[4]={crcn(d,L,0),crcn(d,L,0xffffffff),crcr(d,L,0),crcr(d,L,0xffffffff)};
  for(int k=0;k<4;k++)for(int o=0x20;o<=0x30;o++){uint32_t h=d[o]|d[o+1]<<8|d[o+2]<<16|(uint32_t)d[o+3]<<24;if(v[k]==h||~v[k]==h||__builtin_bswap32(v[k])==h||__builtin_bswap32(~v[k])==h)printf("HDR L=%x k=%d at %x\n",L,k,o);}}
}
