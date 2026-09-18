import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("SW").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (111.400,104.500, 111.400,105.050, 0.30),
    (111.400,105.050, 113.600,105.050, 0.30),
    (113.600,105.050, 113.600,104.500, 0.30),
    (113.600,104.500, 115.287,104.500, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("sw_reb")
