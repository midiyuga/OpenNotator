
from pathlib import Path

SEG_MARKER = b"\x7f\xff\xff\xff"
PPQN = 192
SON_ZERO = 0x1E00

def u16(data, off):
    return ((data[off] << 8) | data[off+1]) if off + 2 <= len(data) else 0

def u32(data, off):
    return ((data[off]<<24)|(data[off+1]<<16)|(data[off+2]<<8)|data[off+3]) if off + 4 <= len(data) else 0

def asc(bs):
    return ''.join(chr(x) if 32 <= x < 127 else '.' for x in bs).strip()

def vlq(v):
    v = max(0, int(v))
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.insert(0, (v & 0x7F) | 0x80)
        v >>= 7
    return bytes(out)

def track_chunk(events):
    events.sort(key=lambda e: (e[0], e[1]))
    out = bytearray()
    last = 0
    for tick, order, data in events:
        out += vlq(max(0, tick-last))
        out += data
        last = tick
    out += b"\x00\xff\x2f\x00"
    return b"MTrk" + len(out).to_bytes(4, "big") + bytes(out)

def track_name(name):
    b = (name or "Track").encode("ascii", "replace")
    return b"\x00\xff\x03" + vlq(len(b)) + b

def tempo_event(bpm):
    bpm = bpm if bpm and bpm > 0 else 120
    mpqn = int(round(60000000 / bpm))
    return b"\x00\xff\x51\x03" + bytes([(mpqn>>16)&255,(mpqn>>8)&255,mpqn&255])

class Segment:
    def __init__(self, index, start, end, slot, name, records):
        self.index=index; self.start=start; self.end=end; self.slot=slot; self.name=name; self.records=records
        self.notes=[]

class SonFile:
    def __init__(self, path):
        self.path=Path(path)
        self.data=self.path.read_bytes()
        self.tempo=u16(self.data, 0x06)
        self.segments=self.parse_segments()
        for s in self.segments:
            s.notes=self.decode_notes(s)
        self.arrangement=self.parse_arrangement()

    def starts(self):
        out=[]; i=0
        while True:
            j=self.data.find(SEG_MARKER, i)
            if j < 0: break
            out.append(j); i=j+4
        return out

    def parse_segments(self):
        starts=self.starts(); segs=[]
        for idx, st in enumerate(starts):
            en=starts[idx+1] if idx+1 < len(starts) else len(self.data)
            slot=self.data[st+0x09] if st+0x0A <= len(self.data) else 0
            name=asc(self.data[st+0x1C:st+0x24]) if st+0x24 <= len(self.data) else ""
            recs=[]
            ev=st+0x32
            count=max(0,(en-ev-4)//6)
            for r in range(count):
                off=ev+r*6
                raw=self.data[off:off+6]
                if len(raw)==6:
                    recs.append((off,raw[0],raw[1],(raw[2]<<8)|raw[3],raw[4],raw[5],raw))
            segs.append(Segment(idx,st,en,slot,name,recs))
        return segs

    def decode_notes(self, seg):
        notes=[]; active={}
        for off,a,op,pos,vh,vl,raw in seg.records:
            if op != 0x90: continue
            tick=pos-SON_ZERO
            note=a
            if vh >= 0x80:
                vel=vh-0x80
                active.setdefault(note,[]).append((tick,vel,off))
            else:
                if active.get(note):
                    start,vel,onoff=active[note].pop(0)
                    notes.append((start,max(start+1,tick),note,vel,onoff,off))
        for note, stack in active.items():
            for start,vel,onoff in stack:
                notes.append((start,start+PPQN,note,vel,onoff,None))
        notes.sort()
        return notes

    def parse_arrangement(self):
        if len(self.segments) <= 16: return []
        out=[]
        for i,(off,a,op,pos,vh,vl,raw) in enumerate(self.segments[16].records):
            if op == 0x30 and vh == 0x7E:
                out.append((i,a,pos-SON_ZERO,pos,off,raw.hex(" ").upper()))
        return out

def write_midi(song, outpath):
    tracks=[]
    tracks.append(track_chunk([(0,0,track_name(song.path.stem)),(0,1,tempo_event(song.tempo))]))
    for seg in [s for s in song.segments if s.notes]:
        ch=max(0,min(15,(seg.slot or 1)-1))
        ev=[(0,0,track_name(seg.name or ("Segment %d"%seg.index)))]
        for st,en,note,vel,onoff,offoff in seg.notes:
            ev.append((st,10,bytes([0x90|ch,max(0,min(127,note)),max(1,min(127,vel))])))
            ev.append((en,11,bytes([0x80|ch,max(0,min(127,note)),0])))
        tracks.append(track_chunk(ev))
    header=b"MThd"+(6).to_bytes(4,"big")+(1).to_bytes(2,"big")+len(tracks).to_bytes(2,"big")+PPQN.to_bytes(2,"big")
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    Path(outpath).write_bytes(header+b"".join(tracks))
