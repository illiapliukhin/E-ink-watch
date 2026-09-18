#!/usr/bin/env python3
"""Pass L: U2 passive RE-PLACEMENT + VBUS spine west + PMID/VSYS clear.
May MOVE latent GND via(111.31,102.9) to a safe spot (DRC-verified).
Never delete GND copper blindly. Revert if power pairs non-zero or GND↔VSYS appears.
"""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE_SHORT = int(sys.argv[2]) if len(sys.argv) > 2 else 21

FIXES = {}

# ---------------------------------------------------------------------------
# L1: Move latent GND via (111.31,102.9) → (109.50,102.90) west of VSYS spine
# ---------------------------------------------------------------------------
FIXES["move_latent_via"] = dict(code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="GND": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
        t.SetPosition(pcbnew.VECTOR2I(mm(109.50),mm(102.90))); n+=1
# stitch new via to nearby GND copper if dangling: short stub to C_IN/R_ISET area
nc=board.GetNetInfo().GetNetItem("GND").GetNetCode(); F=pcbnew.F_Cu
# horizontal to existing via@109.55,104.50 corridor
for x1,y1,x2,y2,w in [
    (109.500,102.900, 109.550,102.900, 0.25),
    (109.550,102.900, 109.550,104.500, 0.25),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("moved", n)
''')

# ---------------------------------------------------------------------------
# L2: VBUS spine west of x=110.0 (clear C_PMID.1 @110.52)
# Also jog VBUS around R_VSYS to clear VBUS↔VSYS
# ---------------------------------------------------------------------------
FIXES["vbus_spine_west"] = dict(code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# delete east VBUS approach @x=110.6 and horizontal to it @y=102.9
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBUS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    # (108.12,102.9)->(110.6,102.9)
    if abs(sy-102.9)<0.05 and abs(ey-102.9)<0.05 and min(sx,ex)<=108.2 and max(sx,ex)>=110.5:
        hit=True
    # vertical x=110.6 from ~102.9 to 105.2 (any segment)
    if abs(sx-110.6)<0.05 and abs(ex-110.6)<0.05 and min(sy,ey)<=105.15 and max(sy,ey)>=102.95:
        hit=True
    # (105.7,104.5)->(108.12,104.5) — will rebuild jogged
    if abs(sy-104.5)<0.05 and abs(ey-104.5)<0.05 and min(sx,ex)<=105.8 and max(sx,ex)>=108.0 and tomm(t.GetWidth())>=0.30:
        hit=True
    if hit:
        board.Remove(t); n+=1
nc=board.GetNetInfo().GetNetItem("VBUS").GetNetCode(); F=pcbnew.F_Cu
# New spine: west vertical @109.85, approach A2 from west at y=105.2
# Jog around R_VSYS: use y=103.70 corridor between C_IN north and R_VSYS
for x1,y1,x2,y2,w in [
    # from west vertical 105.7 down already exists to 104.5 — connect via south jog
    (105.700,104.500, 105.700,103.700, 0.35),
    (105.700,103.700, 108.120,103.700, 0.35),
    (108.120,103.700, 108.120,102.900, 0.35),  # up into existing C_IN north node (may dup with 102.9-104.5)
    # east approach west of 110
    (108.120,102.900, 109.850,102.900, 0.35),
    (109.850,102.900, 109.850,105.200, 0.35),
    (109.850,105.200, 110.600,105.200, 0.35),  # into U2.A2
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del", n, "reb_spine")
''')

# ---------------------------------------------------------------------------
# L3: Re-place C_PMID + resistor row (spread clearances)
#   C_PMID: (111.0,104.3) → (111.20,103.85)  [pad1 clears VBUS@109.85]
#   R_IPRETERM: (112.0,103.5) → (113.10,103.20) east, clear of R_ILIM + C_SYS
#   R_ILIM stay; R_ISET stay
# Rebuild PMID / IPRETERM / ILIM / ISET fanouts
# ---------------------------------------------------------------------------
FIXES["replace_passives"] = dict(code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))

