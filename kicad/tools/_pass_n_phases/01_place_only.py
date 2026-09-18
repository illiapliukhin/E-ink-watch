import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
for fp in board.GetFootprints():
    r=fp.GetReference()
    if r=="R_ILIM":
        fp.SetPosition(pcbnew.VECTOR2I(mm(114.20), mm(105.70)))
    elif r=="C_PMID":
        fp.SetPosition(pcbnew.VECTOR2I(mm(114.00), mm(106.55)))
    elif r=="R_IPRETERM":
        fp.SetPosition(pcbnew.VECTOR2I(mm(114.80), mm(102.90)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("place-only R_ILIM@114.20,105.70 C_PMID@114.00,106.55")
