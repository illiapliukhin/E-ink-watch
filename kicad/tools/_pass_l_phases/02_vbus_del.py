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
    if abs(sy-102.9)<0.05 and abs(ey-102.9)<0.05 and min(sx,ex)<=108.2 and max(sx,ex)>=110.5: hit=True
    if abs(sx-110.6)<0.05 and abs(ex-110.6)<0.05 and min(sy,ey)<=105.15 and max(sy,ey)>=102.95: hit=True
    if abs(sy-104.5)<0.05 and abs(ey-104.5)<0.05 and min(sx,ex)<=105.8 and max(sx,ex)>=108.0 and tomm(t.GetWidth())>=0.30: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vbus_del",n)
