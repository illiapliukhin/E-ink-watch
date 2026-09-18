import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# Move 3V3 via from on-pad 112.41,107.6 to 112.00,108.20 (NW of R_CD, N of R_SCL)
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA" or t.GetNetname()!="3V3": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-112.410)<0.05 and abs(y-107.600)<0.1:
        t.SetPosition(pcbnew.VECTOR2I(mm(112.00), mm(108.20))); n+=1
        print("via ->", 112.00, 108.20)
# reconnect F.Cu from pad2 to new via
nc=board.GetNetInfo().GetNetItem("3V3").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [(112.410,107.600, 112.000,107.600),(112.000,107.600, 112.000,108.200)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.20)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# update any track ends that were on old via
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetNetname()!="3V3": continue
    for end in ("Start","End"):
        pt=t.GetStart() if end=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        if abs(px-112.410)<0.05 and abs(py-107.600)<0.05 and t.GetLayer()!=pcbnew.F_Cu:
            # B.Cu ends at old via
            if end=="Start": t.SetStart(pcbnew.VECTOR2I(mm(112.00),mm(108.20)))
            else: t.SetEnd(pcbnew.VECTOR2I(mm(112.00),mm(108.20)))
            n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
