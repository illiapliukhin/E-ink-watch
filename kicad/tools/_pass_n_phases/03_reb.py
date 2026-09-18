import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")

# Clear all ILIM/IPRETERM copper before rebuild; clear old PMID approach only
for t in list(board.GetTracks()):
    net=t.GetNetname()
    if net in ("ILIM","IPRETERM"):
        board.Remove(t)
        continue
    if net!="PMID":
        continue
    def tomm2(u): return u/1e6
    if t.Type()==pcbnew.PCB_VIA_T:
        x,y=tomm2(t.GetPosition().x),tomm2(t.GetPosition().y)
        if 110.7<=x<=111.6 and 104.1<=y<=104.6:
            board.Remove(t)
        continue
    if t.GetLayerName()!="F.Cu":
        continue
    sx,sy=tomm2(t.GetStart().x),tomm2(t.GetStart().y)
    ex,ey=tomm2(t.GetEnd().x),tomm2(t.GetEnd().y)
    is_stitch=(
        (abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and min(sy,ey)>=105.15 and max(sy,ey)<=105.65)
        or (abs(sy-105.6)<0.05 and abs(ey-105.6)<0.05 and min(sx,ex)>=110.95 and max(sx,ex)<=111.45)
        or (abs(sx-111.4)<0.05 and abs(ex-111.4)<0.05 and min(sy,ey)>=105.55 and max(sy,ey)<=106.05)
    )
    if is_stitch:
        continue
    if (abs(sy-103.85)<0.1 and abs(ey-103.85)<0.1) or (
        abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and max(sy,ey)<=105.25 and min(sy,ey)<=104.40):
        board.Remove(t)

def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
F,B=pcbnew.F_Cu,pcbnew.B_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
def via(x,y,net,drill=0.30,width=0.60):
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(drill))
    try:
        v.SetFrontWidth(mm(width))
    except Exception:
        v.SetWidth(mm(width))
    v.SetNetCode(nc(net)); board.Add(v)
pads={}
for fp in board.GetFootprints():
    if fp.GetReference() in ("R_ILIM","C_PMID","R_IPRETERM","C_VINLS","U2"):
        for p in fp.Pads():
            pads[f"{fp.GetReference()}.{p.GetNumber()}"]=(tomm(p.GetPosition().x),tomm(p.GetPosition().y))
cpmid1=pads["C_PMID.1"]; rilim1=pads["R_ILIM.1"]; ript1=pads["R_IPRETERM.1"]
cvin1=pads["C_VINLS.1"]; a3=pads["U2.A3"]
# PMID B hop A3->C_PMID
via(111.00, 104.75, "PMID", 0.30, 0.60)
via(cpmid1[0], 105.90, "PMID", 0.30, 0.60)
add(F, a3[0], a3[1], 111.00, 104.75, 0.40, "PMID")
add(B, 111.00, 104.75, cpmid1[0], 104.75, 0.45, "PMID")
add(B, cpmid1[0], 104.75, cpmid1[0], 105.90, 0.45, "PMID")
add(F, cpmid1[0], 105.90, cpmid1[0], cpmid1[1], 0.45, "PMID")
# C_VINLS B stitch (avoid 3V3_DISP F @y=106)
via(113.40, 106.28, "PMID", 0.30, 0.60)
add(F, cvin1[0], cvin1[1], 113.40, 106.28, 0.40, "PMID")
add(B, 113.40, 106.28, 113.40, 105.90, 0.40, "PMID")
add(B, 113.40, 105.90, cpmid1[0], 105.90, 0.40, "PMID")
# ILIM
via(110.90, 106.00, "ILIM", 0.25, 0.50)
add(F, 110.60, 106.00, 110.90, 106.00, 0.15, "ILIM")
via(rilim1[0]-0.30, rilim1[1], "ILIM", 0.25, 0.50)
add(F, rilim1[0], rilim1[1], rilim1[0]-0.30, rilim1[1], 0.15, "ILIM")
add(B, 110.90, 106.00, 110.40, 106.00, 0.15, "ILIM")
add(B, 110.40, 106.00, 110.40, rilim1[1], 0.15, "ILIM")
add(B, 110.40, rilim1[1], rilim1[0]-0.30, rilim1[1], 0.15, "ILIM")
# IPRETERM
via(109.70, 106.40, "IPRETERM", 0.25, 0.50)
add(F, 110.20, 106.40, 109.70, 106.40, 0.15, "IPRETERM")
via(ript1[0], ript1[1], "IPRETERM", 0.25, 0.50)
add(B, 109.70, 106.40, 109.70, ript1[1], 0.18, "IPRETERM")
add(B, 109.70, ript1[1], ript1[0], ript1[1], 0.18, "IPRETERM")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("rebuild full", cpmid1, rilim1)
