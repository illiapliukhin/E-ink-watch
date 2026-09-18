#!/usr/bin/env python3
# E Ink Watch KiCad generator (BLE-only, no NFC)
from __future__ import annotations
import json, uuid
from pathlib import Path

ROOT = Path("/workspace/e-ink-watch-kicad")
VERSION = 20231120
GEN = "e-ink-watch-generator"

def uid():
    return str(uuid.uuid4())

def esc(s):
    return str(s).replace(chr(92), chr(92)+chr(92)).replace(chr(34), chr(92)+chr(34))


def pin(num, name, etype, x, y, length, orient, hide=False):
    h = " hide" if hide else ""
    return (
        "        (pin %s line\n"
        "          (at %s %s %s)\n"
        "          (length %s)%s\n"
        "          (name \"%s\" (effects (font (size 1.27 1.27))))\n"
        "          (number \"%s\" (effects (font (size 1.27 1.27))))\n"
        "        )"
    ) % (etype, x, y, orient, length, h, esc(name), esc(num))

def make_ic(lib_id, name, pins, body_w=25.4, body_h=38.1, ref="U", fp="", ds="", desc=""):
    left = [p for p in pins if p[3] == "L"]
    right = [p for p in pins if p[3] == "R"]
    top = [p for p in pins if p[3] == "T"]
    bottom = [p for p in pins if p[3] == "B"]
    hw, plen = body_w / 2, 2.54
    body_h = max(body_h, max(len(left), len(right), 1) * 2.54 + 5.08)
    hh = body_h / 2
    ps = []
    for i, (num, pname, etype, _) in enumerate(left):
        ps.append(pin(num, pname, etype, -hw, hh - 2.54 - i * 2.54, plen, 180))
    for i, (num, pname, etype, _) in enumerate(right):
        ps.append(pin(num, pname, etype, hw, hh - 2.54 - i * 2.54, plen, 0))
    for i, (num, pname, etype, _) in enumerate(top):
        ps.append(pin(num, pname, etype, -hw + 2.54 + i * 2.54, hh, plen, 90))
    for i, (num, pname, etype, _) in enumerate(bottom):
        ps.append(pin(num, pname, etype, -hw + 2.54 + i * 2.54, -hh, plen, 270))
    pj = "\n".join(ps)
    return (
        "    (symbol \"%s\"\n"
        "      (pin_names (offset 1.016))\n"
        "      (exclude_from_sim no)\n"
        "      (in_bom yes)\n"
        "      (on_board yes)\n"
        "      (property \"Reference\" \"%s\" (at 0 %s 0) (effects (font (size 1.27 1.27))))\n"
        "      (property \"Value\" \"%s\" (at 0 %s 0) (effects (font (size 1.27 1.27))))\n"
        "      (property \"Footprint\" \"%s\" (at 0 %s 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (property \"Datasheet\" \"%s\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (property \"Description\" \"%s\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (symbol \"%s_0_1\"\n"
        "        (rectangle (start %s %s) (end %s %s)\n"
        "          (stroke (width 0.254) (type default)) (fill (type background)))\n"
        "      )\n"
        "      (symbol \"%s_1_1\"\n%s\n      )\n"
        "    )"
    ) % (esc(lib_id), ref, hh+1.27, esc(name), -hh-1.27, esc(fp), -hh-2.54,
         esc(ds), esc(desc), esc(lib_id), -hw, -hh, hw, hh, esc(lib_id), pj)

def power_sym(name):
    if name == "GND":
        return (
            "    (symbol \"power:GND\"\n"
            "      (power)\n"
            "      (pin_names (offset 0))\n"
            "      (exclude_from_sim no)\n"
            "      (in_bom yes)\n"
            "      (on_board yes)\n"
            "      (property \"Reference\" \"#PWR\" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))\n"
            "      (property \"Value\" \"GND\" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))\n"
            "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
            "      (property \"Datasheet\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
            "      (symbol \"power:GND_0_1\"\n"
            "        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))\n"
            "          (stroke (width 0) (type default)) (fill (type none)))\n"
            "      )\n"
            "      (symbol \"power:GND_1_1\"\n"
            "        (pin power_in line (at 0 0 270) (length 0) hide\n"
            "          (name \"GND\" (effects (font (size 1.27 1.27))))\n"
            "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
            "        )\n"
            "      )\n"
            "    )"
        )
    return (
        "    (symbol \"power:%s\"\n"
        "      (power)\n"
        "      (pin_names (offset 0))\n"
        "      (exclude_from_sim no)\n"
        "      (in_bom yes)\n"
        "      (on_board yes)\n"
        "      (property \"Reference\" \"#PWR\" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (property \"Value\" \"%s\" (at 0 3.556 0) (effects (font (size 1.27 1.27))))\n"
        "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (property \"Datasheet\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (symbol \"power:%s_0_1\"\n"
        "        (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27))\n"
        "          (stroke (width 0) (type default)) (fill (type none)))\n"
        "        (polyline (pts (xy 0 0) (xy 0 1.27))\n"
        "          (stroke (width 0) (type default)) (fill (type none)))\n"
        "      )\n"
        "      (symbol \"power:%s_1_1\"\n"
        "        (pin power_in line (at 0 0 90) (length 0) hide\n"
        "          (name \"%s\" (effects (font (size 1.27 1.27))))\n"
        "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
        "        )\n"
        "      )\n"
        "    )"
    ) % (esc(name), esc(name), esc(name), esc(name), esc(name))