def move_fp(ref, nx, ny):
    for fp in board.GetFootprints():
        if fp.GetReference()==ref:
            fp.SetPosition(pcbnew.VECTOR2I(mm(nx),mm(ny)))
            return True
    return False

# Move footprints
assert move_fp("C_PMID", 111.20, 103.85)
assert move_fp("R_IPRETERM", 113.10, 103.20)
# R_IPRETERM pads will be at 112.59 / 113.61 @ y=103.20

# Delete old fanout tracks for PMID (north of U2), IPRETERM vertical, and
# resistor-connected ILIM/ISET that end on old pad locations — rebuild clean.
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    net=t.GetNetname()
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if net=="PMID":
        # all F.Cu PMID in pocket — full rebuild of U2 PMID fanout
        if (108<=sx<=114 and 103<=sy<=107) or (108<=ex<=114 and 103<=ey<=107):
            hit=True
    if net=="IPRETERM":
        if (108<=sx<=114 and 103<=sy<=107) or (108<=ex<=114 and 103<=ey<=107):
            hit=True
    if net=="ILIM":
        if (108<=sx<=114 and 103<=sy<=107) or (108<=ex<=114 and 103<=ey<=107):
            hit=True
    if net=="ISET":
        if (108<=sx<=114 and 103<=sy<=107) or (108<=ex<=114 and 103<=ey<=107):
            hit=True
    if hit:
        board.Remove(t); n+=1

def add(net, segs):
    nc=board.GetNetInfo().GetNetItem(net).GetNetCode(); F=pcbnew.F_Cu
    for x1,y1,x2,y2,w in segs:
        t=pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
        t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)

# PMID pads: A3(111,105.2) B3(111,105.6) B4(111.4,105.6) C4(111.4,106.0)
# C_PMID new: pad1(110.72,103.85) pad2(111.68,103.85)
# C_VINLS: pad1(112.8,106.28)
# Stitch U2 PMID cluster WITHOUT crossing VSYS B5(111.8,105.6):
add("PMID", [
    # A3-B3 vertical
    (111.000,105.200, 111.000,105.600, 0.20),
    # B3-B4 horizontal (stop at B4, do NOT go to 111.8)
    (111.000,105.600, 111.400,105.600, 0.20),
    # B4-C4 vertical
    (111.400,105.600, 111.400,106.000, 0.20),
    # C4 east along y=106.15 (between C-row 106.0 and D-row 106.4) to C_VINLS
    # clear of C5 3V3_DISP@111.8,106.0 — use y=106.20, thin
    (111.400,106.000, 111.400,106.200, 0.18),
    (111.400,106.200, 112.800,106.200, 0.18),
    (112.800,106.200, 112.800,106.280, 0.20),
    # north to C_PMID pad1
    (111.000,105.200, 111.000,103.850, 0.25),
    (111.000,103.850, 110.720,103.850, 0.25),
])

# IPRETERM: U2.D1(110.2,106.4) → new R_IPRETERM.1(112.59,103.20)
# Route east-north around U2, clear of pads
add("IPRETERM", [
    (110.200,106.400, 110.200,106.550, 0.18),
    (110.200,106.550, 112.590,106.550, 0.18),
    (112.590,106.550, 112.590,103.200, 0.18),
])

# ILIM: U2.C2(110.6,106.0) → R_ILIM.1(110.29,103.5)
add("ILIM", [
    (110.600,106.000, 110.290,106.000, 0.18),
    (110.290,106.000, 110.290,103.500, 0.18),
])

