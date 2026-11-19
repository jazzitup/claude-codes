import sys, olefile, zlib, struct
f=olefile.OleFileIO(sys.argv[1])
hdr=f.openstream('FileHeader').read(); comp=hdr[36]&1
secs=sorted([e for e in f.listdir() if e[0]=='BodyText'], key=lambda e:int(e[1][7:]))
for s in secs:
    d=f.openstream(s).read()
    if comp: d=zlib.decompress(d,-15)
    i=0; out=[]
    while i<len(d):
        h=struct.unpack('<I',d[i:i+4])[0]; i+=4
        tag=h&0x3ff; lvl=(h>>10)&0x3ff; sz=h>>20
        if sz==0xfff: sz=struct.unpack('<I',d[i:i+4])[0]; i+=4
        if tag==67:
            t=d[i:i+sz]; j=0; txt=''
            while j<len(t):
                c=struct.unpack('<H',t[j:j+2])[0]
                if c in (1,2,3,11,12,14,15,16,17,18,21,22,23): j+=16; continue
                if c in (4,5,6,7,8,9,19,20): j+=16; continue
                if c==10: txt+='\t'
                elif c==13: pass
                elif c<32: pass
                else: txt+=chr(c)
                j+=2
            out.append(txt)
        i+=sz
    print('\n'.join(out))
