#!/usr/bin/env python3
"""Pass-N: nudge C_SYS north to free corridor; shift R_ILIM+C_PMID south>=1mm + east; rebuild sense lines."""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6

# C_SYS was @(112.8,104.0) blocking south shift — nudge north 0.70mm
# R_ILIM 103.5->104.55 (+1.05), C_PMID 103.85->105.00 (+1.15) with dy~1.05 pad clear
for fp in board.GetFootprints():
    r=fp.GetReference()
    if r=="C_SYS":
        fp.SetPosition(pcbnew.VECTOR2I(mm(112.80), mm(103.30)))
    elif r=="R_ILIM":
        fp.SetPosition(pcbnew.VECTOR2I(mm(113.00), mm(104.90)))
    elif r=="C_PMID":
        fp.SetPosition(pcbnew.VECTOR2I(mm(114.00), mm(106.00)))
    elif r=="R_IPRETERM":
        fp.SetPosition(pcbnew.VECTOR2I(mm(114.20), mm(102.80)))

to_remove=[]
for t in board.GetTracks():
    net=t.GetNetname()
    if net in ("ILIM","IPRETERM"):
        to_remove.append(t); continue
    if net=="VSYS" and t.Type()!=pcbnew.PCB_VIA_T and t.GetLayerName()=="F.Cu":
        # retarget C_SYS stub later — remove old stub to former pad y=104.48
        sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
        ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
        if abs(sy-104.48)<0.08 and abs(ey-104.48)<0.08 and max(sx,ex)>=111.7:
            to_remove.append(t)
        continue
    if net!="PMID" or t.Type()==pcbnew.PCB_VIA_T:
        continue
    if t.GetLayerName()!="F.Cu":
        continue
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
for t in to_remove:
    board.Remove(t)

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
    if fp.GetReference() in ("R_ILIM","C_PMID","R_IPRETERM","C_SYS","C_VINLS","U2"):
        for p in fp.Pads():
            pads[f"{fp.GetReference()}.{p.GetNumber()}"]=(tomm(p.GetPosition().x),tomm(p.GetPosition().y))

cpmid1=pads["C_PMID.1"]; rilim1=pads["R_ILIM.1"]; ript1=pads["R_IPRETERM.1"]
csys1=pads["C_SYS.1"]; a3=pads["U2.A3"]; cvin1=pads["C_VINLS.1"]

# VSYS stub to new C_SYS pad1
add(F, 111.80, csys1[1], csys1[0], csys1[1], 0.45, "VSYS")

# PMID: from existing vias @104.35 if present, else from A3 narrow+east on B south of SW via
has_via=False
for t in board.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=="PMID":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-111.0)<0.05 and abs(y-104.35)<0.05:
            has_via=True
if has_via:
    # F from via east/north to C_PMID — via at 111,104.35; C_PMID pad ~112.32,105.55
    add(F, 111.00, 104.35, cpmid1[0], 104.35, 0.40, "PMID")
    add(F, cpmid1[0], 104.35, cpmid1[0], cpmid1[1], 0.40, "PMID")
    # A3 already stitched; via@104.35 links via existing if present
else:
    add(F, a3[0], a3[1], a3[0], 104.35, 0.25, "PMID")
    add(F, a3[0], 104.35, cpmid1[0], 104.35, 0.40, "PMID")
    add(F, cpmid1[0], 104.35, cpmid1[0], cpmid1[1], 0.40, "PMID")

# C_VINLS stitch deferred (3V3_DISP corridor)

# ILIM B — dogbone near new pad; spine x=110.40
via(110.90, 106.00, "ILIM", 0.25, 0.50)
add(F, 110.60, 106.00, 110.90, 106.00, 0.15, "ILIM")
via(rilim1[0]-0.25, rilim1[1], "ILIM", 0.25, 0.50)
add(F, rilim1[0], rilim1[1], rilim1[0]-0.25, rilim1[1], 0.15, "ILIM")
add(B, 110.90, 106.00, 110.40, 106.00, 0.15, "ILIM")
add(B, 110.40, 106.00, 110.40, rilim1[1], 0.15, "ILIM")
add(B, 110.40, rilim1[1], rilim1[0]-0.25, rilim1[1], 0.15, "ILIM")

# IPRETERM
via(109.70, 106.40, "IPRETERM", 0.25, 0.50)
add(F, 110.20, 106.40, 109.70, 106.40, 0.15, "IPRETERM")
via(ript1[0], ript1[1], "IPRETERM", 0.25, 0.50)
add(B, 109.70, 106.40, 109.70, ript1[1], 0.18, "IPRETERM")
add(B, 109.70, ript1[1], ript1[0], ript1[1], 0.18, "IPRETERM")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("csys-nudge place rem", len(to_remove), "C_SYS", csys1, "C_PMID", cpmid1, "R_ILIM", rilim1, "dA3", ((cpmid1[0]-a3[0])**2+(cpmid1[1]-a3[1])**2)**0.5)
