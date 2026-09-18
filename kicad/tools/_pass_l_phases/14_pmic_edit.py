import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-109.5)<0.05 and abs(y-106.4)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(109.10),mm(106.70))); n+=1
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=109.6 and max(sx,ex)>=110.5:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("pmic_edit",n)
