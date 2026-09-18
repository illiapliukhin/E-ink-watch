"""Delete ILIM+IPRETERM copper and rebuild; retarget PMID from existing via only."""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
to_remove=[]
for t in board.GetTracks():
    net=t.GetNetname()
    if net in ("ILIM","IPRETERM"):
        to_remove.append(t); continue
    if net!="PMID" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    is_stitch=(
        (abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and min(sy,ey)>=105.15 and max(sy,ey)<=105.65)
        or (abs(sy-105.6)<0.05 and abs(ey-105.6)<0.05 and min(sx,ex)>=110.95 and max(sx,ex)<=111.45)
        or (abs(sx-111.4)<0.05 and abs(ex-111.4)<0.05 and min(sy,ey)>=105.55 and max(sy,ey)<=106.05)
    )
    if is_stitch: continue
    if abs(sy-103.85)<0.12 and abs(ey-103.85)<0.12:
        to_remove.append(t)
    elif abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and max(sy,ey)<=105.25 and min(sy,ey)<=104.45:
        to_remove.append(t)
for t in to_remove: board.Remove(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)

board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
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
    v.SetDrill(mm(drill))
    try: v.SetFrontWidth(mm(width))
    except Exception: v.SetWidth(mm(width))
    v.SetNetCode(nc(net)); board.Add(v)

pads={}
for fp in board.GetFootprints():
    if fp.GetReference() in ("R_ILIM","C_PMID","R_IPRETERM","U2"):
        for p in fp.Pads():
            pads[f"{fp.GetReference()}.{p.GetNumber()}"]=(tomm(p.GetPosition().x),tomm(p.GetPosition().y))
cpmid1=pads["C_PMID.1"]; rilim1=pads["R_ILIM.1"]; ript1=pads["R_IPRETERM.1"]

# PMID from existing via only (no new A3 stub)
vx=None
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=="PMID":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if 110.8<=x<=111.5 and abs(y-104.35)<0.08:
            vx=x; break
if vx is not None:
    # B.Cu east from via to avoid F mash with SW/ILIM, then via up near C_PMID
    via(cpmid1[0], 104.35, "PMID", 0.25, 0.50)
    add(B, vx, 104.35, cpmid1[0], 104.35, 0.40, "PMID")
    add(F, cpmid1[0], 104.35, cpmid1[0], cpmid1[1], 0.40, "PMID")

# ILIM: dogbone; B at y between pad and not through PMID via@104.35
via(110.90, 106.00, "ILIM", 0.25, 0.50)
add(F, 110.60, 106.00, 110.90, 106.00, 0.15, "ILIM")
via(rilim1[0]-0.30, rilim1[1], "ILIM", 0.25, 0.50)
add(F, rilim1[0], rilim1[1], rilim1[0]-0.30, rilim1[1], 0.15, "ILIM")
add(B, 110.90, 106.00, 110.30, 106.00, 0.15, "ILIM")
add(B, 110.30, 106.00, 110.30, rilim1[1], 0.15, "ILIM")
add(B, 110.30, rilim1[1], rilim1[0]-0.30, rilim1[1], 0.15, "ILIM")

via(109.70, 106.40, "IPRETERM", 0.25, 0.50)
add(F, 110.20, 106.40, 109.70, 106.40, 0.15, "IPRETERM")
via(ript1[0], ript1[1], "IPRETERM", 0.25, 0.50)
add(B, 109.70, 106.40, 109.70, ript1[1], 0.18, "IPRETERM")
add(B, 109.70, ript1[1], ript1[0], ript1[1], 0.18, "IPRETERM")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("ilim/pmid/ipreterm reb", "vx", vx, "C_PMID", cpmid1, "R_ILIM", rilim1)
