import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="3V3_DISP": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-115.55)<0.05 and abs(y-102.75)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(115.55),mm(101.80))); n+=1
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.B_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-115.55)<0.05 and abs(ex-115.55)<0.05:
        t.SetStart(pcbnew.VECTOR2I(mm(115.55),mm(106.00)))
        t.SetEnd(pcbnew.VECTOR2I(mm(115.55),mm(101.80))); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("disp_via",n)
