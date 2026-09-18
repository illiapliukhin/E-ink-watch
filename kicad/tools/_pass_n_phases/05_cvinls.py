import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
F,B=pcbnew.F_Cu,pcbnew.B_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
has=False
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=="PMID":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-113.40)<0.08 and abs(y-106.28)<0.08:
            has=True
if has:
    print("C_VINLS stitch already present")
else:
    def add(layer,x1,y1,x2,y2,w,net):
        t=pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
        t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
    def via(x,y,net,drill=0.30,width=0.60):
        v=pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetDrill(mm(drill)); v.SetWidth(mm(width))
        v.SetNetCode(nc(net)); board.Add(v)
    pads={}
    for fp in board.GetFootprints():
        if fp.GetReference() in ("C_VINLS","C_PMID"):
            for p in fp.Pads():
                pads[f"{fp.GetReference()}.{p.GetNumber()}"]=(tomm(p.GetPosition().x),tomm(p.GetPosition().y))
    cvin=pads["C_VINLS.1"]; cpmid=pads["C_PMID.1"]
    via(113.45, 106.28, "PMID")
    add(F, cvin[0], cvin[1], 113.45, 106.28, 0.40, "PMID")
    add(B, 113.45, 106.28, 113.45, 105.90, 0.40, "PMID")
    add(B, 113.45, 105.90, cpmid[0], 105.90, 0.40, "PMID")
    print("added C_VINLS stitch")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