# ISET: U2.C1(110.2,106.0) → R_ISET.2(110.31,103.5)
add("ISET", [
    (110.200,106.000, 110.310,106.000, 0.18),
    (110.310,106.000, 110.310,103.500, 0.18),
])

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("moved_fps, del_tracks", n)
''')

# ---------------------------------------------------------------------------
# L4: Clear VSYS wrong stubs into PMID pads B4/C4; keep B5-only VSYS
# Also fix SW↔VSYS (jog SW north of C_SYS) and 3V3_DISP↔VSYS (move via / jog)
# ---------------------------------------------------------------------------
FIXES["vsys_pmid_sw_disp"] = dict(code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# Delete VSYS segments that invade x<=111.6 at y~105.6-106.0 (PMID territory)
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    # (111.8,105.6)->(111.4,105.6)
    if abs(sy-105.6)<0.05 and abs(ey-105.6)<0.05 and min(sx,ex)<=111.45 and max(sx,ex)>=111.75:
        hit=True
    # (111.4,105.6)->(111.4,106.0) VSYS on PMID C4
    if abs(sx-111.4)<0.05 and abs(ex-111.4)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=105.95:
        hit=True
    if hit:
        board.Remove(t); n+=1

# Ensure VSYS B5 connection remains: vertical 111.45→105.6 + horiz to 111.8
# (already present). Add C_SYS path if needed — existing (112.8,104.48)->(112.4,104.48)->(112.4,105.6)->(111.8,105.6)

# SW jog: delete (111.4,104.5)->(115.287,104.5) and rebuild north of C_SYS
for t in list(board.GetTracks()):
    if t.GetNetname()!="SW" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # horizontal at y=104.5 toward L_SYS
    if abs(sy-104.5)<0.05 and abs(ey-104.5)<0.05 and max(sx,ex)>=115.0:
        board.Remove(t); n+=1
    # keep short vertical A4→104.5, will extend
nc=board.GetNetInfo().GetNetItem("SW").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    # from A4 already to (111.4,104.5); go north-ish then east above C_SYS
    # Actually A4 is 105.2; corridor at y=104.90 clears C_SYS pad@104.48 (dy=0.42; halfSW0.175+halfpad0.28+clr0.2=0.655 — tight)
    # Use y=105.05 east past C_SYS (x=113.5) then down to L_SYS y=104.5
    (111.400,104.500, 111.400,105.050, 0.30),
    (111.400,105.050, 113.600,105.050, 0.30),
    (113.600,105.050, 113.600,104.500, 0.30),
    (113.600,104.500, 115.287,104.500, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)

# 3V3_DISP: move via@115.55,102.75 → 115.55,101.80 (south of VSYS@102.95)
# and trim F.Cu stubs that skim C_VINLS PMID / C_LDO
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="3V3_DISP": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-115.55)<0.05 and abs(y-102.75)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(115.55),mm(101.80))); n+=1
# update B.Cu vertical that ended at old via
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.B_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-115.55)<0.05 and abs(ex-115.55)<0.05:
        # normalize to (115.55,106.0)->(115.55,101.80)
        t.SetStart(pcbnew.VECTOR2I(mm(115.55),mm(106.00)))
        t.SetEnd(pcbnew.VECTOR2I(mm(115.55),mm(101.80))); n+=1

# Clear 3V3_DISP F stubs near C_VINLS/C_LDO that short PMID
# (112.8,106.32)->(113.0,106.32) and (113.0,106.32)->(113.0,106.0)
# C_LDO pad2 is at 113.5,106.32 — keep connection via (113.0,106.0)->(113.5,106.32) jog
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-106.32)<0.05 and abs(ey-106.32)<0.05 and min(sx,ex)<=112.85 and max(sx,ex)>=112.95:
        hit=True
    if abs(sx-113.0)<0.05 and abs(ex-113.0)<0.05 and min(sy,ey)<=106.05 and max(sy,ey)>=106.25:
        hit=True
    # also the (112.8,106.32) endpoint stubs
    if hit:
        board.Remove(t); n+=1

nc2=board.GetNetInfo().GetNetItem("3V3_DISP").GetNetCode()
# C5(111.8,106.0) → (113.0,106.0) already; extend to C_LDO pad2(113.5,106.32)
for x1,y1,x2,y2,w in [
    (113.000,106.000, 113.500,106.000, 0.30),
    (113.500,106.000, 113.500,106.320, 0.30),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc2); board.Add(t)

# VSYS vs J_STRAP_R pad10: jog VSYS north corridor y=102.95 → 102.40 for x near 116.85
# Or truncate vertical at L_SYS before pad10. Pad10 at 116.85,102.75; L_SYS vertical at 117.412.
# Move VSYS east-corridor south to y=102.40 (farther from pad10 y=102.75 and via)
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # horizontal y=102.95 from ~111.8 to 117.4
    if abs(sy-102.95)<0.05 and abs(ey-102.95)<0.05 and max(sx,ex)>=117.0:
        board.Remove(t); n+=1
    # short (111.8,102.95)->(111.45,102.95)
    if abs(sy-102.95)<0.05 and abs(ey-102.95)<0.05 and max(sx,ex)<=112.0 and min(sx,ex)>=111.4:
        board.Remove(t); n+=1
    # vertical L_SYS (117.412,104.5)->(117.412,102.95)
    if abs(sx-117.412)<0.02 and abs(ex-117.412)<0.02 and min(sy,ey)<=103.0:
        board.Remove(t); n+=1

nc3=board.GetNetInfo().GetNetItem("VSYS").GetNetCode()
for x1,y1,x2,y2,w in [
    # L_SYS down only to 103.40 (north of pad10@102.75), then west at 103.40, then down to 102.40 west of strap
    (117.412,104.500, 117.412,103.400, 0.35),
    (117.412,103.400, 115.000,103.400, 0.35),
    (115.000,103.400, 115.000,102.400, 0.35),
    (115.000,102.400, 111.450,102.400, 0.35),
    (111.450,102.400, 111.450,102.950, 0.35),  # join existing vertical
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del/edit", n)
''')

