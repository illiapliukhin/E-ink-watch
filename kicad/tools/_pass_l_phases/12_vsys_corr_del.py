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
    if abs(sy-102.95)<0.05 and abs(ey-102.95)<0.05 and max(sx,ex)>=117.0: hit=True
    if abs(sy-102.95)<0.05 and abs(ey-102.95)<0.05 and max(sx,ex)<=112.0 and min(sx,ex)>=111.4: hit=True
    if abs(sx-117.412)<0.02 and abs(ex-117.412)<0.02 and min(sy,ey)<=103.0: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vsys_corr_del",n)
