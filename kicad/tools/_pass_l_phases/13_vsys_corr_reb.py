import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VSYS").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (117.412,104.500, 117.412,103.400, 0.35),
    (117.412,103.400, 115.000,103.400, 0.35),
    (115.000,103.400, 115.000,102.400, 0.35),
    (115.000,102.400, 111.450,102.400, 0.35),
    (111.450,102.400, 111.450,102.950, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vsys_corr_reb")
