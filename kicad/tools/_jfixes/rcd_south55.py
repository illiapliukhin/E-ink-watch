import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dy=0.55
pads=[]
for fp in board.GetFootprints():
    if fp.GetReference()!="R_CD": continue
    for p in fp.Pads():
        pads.append((tomm(p.GetPosition().x), tomm(p.GetPosition().y)))
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y+dy)))
    print("R_CD", x, y, "->", y+dy)
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetNetname() not in ("CD","GND"): continue
    for end in ("Start","End"):
        pt=t.GetStart() if end=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for ox,oy in pads:
            if abs(px-ox)<0.12 and abs(py-oy)<0.12:
                if end=="Start": t.SetStart(pcbnew.VECTOR2I(mm(px),mm(py+dy)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(px),mm(py+dy)))
                n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("track ends", n)
