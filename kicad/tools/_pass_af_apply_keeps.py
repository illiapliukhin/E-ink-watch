#!/usr/bin/env python3
"""Replay Pass-AF KEEP edits onto Pass-AE / session-base board."""
import re
import sys
import uuid
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_af_sexpr_lib import add_segment, add_via, load, netnum, save


def uniquify_uuids(text):
    seen = set()
    replaced = [0]

    def replacer(match):
        value = match.group(1)
        if value not in seen:
            seen.add(value)
            return match.group(0)
        replaced[0] += 1
        return f'(uuid "{uuid.uuid4()}")'

    text = re.sub(r'\(uuid "([0-9a-fA-F-]+)"\)', replacer, text)
    return text, replaced[0]


text = load()
text, uuid_replaced = uniquify_uuids(text)
ground_net = netnum(text, "GND")

# SW3: B.Cu wrap via 117.2,108 to via 113.7,110 south of BTN3/LSCTRL.
text = add_segment(text, 117.2, 108.0, 117.2, 111.0, 0.2, "B.Cu", ground_net)
text = add_segment(text, 117.2, 111.0, 113.7, 111.0, 0.2, "B.Cu", ground_net)
text = add_segment(text, 113.7, 111.0, 113.7, 110.0, 0.2, "B.Cu", ground_net)

# SW2 pad 2 @(116.2,111) to GND via @(113.7,110).
text = add_segment(text, 116.2, 111.0, 113.7, 110.0, 0.25, "F.Cu", ground_net)

# J_STRAP_R pad 2: exit +X between pad 1 (3V3_DISP) and pad 3 (EPD_MOSI), B.Cu to via 114.65,97.8.
text = add_segment(text, 116.85, 98.75, 118.4, 98.75, 0.15, "F.Cu", ground_net)
text = add_via(text, 118.4, 98.75, 0.4, 0.2, ground_net)
text = add_segment(text, 118.4, 98.75, 118.4, 99.9, 0.2, "B.Cu", ground_net)
text = add_segment(text, 118.4, 99.9, 114.65, 99.9, 0.2, "B.Cu", ground_net)
text = add_segment(text, 114.65, 99.9, 114.65, 97.8, 0.2, "B.Cu", ground_net)

save(text)
dup_groups = sum(1 for count in Counter(re.findall(r'\(uuid "([^"]+)"\)', text)).values() if count > 1)
print(f"Pass-AF keeps applied uuid_replaced={uuid_replaced} dup_groups={dup_groups}")
if dup_groups:
    raise SystemExit("duplicate UUIDs remain")
