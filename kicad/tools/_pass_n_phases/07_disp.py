import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(u): return u/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayerName()!="F.Cu": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    w=tomm(t.GetWidth())
    if abs(sy-106.0)<0.05 and abs(ey-106.0)<0.05 and min(sx,ex)<=111.85 and w>=0.40:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("trim fat 3V3_DISP", n)
