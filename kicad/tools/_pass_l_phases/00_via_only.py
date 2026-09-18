
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
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("via_only",n)
