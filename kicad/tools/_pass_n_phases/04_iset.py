import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F,B=pcbnew.F_Cu,pcbnew.B_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
def via(x,y,net,drill=0.25,width=0.50):
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(drill)); v.SetWidth(mm(width))
    v.SetNetCode(nc(net)); board.Add(v)
via(109.95, 106.00, "ISET")
add(F, 110.20, 106.00, 109.95, 106.00, 0.15, "ISET")
via(109.71, 103.50, "ISET")
add(B, 109.95, 106.00, 108.80, 106.00, 0.15, "ISET")
add(B, 108.80, 106.00, 108.80, 103.50, 0.15, "ISET")
add(B, 108.80, 103.50, 109.71, 103.50, 0.15, "ISET")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("ISET B @x=108.80")
