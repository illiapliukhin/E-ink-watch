#!/usr/bin/env python3
"""
Parametric 3D case for E Ink wristwatch (CadQuery).
Coordinate system (case): +Z = display face up; +X = 3 o'clock (STRAP_R);
+Y = 12 o'clock (DISP_MAIN). KiCad PCB dy is flipped: case_y = -kicad_dy.
Charging+SWD: rear 2x3 sealed pogo cradle (elastomer-over-pads, NOT USB-C). IP67 design intent.
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
from cadquery import exporters

# =============================================================================
# PARAMETRIC VARIABLES
# =============================================================================

# Outer envelope
CASE_OD = 43.0          # mm — bezel around Ø40 PCB
CASE_ID_CLEAR = 0.15    # radial clearance PCB pocket
PCB_DIA = 40.0
PCB_POCKET_DIA = PCB_DIA + 2 * CASE_ID_CLEAR  # 40.3

# Thickness / stack (Z from bottom outer face upward)
BOTTOM_WALL = 1.4
BATTERY_CAVITY_H = 3.6      # P0: was 3.2; +0.4 so tray (BAT_Z+BAT_FOAM=3.4) clears PCB shelf
# ASSUMED LiPo pouch ~3.0 mm (80–200 mAh class); foam BAT_FOAM=0.4 — measure OEM before tooling
PCB_THICK = 0.8
COMP_HEADROOM = 3.2         # components under PCB toward back cavity
GASKET_H = 0.5
GLASS_RECESS_H = 1.3        # bounding box glass+FPC stiffener
BEZEL_LIP_H = 0.9           # aperture lip above glass
TOP_RIM_H = 0.6

# Derived Z stations (bottom outer = 0)
Z_BOTTOM_OUTER = 0.0
Z_BATTERY_FLOOR = BOTTOM_WALL
Z_PCB_BOTTOM = Z_BATTERY_FLOOR + BATTERY_CAVITY_H          # 5.0 @ cavity 3.6
Z_PCB_TOP = Z_PCB_BOTTOM + PCB_THICK                      # 5.8
Z_GASKET_TOP = Z_PCB_TOP + GASKET_H                       # 6.3
Z_GLASS_TOP = Z_GASKET_TOP + GLASS_RECESS_H               # 7.2
Z_BEZEL_TOP = Z_GLASS_TOP + BEZEL_LIP_H + TOP_RIM_H       # 8.7 — tight; bump cavity

# Recalculate for ~11 mm target with component headroom sharing battery cavity:
# Components sit in same cavity as battery (beside pouch), so no extra COMP stack.
OVERALL_H = Z_BEZEL_TOP  # ~8.7; raise slightly for printability / gasket
# Add mid-ring height for screw flange / split plane
SPLIT_Z = Z_PCB_TOP + 0.2   # top/bottom split just above PCB top shelf
# Extend top bezel so overall ~11 mm
OVERALL_H = 11.0
Z_BEZEL_TOP = OVERALL_H
# Redistribute: keep bottom stack, stretch glass/bezel zone
# Z_PCB_TOP=5.8; SPLIT_Z=6.0; gasket+glass+bezel fill to 11.0

LUG_STRAP_W = 20.0          # strap width parameter (18/20/22)
LUG_GAP = LUG_STRAP_W + 0.4
LUG_LENGTH = 6.5            # radial protrusion of lug body
LUG_THICK = 3.2
LUG_PIN_D = 1.6             # spring-bar hole
LUG_PIN_Y_OFFSET = 0.0

# Display aperture (1.54" active ~27.6 mm class)
DISP_ACTIVE = 27.6
DISP_APERTURE = DISP_ACTIVE + 0.4   # light clearance
DISP_LIP_W = 1.2                    # inward lip under glass
GLASS_POCKET = DISP_ACTIVE + 2.4    # glass bounding box ~30 mm

# FPC channels toward lugs (3 & 9 o'clock)
FPC_H = 0.5               # P0 optional: was 0.4; slight headroom for ZIF+flex
FPC_W = 10.0
FPC_LEN = 8.0               # radial channel length through wall

# Side buttons — KiCad offsets (dx, dy) → case (x, -dy)
# SW1 (9.2, 12.0), SW2 (12.0, 9.0), SW3 (13.5, 5.5) KiCad
SW_KICAD = [(9.2, 12.0), (12.0, 9.0), (13.5, 5.5)]
SW_CASE = [(x, -y) for x, y in SW_KICAD]  # +Y = 12 o'clock
BTN_TUNNEL_D = 3.2
BTN_ACTUATOR_D = 2.4
BTN_CAP_H = 3.5
BTN_Z = SPLIT_Z             # P0: straddle split so tunnels cut top+bottom; switches ~Z_PCB_TOP

# Battery pouch cavity ~3×20×25 mm class
BAT_X, BAT_Y, BAT_Z = 20.0, 25.0, 3.0
BAT_FOAM = 0.4

# Combined charge + SWD pogo cradle on rear (NOT USB-C)
# Matrix nets (PCB B.Cu pads must match): VCHG, GND, SWDIO, SWDCLK, nRESET, [OPT]
POGO_COUNT = 6              # 5 required + 1 optional (3V3_sense / ID / NC)
POGO_COLS = 3
POGO_ROWS = 2
POGO_PITCH = 3.0            # mm — FDM-friendly; cradle±0.2 mm align budget
POGO_HOLE_D = 2.0           # through-hole clearance for pogo tip (~Ø1.0–1.5)
POGO_PAD_RECESS_D = 2.8     # per-pad counterbore from outside
POGO_RECESS_DEPTH = 0.5
# Window center toward J_BAT (0,-15.8) and J_SWD (-11,-11.5) case coords
POGO_ORIGIN_X = -4.0
POGO_ORIGIN_Y = -12.5
POGO_ALIGN_TOL = 0.2        # mm cradle↔case↔PCB pad stack-up target
POGO_WINDOW_MARGIN = 1.5    # extra recess around matrix
POGO_WINDOW_DEPTH = 0.8
POGO_KEY_SLOT = True        # asymmetric key at -X side of window
POGO_CHANNEL_W = 12.0
POGO_CHANNEL_H = 1.4
POGO_NETS = ("VCHG", "GND", "SWDIO", "SWDCLK", "nRESET", "OPT")

# =============================================================================
# IP67 design-intent sealing (NOT lab-certified until tested)
# Target: dust tight + immersion 1 m / 30 min (IEC 60529 IP67)
# =============================================================================
IP_TARGET = "IP67"
IP_CERTIFIED = False          # design intent only — requires lab test
SEAL_SPLIT_ENABLE = True
SEAL_CORD_D = 1.0             # silicone cord Ø1.0 at case split
SEAL_GROOVE_W = 0.95          # groove width (thin OD land; Ø1.0 cord)
SEAL_GROOVE_D = 0.65          # groove depth in bottom face at SPLIT_Z
SEAL_GROOVE_R = 20.70         # mean radius on split land (cavity≈19.95 .. OD/2=21.5)
# Prefer sealed pogo: elastomer sheet over B.Cu pads (cradle compresses)
# Alternate: per-pin gland (POGO_SEAL_MODE = "gland")
POGO_SEAL_MODE = "elastomer"  # "elastomer" | "gland"
POGO_SEAL_SHEET_T = 0.8       # elastomer over-pad sheet thickness (uncompressed)
POGO_SEAL_POCKET_D = 0.55     # pocket depth in back for sheet (compression ~25–35%)
POGO_SEAL_MARGIN = 1.8        # sheet overhang beyond matrix envelope
POGO_GLAND_OD = 3.2           # per-pin gland seat OD (if mode=gland)
POGO_GLAND_ID = 1.4           # tip clearance through gland
POGO_GLAND_DEPTH = 0.9
# Button boots: radial elastomer membrane land (not open tunnel)
BTN_BOOT_LAND_D = 4.0         # outer land for boot flange
BTN_BOOT_GROOVE_D = 0.4       # shallow groove depth for boot bead
# Glass bond: adhesive land under bezel lip (documented; pocket already exists)
GLASS_BOND_LAND_W = 1.5       # radial bond land around aperture
GLASS_GASKET_T = 0.5          # PORON/silicone under glass (matches GASKET_H)

# Screw bosses M1.4 / M1.6
SCREW_D = 1.5               # clearance for M1.4
BOSS_OD = 4.2
BOSS_ID = 1.2               # pilot / heat-set insert M1.4
N_SCREWS = 4
SCREW_R = 17.5              # bolt circle — inside peripheral gasket; seal with O-ring under head

WALL_MIN = 0.8              # FDM ≥0.4; we use ≥0.8
CHAMFER = 0.3

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
RENDERS = ROOT / "renders"



def pogo_positions() -> list[tuple[float, float]]:
    """2×3 grid centered on POGO_ORIGIN; row0 (toward -Y/6 o'clock) = VCHG,GND,SWDIO."""
    positions: list[tuple[float, float]] = []
    x0 = POGO_ORIGIN_X - (POGO_COLS - 1) * POGO_PITCH / 2
    y0 = POGO_ORIGIN_Y - (POGO_ROWS - 1) * POGO_PITCH / 2
    for row in range(POGO_ROWS):
        for col in range(POGO_COLS):
            positions.append((x0 + col * POGO_PITCH, y0 + row * POGO_PITCH))
    return positions[:POGO_COUNT]


def _sw_angles_deg() -> list[float]:
    """Polar angle of each switch from +X (CCW), degrees."""
    out = []
    for x, y in SW_CASE:
        out.append(math.degrees(math.atan2(y, x)))
    return out


def make_lugs(od: float, z0: float, z1: float) -> cq.Workplane:
    """Two pairs of strap lugs at 12/6? No — wristwatch lugs at 12 and 6 for strap
    along 12–6 axis. Strap exits toward 12 and 6; FPC strap displays exit at 3/9
    INTO the strap. So mechanical lugs are at 12 and 6 o'clock."""
    # Actually classic watch: lugs at 12 and 6, strap runs 12↔6.
    # User said FPC exits at 9 and 3 toward strap lugs — meaning flex goes into
    # left/right strap halves. So the strap is still 12–6, and FPC routes into
    # strap near where strap attaches — OR strap is unusual left-right.
    # DESIGN_NOTES: "strain relief у ушек 3/9 часов" — lugs at 3 and 9!
    # So this watch has lugs at 3 o'clock and 9 o'clock (strap left-right on wrist
    # with crown traditionally at 3 — here buttons at lower-right).
    # FPC channels toward lugs at 3/9. Lugs at ±X.
    mid_z = 0.5 * (z0 + z1)
    h = z1 - z0
    lug_r = od / 2 + LUG_LENGTH * 0.55
    parts = []
    for side in (-1, 1):  # -X = 9 o'clock, +X = 3 o'clock
        # Two horns spanning strap width along Y
        for sign_y in (-1, 1):
            y = sign_y * (LUG_GAP / 2 + 1.0)
            lug = (
                cq.Workplane("XY")
                .transformed(offset=(side * (od / 2 + LUG_LENGTH / 2 - 0.5), y, mid_z))
                .box(LUG_LENGTH + 1.0, 2.4, min(h, LUG_THICK), centered=True)
            )
            # spring bar hole along Y through lug
            hole = (
                cq.Workplane("XZ")
                .transformed(offset=(side * (od / 2 + LUG_LENGTH * 0.55), y, mid_z))
                .circle(LUG_PIN_D / 2)
                .extrude(3.0 if sign_y < 0 else -3.0)
            )
            # Simpler: build lug block then cut pin hole along Y
            block = (
                cq.Workplane("XY")
                .center(side * (od / 2 + 2.8), y)
                .rect(LUG_LENGTH, 2.6)
                .extrude(min(h, LUG_THICK))
                .translate((0, 0, mid_z - min(h, LUG_THICK) / 2))
            )
            parts.append(block)
    solid = parts[0]
    for p in parts[1:]:
        solid = solid.union(p)
    # Pin holes through each lug pair (axis = Y)
    for side in (-1, 1):
        hx = side * (od / 2 + 2.8)
        pin = (
            cq.Workplane("XZ")
            .workplane(offset=LUG_GAP / 2 + 3)
            .center(hx, mid_z)
            .circle(LUG_PIN_D / 2)
            .extrude(-(LUG_GAP + 6))
        )
        solid = solid.cut(pin)
    return solid



def _radial_button_tunnels(body: cq.Workplane, z_center: float) -> cq.Workplane:
    """Cut radial SW1–SW3 tunnels at z_center through OD wall (both halves)."""
    r = CASE_OD / 2
    depth = 6.0
    for x, y in SW_CASE:
        ang = math.atan2(y, x)
        cx = (r - depth / 2) * math.cos(ang)
        cy = (r - depth / 2) * math.sin(ang)
        tunnel = (
            cq.Workplane("XY")
            .transformed(
                offset=(cx, cy, z_center),
                rotate=(0, 0, math.degrees(ang)),
            )
            .box(depth + 2.0, BTN_TUNNEL_D, BTN_TUNNEL_D, centered=True)
        )
        body = body.cut(tunnel)
    return body


def make_case_bottom() -> cq.Workplane:
    """Back + lower mid: battery cavity, pogo well, screw bosses, FPC half-channels."""
    od = CASE_OD
    r = od / 2
    h = SPLIT_Z

    body = cq.Workplane("XY").circle(r).extrude(h)

    # Outer slight chamfer on bottom edge
    try:
        body = body.edges("<Z").chamfer(CHAMFER)
    except Exception:
        pass

    # Internal battery + component cavity (cylindrical main)
    cavity_r = PCB_POCKET_DIA / 2 - 0.2
    body = body.faces(">Z").workplane().circle(cavity_r).cutBlind(-(h - BOTTOM_WALL))

    # Rectangular battery tray offset toward +Y (12) leaving room near pogo at -Y
    bat = (
        cq.Workplane("XY")
        .workplane(offset=Z_BATTERY_FLOOR)
        .center(0, 4.0)
        .rect(BAT_X + 0.6, BAT_Y + 0.6)
        .extrude(BAT_Z + BAT_FOAM)
    )
    body = body.cut(bat)

    # PCB seat: annular shelf at Z_PCB_BOTTOM — cut pocket for PCB from SPLIT down to shelf
    # Already cut cavity; add PCB pocket diameter through remaining to shelf depth
    # Shelf: leave ring from cavity_r to pcb pocket — deepen center under PCB for comps
    # Components headroom: cavity already BATTERY_CAVITY_H

    # Screw bosses (solid cylinders from floor up) then pilot holes
    for i in range(N_SCREWS):
        ang = math.radians(45 + i * 90)
        bx = SCREW_R * math.cos(ang)
        by = SCREW_R * math.sin(ang)
        boss = (
            cq.Workplane("XY")
            .workplane(offset=Z_BATTERY_FLOOR)
            .center(bx, by)
            .circle(BOSS_OD / 2)
            .extrude(h - BOTTOM_WALL - 0.15)
        )
        body = body.union(boss)
        # IP67: blind heat-set pilot — does NOT pierce exterior back wall
        pilot = (
            cq.Workplane("XY")
            .workplane(offset=BOTTOM_WALL - 0.05)
            .center(bx, by)
            .circle(BOSS_ID / 2)
            .extrude(h - BOTTOM_WALL + 0.3)
        )
        body = body.cut(pilot)

    # FPC exit channels at 3 and 9 — half in bottom (slot through wall)
    for side in (-1, 1):
        ch = (
            cq.Workplane("XY")
            .workplane(offset=Z_PCB_BOTTOM - FPC_H)
            .center(side * (r - FPC_LEN / 2), 0.5)  # slight +Y like KiCad 0.5
            .rect(FPC_LEN + 2.0, FPC_W)
            .extrude(FPC_H + 0.15)
        )
        body = body.cut(ch)

    # ---- Sealed charge+SWD pogo pocket (IP67 design intent) ----
    # Prefer elastomer sheet over B.Cu pads; cradle compresses seal.
    # Open through-holes alone are NOT IP67 — seal is mandatory.
    # Nets: VCHG GND SWDIO / SWDCLK nRESET OPT; SW_DBG stays internal (no case hole).
    positions = pogo_positions()
    win_w = (POGO_COLS - 1) * POGO_PITCH + POGO_PAD_RECESS_D + 2 * POGO_WINDOW_MARGIN
    win_h = (POGO_ROWS - 1) * POGO_PITCH + POGO_PAD_RECESS_D + 2 * POGO_WINDOW_MARGIN
    seal_w = win_w + 2 * POGO_SEAL_MARGIN
    seal_h = win_h + 2 * POGO_SEAL_MARGIN

    # Outer cradle window (shallow) + seal-sheet pocket (deeper land)
    window = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(POGO_ORIGIN_X, POGO_ORIGIN_Y)
        .rect(win_w, win_h)
        .extrude(min(POGO_WINDOW_DEPTH, BOTTOM_WALL - 0.55))
    )
    body = body.cut(window)
    seal_pocket = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(POGO_ORIGIN_X, POGO_ORIGIN_Y)
        .rect(seal_w, seal_h)
        .extrude(min(POGO_SEAL_POCKET_D, BOTTOM_WALL - 0.55))
    )
    body = body.cut(seal_pocket)
    if POGO_KEY_SLOT:
        # Asymmetric key notch (−X) so cradle cannot mate 180° rotated
        key = (
            cq.Workplane("XY")
            .workplane(offset=0)
            .center(POGO_ORIGIN_X - win_w / 2 - 0.6, POGO_ORIGIN_Y)
            .rect(1.6, 3.0)
            .extrude(POGO_WINDOW_DEPTH + 0.2)
        )
        body = body.cut(key)

    # Blind wells only — leave ≥0.55 mm sealed floor (NO open through-holes).
    # Electrical path: cradle pogo → conductive elastomer pills / sealed pin →
    # recessed pads (bonded/potted) → internal flex to PCB. See IP67_SEALING.md.
    max_well = BOTTOM_WALL - 0.55
    for (px, py), net in zip(positions, POGO_NETS):
        if POGO_SEAL_MODE == "gland":
            # Per-pin O-ring gland seat (blind): tip clearance stays above sealed floor
            gland = (
                cq.Workplane("XY")
                .workplane(offset=0)
                .center(px, py)
                .circle(POGO_GLAND_OD / 2)
                .extrude(min(POGO_GLAND_DEPTH + POGO_WINDOW_DEPTH, max_well))
            )
            body = body.cut(gland)
            tip = (
                cq.Workplane("XY")
                .center(px, py)
                .circle(POGO_GLAND_ID / 2)
                .extrude(min(POGO_GLAND_DEPTH + 0.2, max_well))
            )
            body = body.cut(tip)
        else:
            # Elastomer-over-pads: blind pad recess under membrane sheet
            well_d = min(POGO_RECESS_DEPTH + POGO_WINDOW_DEPTH, max_well)
            well = (
                cq.Workplane("XY")
                .workplane(offset=0)
                .center(px, py)
                .circle(POGO_PAD_RECESS_D / 2)
                .extrude(well_d)
            )
            body = body.cut(well)
        print(f"  pogo {net:7s} @ ({px:.2f}, {py:.2f}) sealed/{POGO_SEAL_MODE} blind")

    # Keepout/channel under matrix toward PCB bottom (J_BAT / J_SWD zone)
    chan = (
        cq.Workplane("XY")
        .workplane(offset=Z_BATTERY_FLOOR)
        .center(POGO_ORIGIN_X, POGO_ORIGIN_Y + 1.0)
        .rect(max(POGO_CHANNEL_W, seal_w + 1.0), seal_h + 6.0)
        .extrude(POGO_CHANNEL_H)
    )
    body = body.cut(chan)

    # Lugs attached to bottom half
    try:
        body = body.union(make_lugs(od, 1.0, h - 0.5))
    except Exception as e:
        print("lug union warn:", e)

    # Button tunnel halves (lower) — same axis as top so actuators reach PCB switches
    body = _radial_button_tunnels(body, BTN_Z)

    # Button boot flange lands (IP67): shallow annular groove at OD end of each tunnel
    if SEAL_SPLIT_ENABLE:
        r_od = CASE_OD / 2
        for x, y in SW_CASE:
            ang = math.atan2(y, x)
            # Land center near outer wall face
            lx = (r_od - 0.6) * math.cos(ang)
            ly = (r_od - 0.6) * math.sin(ang)
            boot = (
                cq.Workplane("XY")
                .transformed(
                    offset=(lx, ly, BTN_Z),
                    rotate=(0, 0, math.degrees(ang)),
                )
                .box(1.2, BTN_BOOT_LAND_D, BTN_BOOT_LAND_D, centered=True)
            )
            body = body.cut(boot)

    # Split-plane annular gasket groove (silicone cord) — IP67 primary mid-seal
    if SEAL_SPLIT_ENABLE:
        # Ring cut into mating face of bottom half (outer circle then inner = annulus)
        groove = (
            cq.Workplane("XY")
            .workplane(offset=h - SEAL_GROOVE_D)
            .circle(SEAL_GROOVE_R + SEAL_GROOVE_W / 2)
            .circle(SEAL_GROOVE_R - SEAL_GROOVE_W / 2)
            .extrude(SEAL_GROOVE_D + 0.05)
        )
        body = body.cut(groove)
        print(
            f"  split gasket groove R={SEAL_GROOVE_R} W={SEAL_GROOVE_W} "
            f"D={SEAL_GROOVE_D} cordØ={SEAL_CORD_D}"
        )

    return body


