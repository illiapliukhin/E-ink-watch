#!/usr/bin/env python3
"""Pass G: surgical pad-pad / power-pocket short fixes. Never delete GND copper."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE_SHORT = int(sys.argv[2]) if len(sys.argv) > 2 else 44

FIXES = {}

# --- 1) Delete erroneous VSYS tracks that sit on PMID pads (B4/C4) ---
FIXES["vsys_pmid_stubs"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    # horizontal onto B4 PMID: (111.800,105.600)-(111.400,105.600)
    if abs(sy-105.600)<0.05 and abs(ey-105.600)<0.05:
        xs=sorted([sx,ex])
        if xs[0]<=111.45 and xs[1]>=111.35 and xs[1]<=111.85:
            # only the short stubs that reach 111.400, not the 111.450-111.800 OK piece
            if xs[0] < 111.55:  # reaches left of B5 center toward B4
                hit=True
    # vertical onto C4 PMID: (111.400,105.600)-(111.400,106.000)
    if abs(sx-111.400)<0.05 and abs(ex-111.400)<0.05:
        ys=sorted([sy,ey])
        if ys[0]<=105.65 and ys[1]>=105.95:
            hit=True
    if hit:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 2) PMID C_VINLS feed: move horizontal off VSYS pad-row Y ---
# delete PMID (112.800,105.600)-(111.400,105.600) and vertical (112.800,106.280)-(112.800,105.600)
# rebuild: pad1 C_VINLS @112.800,106.280 → west at y=106.15 → to 111.400 → south to 105.600 (B4)
FIXES["pmid_cvinls_jog"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMID" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    if abs(sy-105.600)<0.05 and abs(ey-105.600)<0.05 and min(sx,ex)<=111.5 and max(sx,ex)>=112.5:
        hit=True
    if abs(sx-112.800)<0.05 and abs(ex-112.800)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.2:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("PMID").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (112.800,106.280, 112.800,106.15, 0.25),
    (112.800,106.15, 111.400,106.15, 0.25),
    (111.400,106.15, 111.400,105.600, 0.20),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 3) GND stub at C_VINLS pad2: truncate so it doesn't reach PMID track ---
# Do NOT delete GND via; only shorten the tiny F.Cu stub if it overruns
FIXES["gnd_cvinls_trunc"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="GND" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # tiny stub (112.800,105.320)-(112.800,105.400)
    if abs(sx-112.800)<0.05 and abs(ex-112.800)<0.05:
        if min(sy,ey)>=105.30 and max(sy,ey)<=105.45:
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 4) 3V3_DISP stubs into C_VINLS PMID pad ---
FIXES["disp_pmid_trim"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    # (113.000,106.320)-(113.000,106.000) and (112.800,106.320)-(113.000,106.320)
    if abs(sx-113.000)<0.05 and abs(ex-113.000)<0.05 and min(sy,ey)<=106.05 and max(sy,ey)>=106.25:
        hit=True
    if abs(sy-106.320)<0.05 and abs(ey-106.320)<0.05 and min(sx,ex)<=112.85 and max(sx,ex)>=112.95:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("3V3_DISP").GetNetCode(); F=pcbnew.F_Cu
# keep east connection from U2 C5 @111.800,106.000 → 113.000,106.000 only (no south into PMID)
# existing horiz may remain; ensure via path intact
for x1,y1,x2,y2,w in [
    (113.000,106.000, 113.000,106.00, 0.30),  # noop guard
]:
    pass
# just ensure a stub to via area if missing — B.Cu already has (113,106)-(115.55,106)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 5) VBUS south jog clear of R_VSYS 3V3 pad/via ---
FIXES["vbus_south_jog"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBUS" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    # horiz @102.900 spanning 105.5-110.6
    if abs(sy-102.900)<0.05 and abs(ey-102.900)<0.05 and min(sx,ex)<=108.2 and max(sx,ex)>=105.4:
        hit=True
    if abs(sy-102.900)<0.05 and abs(ey-102.900)<0.05 and min(sx,ex)<=110.6 and max(sx,ex)>=108.0:
        hit=True
    # vertical down from C_IN (108.120,104.500)-(108.120,102.900)
    if abs(sx-108.120)<0.05 and abs(ex-108.120)<0.05 and min(sy,ey)<=102.95 and max(sy,ey)>=104.4:
        hit=True
    # stub (105.500,103.700)-(105.500,102.900)
    if abs(sx-105.500)<0.05 and abs(ex-105.500)<0.05 and min(sy,ey)<=102.95 and max(sy,ey)>=103.6:
        hit=True
    # up to U2 (110.600,102.900)-(110.600,105.200)
    if abs(sx-110.600)<0.05 and abs(ex-110.600)<0.05 and min(sy,ey)<=103.0 and max(sy,ey)>=105.1:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBUS").GetNetCode(); F=pcbnew.F_Cu
# corridor at y=102.35 clear of R_VSYS pad2 center 102.975 size~0.95 → south edge ~102.50; track half 0.175 + clr 0.15 → need center <=102.175... use 102.30 with w=0.25
for x1,y1,x2,y2,w in [
    (105.500,103.700, 105.500,102.35, 0.25),
    (105.500,102.35, 108.120,102.35, 0.25),
    (108.120,102.35, 108.120,104.500, 0.35),
    (108.120,102.35, 110.600,102.35, 0.35),
    (110.600,102.35, 110.600,105.200, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 6) Shrink J_STRAP_L south MP (pad size only, keep net) for EPD_RST ---
FIXES["mp_l_south_shrink"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for fp in board.GetFootprints():
    if fp.GetReference()!="J_STRAP_L": continue
    for p in fp.Pads():
        if p.GetNumber()!="MP" or p.GetNetname()!="GND": continue
        if abs(tomm(p.GetPosition().y)-96.350)<0.3:
            # shrink in place; do NOT delete copper elsewhere
            p.SetSize(pcbnew.VECTOR2I(mm(1.0),mm(1.2)))
            p.SetPosition(pcbnew.VECTOR2I(mm(85.50),mm(95.70)))
            n=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 7) EPD_RST: remove corridor through MP; stay high then drop west of MP ---
FIXES["l_rst_around_mp"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_RST" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    if max(sx,ex)>=95: continue
    hit=False
    if abs(sy-96.90)<0.12 and abs(ey-96.90)<0.12 and min(sx,ex)<=84.0 and max(sx,ex)>=87.0: hit=True
    if abs(sx-87.35)<0.1 and abs(ex-87.35)<0.1 and min(sy,ey)<=97.0 and max(sy,ey)>=99.5: hit=True
    if abs(sx-83.50)<0.1 and abs(ex-83.50)<0.1 and min(sy,ey)<=97.0 and max(sy,ey)>=99.5: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_RST").GetNetCode(); F=pcbnew.F_Cu
# via@87.35,99.80 → west at 99.80 past MP → south outside MP → pad
for x1,y1,x2,y2 in [
    (87.35,99.80, 84.20,99.80),
    (84.20,99.80, 84.20,99.75),
    (84.20,99.75, 83.50,99.75),
    (83.50,99.75, 83.15,99.75),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 8) Pad-pad: nudge R_ISET west (clear R_ILIM / C_PMID) ---
FIXES["riset_west"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for fp in board.GetFootprints():
    if fp.GetReference()!="R_ISET": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x-0.70),mm(y)))
    n=1
    # shift connected track endpoints that sat on old pads
    old_p1=(109.290,103.500); new_p1=(109.290-0.70,103.500)
    old_p2=(110.310,103.500); new_p2=(110.310-0.70,103.500)
    for t in list(board.GetTracks()):
        if t.GetClass()=="PCB_VIA": continue
        for end_name in ("Start","End"):
            pt=t.GetStart() if end_name=="Start" else t.GetEnd()
            px,py=tomm(pt.x),tomm(pt.y)
            for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
                if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 9) Pad-pad: nudge R_IPRETERM east (clear R_ILIM GND / C_PMID GND) ---
FIXES["ripre_east"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for fp in board.GetFootprints():
    if fp.GetReference()!="R_IPRETERM": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+0.55),mm(y)))
    n=1
    old_p1=(111.490,103.500); new_p1=(111.490+0.55,103.500)
    old_p2=(112.510,103.500); new_p2=(112.510+0.55,103.500)
    for t in list(board.GetTracks()):
        if t.GetClass()=="PCB_VIA": continue
        for end_name in ("Start","End"):
            pt=t.GetStart() if end_name=="Start" else t.GetEnd()
            px,py=tomm(pt.x),tomm(pt.y)
            for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
                if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 10) C_PMID south nudge (clear resistor row) ---
FIXES["cpmid_south"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for fp in board.GetFootprints():
    if fp.GetReference()!="C_PMID": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y-0.45)))
    n=1
    old_p1=(110.520,103.900); new_p1=(110.520,103.900-0.45)
    old_p2=(111.480,103.900); new_p2=(111.480,103.900-0.45)
    for t in list(board.GetTracks()):
        if t.GetClass()=="PCB_VIA": continue
        for end_name in ("Start","End"):
            pt=t.GetStart() if end_name=="Start" else t.GetEnd()
            px,py=tomm(pt.x),tomm(pt.y)
            for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
                if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 11) R_LSCTRL west nudge (clear SW3 BTN3) ---
FIXES["rlsctrl_west"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for fp in board.GetFootprints():
    if fp.GetReference()!="R_LSCTRL": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x-0.80),mm(y)))
    n=1
    # shift track ends near old pads
    deltas=[(114.600,108.760),(114.600,107.740),(114.600,106.800)]
    for t in list(board.GetTracks()):
        if t.GetClass()=="PCB_VIA": continue
        for end_name in ("Start","End"):
            pt=t.GetStart() if end_name=="Start" else t.GetEnd()
            px,py=tomm(pt.x),tomm(pt.y)
            for ox,oy in deltas:
                if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(ox-0.80),mm(oy)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(ox-0.80),mm(oy)))
    # via at 114.300,108.410
    for t in list(board.GetTracks()):
        if t.GetClass()!="PCB_VIA": continue
        if t.GetNetname()!="3V3": continue
        x,y=tomm(t.GetStart().x),tomm(t.GetStart().y)
        if abs(x-114.300)<0.1 and abs(y-108.410)<0.1:
            t.SetPosition(pcbnew.VECTOR2I(mm(113.500),mm(108.410)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 12) R_SDA south-west nudge (clear U2 CD / 3V3 mash) ---
FIXES["rsda_sw"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
dx,dy=-0.35,+0.55
for fp in board.GetFootprints():
    if fp.GetReference()!="R_SDA": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y+dy)))
    n=1
    old=[(109.440,106.950),(110.460,106.950)]
    for t in list(board.GetTracks()):
        if t.GetClass()=="PCB_VIA": continue
        for end_name in ("Start","End"):
            pt=t.GetStart() if end_name=="Start" else t.GetEnd()
            px,py=tomm(pt.x),tomm(pt.y)
            for ox,oy in old:
                if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(ox+dx),mm(oy+dy)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(ox+dx),mm(oy+dy)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 13) SW corridor y: 104.500 → 104.15 (clear VSYS @104.480 C_SYS) ---
FIXES["sw_y_south"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="SW" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-104.500)<0.08 and abs(ey-104.500)<0.08 and max(sx,ex)>112:
        # shift this horizontal south
        t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(104.15)))
        t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(104.15)))
        n+=1; hit=True
    if abs(sx-111.400)<0.05 and abs(ex-111.400)<0.05 and min(sy,ey)<=104.55 and max(sy,ey)>=105.1:
        # vertical from pad to corridor — retarget end
        if abs(sy-104.500)<0.1:
            t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(104.15))) if abs(sy-104.5)<0.1 else None
            t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(104.15))) if abs(ey-104.5)<0.1 else None
            # rewrite properly:
            ys=sorted([(sy,"s"),(ey,"e")])
            # set the south endpoint to 104.15
            if abs(sy-104.500)<0.1: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(104.15)))
            if abs(ey-104.500)<0.1: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(104.15)))
            n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 14) VSYS east: jog south of 3V3_DISP via@115.55,102.75 and pad10 ---
FIXES["vsys_east_jog"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-102.950)<0.05 and abs(ey-102.950)<0.05 and max(sx,ex)>=115:
        hit=True
    if abs(sx-117.412)<0.05 and abs(ex-117.412)<0.05:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VSYS").GetNetCode(); F=pcbnew.F_Cu
# from 111.800,102.950 go east only to 114.5, then south, then east at y=103.60 clear of via/pad
for x1,y1,x2,y2,w in [
    (111.800,102.950, 114.50,102.950, 0.35),
    (114.50,102.950, 114.50,103.60, 0.35),
    (114.50,103.60, 117.412,103.60, 0.35),
    (117.412,103.60, 117.412,104.500, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 15) PMIC_INT via: nudge east clear of VBAT tracks ---
FIXES["pmic_int_via"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# pad D2 is at 110.600,106.400 — via sits on pad; move via south-east off VBAT row
vias=[]
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetStart().x),tomm(t.GetStart().y)
    if abs(x-110.600)<0.1 and abs(y-106.400)<0.1:
        vias.append(t)
# keep one via, move it; delete dupes
if vias:
    vias[0].SetPosition(pcbnew.VECTOR2I(mm(110.600),mm(106.85)))
    n+=1
    for v in vias[1:]:
        board.Remove(v); n+=1
# add short stub from pad to via if needed
nc=board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode()
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(110.600),mm(106.400)))
t.SetEnd(pcbnew.VECTOR2I(mm(110.600),mm(106.85)))
t.SetWidth(mm(0.18)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 16) NTC/R_TS: nudge NTC north clear of R_TS VBUS pad ---
FIXES["ntc_north"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
dy=+0.40
for fp in board.GetFootprints():
    if fp.GetReference()!="NTC_BAT": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y+dy)))
    n=1
    old=[(107.690,107.800),(108.710,107.800)]
    for t in list(board.GetTracks()):
        if t.GetClass()=="PCB_VIA": continue
        for end_name in ("Start","End"):
            pt=t.GetStart() if end_name=="Start" else t.GetEnd()
            px,py=tomm(pt.x),tomm(pt.y)
            for ox,oy in old:
                if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(ox),mm(oy+dy)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(ox),mm(oy+dy)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 17) C_IN west nudge clear of R_VSYS ---
FIXES["cin_west"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
dx=-0.50
for fp in board.GetFootprints():
    if fp.GetReference()!="C_IN": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y)))
    n=1
    old=[(108.120,104.500),(109.080,104.500)]
    for t in list(board.GetTracks()):
        if t.GetClass()=="PCB_VIA": continue
        for end_name in ("Start","End"):
            pt=t.GetStart() if end_name=="Start" else t.GetEnd()
            px,py=tomm(pt.x),tomm(pt.y)
            for ox,oy in old:
                if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(ox+dx),mm(oy)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(ox+dx),mm(oy)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 18) EPD_DC / EPD_RST: jog DC clear of RST via@112.65,99.80 ---
FIXES["epd_dc_rst"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_DC" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    # track near (112.900,99.100) length 1.65
    if min(sx,ex)<=113.0 and max(sx,ex)>=112.5 and min(sy,ey)<=99.2 and max(sy,ey)>=98.9:
        if abs(sy-99.100)<0.15 or abs(ey-99.100)<0.15 or abs(sx-112.900)<0.15:
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
# inspect remaining DC near zone — add jog south of via
nc=board.GetNetInfo().GetNetItem("EPD_DC").GetNetCode(); F=pcbnew.F_Cu
# conservative stub jog at y=98.70
for x1,y1,x2,y2 in [
    (112.90,99.10, 112.90,98.70),
    (112.90,98.70, 114.50,98.70),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 19) MAIN MOSI/SCK share y=84.90: jog MOSI ---
FIXES["main_mosi_y"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_MOSI" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    if max(sx,ex)>110: continue
    hit=False
    if abs(sy-84.90)<0.08 and abs(ey-84.90)<0.08 and min(sx,ex)<=101.6 and max(sx,ex)>=98:
        hit=True
    if abs(sx-101.60)<0.1 and abs(ex-101.60)<0.1 and min(sy,ey)<=85.0 and max(sy,ey)>=86.2:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_MOSI").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [
    (101.60,86.35, 101.60,84.55),
    (101.60,84.55, 99.25,84.55),
    (99.25,84.55, 99.25,84.90),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 20) CD track: jog north clear of R_SDA 3V3 ---
FIXES["cd_north"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="CD" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-106.800)<0.05 and abs(ey-106.800)<0.05 and min(sx,ex)<=110.7 and max(sx,ex)>=112.5:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("CD").GetNetCode(); F=pcbnew.F_Cu
# from pad E2 @110.600,106.800 go south slightly then east (away from R_SDA @106.95)
for x1,y1,x2,y2 in [
    (110.600,106.800, 110.600,107.35),
    (110.600,107.35, 112.800,107.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 21) 3V3 near SCL via: nudge via ---
FIXES["scl_3v3_via"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="3V3": continue
    x,y=tomm(t.GetStart().x),tomm(t.GetStart().y)
    if abs(x-112.010)<0.1 and abs(y-106.900)<0.1:
        t.SetPosition(pcbnew.VECTOR2I(mm(112.010),mm(107.600)))
        n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- 22) nRESET_POGO clear VBAT via@96.20,106.25 ---
FIXES["nreset_pogo_y"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="nRESET_POGO" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    if abs(sy-106.50)<0.08 and abs(ey-106.50)<0.08 and min(sx,ex)<=93.5 and max(sx,ex)>=98.0: hit=True
    if abs(sx-98.30)<0.1 and abs(ex-98.30)<0.1: hit=True
    if abs(sy-111.00)<0.08 and abs(ey-111.00)<0.08 and min(sx,ex)<=96.1 and max(sx,ex)>=98.2: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("nRESET_POGO").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [
    (93.45,106.50, 93.45,107.30),
    (93.45,107.30, 98.30,107.30),
    (98.30,107.30, 98.30,111.00),
    (98.30,111.00, 96.00,111.00),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 23) BTN3 B.Cu clear 3V3 via@102.52,109.40 ---
FIXES["btn3_y110"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="BTN3" or t.GetLayer()!=pcbnew.B_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    if abs(sy-109.15)<0.12 and abs(ey-109.15)<0.12 and min(sx,ex)<=99: hit=True
    if abs(sx-98.80)<0.1 and abs(ex-98.80)<0.1 and max(sy,ey)>=109.0: hit=True
    if abs(sx-114.80)<0.1 and abs(ex-114.80)<0.1 and min(sy,ey)<=109.2 and max(sy,ey)>=108.0: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("BTN3").GetNetCode(); B=pcbnew.B_Cu
for x1,y1,x2,y2 in [
    (98.80,93.95, 98.80,110.20),
    (98.80,110.20, 114.80,110.20),
    (114.80,110.20, 114.80,108.00),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(B); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- 24) LSCTRL track clear 3V3 via after rlsctrl move (fallback jog) ---
FIXES["lsctrl_jog"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="LSCTRL" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-106.800)<0.05 and abs(ey-106.800)<0.05 and min(sx,ex)<=111.1 and max(sx,ex)>=114.0:
        board.Remove(t); n+=1
    if abs(sx-114.600)<0.05 and abs(ex-114.600)<0.05 and min(sy,ey)<=106.9 and max(sy,ey)>=108.7:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
# find current R_LSCTRL pad1
fp=None
for f in board.GetFootprints():
    if f.GetReference()=="R_LSCTRL": fp=f; break
def tomm(v): return v/1e6
px=py=None
for p in fp.Pads():
    if p.GetNumber()=="1":
        px,py=tomm(p.GetPosition().x),tomm(p.GetPosition().y)
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode(); F=pcbnew.F_Cu
# U2 E3 @111.000,106.800 → east at 106.55 (south of CD row) → to resistor
for x1,y1,x2,y2 in [
    (111.000,106.800, 111.000,106.50),
    (111.000,106.50, px,106.50),
    (px,106.50, px,py),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb", px, py)
''')

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
    POWER=[("GND","VBUS"),("GND","VBAT"),("GND","VBUS_POGO"),("3V3","GND"),("3V3_DISP","GND"),("GND","SW"),("3V3","3V3_DISP"),("GND","VSYS")]
    power={f"{a}|{b}": pairs.get(tuple(sorted([a,b])),0) for a,b in POWER}
    # latent check
    latent = ("GND","VSYS") in pairs and pairs[("GND","VSYS")]>0
    return drc_n, short, power, pairs, latent

def main():
    if FIX not in FIXES:
        print("unknown", FIX, "known", list(FIXES)); sys.exit(1)
    fix=FIXES[FIX]
    snap=ROOT/f"backups/_try_{FIX}.kicad_pcb"
    shutil.copy2(PCB, snap)
    r=subprocess.run([sys.executable,"-c",fix["del_code"]], cwd=str(ROOT), capture_output=True, text=True)
    print("del:", r.stdout.strip(), (r.stderr[-400:] if r.returncode else ""))
    if r.returncode!=0:
        shutil.copy2(snap, PCB); print("FAIL del"); sys.exit(2)
    if fix["reb_code"]:
        r=subprocess.run([sys.executable,"-c",fix["reb_code"]], cwd=str(ROOT), capture_output=True, text=True)
        print("reb:", r.stdout.strip(), "rc", r.returncode)
        if r.returncode!=0:
            shutil.copy2(snap, PCB); print("FAIL reb"); sys.exit(2)
    drc_n, short, power, pairs, latent = drc()
    keep = all(v==0 for v in power.values()) and short < BASE_SHORT and not latent
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(10)]
    print(json.dumps({"fix":FIX,"drc":drc_n,"shorting":short,"base":BASE_SHORT,"power_ok":all(v==0 for v in power.values()),"latent_gnd_vsys":latent,"keep":keep,"top":top,"power":power}))
    if not keep:
        shutil.copy2(snap, PCB)
        print("REVERTED")
        sys.exit(2)
    print("KEEP")

if __name__=="__main__":
    main()
