import pcbnew, subprocess, re, shutil, json
from collections import Counter
from pathlib import Path

ROOT = Path('/workspace/e-ink-watch-kicad')
PCB = ROOT / 'e-ink-watch.kicad_pcb'

def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))

def refill_save():
    b=pcbnew.LoadBoard(str(PCB))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)

def drc(out_name='_drc_inc.txt'):
    refill_save()
    out = ROOT/'reports'/out_name
    subprocess.check_call(['kicad-cli','pcb','drc','--format','report','--output',str(out),str(PCB)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text=out.read_text()
    n=int(re.search(r'Found (\d+)', text).group(1))
    s=text.count('[shorting_items]')
    pairs=Counter()
    for blk in re.split(r'\[shorting_items\]:', text)[1:]:
        m=re.search(r'nets ([^\s]+) and ([^\s\)]+)', blk.split('\n[')[0])
        if m: pairs[tuple(sorted(m.groups()))]+=1
    POWER=[("GND","VBUS"),("GND","VBAT"),("GND","VBUS_POGO"),("3V3","GND"),("3V3_DISP","GND"),("GND","SW"),("3V3","3V3_DISP"),("GND","VSYS")]
    power={f'{a}|{b}': pairs.get(tuple(sorted([a,b])),0) for a,b in POWER}
    b=pcbnew.LoadBoard(str(PCB))
    via=any(t.GetClass()=='PCB_VIA' and t.GetNetname()=='GND'
            and abs(tomm(t.GetPosition().x)-111.31)<0.02
            and abs(tomm(t.GetPosition().y)-102.9)<0.02 for t in b.GetTracks())
    return n,s,power,pairs,via

def report(tag, base):
    n,s,power,pairs,via = drc()
    latent = pairs.get(('GND','VSYS'),0)>0
    keep = all(v==0 for v in power.values()) and s < base and via and not latent
    print(json.dumps({'tag':tag,'drc':n,'short':s,'base':base,'keep':keep,'power':power,
                      'via':via,'latent':latent,'top':pairs.most_common(14)}, indent=0))
    return keep, s
