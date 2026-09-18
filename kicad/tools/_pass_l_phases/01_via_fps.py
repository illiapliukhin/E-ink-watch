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
        t.SetPosition(pcbnew.VECTOR2I(mm(112.20),mm(102.20))); n+=1
for ref,nx,ny in [("C_PMID",111.30,103.70),("R_IPRETERM",113.20,103.10)]:
    for fp in board.GetFootprints():
        if fp.GetReference()==ref:
            fp.SetPosition(pcbnew.VECTOR2I(mm(nx),mm(ny)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("via",n,"fps_ok")