PASSIVE_R = (
    "    (symbol \"Device:R\"\n"
    "      (pin_numbers hide)\n"
    "      (pin_names (offset 0))\n"
    "      (exclude_from_sim no)\n"
    "      (in_bom yes)\n"
    "      (on_board yes)\n"
    "      (property \"Reference\" \"R\" (at 2.032 0 90) (effects (font (size 1.27 1.27))))\n"
    "      (property \"Value\" \"R\" (at -2.032 0 90) (effects (font (size 1.27 1.27))))\n"
    "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (symbol \"Device:R_0_1\"\n"
    "        (rectangle (start -1.016 -2.54) (end 1.016 2.54)\n"
    "          (stroke (width 0.254) (type default)) (fill (type none)))\n"
    "      )\n"
    "      (symbol \"Device:R_1_1\"\n"
    "        (pin passive line (at 0 3.81 270) (length 1.27)\n"
    "          (name \"~\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "        (pin passive line (at 0 -3.81 90) (length 1.27)\n"
    "          (name \"~\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"2\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "      )\n"
    "    )"
)
PASSIVE_C = (
    "    (symbol \"Device:C\"\n"
    "      (pin_numbers hide)\n"
    "      (pin_names (offset 0.254))\n"
    "      (exclude_from_sim no)\n"
    "      (in_bom yes)\n"
    "      (on_board yes)\n"
    "      (property \"Reference\" \"C\" (at 0.635 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))\n"
    "      (property \"Value\" \"C\" (at 0.635 -2.54 0) (effects (font (size 1.27 1.27)) (justify left)))\n"
    "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (symbol \"Device:C_0_1\"\n"
    "        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762))\n"
    "          (stroke (width 0.508) (type default)) (fill (type none)))\n"
    "        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762))\n"
    "          (stroke (width 0.508) (type default)) (fill (type none)))\n"
    "      )\n"
    "      (symbol \"Device:C_1_1\"\n"
    "        (pin passive line (at 0 3.81 270) (length 2.794)\n"
    "          (name \"~\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "        (pin passive line (at 0 -3.81 90) (length 2.794)\n"
    "          (name \"~\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"2\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "      )\n"
    "    )"
)
PASSIVE_FB = (
    "    (symbol \"Device:FerriteBead\"\n"
    "      (pin_numbers hide)\n"
    "      (pin_names (offset 1.016) hide)\n"
    "      (exclude_from_sim no)\n"
    "      (in_bom yes)\n"
    "      (on_board yes)\n"
    "      (property \"Reference\" \"FB\" (at 0 2.54 0) (effects (font (size 1.27 1.27))))\n"
    "      (property \"Value\" \"FerriteBead\" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))\n"
    "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (symbol \"Device:FerriteBead_0_1\"\n"
    "        (rectangle (start -1.27 -2.54) (end 1.27 2.54)\n"
    "          (stroke (width 0.254) (type default)) (fill (type none)))\n"
    "      )\n"
    "      (symbol \"Device:FerriteBead_1_1\"\n"
    "        (pin passive line (at 0 3.81 270) (length 1.27)\n"
    "          (name \"~\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "        (pin passive line (at 0 -3.81 90) (length 1.27)\n"
    "          (name \"~\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"2\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "      )\n"
    "    )"
)
CRYSTAL = (
    "    (symbol \"Device:Crystal\"\n"
    "      (pin_numbers hide)\n"
    "      (pin_names (offset 1.016) hide)\n"
    "      (exclude_from_sim no)\n"
    "      (in_bom yes)\n"
    "      (on_board yes)\n"
    "      (property \"Reference\" \"Y\" (at 0 3.175 0) (effects (font (size 1.27 1.27))))\n"
    "      (property \"Value\" \"Crystal\" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))\n"
    "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (symbol \"Device:Crystal_0_1\"\n"
    "        (rectangle (start -1.27 -2.54) (end 1.27 2.54)\n"
    "          (stroke (width 0.254) (type default)) (fill (type none)))\n"
    "      )\n"
    "      (symbol \"Device:Crystal_1_1\"\n"
    "        (pin passive line (at -3.81 0 0) (length 1.524)\n"
    "          (name \"1\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "        (pin passive line (at 3.81 0 180) (length 1.524)\n"
    "          (name \"2\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"2\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "      )\n"
    "    )"
)
SW_PUSH = (
    "    (symbol \"Switch:SW_Push\"\n"
    "      (pin_names (offset 1.016) hide)\n"
    "      (exclude_from_sim no)\n"
    "      (in_bom yes)\n"
    "      (on_board yes)\n"
    "      (property \"Reference\" \"SW\" (at 1.27 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))\n"
    "      (property \"Value\" \"SW_Push\" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))\n"
    "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (symbol \"Switch:SW_Push_0_1\"\n"
    "        (circle (center -2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))\n"
    "        (circle (center 2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))\n"
    "        (polyline (pts (xy -2.032 0) (xy 2.032 0)) (stroke (width 0) (type default)) (fill (type none)))\n"
    "      )\n"
    "      (symbol \"Switch:SW_Push_1_1\"\n"
    "        (pin passive line (at -5.08 0 0) (length 2.54)\n"
    "          (name \"1\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "        (pin passive line (at 5.08 0 180) (length 2.54)\n"
    "          (name \"2\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"2\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "      )\n"
    "    )"
)
Q_PMOS = (
    "    (symbol \"Device:Q_PMOS_GSD\"\n"
    "      (pin_names (offset 0) hide)\n"
    "      (exclude_from_sim no)\n"
    "      (in_bom yes)\n"
    "      (on_board yes)\n"
    "      (property \"Reference\" \"Q\" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))\n"
    "      (property \"Value\" \"Q_PMOS_GSD\" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))\n"
    "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
    "      (symbol \"Device:Q_PMOS_GSD_0_1\"\n"
    "        (circle (center 1.651 0) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))\n"
    "        (polyline (pts (xy 0.254 0) (xy -2.54 0)) (stroke (width 0) (type default)) (fill (type none)))\n"
    "        (polyline (pts (xy 0.762 1.27) (xy 2.54 1.27) (xy 2.54 2.54)) (stroke (width 0) (type default)) (fill (type none)))\n"
    "        (polyline (pts (xy 0.762 -1.27) (xy 2.54 -1.27) (xy 2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none)))\n"
    "      )\n"
    "      (symbol \"Device:Q_PMOS_GSD_1_1\"\n"
    "        (pin input line (at -5.08 0 0) (length 2.54)\n"
    "          (name \"G\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"1\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "        (pin passive line (at 2.54 5.08 270) (length 2.54)\n"
    "          (name \"S\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"2\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "        (pin passive line (at 2.54 -5.08 90) (length 2.54)\n"
    "          (name \"D\" (effects (font (size 1.27 1.27))))\n"
    "          (number \"3\" (effects (font (size 1.27 1.27))))\n"
    "        )\n"
    "      )\n"
    "    )"
)

def conn_sym(n, name):
    lib_id = "Connector:%s" % name
    body_h = n * 2.54 + 2.54
    hh = body_h / 2
    hw = 5.08
    ps = []
    for i in range(n):
        y = hh - 2.54 - i * 2.54
        ps.append(pin(str(i + 1), "Pin_%d" % (i + 1), "passive", -hw, y, 2.54, 180))
    pj = "\n".join(ps)
    return (
        "    (symbol \"%s\"\n"
        "      (pin_names (offset 1.016) hide)\n"
        "      (exclude_from_sim no)\n"
        "      (in_bom yes)\n"
        "      (on_board yes)\n"
        "      (property \"Reference\" \"J\" (at 0 %s 0) (effects (font (size 1.27 1.27))))\n"
        "      (property \"Value\" \"%s\" (at 0 %s 0) (effects (font (size 1.27 1.27))))\n"
        "      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n"
        "      (symbol \"%s_0_1\"\n"
        "        (rectangle (start %s %s) (end %s %s)\n"
        "          (stroke (width 0.254) (type default)) (fill (type background)))\n"
        "      )\n"
        "      (symbol \"%s_1_1\"\n%s\n      )\n"
        "    )"
    ) % (lib_id, hh + 1.27, esc(name), -hh - 1.27, lib_id, -hw + 2.54, -hh, hw, hh, lib_id, pj)

BQ_PINS = [
    ("1","IN","power_in","L"),("2","PMID","passive","L"),("3","BAT","passive","L"),
    ("4","TS","passive","L"),("5","GND","power_in","L"),("6","/CD","input","L"),
    ("7","LSCTRL","passive","R"),("8","LDO","power_out","R"),("9","SW","passive","R"),
    ("10","SYS","power_out","R"),("11","SDA","bidirectional","R"),("12","SCL","input","R"),
    ("13","INT","open_collector","R"),("14","/MR","input","R"),("15","PG","open_collector","R"),
    ("EP","EPAD","passive","B"),
]
# BLE-only nRF52840 logical map — no NFC_FD, NFCT pins unused/free as GPIO
NRF_PINS = [
    ("1","VDD","power_in","L"),("2","VDDH","power_in","L"),("3","DEC4","passive","L"),
    ("4","GND","power_in","L"),("5","SWDCLK","input","L"),("6","SWDIO","bidirectional","L"),
    ("7","RESET","input","L"),("8","XC1","passive","L"),("9","XC2","passive","L"),
    ("10","XL1","passive","L"),("11","XL2","passive","L"),
    ("12","P0.03_SCK","bidirectional","R"),("13","P0.04_MOSI","bidirectional","R"),
    ("14","P0.06_CS_M","bidirectional","R"),("15","P0.07_CS_L","bidirectional","R"),
    ("16","P0.08_CS_R","bidirectional","R"),("17","P0.26_DC","bidirectional","R"),
    ("18","P0.27_RST","bidirectional","R"),("19","P0.28_BUSY_M","bidirectional","R"),
    ("20","P0.29_BUSY_L","bidirectional","R"),("21","P0.30_BUSY_R","bidirectional","R"),
    ("22","P0.31_DISP_EN","bidirectional","R"),("23","P0.11_SDA","bidirectional","R"),
    ("24","P0.12_SCL","bidirectional","R"),("25","P0.15_PMIC_INT","bidirectional","R"),
    ("26","P1.01_BTN1","bidirectional","R"),("27","P1.02_BTN2","bidirectional","R"),
    ("28","P1.03_BTN3","bidirectional","R"),("29","ANT","passive","T"),
]

def ic_libs():
    return {
        "EInkWatch:BQ25120A": make_ic(
            "EInkWatch:BQ25120A", "BQ25120A", BQ_PINS, 30.48, 45.72,
            fp="TBD:BQ25120A_DSBGA", ds="https://www.ti.com/product/BQ25120A",
            desc="Wearable charger+LDO placeholder"),
        "EInkWatch:nRF52840": make_ic(
            "EInkWatch:nRF52840", "nRF52840", NRF_PINS, 35.56, 70.0,
            fp="TBD:nRF52840_QIAA_or_MDBT50Q",
            ds="https://www.nordicsemi.com/Products/nRF52840",
            desc="Logical BLE wearable pin map NOT full package; NFC unused"),
    }

def place_sym(lib_id, ref, value, x, y, rot=0, fp="TBD"):
    su = uid()
    return (
        "  (symbol\n"
        "    (lib_id \"%s\")\n"
        "    (at %s %s %s)\n"
        "    (unit 1)\n"
        "    (exclude_from_sim no)\n"
        "    (in_bom yes)\n"
        "    (on_board yes)\n"
        "    (dnp no)\n"
        "    (uuid \"%s\")\n"
        "    (property \"Reference\" \"%s\" (at %s %s %s) (effects (font (size 1.27 1.27))))\n"
        "    (property \"Value\" \"%s\" (at %s %s %s) (effects (font (size 1.27 1.27))))\n"
        "    (property \"Footprint\" \"%s\" (at %s %s %s) (effects (font (size 1.27 1.27)) hide))\n"
        "    (property \"Datasheet\" \"~\" (at %s %s %s) (effects (font (size 1.27 1.27)) hide))\n"
        "    (instances\n"
        "      (project \"e-ink-watch\"\n"
        "        (path \"/ROOTUUID\" (reference \"%s\") (unit 1))\n"
        "      )\n"
        "    )\n"
        "  )\n"
    ) % (esc(lib_id), x, y, rot, su, esc(ref), x, y+5.08, rot, esc(value), x, y-5.08, rot,
         esc(fp), x, y, rot, x, y, rot, esc(ref))

def wire(x1, y1, x2, y2):
    return "  (wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid \"%s\"))\n" % (
        x1, y1, x2, y2, uid())

def junction(x, y):
    return "  (junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid \"%s\"))\n" % (x, y, uid())

def label(name, x, y, rot=0):
    return (
        "  (label \"%s\" (at %s %s %s) (fields_autoplaced yes)\n"
        "    (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid \"%s\"))\n"
    ) % (esc(name), x, y, rot, uid())

def hlabel(name, x, y, rot=0, shape="bidirectional"):
    return (
        "  (hierarchical_label \"%s\" (shape %s) (at %s %s %s)\n"
        "    (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)) (uuid \"%s\"))\n"
    ) % (esc(name), shape, x, y, rot, uid())

def text_note(txt, x, y):
    return (
        "  (text \"%s\" (exclude_from_sim no) (at %s %s 0)\n"
        "    (effects (font (size 1.5 1.5)) (justify left bottom)) (uuid \"%s\"))\n"
    ) % (esc(txt), x, y, uid())

def sheet_box(name, fname, x, y, w, h, pins):
    su = uid()
    pin_sexps = []
    for pname, shape, side, off in pins:
        if side == "L":
            px, py, rot = x, y + h - off, 180
        elif side == "R":
            px, py, rot = x + w, y + h - off, 0
        elif side == "T":
            px, py, rot = x + off, y + h, 90
        else:
            px, py, rot = x + off, y, 270
        just = "right" if side == "L" else "left"
        pin_sexps.append(
            "    (pin \"%s\" %s\n"
            "      (at %s %s %s)\n"
            "      (effects (font (size 1.27 1.27)) (justify %s))\n"
            "      (uuid \"%s\")\n"
            "    )" % (esc(pname), shape, px, py, rot, just, uid())
        )
    pj = "\n".join(pin_sexps)
    return (
        "  (sheet\n"
        "    (at %s %s)\n"
        "    (size %s %s)\n"
        "    (exclude_from_sim no)\n"
        "    (in_bom yes)\n"
        "    (on_board yes)\n"
        "    (dnp no)\n"
        "    (fields_autoplaced yes)\n"
        "    (stroke (width 0.1524) (type solid))\n"
        "    (fill (color 0 0 0 0.0))\n"
        "    (uuid \"%s\")\n"
        "    (property \"Sheetname\" \"%s\" (at %s %s 0)\n"
        "      (effects (font (size 1.27 1.27)) (justify left bottom)))\n"
        "    (property \"Sheetfile\" \"%s\" (at %s %s 0)\n"
        "      (effects (font (size 1.27 1.27)) (justify left top)))\n"
        "%s\n"
        "  )\n"
    ) % (x, y, w, h, su, esc(name), x, y+h+0.5, esc(fname), x, y-0.5, pj)

def title_block(title, comment=""):
    return (
        "  (title_block\n"
        "    (title \"%s\")\n"
        "    (date \"2026-09-18\")\n"
        "    (rev \"0.2-concept-ble\")\n"
        "    (company \"E Ink Watch Concept\")\n"
        "    (comment 1 \"%s\")\n"
        "  )\n"
    ) % (esc(title), esc(comment))

def lib_block(syms):
    return "  (lib_symbols\n" + "\n".join(syms) + "\n  )\n"

def sch_wrap(sheet_uuid, paper, title, comment, libs, body, page):
    return (
        "(kicad_sch\n"
        "  (version %s)\n"
        "  (generator \"%s\")\n"
        "  (generator_version \"1.0\")\n"
        "  (uuid \"%s\")\n"
        "  (paper \"%s\")\n"
        "%s%s%s"
        "  (sheet_instances\n    (path \"/\" (page \"%s\"))\n  )\n)\n"
    ) % (VERSION, GEN, sheet_uuid, paper, title_block(title, comment), lib_block(libs),
         "".join(body), page)

def balance_check(text, name):
    depth = 0
    in_str = False
    esc_c = False
    for i, ch in enumerate(text):
        if in_str:
            if esc_c:
                esc_c = False
            elif ch == "\\":
                esc_c = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise RuntimeError("%s: extra ) at %s" % (name, i))
    if depth != 0:
        raise RuntimeError("%s: unbalanced depth=%s" % (name, depth))
    print("OK", name)

def gen_power():
    ics = ic_libs()
    libs = [ics["EInkWatch:BQ25120A"], PASSIVE_R, PASSIVE_C, PASSIVE_FB, Q_PMOS,
            conn_sym(2, "Conn_01x02"),
            power_sym("GND"), power_sym("VBUS"), power_sym("VBAT"),
            power_sym("VSYS"), power_sym("3V3"), power_sym("3V3_DISP")]
    b = []
    b.append(text_note("POWER: LiPo + BQ25120A + 3V3 + switched 3V3_DISP. Footprints TBD.", 20, 180))
    b.append(place_sym("Connector:Conn_01x02", "J1", "LiPo+PCM", 40, 120, fp="TBD:JST_PH_2pin"))
    b.append(place_sym("EInkWatch:BQ25120A", "U1", "BQ25120A", 100, 110, fp="TBD:BQ25120A_DSBGA"))
    b.append(place_sym("Device:Q_PMOS_GSD", "Q1", "P-FET_DISP", 160, 90, fp="TBD:SOT23"))
    b.append(place_sym("Device:C", "C1", "10uF", 100, 50, fp="TBD:0402"))
    b.append(place_sym("Device:C", "C2", "1uF", 115, 50, fp="TBD:0402"))
    b.append(place_sym("Device:C", "C3", "10uF", 160, 50, fp="TBD:0402"))
    b.append(place_sym("Device:R", "R1", "10k", 160, 130, fp="TBD:0402"))
    b.append(place_sym("Device:FerriteBead", "FB1", "BLM18", 55, 70, fp="TBD:0603"))
    for ref, lib, val, x, y in [
        ("#PWR01", "power:VBUS", "VBUS", 55, 55), ("#PWR02", "power:VBAT", "VBAT", 40, 150),
        ("#PWR03", "power:VSYS", "VSYS", 140, 70), ("#PWR04", "power:3V3", "3V3", 140, 150),
        ("#PWR05", "power:3V3_DISP", "3V3_DISP", 185, 70), ("#PWR06", "power:GND", "GND", 100, 160),
        ("#PWR07", "power:GND", "GND", 40, 160), ("#PWR08", "power:GND", "GND", 160, 160)]:
        b.append(place_sym(lib, ref, val, x, y, fp=""))
    for name, x, y, rot, shape in [
        ("VBUS", 55, 40, 90, "input"), ("VBAT", 25, 120, 180, "bidirectional"),
        ("VSYS", 145, 85, 0, "output"), ("3V3", 145, 140, 0, "output"),
        ("3V3_DISP", 195, 85, 0, "output"), ("SDA", 130, 100, 0, "bidirectional"),
        ("SCL", 130, 95, 0, "input"), ("PMIC_INT", 130, 90, 0, "output"),
        ("DISP_EN", 145, 130, 180, "input"), ("GND", 100, 175, 270, "bidirectional")]:
        b.append(hlabel(name, x, y, rot, shape))
    b.append(wire(55, 40, 55, 55)); b.append(wire(40, 150, 40, 145))
    b.append(wire(140, 70, 145, 70)); b.append(wire(140, 70, 140, 85))
    b.append(wire(185, 70, 195, 70)); b.append(wire(185, 70, 185, 85))
    b.append(wire(160, 130, 145, 130)); b.append(wire(100, 160, 100, 175))
    b.append(text_note("VBUS->IN; LiPo->BAT; SYS->VSYS; LDO->3V3; Q1 gates 3V3_DISP via DISP_EN.", 20, 30))
    return sch_wrap(uid(), "A3", "Power — BQ25120A / LiPo / rails", "Sheet: power", libs, b, "2")

def gen_mcu():
    ics = ic_libs()
    libs = [ics["EInkWatch:nRF52840"], PASSIVE_R, PASSIVE_C, CRYSTAL,
            power_sym("GND"), power_sym("3V3"), power_sym("VSYS")]
    b = []
    b.append(text_note(
        "MCU/RF: nRF52840 BLE-only (no NFC). Logical pin map NOT full aQFN73. FP TBD.\\n"
        "Pairing: long-press BTN1 ~3s -> BLE adv ~60s, then sleep.", 15, 190))
    b.append(place_sym("EInkWatch:nRF52840", "U2", "nRF52840", 110, 100, fp="TBD:nRF52840_QIAA_or_MDBT50Q"))
    b.append(place_sym("Device:Crystal", "Y1", "32MHz", 40, 60, fp="TBD:HF_XTAL"))
    b.append(place_sym("Device:Crystal", "Y2", "32.768kHz", 40, 100, fp="TBD:ABS07"))
    for ref, val, x, y in [("C10", "12pF", 55, 45), ("C11", "12pF", 55, 75),
                           ("C12", "12pF", 55, 90), ("C13", "12pF", 55, 115), ("C14", "100nF", 70, 150)]:
        b.append(place_sym("Device:C", ref, val, x, y, fp="TBD:0402"))
    b.append(place_sym("Device:R", "R10", "10k", 70, 170, fp="TBD:0402"))
    for ref, lib, val, x, y in [("#PWR10", "power:3V3", "3V3", 70, 40),
                                ("#PWR11", "power:VSYS", "VSYS", 85, 40),
                                ("#PWR12", "power:GND", "GND", 110, 170)]:
        b.append(place_sym(lib, ref, val, x, y, fp=""))
    for t in [
        ("3V3", 70, 25, 90, "input"), ("VSYS", 85, 25, 90, "input"), ("GND", 110, 185, 270, "bidirectional"),
        ("SWDCLK", 55, 130, 180, "bidirectional"), ("SWDIO", 55, 135, 180, "bidirectional"),
        ("NRST", 55, 140, 180, "bidirectional"),
        ("EPD_SCK", 165, 70, 0, "output"), ("EPD_MOSI", 165, 75, 0, "output"),
        ("EPD_CS_MAIN", 165, 80, 0, "output"), ("EPD_CS_L", 165, 85, 0, "output"),
        ("EPD_CS_R", 165, 90, 0, "output"), ("EPD_DC", 165, 95, 0, "output"),
        ("EPD_RST", 165, 100, 0, "output"),
        ("EPD_BUSY_MAIN", 165, 105, 0, "input"), ("EPD_BUSY_L", 165, 110, 0, "input"),
        ("EPD_BUSY_R", 165, 115, 0, "input"), ("DISP_EN", 165, 120, 0, "output"),
        ("SDA", 165, 130, 0, "bidirectional"), ("SCL", 165, 135, 0, "output"),
        ("PMIC_INT", 165, 145, 0, "input"),
        ("BTN1", 165, 155, 0, "input"), ("BTN2", 165, 160, 0, "input"), ("BTN3", 165, 165, 0, "input")]:
        b.append(hlabel(*t))
    b.append(text_note("SPI0->E Ink; I2C0->PMIC; SWD+buttons->UI. No NTAG/NFC coil.", 15, 25))
    return sch_wrap(uid(), "A3", "MCU / RF — nRF52840 BLE", "Sheet: mcu_rf", libs, b, "3")

def gen_displays():
    libs = [conn_sym(10, "Conn_01x10"), PASSIVE_R, PASSIVE_C,
            power_sym("GND"), power_sym("3V3_DISP")]
    b = []
    b.append(text_note(
        "DISPLAYS: 3x FPC MAIN/STRAP_L/STRAP_R shared SPI, per-panel CS/BUSY. FP TBD.", 15, 185))
    b.append(place_sym("Connector:Conn_01x10", "J2", "FPC_MAIN_EPD", 60, 100, fp="TBD:ZIF_0.5mm_10pin"))
    b.append(place_sym("Connector:Conn_01x10", "J3", "FPC_STRAP_L", 120, 100, fp="TBD:ZIF_0.5mm_10pin"))
    b.append(place_sym("Connector:Conn_01x10", "J4", "FPC_STRAP_R", 180, 100, fp="TBD:ZIF_0.5mm_10pin"))
    for ref, x in [("R20", 40), ("R21", 100), ("R22", 160)]:
        b.append(place_sym("Device:R", ref, "33R_SPI", x, 40, fp="TBD:0402"))
    for ref, x in [("C30", 60), ("C31", 120), ("C32", 180)]:
        b.append(place_sym("Device:C", ref, "1uF", x, 150, fp="TBD:0603"))
    for ref, lib, val, x, y in [
        ("#PWR30", "power:3V3_DISP", "3V3_DISP", 60, 50),
        ("#PWR31", "power:3V3_DISP", "3V3_DISP", 120, 50),
        ("#PWR32", "power:3V3_DISP", "3V3_DISP", 180, 50),
        ("#PWR33", "power:GND", "GND", 60, 160),
        ("#PWR34", "power:GND", "GND", 120, 160),
        ("#PWR35", "power:GND", "GND", 180, 160)]:
        b.append(place_sym(lib, ref, val, x, y, fp=""))
    for t in [
        ("3V3_DISP", 60, 35, 90, "input"), ("GND", 90, 175, 270, "bidirectional"),
        ("EPD_SCK", 30, 70, 180, "input"), ("EPD_MOSI", 30, 75, 180, "input"),
        ("EPD_DC", 30, 80, 180, "input"), ("EPD_RST", 30, 85, 180, "input"),
        ("EPD_CS_MAIN", 30, 95, 180, "input"), ("EPD_CS_L", 30, 100, 180, "input"),
        ("EPD_CS_R", 30, 105, 180, "input"),
        ("EPD_BUSY_MAIN", 30, 115, 180, "output"), ("EPD_BUSY_L", 30, 120, 180, "output"),
        ("EPD_BUSY_R", 30, 125, 180, "output")]:
        b.append(hlabel(*t))
    b.append(text_note("Logical FPC: VCI GND MOSI SCK CS DC RST BUSY. Verify lot pinout.", 15, 20))
    return sch_wrap(uid(), "A3", "Displays — 3x E Ink FPC", "Sheet: displays", libs, b, "4")

def gen_ui():
    libs = [SW_PUSH, conn_sym(4, "Conn_01x04"), conn_sym(2, "Conn_01x02"), PASSIVE_R,
            power_sym("GND"), power_sym("3V3"), power_sym("VBUS")]
    b = []
    b.append(text_note(
        "UI/DEBUG: BTN1 long-press ~3s = BLE pairing window ~60s. SWD + optional USB VBUS. FP TBD.",
        15, 170))
    b.append(place_sym("Switch:SW_Push", "SW1", "BTN1_PAIR", 50, 80, fp="TBD:tactile_side"))
    b.append(place_sym("Switch:SW_Push", "SW2", "BTN2", 50, 110, fp="TBD:tactile_side"))
    b.append(place_sym("Switch:SW_Push", "SW3", "BTN3", 50, 140, fp="TBD:tactile_side"))
    b.append(place_sym("Connector:Conn_01x04", "J5", "SWD", 130, 80, fp="TBD:TagConnect_or_1x04"))
    b.append(place_sym("Connector:Conn_01x02", "J6", "USB_VBUS", 130, 130, fp="TBD:USB_C_or_pogo"))
    for ref, val, x, y in [("R30", "10k", 80, 70), ("R31", "10k", 80, 100), ("R32", "10k", 80, 130)]:
        b.append(place_sym("Device:R", ref, val, x, y, fp="TBD:0402"))
    for ref, lib, val, x, y in [
        ("#PWR40", "power:3V3", "3V3", 80, 50), ("#PWR41", "power:GND", "GND", 50, 160),
        ("#PWR42", "power:GND", "GND", 130, 160), ("#PWR43", "power:VBUS", "VBUS", 150, 115)]:
        b.append(place_sym(lib, ref, val, x, y, fp=""))
    for t in [
        ("3V3", 80, 35, 90, "input"), ("GND", 90, 175, 270, "bidirectional"),
        ("VBUS", 160, 115, 0, "output"),
        ("BTN1", 100, 80, 0, "output"), ("BTN2", 100, 110, 0, "output"), ("BTN3", 100, 140, 0, "output"),
        ("SWDCLK", 155, 70, 0, "bidirectional"), ("SWDIO", 155, 75, 0, "bidirectional"),
        ("NRST", 155, 85, 0, "bidirectional")]:
        b.append(hlabel(*t))
    return sch_wrap(uid(), "A3", "Connectors / UI — BLE pair button + SWD", "Sheet: connectors_ui", libs, b, "5")

def gen_root():
    root_uuid = uid()
    b = []
    b.append(text_note(
        "E Ink Watch root (BLE-only, no NFC). Open e-ink-watch.kicad_pro in KiCad 8/9.", 20, 200))
    b.append(sheet_box("Power", "power.kicad_sch", 30, 40, 50, 70, [
        ("VBUS", "input", "L", 10), ("VBAT", "bidirectional", "L", 20), ("GND", "bidirectional", "L", 30),
        ("DISP_EN", "input", "L", 45), ("SDA", "bidirectional", "L", 55), ("SCL", "input", "L", 62),
        ("VSYS", "output", "R", 15), ("3V3", "output", "R", 25), ("3V3_DISP", "output", "R", 35),
        ("PMIC_INT", "output", "R", 50)]))
    b.append(sheet_box("MCU_RF", "mcu_rf.kicad_sch", 120, 30, 55, 90, [
        ("3V3", "input", "L", 10), ("VSYS", "input", "L", 18), ("GND", "bidirectional", "L", 26),
        ("PMIC_INT", "input", "L", 40), ("SDA", "bidirectional", "L", 50), ("SCL", "bidirectional", "L", 58),
        ("BTN1", "input", "B", 10), ("BTN2", "input", "B", 20), ("BTN3", "input", "B", 30),
        ("SWDCLK", "bidirectional", "B", 40), ("SWDIO", "bidirectional", "B", 50), ("NRST", "bidirectional", "B", 60),
        ("EPD_SCK", "output", "R", 8), ("EPD_MOSI", "output", "R", 15), ("EPD_CS_MAIN", "output", "R", 22),
        ("EPD_CS_L", "output", "R", 29), ("EPD_CS_R", "output", "R", 36), ("EPD_DC", "output", "R", 43),
        ("EPD_RST", "output", "R", 50), ("EPD_BUSY_MAIN", "input", "R", 57), ("EPD_BUSY_L", "input", "R", 64),
        ("EPD_BUSY_R", "input", "R", 71), ("DISP_EN", "output", "R", 80)]))
    b.append(sheet_box("Displays", "displays.kicad_sch", 220, 30, 50, 80, [
        ("3V3_DISP", "input", "T", 20), ("GND", "bidirectional", "B", 20),
        ("EPD_SCK", "input", "L", 8), ("EPD_MOSI", "input", "L", 15), ("EPD_DC", "input", "L", 22),
        ("EPD_RST", "input", "L", 29), ("EPD_CS_MAIN", "input", "L", 36), ("EPD_CS_L", "input", "L", 43),
        ("EPD_CS_R", "input", "L", 50), ("EPD_BUSY_MAIN", "output", "L", 57), ("EPD_BUSY_L", "output", "L", 64),
        ("EPD_BUSY_R", "output", "L", 71)]))
    b.append(sheet_box("Connectors_UI", "connectors_ui.kicad_sch", 120, 150, 55, 45, [
        ("3V3", "input", "T", 15), ("GND", "bidirectional", "L", 15), ("VBUS", "output", "L", 30),
        ("BTN1", "output", "T", 30), ("BTN2", "output", "T", 40), ("BTN3", "output", "T", 50),
        ("SWDCLK", "bidirectional", "R", 15), ("SWDIO", "bidirectional", "R", 25), ("NRST", "bidirectional", "R", 35)]))

    def w(*a):
        b.append(wire(*a))

    # 3V3 Power(80,85)->MCU(120,110)->UI(135,195)
    w(80, 85, 100, 85); w(100, 85, 100, 110); w(100, 110, 120, 110)
    b.append(junction(100, 110))
    w(100, 110, 100, 195); w(100, 195, 135, 195); b.append(label("3V3", 102, 110))
    # VSYS
    w(80, 95, 110, 95); w(110, 95, 110, 102); w(110, 102, 120, 102); b.append(label("VSYS", 85, 95))
    # 3V3_DISP
    w(80, 75, 90, 75); w(90, 75, 90, 20); w(90, 20, 240, 20); w(240, 20, 240, 110)
    b.append(label("3V3_DISP", 95, 20))
    # GND
    w(30, 80, 20, 80); w(20, 80, 20, 94); w(20, 94, 120, 94)
    w(20, 94, 20, 180); w(20, 180, 120, 180); w(20, 80, 20, 30); w(20, 30, 240, 30)
    b.append(label("GND", 22, 94))
    # I2C Power<->MCU
    w(30, 55, 25, 55); w(25, 55, 25, 70); w(25, 70, 120, 70); b.append(label("SDA", 27, 70))
    w(30, 48, 22, 48); w(22, 48, 22, 62); w(22, 62, 120, 62); b.append(label("SCL", 24, 62))
    # PMIC_INT
    w(80, 60, 115, 60); w(115, 60, 115, 80); w(115, 80, 120, 80); b.append(label("PMIC_INT", 85, 60))
    # DISP_EN
    w(175, 40, 185, 40); w(185, 40, 185, 15); w(185, 15, 10, 15); w(10, 15, 10, 65); w(10, 65, 30, 65)
    b.append(label("DISP_EN", 12, 15))
    # SPI MCU->Displays
    for name, m_off, d_off in [
        ("EPD_SCK", 8, 8), ("EPD_MOSI", 15, 15), ("EPD_CS_MAIN", 22, 36), ("EPD_CS_L", 29, 43),
        ("EPD_CS_R", 36, 50), ("EPD_DC", 43, 22), ("EPD_RST", 50, 29),
        ("EPD_BUSY_MAIN", 57, 57), ("EPD_BUSY_L", 64, 64), ("EPD_BUSY_R", 71, 71)]:
        my = 30 + 90 - m_off
        dy = 30 + 80 - d_off
        mid = 195
        w(175, my, mid, my); w(mid, my, mid, dy); w(mid, dy, 220, dy)
        b.append(label(name, mid + 1, min(my, dy)))
    # buttons
    w(150, 195, 150, 125); w(150, 125, 130, 125); w(130, 125, 130, 120); b.append(label("BTN1", 152, 150))
    w(160, 195, 160, 130); w(160, 130, 140, 130); w(140, 130, 140, 120); b.append(label("BTN2", 162, 150))
    w(170, 195, 170, 135); w(170, 135, 150, 135); w(150, 135, 150, 120); b.append(label("BTN3", 172, 150))
    # SWD
    w(175, 180, 200, 180); w(200, 180, 200, 210); w(200, 210, 160, 210); w(160, 210, 160, 120)
    b.append(label("SWDCLK", 202, 210))
    w(175, 170, 205, 170); w(205, 170, 205, 215); w(205, 215, 170, 215); w(170, 215, 170, 120)
    b.append(label("SWDIO", 207, 215))
    w(175, 160, 210, 160); w(210, 160, 210, 220); w(210, 220, 180, 220); w(180, 220, 180, 120)
    b.append(label("NRST", 212, 220))
    # VBUS
    w(120, 165, 15, 165); w(15, 165, 15, 100); w(15, 100, 30, 100); b.append(label("VBUS", 17, 130))
    b.append(text_note("Sheets: Power | MCU_RF | Displays | Connectors_UI (NO NFC)", 220, 150))

    content = (
        "(kicad_sch\n"
        "  (version %s)\n"
        "  (generator \"%s\")\n"
        "  (generator_version \"1.0\")\n"
        "  (uuid \"%s\")\n"
        "  (paper \"A2\")\n"
        "%s%s%s"
        "  (sheet_instances\n    (path \"/%s\" (page \"1\"))\n  )\n)\n"
    ) % (VERSION, GEN, root_uuid, title_block("E Ink Watch — Root (BLE-only)",
         "Wearable E Ink wristwatch PCB — no NFC"),
         lib_block([]), "".join(b), root_uuid)
    return content, root_uuid

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "libraries").mkdir(exist_ok=True)
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "tools").mkdir(exist_ok=True)

    ics = ic_libs()
    combined = []
    for full, sexp in ics.items():
        short = full.split(":")[-1]
        adj = sexp.replace('"%s"' % full, '"%s"' % short, 1).replace('"%s_' % full, '"%s_' % short)
        combined.append(adj)
    lib_content = (
        "(kicad_symbol_lib\n  (version %s)\n  (generator \"%s\")\n"
        "  (generator_version \"1.0\")\n%s\n)\n"
    ) % (VERSION, GEN, "\n".join(combined))
    (ROOT / "libraries" / "EInkWatch.kicad_sym").write_text(lib_content, encoding="utf-8")
    balance_check(lib_content, "EInkWatch.kicad_sym")
    for full, sexp in ics.items():
        short = full.split(":")[-1]
        adj = sexp.replace('"%s"' % full, '"%s"' % short, 1).replace('"%s_' % full, '"%s_' % short)
        lines = [(ln[2:] if ln.startswith("    ") else ln) for ln in adj.splitlines()]
        single = (
            "(kicad_symbol_lib\n  (version %s)\n  (generator \"%s\")\n"
            "  (generator_version \"1.0\")\n%s\n)\n"
        ) % (VERSION, GEN, "\n".join(lines))
        (ROOT / "libraries" / ("%s.kicad_sym" % short)).write_text(single, encoding="utf-8")
        balance_check(single, "%s.kicad_sym" % short)

    # Remove NFC sheet if present from earlier attempts
    nfc = ROOT / "nfc.kicad_sch"
    if nfc.exists():
        nfc.unlink()
    ntag = ROOT / "libraries" / "NT3H2211.kicad_sym"
    if ntag.exists():
        ntag.unlink()

    root_c, root_uuid = gen_root()
    files = {
        "power.kicad_sch": gen_power(),
        "mcu_rf.kicad_sch": gen_mcu(),
        "displays.kicad_sch": gen_displays(),
        "connectors_ui.kicad_sch": gen_ui(),
        "e-ink-watch.kicad_sch": root_c,
    }
    for name, content in files.items():
        content = content.replace("/ROOTUUID", "/%s" % root_uuid)
        (ROOT / name).write_text(content, encoding="utf-8")
        balance_check(content, name)

    pro = {
        "board": {"design_settings": {"defaults": {}, "diff_pair_dimensions": [], "drc_exclusions": [],
                                       "rules": {}, "track_widths": [], "via_dimensions": []},
                  "layer_presets": [], "viewports": []},
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": ["EInkWatch"]},
        "meta": {"filename": "e-ink-watch.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [{"bus_width": 12, "clearance": 0.2, "diff_pair_gap": 0.25,
                         "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0,
                         "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "Default",
                         "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                         "track_width": 0.25, "via_diameter": 0.8, "via_drill": 0.4, "wire_width": 6}],
            "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": []},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "specctra_dsn": "", "step": "", "vrml": ""},
                   "page_layout_descr_file": ""},
        "schematic": {
            "annotate_start_num": 0,
            "drawing": {"dashed_lines_dash_length_ratio": 12.0, "dashed_lines_gap_length_ratio": 3.0,
                        "default_line_thickness": 6.0, "default_text_size": 50.0, "field_names": [],
                        "intersheets_ref_own_page": False, "intersheets_ref_prefix": "",
                        "intersheets_ref_short": False, "intersheets_ref_show": False,
                        "intersheets_ref_suffix": "", "junction_size_choice": 3, "label_size_ratio": 0.375,
                        "operating_point_overlay_i_precision": 3, "operating_point_overlay_i_range": "~A",
                        "operating_point_overlay_v_precision": 3, "operating_point_overlay_v_range": "~V",
                        "overbar_offset_ratio": 1.23, "pin_symbol_size": 25.0, "text_offset_ratio": 0.15},
            "legacy_lib_dir": "", "legacy_lib_list": [], "net_format_name": "",
            "page_layout_descr_file": "", "plot_directory": "",
            "spice_current_sheet_as_root": False, "spice_external_command": "",
            "spice_model_current_sheet_as_root": True, "spice_save_all_currents": False,
            "spice_save_all_dissipations": False, "spice_save_all_voltages": False,
            "subpart_first_id": 65, "subpart_id_separator": 0},
        "sheets": [["ROOT", "Root"]],
        "text_variables": {},
    }
    (ROOT / "e-ink-watch.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8")
    (ROOT / "sym-lib-table").write_text(
        "(sym_lib_table\n  (version 7)\n"
        "  (lib (name \"EInkWatch\")(type \"KiCad\")(uri \"${KIPRJMOD}/libraries/EInkWatch.kicad_sym\")"
        "(options \"\")(descr \"Project-local ICs TBD footprints — BLE-only\"))\n)\n",
        encoding="utf-8")
    (ROOT / "fp-lib-table").write_text("(fp_lib_table\n  (version 7)\n)\n", encoding="utf-8")
    print("ROOT_UUID", root_uuid)
    print("DONE", ROOT)

if __name__ == "__main__":
    main()
