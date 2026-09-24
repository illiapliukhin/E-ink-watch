#!/usr/bin/env python3
"""Send U2 pocket images + corrections to gpt-6-sol. Key from env, never logged."""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

API = "https://api.experientiallabs.ai/v1/chat/completions"
VIEWS = Path("reports/sol_views")


def b64_png(path: Path) -> str:
    data = path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def image_part(path: Path, caption: str) -> list[dict]:
    return [
        {"type": "text", "text": caption},
        {
            "type": "image_url",
            "image_url": {"url": b64_png(path), "detail": "high"},
        },
    ]


def main():
    key = os.environ.get("EXPLABS_API_KEY") or Path("/tmp/.explabs_key").read_text().strip()
    if not key.startswith("xpl_"):
        sys.exit("missing EXPLABS_API_KEY")

    system = (
        "You are a senior KiCad 9 PCB layout engineer reviewing a real Ø40 mm 4-layer board. "
        "You MUST read the attached images before proposing coordinates. "
        "If a previous idea conflicts with copper visible in the images, discard it. "
        "Coordinates in millimetres, orthogonal tracks only. "
        "KiCad 0402 rotation 90 is CLOCKWISE: pad1 at (x, y+0.51), pad2 at (x, y-0.51). "
        "Through vias only, layers F.Cu–B.Cu, drill ≥0.15, size ≥0.25 unless a scan shows no overlap. "
        "In1.Cu is a solid GND plane. In2.Cu is a solid 3V3 plane. NEVER route signals on In1/In2. "
        "Do not delete copper as a first step. Hard gate: no copper overlap (shorting_items=0). "
        "Do not move U2. Do not apply VBUS on the dock. FH12 GND exits +X. "
        "Reply in Russian. Give 3 named, mutually different floorplan+routing variants, "
        "then ONE first combined KEEP (single save, in-place only) that clears ILIM↔PMID, "
        "CD through E-row, and R_SCL pad1 on SDA together."
    )

    text = """CORRECTIONS — your last proposal was checked on the real board (images attached). Do not repeat these.

WRONG 1: TS via (108.00, 105.65) size 0.35.
WHY: VBAT F vertical sits at x=108.12 w=0.35 (y=105.60–105.80) and VBAT F horizontal y=105.60 w=0.28 from x=108.12 to B1. ISET B.Cu vertical is at x=108.20 w=0.15. Your via overlaps all three (edges −0.23 / −0.19 / −0.05).
WHAT WE DID: in-place KEEP ts_via_corner — existing via moved to the TS B.Cu elbow (107.8, 105.65) size 0.25/0.15. DRC shorting=0, unc 10→11. Green ring on the F.Cu map. F stubs at x=110.4 y=105.65–106.0 still overlap VBAT and run through C2 ILIM.

WRONG 2: CD/SDA hauls on In1.Cu / In2.Cu.
WHY: this stackup is F / In1(GND plane) / In2(3V3 plane) / B. A signal via to In1 shorts to GND; to In2 shorts to 3V3. Use only F.Cu and B.Cu for CD, SDA, SCL, TS, ILIM.

WRONG 3: C2/C3 filled microvia 0.20/0.10.
WHY: every via on this board is through F–B. No HDI. Do not propose via-in-pad on the DSBGA.

WRONG 4: ILIM park (109.65, 106.30) with one F segment C2→park.
WHY: pad-clear, but the diagonal from C2 (110.6, 106.0) clips C1 ISET. Also IPRETERM vias (110.05, 106.40) 0.5 and (109.45, 106.70) 0.45 are tight (edge +0.012).

WRONG 5: moving ILIM via alone to (110.75, 105.80) 0.20.
WHY: geometry vs PMID/VBAT is clear, file length unchanged, but DRC still reported CD↔3V3 (R_SCL pad2) and CD↔SCL (E-row through E5). Latent CD/SDA/SCL overlaps get promoted. Next KEEP must change ILIM + CD E-row + R_SCL in ONE save, in-place, no new copper.

WRONG 6: east R_SCL cluster near (115.6, 109.5) without checking SW2.
WHY: SW2 B3U-1000P is at (114.5, 111). Body ~3.3×2.5 mm. Image 3 shows it south-east of the BGA.

CURRENT STATE (match the images):
U2 BQ25120A DSBGA-25 P0.4 mm at (111, 106), pads Ø0.23. KEEP ISET via (108.55, 106.0) 0.35/0.15. KEEP TS via (107.8, 105.65) 0.25/0.15.
ILIM via still (111.45, 105.8) 0.5 on PMID F w=0.4 at x=111.4 (B4/C4). ILIM F (110.6, 106.0)–(111.45, 105.8) also overlaps C3.
CD F y=106.8 from E2 (110.6, 106.8) through E3/E4/E5 to x=112.8; vertical x=112.8 y=106.8–108.26.
R_SCL (112.0, 107.8) rot 0, pad1 SCL (111.49, 107.8) on SDA F x=111.4; pad2 3V3 (112.51, 107.8).
R_SDA (111.5, 109.0) 0; R_CD (113.5, 107.75) 90; C_LDO (113.5, 106.8) 90; R_LSCTRL (114.6, 108.25) 90; R_ILIM (115.6, 106.6) 0; R_TS (108.0, 107.0) 0.
3V3 via (112.16, 107.60) 0.6; CD via (113.30, 108.41) 0.6; LSCTRL via (110.80, 107.80) 0.35.
TS F stubs still (110.4, 105.65)–(110.4, 106.0)–(111.0, 106.0). C3 also has (111.0, 106.0)–(111.0, 106.12).

TASK after looking at all four images:
Propose 3 DISTINCT variants (different 0402 cluster locations). For each: new (at x y rot) of moved 0402s; via at/size on existing copper if possible; orthogonal F/B stubs with coordinates; which latent each stub is meant to clear; main risk vs SW2 / 3V3 via / CD via / LSCTRL via / VBAT x=108.12.
Then pick ONE combined first KEEP for a single in-place save: ILIM via slide + CD E-row retract + R_SCL move/rotate (pad1 at +Y if rot=90). No added segments. List exact set_via_at / set_seg_ends / set_fp_at numbers.
If a coordinate is hidden on an image, say so and do not invent a via on unknown copper.
"""

    content: list[dict] = [{"type": "text", "text": text}]
    content.extend(
        image_part(
            VIEWS / "u2_pocket_fcu_annotated.png",
            "IMAGE 1 — annotated F.Cu, mm grid 0.4 (BGA pitch). Red boxes = latents. Green ring = KEEP TS via (107.8, 105.65). Colors: magenta PMID, yellow ILIM, cyan TS, pink CD, blue SCL, green SDA, red 3V3, orange 3V3_DISP.",
        )
    )
    content.extend(
        image_part(
            VIEWS / "u2_pocket_bcu_annotated.png",
            "IMAGE 2 — annotated B.Cu, same window. F.Cu ghosted. TS L-shape, ILIM y=105.80, ISET x=108.20. Through vias punch In1 GND and In2 3V3.",
        )
    )
    content.extend(
        image_part(
            VIEWS / "u2_3d_close.png",
            "IMAGE 3 — KiCad 3D top, zoom on U2. 5×5 DSBGA is the yellow/grey ball grid. SW2 is the large grey rectangle lower-right. Read real silk: R_TS, R_SDA, C_BAT, NTC.",
        )
    )
    content.extend(
        image_part(
            VIEWS / "board_3d_top.png",
            "IMAGE 4 — KiCad 3D wider top. U2 is the dense 5×5 on the right. U1 nRF is the large QFN upper-right. Do not route through U1 or the debug pogo on the left.",
        )
    )

    payload = {
        "model": "gpt-6-sol",
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    }
    req = urllib.request.Request(
        API,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        body = json.loads(resp.read().decode())
    Path("/tmp/sol_vision_raw.json").write_text(json.dumps({k: body[k] for k in body if k != "choices"}, indent=2)[:2000])
    if "error" in body:
        print("ERROR", body["error"])
        sys.exit(1)
    msg = body["choices"][0]["message"]["content"]
    Path("/tmp/sol_vision_variants.md").write_text(msg)
    Path("reports/PASS_AG_SOL_VISION.md").write_text(
        "# gpt-6-sol after images + corrections\n\n"
        "Images: `reports/sol_views/u2_pocket_fcu_annotated.png`, "
        "`u2_pocket_bcu_annotated.png`, `u2_3d_close.png`, `board_3d_top.png`.\n\n"
        + msg
    )
    print("model", body.get("model"))
    print("usage", body.get("usage"))
    print("content_len", len(msg))
    print(msg)


if __name__ == "__main__":
    main()
