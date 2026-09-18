import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-106.32)<0.05 and abs(ey-106.32)<0.05 and min(sx,ex)<=112.85 and max(sx,ex)>=112.95: hit=True
    if abs(sx-113.0)<0.05 and abs(ex-113.0)<0.05 and min(sy,ey)<=106.05 and max(sy,ey)>=106.25: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("disp_stub_del",n)
