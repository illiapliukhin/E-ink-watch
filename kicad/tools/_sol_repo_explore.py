#!/usr/bin/env python3
"""Let gpt-6-sol browse this workspace with tools, then propose a U2 reconnect KEEP.

Key from EXPLABS_API_KEY or /tmp/.explabs_key. Never logged, never written to the repo.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sol_board_query import inspect_window, probe_segment, probe_via

API = "https://api.experientiallabs.ai/v1/chat/completions"
ROOT = Path(__file__).resolve().parents[2]
BOARD_REL = "kicad/e-ink-watch.kicad_pcb"
REPORT = ROOT / "kicad/reports/PASS_AG_SOL_EXPLORE.md"
TRACE = Path("/tmp/sol_explore_trace.jsonl")
MAX_ROUNDS = 18
MAX_IMAGE_BYTES = 1_500_000
MAX_IMAGES_TOTAL = 8
READ_LINE_LIMIT = 220
GREP_MATCH_LIMIT = 80
LIST_ENTRY_LIMIT = 120
GLOB_LIMIT = 160

DENIED_NAMES = {
    ".explabs_key",
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials",
}
DENIED_SUBSTRINGS = ("explabs_key", "api_key", "service_account")
SKIP_DIR_NAMES = {".git", "__pycache__", "backups", "node_modules", ".venv", ".cursor"}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List a directory under the workspace root. Non-recursive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory relative to workspace, e.g. '.', 'kicad', 'kicad/reports'",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file as numbered lines. Use offset/limit for large files. Do not dump the whole .kicad_pcb.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset": {
                        "type": "integer",
                        "description": "1-based start line, default 1",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max lines, default 220, max 400",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search file contents with a Python regex. Prefer this over reading the whole PCB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {
                        "type": "string",
                        "description": "File or directory relative to workspace",
                    },
                    "glob": {
                        "type": "string",
                        "description": "Optional filename glob, e.g. '*.md' or '*.kicad_pcb'",
                    },
                    "max_matches": {"type": "integer"},
                },
                "required": ["pattern", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files by glob relative to workspace, e.g. 'kicad/reports/*.md'",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_image",
            "description": "Load a PNG/JPEG under the workspace so you can see it. Call this for pocket maps and 3D views.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_pcb_window",
            "description": "List tracks, through vias, and pads inside a millimetre window of e-ink-watch.kicad_pcb.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x0": {"type": "number"},
                    "y0": {"type": "number"},
                    "x1": {"type": "number"},
                    "y1": {"type": "number"},
                    "layer": {
                        "type": "string",
                        "description": "Optional F.Cu or B.Cu. Omit for both signal layers.",
                    },
                },
                "required": ["x0", "y0", "x1", "y1"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "probe_clearance",
            "description": "Geometry probe of a proposed via or orthogonal segment against other-net copper. Does not edit the board. Use before naming a KEEP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "description": "via or segment"},
                    "net": {"type": "string"},
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "size": {"type": "number"},
                    "x1": {"type": "number"},
                    "y1": {"type": "number"},
                    "x2": {"type": "number"},
                    "y2": {"type": "number"},
                    "width": {"type": "number"},
                    "layer": {"type": "string"},
                },
                "required": ["kind", "net"],
            },
        },
    },
]


def load_key() -> str:
    key = os.environ.get("EXPLABS_API_KEY")
    if not key:
        key_path = Path("/tmp/.explabs_key")
        if key_path.is_file():
            key = key_path.read_text().strip()
    if not key or not key.startswith("xpl_"):
        sys.exit("missing EXPLABS_API_KEY")
    return key


def resolve_path(raw: str) -> Path | str:
    if not raw or raw.strip() != raw:
        raw = (raw or "").strip()
    if not raw:
        return "empty path"
    if ".." in Path(raw).parts:
        return "path escapes workspace"
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            resolved = candidate.resolve()
        except OSError:
            return "unreadable path"
    else:
        resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return "path escapes workspace"
    name = resolved.name.lower()
    if name in DENIED_NAMES or any(token in name for token in DENIED_SUBSTRINGS):
        return "denied: secret path"
    text = str(resolved).lower()
    if any(token in text for token in DENIED_SUBSTRINGS):
        return "denied: secret path"
    return resolved


def list_dir(path: str) -> str:
    resolved = resolve_path(path)
    if isinstance(resolved, str):
        return f"ERROR {resolved}"
    if not resolved.is_dir():
        return "ERROR not a directory"
    entries = []
    for child in sorted(resolved.iterdir(), key=lambda item: item.name.lower()):
        if child.name in SKIP_DIR_NAMES or child.name in DENIED_NAMES:
            continue
        mark = "/" if child.is_dir() else ""
        size = ""
        if child.is_file():
            size = f" {child.stat().st_size}B"
        entries.append(f"{child.name}{mark}{size}")
        if len(entries) >= LIST_ENTRY_LIMIT:
            entries.append("… truncated")
            break
    rel = resolved.relative_to(ROOT)
    return f"{rel or '.'}\n" + "\n".join(entries)


def read_file(path: str, offset: int = 1, limit: int | None = None) -> str:
    resolved = resolve_path(path)
    if isinstance(resolved, str):
        return f"ERROR {resolved}"
    if not resolved.is_file():
        return "ERROR not a file"
    if resolved.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bin"}:
        return "ERROR binary; use read_image for pictures"
    limit = READ_LINE_LIMIT if limit is None else int(limit)
    limit = max(1, min(limit, 400))
    offset = max(1, int(offset or 1))
    if resolved.name.endswith(".kicad_pcb") and offset == 1 and limit >= 200:
        return (
            f"ERROR {BOARD_REL} is a large sexpr. Use grep or inspect_pcb_window, "
            "or read_file with a tight offset/limit."
        )
    try:
        lines = resolved.read_text(errors="replace").splitlines()
    except OSError as exc:
        return f"ERROR {exc}"
    chunk = lines[offset - 1 : offset - 1 + limit]
    numbered = [f"{offset + index}|{line[:400]}" for index, line in enumerate(chunk)]
    rel = resolved.relative_to(ROOT)
    return (
        f"{rel} lines {offset}-{offset + len(chunk) - 1} of {len(lines)}\n"
        + "\n".join(numbered)
    )


def iter_files(path: Path, glob_pat: str | None):
    if path.is_file():
        yield path
        return
    pattern = glob_pat or "*"
    for child in path.rglob(pattern):
        if not child.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in child.parts):
            continue
        if child.name in DENIED_NAMES:
            continue
        yield child


def grep(pattern: str, path: str, glob_pat: str | None = None, max_matches: int | None = None) -> str:
    resolved = resolve_path(path)
    if isinstance(resolved, str):
        return f"ERROR {resolved}"
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        return f"ERROR bad regex: {exc}"
    max_matches = GREP_MATCH_LIMIT if max_matches is None else int(max_matches)
    max_matches = max(1, min(max_matches, 120))
    hits = []
    files_seen = 0
    for file_path in iter_files(resolved, glob_pat):
        if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bin"}:
            continue
        files_seen += 1
        if files_seen > 400:
            hits.append("… too many files")
            break
        try:
            text = file_path.read_text(errors="replace")
        except OSError:
            continue
        rel = file_path.relative_to(ROOT)
        for index, line in enumerate(text.splitlines(), start=1):
            if compiled.search(line):
                hits.append(f"{rel}:{index}:{line[:300]}")
                if len(hits) >= max_matches:
                    return "\n".join(hits)
    return "\n".join(hits) if hits else "no matches"


def glob_files(pattern: str) -> str:
    if ".." in Path(pattern).parts:
        return "ERROR path escapes workspace"
    matches = []
    for path in sorted(ROOT.glob(pattern)):
        if any(part in SKIP_DIR_NAMES for part in path.relative_to(ROOT).parts):
            continue
        if path.name in DENIED_NAMES:
            continue
        mark = "/" if path.is_dir() else ""
        matches.append(str(path.relative_to(ROOT)) + mark)
        if len(matches) >= GLOB_LIMIT:
            matches.append("… truncated")
            break
    return "\n".join(matches) if matches else "no matches"


def b64_png(path: Path) -> str:
    data = path.read_bytes()
    mime = "image/png"
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    elif suffix == ".gif":
        mime = "image/gif"
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


class Explorer:
    def __init__(self) -> None:
        self.images_sent = 0
        self.pending_images: list[Path] = []
        self.trace: list[dict] = []

    def read_image(self, path: str) -> str:
        resolved = resolve_path(path)
        if isinstance(resolved, str):
            return f"ERROR {resolved}"
        if not resolved.is_file():
            return "ERROR not a file"
        if resolved.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            return "ERROR not an image"
        size = resolved.stat().st_size
        if size > MAX_IMAGE_BYTES:
            return f"ERROR image too large ({size} bytes)"
        if self.images_sent + len(self.pending_images) >= MAX_IMAGES_TOTAL:
            return "ERROR image budget exhausted; reason from files you already opened"
        self.pending_images.append(resolved)
        rel = resolved.relative_to(ROOT)
        return f"IMAGE queued {rel} {size}B — look at the following user image message"

    def probe_clearance(self, args: dict) -> str:
        kind = str(args.get("kind") or "")
        net = str(args.get("net") or "")
        if not net:
            return "ERROR net required"
        if kind == "via":
            try:
                return probe_via(float(args["x"]), float(args["y"]), float(args["size"]), net)
            except (KeyError, TypeError, ValueError) as exc:
                return f"ERROR via needs x,y,size: {exc}"
        if kind == "segment":
            try:
                return probe_segment(
                    float(args["x1"]),
                    float(args["y1"]),
                    float(args["x2"]),
                    float(args["y2"]),
                    float(args["width"]),
                    str(args["layer"]),
                    net,
                )
            except (KeyError, TypeError, ValueError) as exc:
                return f"ERROR segment needs x1,y1,x2,y2,width,layer: {exc}"
        return "ERROR kind must be via or segment"

    def dispatch(self, name: str, args: dict) -> str:
        try:
            if name == "list_dir":
                return list_dir(str(args.get("path", ".")))
            if name == "read_file":
                return read_file(
                    str(args.get("path", "")),
                    int(args.get("offset") or 1),
                    args.get("limit"),
                )
            if name == "grep":
                return grep(
                    str(args.get("pattern", "")),
                    str(args.get("path", ".")),
                    args.get("glob"),
                    args.get("max_matches"),
                )
            if name == "glob":
                return glob_files(str(args.get("pattern", "")))
            if name == "read_image":
                return self.read_image(str(args.get("path", "")))
            if name == "inspect_pcb_window":
                return inspect_window(
                    float(args["x0"]),
                    float(args["y0"]),
                    float(args["x1"]),
                    float(args["y1"]),
                    args.get("layer"),
                )
            if name == "probe_clearance":
                return self.probe_clearance(args)
            return f"ERROR unknown tool {name}"
        except Exception as exc:  # noqa: BLE001 — tool boundary
            return f"ERROR {type(exc).__name__}: {exc}"


def tool_call_id(call: dict) -> str:
    return str(call.get("id") or call.get("call_id") or "")


def tool_name(call: dict) -> str:
    function = call.get("function") or {}
    return str(call.get("name") or function.get("name") or "")


def tool_args(call: dict) -> dict:
    function = call.get("function") or {}
    raw = call.get("arguments", function.get("arguments", {}))
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def chat(key: str, messages: list, timeout: int = 240) -> dict:
    payload = {
        "model": "gpt-6-sol",
        "stream": False,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
    }
    request = urllib.request.Request(
        API,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:2000]
        raise SystemExit(f"HTTP {exc.code} {detail}") from exc
    if "error" in body:
        raise SystemExit(f"API error {body['error']}")
    return body


def image_user_message(paths: list[Path]) -> dict:
    content: list[dict] = [
        {
            "type": "text",
            "text": "Images you requested via read_image. Read them before proposing coordinates.",
        }
    ]
    for path in paths:
        rel = path.relative_to(ROOT)
        content.append({"type": "text", "text": f"IMAGE {rel}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": b64_png(path), "detail": "high"},
            }
        )
    return {"role": "user", "content": content}


def compact_assistant(message: dict) -> dict:
    kept = {"role": "assistant"}
    if message.get("content"):
        kept["content"] = message["content"]
    if message.get("tool_calls"):
        kept["tool_calls"] = message["tool_calls"]
    return kept


def write_report(
    trace: list[dict],
    final_text: str,
    usage: dict | None,
    report_path: Path = REPORT,
) -> None:
    calls = []
    for row in trace:
        if row.get("role") == "tool":
            calls.append(
                f"- `{row.get('name')}` `{json.dumps(row.get('args', {}), ensure_ascii=False)[:240]}`"
            )
    body = (
        "# gpt-6-sol repo explorer (2026-09-24)\n\n"
        "Sol used workspace tools. API key is not in the repo. "
        "Coordinates below are **Sol's**, not yet a DRC KEEP unless a later section says KEEP.\n\n"
        "## Tool calls\n\n"
        + ("\n".join(calls) if calls else "- (none)\n")
        + "\n\n## Usage\n\n"
        + json.dumps(usage or {}, indent=2)
        + "\n\n## Sol reply\n\n"
        + (final_text or "_(empty)_")
        + "\n"
    )
    report_path.write_text(body)
    TRACE.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in trace) + "\n")


SYSTEM = (
    "You are gpt-6-sol, a senior KiCad 9 PCB layout engineer. "
    "The workspace is a real Ø40 mm 4-layer E Ink watch board. "
    "You MUST use tools to open files yourself. Do not invent file contents, coordinates, or DRC numbers. "
    "Start with list_dir and glob, then read cursor.md, kicad/LIVE_LOG.txt, Pass-AG reports, "
    "inspect the board copper, and look at pocket images under kicad/reports/sol_views/. "
    "Hard gates you may not relax: shorting_items=0; power-priority shorts=0; PMID pocket shorts=0; "
    "do not apply VBUS on the dock; In1.Cu is a GND plane and In2.Cu is a 3V3 plane — never haul signals there; "
    "through vias F.Cu–B.Cu only; prefer in-place set_via_at / set_seg_ends / set_fp_at; "
    "KiCad 0402 rotation 90 is clockwise so pad1 is at (x, y+0.51). Do not move U2. "
    "Do not request secrets or API keys; tools will refuse them. "
    "When you have enough evidence, stop calling tools and reply in Russian with: "
    "what you actually opened; three mutually different orthogonal F/B reconnect variants for the current U2 islands; "
    "then ONE first combined KEEP as exact set_via_at / set_seg_ends / set_fp_at / add_segment / add_via numbers. "
    "Probe every new via and segment with probe_clearance before naming it KEEP. "
    "If a coordinate is not in a file or image you opened, say so."
)

USER = (
    "Заставь Сола самого лазить в репозитории и изучать все что ему нужно "
    "для продолжения проектирования нашей платы.\n\n"
    "Workspace root: /workspace. Board file: kicad/e-ink-watch.kicad_pcb. "
    "Do not wait for a human brief. Open the repo with tools, then continue U2 reconnect design."
)


def main() -> None:
    key = load_key()
    os.chdir(ROOT / "kicad")
    explorer = Explorer()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER},
    ]
    extra = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else ""
    report_path = REPORT
    if extra.strip():
        messages.append({"role": "user", "content": extra.strip()})
        report_path = ROOT / "kicad/reports/PASS_AG_SOL_EXPLORE_FOLLOWUP.md"
        if len(sys.argv) > 2:
            report_path = ROOT / sys.argv[2]
        print("FOLLOWUP attached", len(extra), "chars", flush=True)
    final_text = ""
    usage = None
    TRACE.write_text("")
    for round_index in range(1, MAX_ROUNDS + 1):
        print(f"ROUND {round_index}", flush=True)
        body = chat(key, messages)
        usage = body.get("usage")
        choice = body["choices"][0]
        message = choice["message"]
        finish = choice.get("finish_reason")
        print("finish", finish, "model", body.get("model"), "usage", usage, flush=True)
        calls = message.get("tool_calls") or []
        explorer.trace.append(
            {
                "round": round_index,
                "finish": finish,
                "content_len": len(message.get("content") or ""),
                "tool_calls": [tool_name(call) for call in calls],
            }
        )
        if calls:
            messages.append(compact_assistant(message))
            explorer.pending_images = []
            for call in calls:
                name = tool_name(call)
                args = tool_args(call)
                result = explorer.dispatch(name, args)
                call_id = tool_call_id(call)
                print(f"  {name} {json.dumps(args, ensure_ascii=False)[:180]}", flush=True)
                print(f"    -> {result.splitlines()[0][:160]}", flush=True)
                explorer.trace.append({"role": "tool", "name": name, "args": args, "result_head": result[:500]})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result[:12000],
                    }
                )
            if explorer.pending_images:
                queued = list(explorer.pending_images)
                explorer.images_sent += len(queued)
                messages.append(image_user_message(queued))
                explorer.pending_images = []
            if round_index == MAX_ROUNDS:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "No more tool rounds. Write the three variants and "
                            "the combined KEEP now from what you already opened. "
                            "If none is KEEP, say so in Russian."
                        ),
                    }
                )
                print("FINALIZE after last tool round", flush=True)
                body = chat(key, messages)
                usage = body.get("usage")
                choice = body["choices"][0]
                message = choice["message"]
                finish = choice.get("finish_reason")
                print("finish", finish, "model", body.get("model"), "usage", usage, flush=True)
                explorer.trace.append(
                    {
                        "round": "finalize",
                        "finish": finish,
                        "content_len": len(message.get("content") or ""),
                        "tool_calls": [
                            tool_name(call) for call in (message.get("tool_calls") or [])
                        ],
                    }
                )
                final_text = message.get("content") or "(max rounds, empty finalize)"
                break
            continue
        final_text = message.get("content") or ""
        if round_index == 1 and not final_text.strip():
            messages.append(compact_assistant(message))
            messages.append(
                {
                    "role": "user",
                    "content": "You returned no tools and no text. Call list_dir on '.' then glob '**/*.md'.",
                }
            )
            continue
        if round_index == 1 and "set_" not in final_text and "KEEP" not in final_text:
            messages.append(compact_assistant(message))
            messages.append(
                {
                    "role": "user",
                    "content": "You have not opened the repo yet. Use tools: list_dir '.', then read cursor.md and kicad/LIVE_LOG.txt.",
                }
            )
            continue
        break
    else:
        final_text = final_text or "(max rounds, no final text)"
    write_report(explorer.trace, final_text, usage, report_path)
    print("WROTE", report_path)
    print(final_text)


if __name__ == "__main__":
    main()
