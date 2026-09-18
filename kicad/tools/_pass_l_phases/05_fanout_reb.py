import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
def add(net, segs):
    nc=board.GetNetInfo().GetNetItem(net).GetNetCode()
    for x1,y1,x2,y2,w in segs:
        t=pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
        t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
add("PMID", [
    (111.000,105.200, 111.000,105.600, 0.20),
    (111.000,105.600, 111.400,105.600, 0.20),
    (111.400,105.600, 111.400,106.000, 0.20),
    (111.400,106.000, 111.400,106.220, 0.18),
    (111.400,106.220, 112.800,106.220, 0.18),
    (112.800,106.220, 112.800,106.280, 0.20),
    (111.000,105.200, 111.000,103.700, 0.25),
    (111.000,103.700, 110.820,103.700, 0.25),
])
add("IPRETERM", [
    (110.200,106.400, 110.200,106.550, 0.18),
    (110.200,106.550, 112.690,106.550, 0.18),
    (112.690,106.550, 112.690,103.100, 0.18),
])
add("ILIM", [
    (110.600,106.000, 110.290,106.000, 0.18),
    (110.290,106.000, 110.290,103.500, 0.18),
])
add("ISET", [
    (110.200,106.000, 110.310,106.000, 0.18),
    (110.310,106.000, 110.310,103.500, 0.18),
])
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("fanout_reb")
