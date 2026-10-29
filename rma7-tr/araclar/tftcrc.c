// TJC/Nextion X-serisi TFT dosya sağlaması (word tabanlı, augmented CRC32 0x04C11DB7)
// kullanım: tftcrc dosya [--fix]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static uint32_t T[256];
static inline uint32_t ub(uint32_t r,uint8_t v){return (((r&0xFFFFFF)<<8)|v)^T[r>>24];}
int main(int c,char**v){FILE*f=fopen(v[1],"rb");if(!f){perror("open");return 2;}fseek(f,0,2);long n=ftell(f);rewind(f);uint8_t*d=malloc(n);
 if(fread(d,1,n,f)!=(size_t)n)return 2;fclose(f);
 for(uint32_t i=0;i<256;i++){uint64_t r=(uint64_t)i<<24;for(int k=0;k<8;k++){r<<=1;if(r>>32)r^=0x104C11DB7ULL;}T[i]=(uint32_t)r;}
 long m=(n-4)/4;uint32_t r=0;
 for(long i=0;i<=m;i++){uint32_t w=i<m?(d[4*i]|d[4*i+1]<<8|d[4*i+2]<<16|(uint32_t)d[4*i+3]<<24):0;if(i==0)w^=0xFFFFFFFF;
  r=ub(r,w>>24);r=ub(r,w>>16);r=ub(r,w>>8);r=ub(r,w);}
 r^=d[3]^d[0x2e]^d[0x3c];
 uint32_t s=d[n-4]|d[n-3]<<8|d[n-2]<<16|(uint32_t)d[n-1]<<24;
 printf("stored=%08X calc=%08X %s\n",s,r,s==r?"OK":"MISMATCH");
 if(c>2&&!strcmp(v[2],"--fix")&&s!=r){memcpy(d+n-4,&r,4);f=fopen(v[1],"r+b");fseek(f,n-4,0);fwrite(&r,4,1,f);fclose(f);printf("fixed\n");}
 return s==r?0:1;}
