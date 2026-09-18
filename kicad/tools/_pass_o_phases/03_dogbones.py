#!/usr/bin/env python3
"""Finish ILIM/PMID/IPRETERM dogbones to shifted pads; clean dead PMID @y=103.85."""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6

# Remove dead old PMID fanout at y≈103.85 (pre Pass-N C_PMID) and incomplete stubs
to_remove = []
for t in board.GetTracks():
    net = t.GetNetname()
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    if net == "PMID" and t.GetLayerName() == "F.Cu":
        # old horizontal/vertical leftovers south of new C_PMID
        if abs(sy-103.85)<0.08 and abs(ey-103.85)<0.08 and min(sx,ex)>=110.9 and max(sx,ex)<=112.5:
            to_remove.append(t)
        elif abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and max(sy,ey)<=104.0 and min(sy,ey)>=103.7:
            to_remove.append(t)
    # incomplete ILIM F stub near old mid via that doesn't reach pad
    if net == "ILIM" and t.GetLayerName() == "F.Cu":
        if abs(sy-105.7)<0.05 and abs(ey-105.7)<0.05 and max(sx,ex)<113.8:
            # keep for now — will extend from via
            pass
for t in to_remove:
    board.Remove(t)

F, B = pcbnew.F_Cu, pcbnew.B_Cu
ni = board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer, x1, y1, x2, y2, w, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
def via(x, y, net, drill=0.25, width=0.50):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(drill))
    try: v.SetWidth(mm(width))
    except Exception: pass
    try: v.SetFrontWidth(mm(width))
    except Exception: pass
    v.SetNetCode(nc(net)); board.Add(v)

pads = {}
for fp in board.GetFootprints():
    if fp.GetReference() in ("R_ILIM", "C_PMID", "R_IPRETERM", "U2", "C_VINLS"):
        for p in fp.Pads():
            pads[f"{fp.GetReference()}.{p.GetNumber()}"] = (tomm(p.GetPosition().x), tomm(p.GetPosition().y))

rilim = pads["R_ILIM.1"]      # ILIM
cpmid = pads["C_PMID.1"]      # PMID
ript = pads["R_IPRETERM.1"]   # IPRETERM

# --- ILIM dogbone: existing via @(113.44,105.7) → pad @(114.29,106.15) ---
# Use F short dogbone; corridor cleared by C_LDO north shift
via(rilim[0]-0.35, rilim[1], "ILIM", 0.25, 0.50)
add(F, rilim[0], rilim[1], rilim[0]-0.35, rilim[1], 0.15, "ILIM")
# B hop from existing mid via 113.44,105.7 up to dogbone via
add(B, 113.44, 105.70, 113.44, rilim[1], 0.15, "ILIM")
add(B, 113.44, rilim[1], rilim[0]-0.35, rilim[1], 0.15, "ILIM")

# --- IPRETERM dogbone: lower B to y=102.50 to clear VSYS @y=102.95 ---
# Remove old B at y=102.8 that shorts VSYS
to_remove2 = []
for t in board.GetTracks():
    if t.GetNetname() != "IPRETERM":
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        # old pad-side via left of new pad
        if abs(x-113.29)<0.05 and abs(y-102.8)<0.05:
            to_remove2.append(t)
        continue
    sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
    if t.GetLayerName() == "B.Cu":
        if abs(sy-102.8)<0.05 or abs(ey-102.8)<0.05:
            to_remove2.append(t)
        elif abs(sx-109.7)<0.05 and abs(ex-109.7)<0.05 and min(sy,ey)<=103.0:
            to_remove2.append(t)
for t in to_remove2:
    board.Remove(t)

# Rebuild IPRETERM B lower: via west of pad, route at y=102.50
via(ript[0]-0.40, 102.50, "IPRETERM", 0.25, 0.50)
add(F, ript[0], ript[1], ript[0]-0.40, ript[1], 0.15, "IPRETERM")
add(F, ript[0]-0.40, ript[1], ript[0]-0.40, 102.50, 0.15, "IPRETERM")
# from existing west via @(109.7,106.4) down then east at y=102.50
add(B, 109.70, 106.40, 109.70, 102.50, 0.15, "IPRETERM")
add(B, 109.70, 102.50, ript[0]-0.40, 102.50, 0.18, "IPRETERM")

# --- PMID to C_PMID: B.Cu from existing via @111.0/111.35,104.35 east, via up near pad ---
# Prefer path south of C_VINLS GND @(112.8,105.32) and north of eased MP
vx = 111.00
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "PMID":
        x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
        if 110.8 <= x <= 111.5 and abs(y-104.35) < 0.08:
            vx = x
# via under/near C_PMID pad1, slightly west to stay on pad
via(cpmid[0], 104.80, "PMID", 0.25, 0.55)
add(B, vx, 104.35, cpmid[0], 104.35, 0.40, "PMID")
add(B, cpmid[0], 104.35, cpmid[0], 104.80, 0.40, "PMID")
add(F, cpmid[0], 104.80, cpmid[0], cpmid[1], 0.40, "PMID")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"dogbones rem_dead={len(to_remove)} rem_ipre={len(to_remove2)} C_PMID={cpmid} R_ILIM={rilim} R_IPT={ript} vx={vx}")
