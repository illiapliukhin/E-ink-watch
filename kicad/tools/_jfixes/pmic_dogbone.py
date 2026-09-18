import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=109.55 and max(sx,ex)>=110.55:
        board.Remove(t); n+=1
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA" or t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-109.5)<0.05 and abs(y-106.4)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(109.50), mm(106.95))); n+=1
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.B_Cu: continue
    for end in ("Start","End"):
        pt=t.GetStart() if end=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        if abs(px-109.5)<0.05 and abs(py-106.4)<0.05:
            if end=="Start": t.SetStart(pcbnew.VECTOR2I(mm(109.50),mm(106.95)))
            else: t.SetEnd(pcbnew.VECTOR2I(mm(109.50),mm(106.95)))
            n+=1
nc=board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [(110.600,106.400, 110.600,106.950),(110.600,106.950, 109.500,106.950)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.15)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("edits", n)
