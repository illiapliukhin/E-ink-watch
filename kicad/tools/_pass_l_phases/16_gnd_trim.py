import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="GND" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-112.8)<0.05 and abs(ex-112.8)<0.05 and min(sy,ey)>=105.30 and max(sy,ey)<=105.45:
        board.Remove(t); n+=1
    elif abs(sx-112.8)<0.05 and abs(sy-105.4)<0.05 and abs(ex-sx)<0.01 and abs(ey-sy)<0.01:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("gnd_trim",n)