def make_case_top() -> cq.Workplane:
    """Bezel / top mid: display aperture, glass recess, button tunnels, FPC upper."""
    od = CASE_OD
    r = od / 2
    z0 = SPLIT_Z
    h = OVERALL_H - SPLIT_Z

    body = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .circle(r)
        .extrude(h)
    )

    # Inner PCB pocket continuing
    body = (
        body.faces("<Z")
        .workplane()
        .circle(PCB_POCKET_DIA / 2)
        .cutBlind(-(min(1.2, h * 0.35)))
    )

    # Glass pocket from top — ring between DISP_APERTURE and GLASS_POCKET = bond land
    glass_depth = GLASS_RECESS_H + GLASS_GASKET_T * 0.5
    body = (
        body.faces(">Z")
        .workplane()
        .rect(GLASS_POCKET, GLASS_POCKET)
        .cutBlind(-glass_depth)
    )

    # Adhesive/gasket trench around aperture (IP67 glass seal land)
    bond_outer = min(GLASS_POCKET - 0.2, DISP_APERTURE + 2 * GLASS_BOND_LAND_W)
    bond_trench = (
        cq.Workplane("XY")
        .workplane(offset=OVERALL_H - glass_depth)
        .rect(bond_outer, bond_outer)
        .rect(DISP_APERTURE + 0.25, DISP_APERTURE + 0.25)
        .extrude(0.25)
    )
    body = body.cut(bond_trench)

    # Display aperture through
    body = (
        body.faces(">Z")
        .workplane()
        .rect(DISP_APERTURE, DISP_APERTURE)
        .cutThruAll()
    )

    # Screw through holes aligned with bosses
    for i in range(N_SCREWS):
        ang = math.radians(45 + i * 90)
        bx = SCREW_R * math.cos(ang)
        by = SCREW_R * math.sin(ang)
        hole = (
            cq.Workplane("XY")
            .workplane(offset=z0 - 0.1)
            .center(bx, by)
            .circle(SCREW_D / 2)
            .extrude(h + 0.3)
        )
        body = body.cut(hole)

    # FPC channels upper half at 3/9 — through-wall at split (pairs with bottom half)
    for side in (-1, 1):
        ch2 = (
            cq.Workplane("XY")
            .workplane(offset=z0 - 0.15)
            .center(side * (r - FPC_LEN / 2), 0.5)
            .rect(FPC_LEN + 2.0, FPC_W)
            .extrude(FPC_H + 0.55)
        )
        body = body.cut(ch2)

    # Button tunnels — radial holes from OD toward center at switch angles (shared axis w/ bottom)
    body = _radial_button_tunnels(body, BTN_Z)

    # Button boot flange lands in top half (pairs with bottom)
    if SEAL_SPLIT_ENABLE:
        r_od = CASE_OD / 2
        for x, y in SW_CASE:
            ang = math.atan2(y, x)
            lx = (r_od - 0.6) * math.cos(ang)
            ly = (r_od - 0.6) * math.sin(ang)
            boot = (
                cq.Workplane("XY")
                .transformed(
                    offset=(lx, ly, BTN_Z),
                    rotate=(0, 0, math.degrees(ang)),
                )
                .box(1.2, BTN_BOOT_LAND_D, BTN_BOOT_LAND_D, centered=True)
            )
            body = body.cut(boot)

    # Outer top chamfer
    try:
        body = body.edges(">Z").chamfer(0.25)
    except Exception:
        pass

    return body


