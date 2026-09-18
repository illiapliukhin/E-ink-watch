import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBUS").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (105.700,104.500, 105.700,103.700, 0.35),
    (105.700,103.700, 108.120,103.700, 0.35),
    (108.120,103.700, 108.120,102.900, 0.35),
    (108.120,102.900, 109.850,102.900, 0.35),
    (109.850,102.900, 109.850,105.200, 0.35),
    (109.850,105.200, 110.600,105.200, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vbus_reb")
