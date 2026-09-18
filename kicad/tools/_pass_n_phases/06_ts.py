import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
to_del=[]
for t in board.GetTracks():
    if t.GetNetname()!="TS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if (abs(sx-108.71)<0.15 or abs(ex-108.71)<0.15) and max(sx,ex)>110.5:
        to_del.append(t)
    elif abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and min(sy,ey)<=106.05 and max(sy,ey)>=107.2:
        to_del.append(t)
for t in to_del: board.Remove(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
# reload for clean add
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
nc=board.GetNetInfo().GetNetItem("TS").GetNetCode(); F=pcbnew.F_Cu
def add(x1,y1,x2,y2,w=0.15):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
add(111.00, 106.00, 111.00, 107.25)
add(111.00, 107.25, 108.71, 107.25)
add(108.71, 107.25, 108.71, 107.00)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("TS ortho del", len(to_del))