# ---------------------------------------------------------------------------
# L5: PMIC_INT residual — move via further west + thin VBAT clear
# ---------------------------------------------------------------------------
FIXES["pmic_int_clear"] = dict(code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# Move PMIC_INT via 109.5,106.4 → 109.10,106.70 (NW, clear VBAT@y=106.4 and TS)
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-109.5)<0.05 and abs(y-106.4)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(109.10),mm(106.70))); n+=1
# Replace F stub D2→via
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=109.6 and max(sx,ex)>=110.5:
        board.Remove(t); n+=1
nc=board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (110.600,106.400, 110.600,106.700, 0.15),
    (110.600,106.700, 109.100,106.700, 0.15),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("pmic", n)
''')

# ---------------------------------------------------------------------------
# L6: GND stubs near C_VINLS that short PMID (trim length, do NOT delete vias)
# ---------------------------------------------------------------------------
FIXES["gnd_pmid_trim"] = dict(code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# GND track (112.8,105.32)->(112.8,105.40) almost into PMID@105.60 — shorten/remove spur only
for t in list(board.GetTracks()):
    if t.GetNetname()!="GND" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # tiny spur north from C_VINLS GND pad toward PMID
    if abs(sx-112.8)<0.05 and abs(ex-112.8)<0.05 and min(sy,ey)>=105.30 and max(sy,ey)<=105.45:
        board.Remove(t); n+=1
    # zero-len blob at 112.8,105.40
    if abs(sx-112.8)<0.05 and abs(ex-112.8)<0.05 and abs(sy-105.4)<0.05 and abs(ey-105.4)<0.05:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("gnd_trim", n)
''')

# Combined mega-fix for atomic apply
FIXES["all"] = None  # handled specially


def zone_refill():
    code = r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
