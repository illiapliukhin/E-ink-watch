#!/usr/bin/env python3
"""Pass-L topology: fat power reconnect + VBUS west + passive placement.
I_peak assume 0.5 A charge class on VBUS/VBAT/PMID/VSYS.
Widths: PowerFat 0.50 (VBUS/VBAT/PMID), Power 0.45 (VSYS), Signal 0.18.
"""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
W_FAT, W_PWR, W_SIG = 0.50, 0.45, 0.18

def fill():
    subprocess.run([sys.executable,"-c",'''
import pcbnew
b=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", b)
'''], cwd=str(ROOT), capture_output=True, check=True)

def drc():
    out = ROOT/"reports/_drc_inc.txt"
    subprocess.check_call(["kicad-cli","pcb","drc","--format","report","--output",str(out),str(PCB)],
                          cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text=out.read_text()
    short=text.count("[shorting_items]")
    drc_n=int(re.search(r"Found (\d+)", text).group(1))
    pairs=Counter()
    for b in re.split(r"\[shorting_items\]:", text)[1:]:
        m=re.search(r"nets ([^\s]+) and ([^\s\)]+)", b.split("\n[")[0])
        if m: pairs[tuple(sorted(m.groups()))]+=1
    POWER=[("GND","VBUS"),("GND","VBAT"),("GND","VBUS_POGO"),("3V3","GND"),("3V3_DISP","GND"),
           ("GND","SW"),("3V3","3V3_DISP"),("GND","VSYS")]
    power={f"{a}|{b}": pairs.get(tuple(sorted([a,b])),0) for a,b in POWER}
    return drc_n, short, power, pairs

def try_phase(name, code, max_short=None, allow_eq=True):
    snap=ROOT/"backups/_topo_snap.kicad_pcb"
    shutil.copy2(PCB, snap)
    r=subprocess.run([sys.executable,"-c",code], cwd=str(ROOT), capture_output=True, text=True)
    print(f"--- {name} --- {r.stdout.strip()[:160]}")
    if r.returncode!=0:
        print("FAIL", (r.stderr or "")[-400:]); shutil.copy2(snap, PCB); return False, None
    fill()
    drc_n, short, power, pairs = drc()
    power_ok=all(v==0 for v in power.values())
    latent=pairs.get(("GND","VSYS"),0)>0
    print(f"  short={short} power_ok={power_ok} latent={latent} top={pairs.most_common(8)}")
    keep = power_ok and not latent
    if max_short is not None:
        keep = keep and (short <= max_short if allow_eq else short < max_short)
    if not keep:
        shutil.copy2(snap, PCB); print("  REVERT"); return False, short
    print("  KEEP"); return True, short

def main():
    base = drc()[1]
    print("BASE", base, drc()[2])

    # 1) C_PMID closer to C_VINLS (east cluster, ~2mm from U2 A3/C4)
    #    (113.50, 105.90) rot90: pad1 PMID ~113.50,106.38 near C_VINLS pad1 112.80,106.28
    ok,_=try_phase("cpmid_place", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
for fp in board.GetFootprints():
    if fp.GetReference()=="C_PMID":
        fp.SetPosition(pcbnew.VECTOR2I(mm(113.50),mm(105.90)))
        fp.SetOrientationDegrees(90)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("C_PMID->113.50,105.90 rot90")
''', max_short=base+3)

    # 2) Fat PMID island + hop to C_VINLS/C_PMID + 2-via B.Cu to A3
    #    Separate del/reb processes
    ok,_=try_phase("pmid_del", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMID": continue
    board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del",n)
''', max_short=base+5)

    ok,_=try_phase("pmid_fat", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("PMID").GetNetCode()
F,B=pcbnew.F_Cu,pcbnew.B_Cu
W=0.50; Ws=0.40
def add(layer,x1,y1,x2,y2,w):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc); board.Add(t)
def via(x,y):
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(0.30)); v.SetWidth(mm(0.60))
    v.SetNetCode(nc); board.Add(v)