def make_button_cap() -> cq.Workplane:
    """Single printable side-button actuator stub (×3 needed)."""
    stem = (
        cq.Workplane("XY")
        .circle(BTN_ACTUATOR_D / 2 - 0.05)
        .extrude(BTN_CAP_H)
    )
    head = (
        cq.Workplane("XY")
        .workplane(offset=BTN_CAP_H)
        .circle(BTN_TUNNEL_D / 2 + 0.3)
        .extrude(1.2)
    )
    # Flange stop
    stop = (
        cq.Workplane("XY")
        .workplane(offset=BTN_CAP_H - 0.8)
        .circle(BTN_TUNNEL_D / 2 + 0.15)
        .extrude(0.5)
    )
    return stem.union(head).union(stop)


def make_assembly() -> cq.Workplane:
    bottom = make_case_bottom()
    top = make_case_top()
    # Separate in Z slightly for visual assembly STL (optional gap 0)
    return bottom.union(top)


def export_all() -> dict:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)

    print("Building case_bottom...")
    bottom = make_case_bottom()
    print("Building case_top...")
    top = make_case_top()
    print("Building button_cap...")
    cap = make_button_cap()
    print("Building assembly...")
    asm = bottom.union(top)

    paths = {}
    for name, obj in [
        ("case_bottom", bottom),
        ("case_top", top),
        ("button_cap", cap),
        ("case_assembly", asm),
    ]:
        stl = EXPORTS / f"{name}.stl"
        print(f"Export STL {stl}...")
        exporters.export(obj, str(stl))
        paths[name] = str(stl)
        # STEP
        try:
            step = EXPORTS / f"{name}.step"
            exporters.export(obj, str(step))
            paths[f"{name}_step"] = str(step)
        except Exception as e:
            print(f"STEP skip {name}: {e}")

    # Dimension SVG orthographic (simple 2D projection via DXF of top outline)
    try:
        _write_dims_svg(RENDERS / "dimensions.svg")
        paths["dims_svg"] = str(RENDERS / "dimensions.svg")
    except Exception as e:
        print("SVG dims:", e)

    # Manifest
    manifest = EXPORTS / "MANIFEST.txt"
    manifest.write_text(
        "\n".join(
            [
                f"CASE_OD={CASE_OD}",
                f"OVERALL_H={OVERALL_H}",
                f"PCB_POCKET_DIA={PCB_POCKET_DIA}",
                f"DISP_APERTURE={DISP_APERTURE}",
                f"LUG_STRAP_W={LUG_STRAP_W}",
                f"SPLIT_Z={SPLIT_Z}",
                f"BATTERY_CAVITY_H={BATTERY_CAVITY_H}",
                f"Z_PCB_BOTTOM={Z_PCB_BOTTOM}",
                f"Z_PCB_TOP={Z_PCB_TOP}",
                f"BTN_Z={BTN_Z}",
                f"POGO_COUNT={POGO_COUNT}",
                f"POGO_PITCH={POGO_PITCH}",
                f"POGO_ORIGIN=({POGO_ORIGIN_X},{POGO_ORIGIN_Y})",
                f"POGO_NETS={POGO_NETS}",
                f"POGO_ALIGN_TOL=±{POGO_ALIGN_TOL}",
                f"charging=pogo_charge+SWD_cradle (no USB-C)",
                f"IP_TARGET={IP_TARGET}",
                f"IP_CERTIFIED={IP_CERTIFIED}",
                f"POGO_SEAL_MODE={POGO_SEAL_MODE}",
                f"SEAL_CORD_D={SEAL_CORD_D} SEAL_GROOVE_R={SEAL_GROOVE_R}",
                f"POGO_SEAL_POCKET_D={POGO_SEAL_POCKET_D} POGO_SEAL_MARGIN={POGO_SEAL_MARGIN}",
                f"SW_CASE={SW_CASE}",
                f"FPC_W={FPC_W} FPC_H={FPC_H}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Pogo matrix + IP67 seal pocket notes (case coords)
    positions = pogo_positions()
    win_w = (POGO_COLS - 1) * POGO_PITCH + POGO_PAD_RECESS_D + 2 * POGO_WINDOW_MARGIN
    win_h = (POGO_ROWS - 1) * POGO_PITCH + POGO_PAD_RECESS_D + 2 * POGO_WINDOW_MARGIN
    lines = [
        "POGO MATRIX (case coords, mm) — sealed charge + SWD cradle (IP67 intent)",
        f"Origin center: ({POGO_ORIGIN_X}, {POGO_ORIGIN_Y})  pitch {POGO_PITCH}  rows={POGO_ROWS} cols={POGO_COLS}",
        f"Align tolerance: ±{POGO_ALIGN_TOL} mm",
        f"Key notch: -X side of window",
        f"Seal mode: {POGO_SEAL_MODE}  pocket depth={POGO_SEAL_POCKET_D}  margin={POGO_SEAL_MARGIN}",
        f"Seal sheet envelope: {win_w + 2*POGO_SEAL_MARGIN:.1f} x {win_h + 2*POGO_SEAL_MARGIN:.1f} mm",
        f"IP_TARGET={IP_TARGET}  IP_CERTIFIED={IP_CERTIFIED} (lab test required)",
        "",
        "Row toward 6 o'clock (y=-14):",
    ]
    for i, ((px, py), net) in enumerate(zip(positions, POGO_NETS)):
        if i == 3:
            lines.append("Row toward center (y=-11):")
        lines.append(f"  ({px:.2f},{py:.2f}) {net}")
    lines += [
        "",
        "PCB must provide matching B.Cu pads under elastomer (no vias in seal land).",
        "SW_DBG remains internal — no case opening. No USB-C.",
        f"KiCad refs nearby: J_BAT (0,-15.8), J_SWD (-11,-11.5) in case coords.",
    ]
    (EXPORTS / "POGO_MATRIX.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    seal_txt = EXPORTS / "SEAL_PARAMS.txt"
    seal_txt.write_text(
        "\n".join(
            [
                f"IP_TARGET={IP_TARGET}",
                f"IP_CERTIFIED={IP_CERTIFIED}",
                f"SEAL_CORD_D={SEAL_CORD_D}",
                f"SEAL_GROOVE_W={SEAL_GROOVE_W}",
                f"SEAL_GROOVE_D={SEAL_GROOVE_D}",
                f"SEAL_GROOVE_R={SEAL_GROOVE_R}",
                f"POGO_SEAL_MODE={POGO_SEAL_MODE}",
                f"POGO_SEAL_SHEET_T={POGO_SEAL_SHEET_T}",
                f"POGO_SEAL_POCKET_D={POGO_SEAL_POCKET_D}",
                f"POGO_SEAL_MARGIN={POGO_SEAL_MARGIN}",
                f"POGO_GLAND_OD={POGO_GLAND_OD}",
                f"POGO_GLAND_ID={POGO_GLAND_ID}",
                f"BTN_BOOT_LAND_D={BTN_BOOT_LAND_D}",
                f"GLASS_BOND_LAND_W={GLASS_BOND_LAND_W}",
                f"GLASS_GASKET_T={GLASS_GASKET_T}",
                "note=design intent IP67 — not lab-certified",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return paths


def _write_dims_svg(path: Path) -> None:
    od = CASE_OD
    s = 4.0  # scale px/mm
    w, h = int(od * s + 80), int(od * s + 140)
    cx, cy = w // 2, 50 + int(od * s / 2)
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">\n'
        '<style>text{font-family:monospace;font-size:11px;fill:#222}</style>\n'
        '<rect width="100%" height="100%" fill="#fafafa"/>\n'
        '<text x="12" y="20">E-Ink watch case — sealed pogo (IP67 intent, not certified)</text>\n'
        f'<circle cx="{cx}" cy="{cy}" r="{od/2*s}" fill="#ddd" stroke="#333" stroke-width="2"/>\n'
        f'<rect x="{cx-DISP_APERTURE/2*s}" y="{cy-DISP_APERTURE/2*s}" '
        f'width="{DISP_APERTURE*s}" height="{DISP_APERTURE*s}" fill="#e8f0ff" stroke="#246"/>\n'
    )
    win_w = (POGO_COLS - 1) * POGO_PITCH + POGO_PAD_RECESS_D + 2 * POGO_WINDOW_MARGIN
    win_h = (POGO_ROWS - 1) * POGO_PITCH + POGO_PAD_RECESS_D + 2 * POGO_WINDOW_MARGIN
    wx = cx + (POGO_ORIGIN_X - win_w / 2) * s
    wy = cy - (POGO_ORIGIN_Y + win_h / 2) * s
    svg += (
        f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{win_w*s:.1f}" height="{win_h*s:.1f}" '
        f'fill="#cfc" stroke="#060"/>\n'
        '<g stroke="#060" fill="#8c8">\n'
    )
    for (px, py), net in zip(pogo_positions(), POGO_NETS):
        sx = cx + px * s
        sy = cy - py * s
        svg += f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{POGO_PAD_RECESS_D/2*s:.1f}"/>\n'
        svg += f'<text x="{sx + 5:.1f}" y="{sy + 3:.1f}" font-size="8">{net}</text>\n'
    svg += (
        '</g>\n'
        f'<rect x="{cx + (od/2-4)*s}" y="{cy - FPC_W/2*s}" width="{4*s}" height="{FPC_W*s}" '
        f'fill="#fc6" stroke="#960"/>\n'
        f'<rect x="{cx - (od/2)*s}" y="{cy - FPC_W/2*s}" width="{4*s}" height="{FPC_W*s}" '
        f'fill="#fc6" stroke="#960"/>\n'
        f'<text x="12" y="{h-64}">OD Ø{CASE_OD} · H {OVERALL_H} · PCB pocket Ø{PCB_POCKET_DIA} · '
        f'aperture {DISP_APERTURE}□</text>\n'
        f'<text x="12" y="{h-48}">Pogo {POGO_ROWS}×{POGO_COLS} pitch {POGO_PITCH} mm @ '
        f'({POGO_ORIGIN_X},{POGO_ORIGIN_Y}) · align ±{POGO_ALIGN_TOL} mm</text>\n'
        f'<text x="12" y="{h-32}">Nets: VCHG GND SWDIO / SWDCLK nRESET OPT — cradle mates to back, '
        f'no USB-C</text>\n'
        f'<text x="12" y="{h-16}">Lugs {LUG_STRAP_W} mm @ 3/9 · FPC {FPC_W}×{FPC_H} · plastic back (BLE)</text>\n'
        '</svg>\n'
    )
    path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    print("SW angles deg:", _sw_angles_deg())
    print("SPLIT_Z", SPLIT_Z, "OVERALL_H", OVERALL_H)
    paths = export_all()
    for k, v in paths.items():
        print(f"  {k}: {v}")
    print("DONE")
