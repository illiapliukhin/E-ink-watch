import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-105.6)<0.05 and abs(ey-105.6)<0.05 and min(sx,ex)<=111.45 and max(sx,ex)>=111.75: hit=True
    if abs(sx-111.4)<0.05 and abs(ex-111.4)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=105.95: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vsys_stub_del",n)