filler=pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("filled")
'''
    r=subprocess.run([sys.executable,"-c",code], cwd=str(ROOT), capture_output=True, text=True)
    return r.returncode==0, r.stdout.strip(), r.stderr[-300:] if r.stderr else ""


def drc():
    out = ROOT/"reports/_drc_inc.txt"
    subprocess.check_call(["kicad-cli","pcb","drc","--format","report","--output",str(out),str(PCB)],
                          cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text=out.read_text()
    drc_n=int(re.search(r"Found (\d+)", text).group(1))
    short=text.count("[shorting_items]")
    pairs=Counter()
    for b in re.split(r"\[shorting_items\]:", text)[1:]:
        m=re.search(r"nets ([^\s]+) and ([^\s\)]+)", b.split("\n[")[0])
        if m: pairs[tuple(sorted(m.groups()))]+=1
    POWER=[("GND","VBUS"),("GND","VBAT"),("GND","VBUS_POGO"),("3V3","GND"),("3V3_DISP","GND"),
           ("GND","SW"),("3V3","3V3_DISP"),("GND","VSYS")]
    power={f"{a}|{b}": pairs.get(tuple(sorted([a,b])),0) for a,b in POWER}
    latent = pairs.get(("GND","VSYS"),0)>0
    # via may have moved — report where GND vias near old spot are
    import pcbnew
    board=pcbnew.LoadBoard(str(PCB))
    def tomm(v): return v/1e6
    via_old=False; via_new=False; vias=[]
    for t in board.GetTracks():
        if t.GetClass()!="PCB_VIA": continue
        if t.GetNetname()!="GND": continue
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-111.31)<0.02 and abs(y-102.9)<0.02: via_old=True
        if abs(x-109.50)<0.05 and abs(y-102.9)<0.05: via_new=True
        if 108<=x<=114 and 101.5<=y<=104.5:
            vias.append((round(x,3),round(y,3)))
    return drc_n, short, power, pairs, latent, via_old, via_new, vias


def run_one(name, code, base, allow_equal=False):
    snap=ROOT/f"backups/_try_{name}.kicad_pcb"
    shutil.copy2(PCB, snap)
    r=subprocess.run([sys.executable,"-c",code], cwd=str(ROOT), capture_output=True, text=True)
    print(f"[{name}] out:", r.stdout.strip())
    if r.returncode!=0:
        print(f"[{name}] FAIL", r.stderr[-500:]); shutil.copy2(snap, PCB); return False, base, None
    # zone refill then DRC
    ok, fo, fe = zone_refill()
    print(f"[{name}] fill:", fo, fe[:200] if fe else "")
    drc_n, short, power, pairs, latent, via_old, via_new, vias = drc()
    power_ok = all(v==0 for v in power.values())
    if allow_equal:
        keep = power_ok and short <= base and not latent
    else:
        keep = power_ok and short < base and not latent
    # allow keep on equal if power ok and not latent for intermediate staging? only if allow_equal
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(15)]
    result={"fix":name,"drc":drc_n,"shorting":short,"base":base,"power_ok":power_ok,
            "latent_gnd_vsys":latent,"via_old":via_old,"via_new":via_new,"vias_near":vias,
            "keep":keep,"top":top,"power":power}
    print(json.dumps(result, indent=0))
    if not keep:
        shutil.copy2(snap, PCB)
        print(f"[{name}] REVERTED")
        return False, base, result
    print(f"[{name}] KEEP")
    return True, short, result


def main():
    if FIX == "all":
        order = ["move_latent_via","vbus_spine_west","replace_passives","vsys_pmid_sw_disp","pmic_int_clear","gnd_pmid_trim"]
        base = BASE_SHORT
        kept=[]
        for name in order:
            # intermediate steps: allow equal shorting if power still 0 (placement may reshuffle)
            allow_eq = name in ("move_latent_via",)
            ok, base_or_short, res = run_one(name, FIXES[name]["code"], base, allow_equal=allow_eq)
            if ok:
                kept.append(name)
                base = base_or_short
            else:
                # try continue? No — report and stop this step; try next only if we want
                # For coordinated plan, continue trying remaining on current board state
                print(f"skip continue after fail of {name}")
        # final report
        drc_n, short, power, pairs, latent, via_old, via_new, vias = drc()
        top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(15)]
        print("FINAL", json.dumps({"kept":kept,"shorting":short,"drc":drc_n,"power":power,
            "latent":latent,"via_old":via_old,"via_new":via_new,"top":top}, indent=0))
        return
    if FIX not in FIXES or FIXES[FIX] is None:
        print("unknown", FIX, "known", [k for k in FIXES if FIXES[k]]); sys.exit(1)
    ok, _, _ = run_one(FIX, FIXES[FIX]["code"], BASE_SHORT, allow_equal=(FIX=="move_latent_via"))
    sys.exit(0 if ok else 2)

if __name__=="__main__":
    main()
