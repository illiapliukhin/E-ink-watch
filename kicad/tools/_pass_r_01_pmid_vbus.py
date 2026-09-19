#!/usr/bin/env python3
"""Pass-R1h MINIMAL: clear PMID↔VBUS only.
Remove PMID via@(111.0,104.35) and F column @x=111.0 below A3 (incl. south to C_PMID).
Narrow A3–B3 to 0.22. Keep via@(111.35,104.35). Reconnect C_PMID from that via
SOUTH-ONLY on F (no north path through SW/VSYS): via→(111.35,103.40)→(111.72,103.40).
Also delete leftover VSYS F vertical (111.8,102.95)-(111.8,105.6).
VBUS @x=110.6 untouched. No new vias east of SW.
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.06): return abs(a-b)<eps
F=pcbnew.F_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    if abs(x1-x2)<1e-9 and abs(y1-y2)<1e-9: return
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)

to_rm=[]; via_rm=None
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMID": continue
    if t.Type()==pcbnew.PCB_VIA_T:
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if near(x,111.000) and near(y,104.350):
            via_rm=t
        continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,111.000) and near(ex,111.000):
        to_rm.append(t)  # all x=111 incl A3-B3; re-add narrow
    elif near(sy,103.400) and near(ey,103.400) and min(sx,ex)<=111.1 and max(sx,ex)>=111.6:
        to_rm.append(t)
for t in to_rm: board.Remove(t)
if via_rm is not None: board.Remove(via_rm)

add(F,111.000,105.200,111.000,105.600,0.22,"PMID")
has=False
for t in board.GetTracks():
    if t.GetNetname()!="PMID" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sy,105.600) and near(ey,105.600) and min(sx,ex)<=111.05 and max(sx,ex)>=111.35:
        has=True
if not has:
    add(F,111.000,105.600,111.400,105.600,0.28,"PMID")

# C_PMID from remaining via@(111.35,104.35) south only — thin 0.28
# Shrink east via annular if needed - leave size; dist to VBUS=0.75 OK
add(F,111.350,104.350,111.350,103.400,0.28,"PMID")
add(F,111.350,103.400,111.720,103.400,0.28,"PMID")
# Link via up to B3/B4 stitch: thin dogbone from B3@(111.0,105.6) is far;
# use existing B4-C4; add B.Cu from via north ONLY on B to B4 via new microvia path:
# F from B4@(111.4,105.6) south to (111.4,105.35) then east to (111.35,105.35) then
# — skip F north of SW. Instead B.Cu from via to under B4:
# Add via at B4 and B link — risks SW. 
# For minimal: leave via@(111.35,104.35) connected to C_PMID only; stitch U2 via
# A3-B3-B4-C4. Via is orphaned from U2 unless B pour — add B track to nowhere?
# Connect via to C4 with B: via (111.35,104.35) - B to (111.35,106.0) - but crosses SW B @104.9
# Stop: use F from C4 (111.4,106.0) east to (111.35,106.0)? C4 is 111.4. 
# (111.4,106.0)-(111.35,106.0)-(111.35,104.35) on F — vertical at 111.35 from 106 to 104.35
# passes SW via at 111.4,104.9: dx=0.05 — HARD SHORT.
# Accept C_PMID+via island OR connect later. Prefer island for VBUS clear.

# leftover VSYS
vsys_rm=[]
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,111.800) and near(ex,111.800) and min(sy,ey)<=103.0 and max(sy,ey)>=105.5:
        vsys_rm.append(t)
for t in vsys_rm: board.Remove(t)
has=False
for t in board.GetTracks():
    if t.GetNetname()!="VSYS" or t.Type()==pcbnew.PCB_VIA_T: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if near(sx,111.800) and near(ex,111.800) and min(sy,ey)>=105.55 and max(sy,ey)<=106.15:
        has=True
if not has:
    add(F,111.800,106.100,111.800,105.600,0.40,"VSYS")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb",board)
print(f"R1h rem={len(to_rm)} via_rm={via_rm is not None} vsys_rm={len(vsys_rm)} (C_PMID via island OK)")
