import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(u): return u/1e6
n=0
# Only remove ILIM + IPRETERM copper (stale at old Y) and old PMID F approach at y~103.85
# Do NOT touch PMID stitch or other nets (avoid 3V3_DISP/GND collateral from zone weirdness)
for t in list(board.GetTracks()):
    net=t.GetNetname()
    if net == "ILIM":
        board.Remove(t); n+=1
        continue
    if net == "IPRETERM":
        board.Remove(t); n+=1
        continue
    if net != "PMID":
        continue
    if t.Type()==pcbnew.PCB_VIA_T:
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        # old pocket vias near y=104.35 only
        if 110.7<=x<=111.6 and 104.1<=y<=104.6:
            board.Remove(t); n+=1
        continue
    if t.GetLayerName()!="F.Cu":
        continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # keep U2 A3-B3-B4-C4 stitch
    is_stitch=False
    if abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and min(sy,ey)>=105.15 and max(sy,ey)<=105.65:
        is_stitch=True
    if abs(sy-105.6)<0.05 and abs(ey-105.6)<0.05 and min(sx,ex)>=110.95 and max(sx,ex)<=111.45:
        is_stitch=True
    if abs(sx-111.4)<0.05 and abs(ex-111.4)<0.05 and min(sy,ey)>=105.55 and max(sy,ey)<=106.05:
        is_stitch=True
    # old C_PMID approach at y~103.85 or stub down from A3 to 104.35
    is_old=False
    if abs(sy-103.85)<0.1 and abs(ey-103.85)<0.1:
        is_old=True
    if abs(sx-111.0)<0.05 and abs(ex-111.0)<0.05 and max(sy,ey)<=105.25 and min(sy,ey)<=104.40:
        is_old=True
    if is_old and not is_stitch:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("deleted selective",n)
