#!/usr/bin/env python3
"""Run a named jfix script with snap/DRC/guard/revert. Always zone-fills before DRC."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE = int(sys.argv[2]) if len(sys.argv)>2 else 21
SCRIPT = ROOT / "tools" / "_jfixes" / f"{FIX}.py"
assert SCRIPT.exists(), SCRIPT

snap = ROOT / f"backups/_try_{FIX}.kicad_pcb"
shutil.copy2(PCB, snap)

r = subprocess.run([sys.executable, str(SCRIPT)], cwd=str(ROOT), capture_output=True, text=True)
print("mut:", r.stdout.strip(), (r.stderr[-400:] if r.returncode else ""))
if r.returncode != 0:
    shutil.copy2(snap, PCB); print("FAIL mut"); sys.exit(2)

# zone fill
fill = subprocess.run([sys.executable, "-c",
    'import pcbnew; b=pcbnew.LoadBoard("e-ink-watch.kicad_pcb"); '
    'pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard("e-ink-watch.kicad_pcb", b); print("ok")'],
    cwd=str(ROOT), capture_output=True, text=True)
print("fill:", fill.stdout.strip(), fill.returncode)
if fill.returncode!=0:
    print(fill.stderr[-400:]); shutil.copy2(snap, PCB); sys.exit(3)

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

# via check in isolated process
via_r = subprocess.run([sys.executable, "-c",
    'import pcbnew\n'
    'b=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")\n'
    'via=False\n'
    'for t in b.Tracks():\n'
    '  if t.GetClass()=="PCB_VIA" and t.GetNetname()=="GND":\n'
    '    x,y=t.GetPosition().x/1e6,t.GetPosition().y/1e6\n'
    '    if abs(x-111.31)<0.02 and abs(y-102.9)<0.02: via=True\n'
    'print("1" if via else "0")\n'],
    cwd=str(ROOT), capture_output=True, text=True)
via_present = via_r.stdout.strip()=="1"

power_ok = all(v==0 for v in power.values())
keep = power_ok and short < BASE and not latent and via_present
top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(14)]
print(json.dumps({"fix":FIX,"drc":drc_n,"shorting":short,"base":BASE,"power_ok":power_ok,
                  "latent_gnd_vsys":latent,"via_present":via_present,"keep":keep,"top":top,"power":power}, indent=0))
if not keep:
    shutil.copy2(snap, PCB)
    print("REVERTED")
    sys.exit(2)
print("KEEP")