# U2 PMID stitch — stop west of VSYS B5 @111.80
add(F, 111.000,105.200, 111.000,105.600, Ws)   # A3-B3
add(F, 111.000,105.600, 111.400,105.600, Ws)   # B3-B4 (ends at B4)
add(F, 111.400,105.600, 111.400,106.000, Ws)   # B4-C4
# Short hop C_VINLS pad1 (112.80,106.28) <-> C_PMID pad1 (~113.50,106.38)
add(F, 112.800,106.280, 113.500,106.380, W)
# Two vias near A3 and near C_VINLS for layer change (battery/PMID feed)
via(111.000, 104.900)
via(112.800, 106.280)
via(111.200, 104.900)  # second via near A3 for current
# B.Cu fat link
add(B, 111.000,104.900, 112.800,104.900, W)
add(B, 112.800,104.900, 112.800,106.280, W)
# F stub A3 to via
add(F, 111.000,105.200, 111.000,104.900, Ws)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("pmid_fat W=0.50")
''', max_short=base+8)  # allow temporary rise for topology restore

    # 3) VBUS spine west of x=110, width 0.50
    ok,_=try_phase("vbus_del", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBUS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    # east spine @110.6
    if abs(sx-110.6)<0.05 and abs(ex-110.6)<0.05 and max(sy,ey)>=102.9: hit=True
    if abs(sy-102.9)<0.05 and abs(ey-102.9)<0.05 and max(sx,ex)>=110.5: hit=True
    # old mid segments we will rebuild fat
    if abs(sy-103.85)<0.05 and abs(ey-103.85)<0.05 and min(sx,ex)<=105.8: hit=True
    if abs(sx-108.12)<0.05 and abs(ex-108.12)<0.05 and min(sy,ey)>=103.7 and max(sy,ey)<=104.55: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del",n)
''', max_short=base+8)

    ok,_=try_phase("vbus_west_fat", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBUS").GetNetCode(); F=pcbnew.F_Cu
W=0.50
# South jog around R_VSYS, then west spine @109.80 into A2
for x1,y1,x2,y2,w in [
    (105.700,104.500, 105.700,103.700, W),
    (105.700,103.700, 108.120,103.700, W),
    (108.120,103.700, 108.120,102.900, W),
    (108.120,102.900, 109.800,102.900, W),
    (109.800,102.900, 109.800,105.200, W),
    (109.800,105.200, 110.600,105.200, W),  # into U2.A2
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vbus west W=0.50")
''', max_short=base+8)

    # 4) Widen VSYS B5 column to 0.45 (edit existing)
    ok,_=try_phase("vsys_widen", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # B5 vertical
    if abs(sx-111.80)<0.05 and abs(ex-111.80)<0.05 and max(sy,ey)>=105.0:
        t.SetWidth(mm(0.45)); n+=1
    # C_SYS to B5
    if abs(sy-104.48)<0.05 and abs(ey-104.48)<0.05 and min(sx,ex)>=111.7:
        t.SetWidth(mm(0.45)); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("widen",n)
''', max_short=base+8)

    # 5) ISET signal reconnect (0.18) — west of power
    ok,_=try_phase("iset", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("ISET").GetNetCode(); F=pcbnew.F_Cu
# R_ISET@109.2 pad2@109.71 — keep clear of VBUS@109.80
for x1,y1,x2,y2,w in [
    (110.200,106.000, 109.500,106.000, 0.18),
    (109.500,106.000, 109.500,103.500, 0.18),
    (109.500,103.500, 109.710,103.500, 0.18),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("iset")
''', max_short=base+8)

    # 6) R_IPRETERM closer to D1 but clear of power — currently NE; move to (109.0, 107.8) south-west?
    # Keep current east placement if already clear; only nudge if GND short remains
    # Optional: fatten IPRETERM B.Cu slightly stays signal

    drc_n, short, power, pairs = drc()
    print("FINAL", json.dumps({
        "shorting": short, "drc": drc_n, "power": power,
        "top": [f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(12)],
        "I_peak_A": 0.5,
        "widths_mm": {"VBUS_VBAT_PMID": W_FAT, "VSYS": W_PWR, "Signal": W_SIG},
    }, indent=2))
    (ROOT/"reports/_shorts_passl_topo.json").write_text(json.dumps({
        "shorting": short, "drc": drc_n, "power": power,
        "top": [f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(15)],
        "I_peak_A": 0.5,
        "widths_mm": {"VBUS_VBAT_PMID": W_FAT, "VSYS": W_PWR, "Signal": W_SIG},
    }, indent=2))
    shutil.copy2(ROOT/"reports/_drc_inc.txt", ROOT/"reports/drc_shorts_passl_topo.txt")
    shutil.copy2(PCB, ROOT/f"backups/passl_topo_s{short}.kicad_pcb")
    shutil.copy2(PCB, ROOT/f"e-ink-watch-backups/passl_topo_s{short}.kicad_pcb")

if __name__=="__main__":
    main()
