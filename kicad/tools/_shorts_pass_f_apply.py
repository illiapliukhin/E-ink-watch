#!/usr/bin/env python3
"""Pass F: one-at-a-time surgical non-power short fixes. Never delete GND copper."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE_SHORT = int(sys.argv[2]) if len(sys.argv) > 2 else 52

FIXES = {}

# 1) Delete duplicate orphan 3V3 stubs into U1 pad31
FIXES["u1_3v3_trim"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)>1e-4: continue
    if abs(sx-97.0)<0.05 and abs(min(sy,ey)-86.35)<0.05 and abs(max(sy,ey)-87.5)<0.05:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# 2) L EPD_RST: remove south corridor through MP/GND via; stay at pad Y
FIXES["l_rst_high"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_RST" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    # horizontal corridor through MP @y=96.90
    if abs(sy-96.90)<0.12 and abs(ey-96.90)<0.12 and xmin<=84.0 and xmax>=87.0: hit=True
    # vertical down from via to corridor
    if abs(sx-87.35)<0.1 and abs(ex-87.35)<0.1 and ymin<=97.0 and ymax>=99.5: hit=True
    # vertical up from corridor to pad stub
    if abs(sx-83.50)<0.1 and abs(ex-83.50)<0.1 and ymin<=97.0 and ymax>=99.5: hit=True
    # old pad stub may stay; also remove prior 97.55 corridor if present
    if abs(sy-97.55)<0.12 and abs(ey-97.55)<0.12 and xmin<=84.0 and xmax>=87.0: hit=True
    if abs(sy-97.80)<0.12 and abs(ey-97.80)<0.12 and xmin<=84.0 and xmax>=87.0: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_RST").GetNetCode(); F=pcbnew.F_Cu
# stay at y=99.80: via → west → pad stub (pad already has 83.50-83.15 @99.75)
for x1,y1,x2,y2 in [
    (87.35,99.80, 84.00,99.80),
    (84.00,99.80, 84.00,99.75),
    (84.00,99.75, 83.50,99.75),
    (83.50,99.75, 83.15,99.75),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# 3) Shrink J_STRAP_L south MP (belt for RST if any skim remains)
FIXES["mp_south_shrink"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for fp in board.GetFootprints():
    if fp.GetReference()!="J_STRAP_L": continue
    for p in fp.Pads():
        if p.GetNumber()!="MP" or p.GetNetname()!="GND": continue
        if abs(tomm(p.GetPosition().y)-96.35)<0.3:
            p.SetSize(pcbnew.VECTOR2I(mm(1.0),mm(1.4)))
            p.SetPosition(pcbnew.VECTOR2I(mm(85.70),mm(95.80)))
            n=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# 4) MAIN CS channel y=85.00 → 85.45 (clear MOSI @84.90)
FIXES["main_cs_y"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_CS_MAIN" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    if abs(sx-100.80)<0.1 and abs(ex-100.80)<0.1 and ymin<=85.1 and ymax>=86.2: hit=True
    if abs(sy-85.00)<0.08 and abs(ey-85.00)<0.08 and xmin<=99.8 and xmax>=100.7: hit=True
    if abs(sx-99.75)<0.1 and abs(ex-99.75)<0.1 and ymin<=83.2 and ymax>=85.1: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_CS_MAIN").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [
    (100.80,86.35, 100.80,85.45),
    (100.80,85.45, 99.75,85.45),
    (99.75,85.45, 99.75,83.15),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# 5) R SCK vertical x=115.65 → 115.20 (clear MOSI via@115.90)
FIXES["r_sck_x"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_SCK" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    if abs(sx-115.65)<0.1 and abs(ex-115.65)<0.1 and ymin<=97.0 and ymax>=99.5: hit=True
    if abs(sy-99.75)<0.08 and abs(ey-99.75)<0.08 and xmin<=115.7 and xmax>=116.8: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_SCK").GetNetCode(); F=pcbnew.F_Cu
# keep via@115.65,96.80 — jog west then north then to pad
for x1,y1,x2,y2 in [
    (115.65,96.80, 115.20,96.80),
    (115.20,96.80, 115.20,99.75),
    (115.20,99.75, 116.85,99.75),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# 6) nRESET: jog south of J_SWD pad bottoms (clear pad3 SWDCLK)
FIXES["nreset_jog"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="nRESET" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    # stub and north jog that skim pad
    if abs(sy-106.50)<0.08 and abs(ey-106.50)<0.08 and xmin<=87.6 and xmax>=88.3: hit=True
    if abs(sx-88.40)<0.1 and abs(ex-88.40)<0.1 and ymin<=106.5 and ymax>=107.2: hit=True
    if abs(sy-107.20)<0.08 and abs(ey-107.20)<0.08 and xmin<=88.5 and xmax>=91.5: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("nRESET").GetNetCode(); F=pcbnew.F_Cu
# stay at y=106.85 (below J_SWD pad bottoms ~107.15), then up into pad4 column
for x1,y1,x2,y2 in [
    (87.55,106.50, 88.40,106.50),
    (88.40,106.50, 88.40,106.85),
    (88.40,106.85, 91.62,106.85),
    (91.62,106.85, 91.62,108.00),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# 7) nRESET_POGO: move vertical off GND stub @97.48
FIXES["nreset_pogo_x"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="nRESET_POGO" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    if abs(sx-97.50)<0.1 and abs(ex-97.50)<0.1 and ymin<=106.6 and ymax>=110.5: hit=True
    if abs(sy-111.00)<0.08 and abs(ey-111.00)<0.08 and xmin<=96.1 and xmax>=97.4: hit=True
    if abs(sx-96.00)<0.1 and abs(ex-96.00)<0.1 and ymin<=108.0 and ymax>=111.0: hit=True
    if abs(sy-106.50)<0.08 and abs(ey-106.50)<0.08 and xmin<=93.5 and xmax>=95.4: hit=True
    # diagonal/jog piece
    if abs(sx-95.45)<0.15 and abs(sy-106.50)<0.15 and abs(ex-96.00)<0.15 and abs(ey-108.00)<0.15: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("nRESET_POGO").GetNetCode(); F=pcbnew.F_Cu
# from SW_DBG pad4 @93.45,106.50 → east to 98.30 → south to pogo y=111 → west to 96
for x1,y1,x2,y2 in [
    (93.45,106.50, 98.30,106.50),
    (98.30,106.50, 98.30,111.00),
    (98.30,111.00, 96.00,111.00),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# 8) PMIC_INT: delete B.Cu overrun into GND vias (keep to y=106.40)
FIXES["pmic_int_trunc"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.GetLayer()!=pcbnew.B_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    ymin,ymax=min(sy,ey),max(sy,ey)
    # the long one that reaches 107.5
    if abs(sx-94.20)<0.1 and abs(ex-94.20)<0.1 and ymax>=107.3:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# 9) BTN3 B: y=109.15 → 110.20 (clear 3V3 via@102.52,109.40)
FIXES["btn3_y110"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="BTN3" or t.GetLayer()!=pcbnew.B_Cu: continue
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
    return drc_n, short, power, pairs

def main():
    if FIX not in FIXES:
        print("unknown", FIX, "known", list(FIXES)); sys.exit(1)
    fix=FIXES[FIX]
    snap=ROOT/f"backups/_try_{FIX}.kicad_pcb"
    shutil.copy2(PCB, snap)
    r=subprocess.run([sys.executable,"-c",fix["del_code"]], cwd=str(ROOT), capture_output=True, text=True)
    print("del:", r.stdout.strip(), (r.stderr[-300:] if r.returncode else ""))
    if r.returncode!=0:
        shutil.copy2(snap, PCB); print("FAIL del"); sys.exit(2)
    if fix["reb_code"]:
        r=subprocess.run([sys.executable,"-c",fix["reb_code"]], cwd=str(ROOT), capture_output=True, text=True)
        print("reb:", r.stdout.strip(), "rc", r.returncode)
        if r.returncode!=0:
            shutil.copy2(snap, PCB); print("FAIL reb"); sys.exit(2)
    drc_n, short, power, pairs = drc()
    ok=all(v==0 for v in power.values()) and short <= BASE_SHORT
    # also require strict improvement OR equal with other gains — keep if short < base OR (short==base and we want allow)
    improve = short < BASE_SHORT
    keep = ok and (improve or short == BASE_SHORT and FIX in ("mp_south_shrink",))
    # Actually for equal shorting without power break, only keep if not worse; prefer strict improve
    keep = all(v==0 for v in power.values()) and short < BASE_SHORT
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(8)]
    print(json.dumps({"fix":FIX,"drc":drc_n,"shorting":short,"base":BASE_SHORT,"power_ok":all(v==0 for v in power.values()),"power":power,"keep":keep,"top":top}))
    if not keep:
        shutil.copy2(snap, PCB)
        print("REVERTED")
        sys.exit(2)
    print("KEEP")

if __name__=="__main__":
    main()
