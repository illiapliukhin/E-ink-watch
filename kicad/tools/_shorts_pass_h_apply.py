#!/usr/bin/env python3
"""Pass H: non-PMIC surgical shorts (BTN/VBUS, TS/VBUS, LSCTRL, BTN3). Never delete GND copper."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE_SHORT = int(sys.argv[2]) if len(sys.argv) > 2 else 34

FIXES = {}

# --- H1: Move SW3 east to clear R_LSCTRL pad stack ---
FIXES["sw3_east"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(v): return v/1e6
fp=None
for f in board.GetFootprints():
    if f.GetReference()=="SW3": fp=f; break
oldx,oldy=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
# +0.90 mm east: pad1 114.80→115.70; left edge ~115.25 vs R_LSCTRL right 114.87
dx=0.90
fp.SetPosition(pcbnew.VECTOR2I(mm(oldx+dx), mm(oldy)))
# Move attached BTN3 copper that was locked to old pad1 x=114.80
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="BTN3": continue
    if t.GetClass()=="PCB_VIA":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-114.80)<0.05 and abs(y-109.50)<0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(114.80+dx), mm(y))); n+=1
        continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    ch=False
    if abs(sx-114.80)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx+dx),mm(sy))); ch=True
    if abs(ex-114.80)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex+dx),mm(ey))); ch=True
    if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"sw3 {oldx},{oldy} -> {oldx+dx},{oldy} moved_trk={n}")
''', reb_code=None)

# --- H2: Delete bogus 3V3 track from R_LSCTRL pad1 (LSCTRL) to 3V3 via ---
FIXES["bogus_3v3_ls"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # (114.6,108.76)-(114.3,108.41) from LSCTRL pad1 to 3V3 via
    pts=sorted([(round(sx,2),round(sy,2)),(round(ex,2),round(ey,2))])
    if pts==[(114.3,108.41),(114.6,108.76)] or pts==[(114.30,108.41),(114.60,108.76)]:
        board.Remove(t); n+=1
    elif abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08:
        board.Remove(t); n+=1
    elif abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
# Proper 3V3: pad2 @114.600,107.740 → west/south to via @114.300,108.410
# Use path that stays on pad2 side: (114.6,107.74)-(114.3,107.74)-(114.3,108.41)
nc=board.GetNetInfo().GetNetItem("3V3").GetNetCode(); F=pcbnew.F_Cu
# avoid dup if east stub already exists
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.20)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- H3: LSCTRL jog west of R_LSCTRL pad2 / 3V3 via ---
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
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0:
        hit=True
    if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode(); F=pcbnew.F_Cu
# U2 E3 @111.000,106.800 → east to 113.55 → north to pad1 y → east to pad1
# x=113.55 clears 3V3 via@114.30 (left 114.0) and pad2@114.60
for x1,y1,x2,y2 in [
    (111.000,106.800, 113.550,106.800),
    (113.550,106.800, 113.550,108.760),
    (113.550,108.760, 114.600,108.760),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- H4: BTN3 B.Cu dogbone around 3V3 via@102.52,109.40 ---
FIXES["btn3_dogbone"] = dict(del_code=r'''
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
    # long horizontal at y=109.15
    if abs(sy-109.15)<0.12 and abs(ey-109.15)<0.12 and min(sx,ex)<=100 and max(sx,ex)>=110:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(v): return v/1e6
# find current BTN3 via / east x (after SW3 move)
east_x=114.80
for t in board.GetTracks():
    if t.GetClass()=="PCB_VIA" and t.GetNetname()=="BTN3":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(y-109.50)<0.2: east_x=x
nc=board.GetNetInfo().GetNetItem("BTN3").GetNetCode(); B=pcbnew.B_Cu
# dogbone north around 3V3@102.52,109.40 and GND@103.10,109.80
for x1,y1,x2,y2 in [
    (98.80,109.15, 101.70,109.15),
    (101.70,109.15, 101.70,110.35),
    (101.70,110.35, 103.60,110.35),
    (103.60,110.35, 103.60,109.15),
    (103.60,109.15, east_x,109.15),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(B); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb", east_x)
''')

# --- H5: TS clear R_TS VBUS pad — jog west ---
FIXES["ts_west_jog"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="TS" or t.GetLayer()!=pcbnew.F_Cu: continue
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    # vertical down from NTC into VBUS: (107.69,108.15)-(107.69,107.3)
    if abs(sx-107.69)<0.05 and abs(ex-107.69)<0.05 and min(sy,ey)<=107.4 and max(sy,ey)>=108.0:
        hit=True
    # horizontal (107.69,107.3)-(111.0,107.3)
    if abs(sy-107.30)<0.05 and abs(ey-107.30)<0.05 and min(sx,ex)<=107.8 and max(sx,ex)>=110.5:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("TS").GetNetCode(); F=pcbnew.F_Cu
# NTC pad1 @107.690,108.150 → west to 107.00 → south to 107.55 → east to 111.0 → to U2
# stay clear of R_TS VBUS pad @107.690,107.000 (top ~107.32)
for x1,y1,x2,y2 in [
    (107.690,108.150, 107.000,108.150),
    (107.000,108.150, 107.000,107.550),
    (107.000,107.550, 111.000,107.550),
    (111.000,107.550, 111.000,106.000),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- H6: VBUS clear SW1 BTN1 pad — west corridor ---
FIXES["vbus_sw1_clear"] = dict(del_code=r'''
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
    # horizontals at y=112 through SW1
    if abs(sy-112.00)<0.08 and abs(ey-112.00)<0.08 and min(sx,ex)<=106.0 and max(sx,ex)>=106.5:
        hit=True
    # vertical spine x=107 from 112 to 104.5
    if abs(sx-107.00)<0.08 and abs(ex-107.00)<0.08 and min(sy,ey)<=105 and max(sy,ey)>=111:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBUS").GetNetCode(); F=pcbnew.F_Cu
# west corridor x=106.40 clears SW1 left edge 107.05 (w=0.35 → right 106.575, clr 0.475)
for x1,y1,x2,y2,w in [
    (105.7875,112.000, 106.400,112.000, 0.35),
    (106.400,112.000, 106.400,104.500, 0.35),
    (106.400,104.500, 108.120,104.500, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')


# --- H2+H3 combo: delete bogus 3V3 + LSCTRL jog (reconnect pad2 safely) ---
FIXES["lsctrl_combo"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1; continue
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
        hit=False
        if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0: hit=True
        if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5: hit=True
        if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
for x1,y1,x2,y2 in [
    (111.000,106.800, 113.550,106.800),
    (113.550,106.800, 113.550,108.760),
    (113.550,108.760, 114.600,108.760),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# 3V3 pad2 to via — path stays south of LSCTRL y=108.76 stub
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.20)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


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
    latent = pairs.get(("GND","VSYS"),0)>0
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
    keep = all(v==0 for v in power.values()) and short <= BASE_SHORT and not latent
    # allow equal shorting only if we didn't make power worse; prefer strict lower for keep of "progress"
    # Actually for intermediate: keep if shorting not higher and power ok
    keep = all(v==0 for v in power.values()) and short <= BASE_SHORT and not latent
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(12)]
    print(json.dumps({"fix":FIX,"drc":drc_n,"shorting":short,"base":BASE_SHORT,"power_ok":all(v==0 for v in power.values()),"latent_gnd_vsys":latent,"keep":keep,"top":top,"power":power}))
    if not keep:
        shutil.copy2(snap, PCB)
        print("REVERTED")
        sys.exit(2)
    print("KEEP")

if __name__=="__main__":
    main()
