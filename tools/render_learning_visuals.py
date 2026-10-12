#!/usr/bin/env python3
"""Render original, accessible checkpoint roadmaps from authoritative lab tasks.

Each lesson keeps its service topology. These companion SVGs show the actual
five-task learning sequence, with original pictorial service symbols and the
checkpoint identifiers used by validation. No browser, external font, service,
or generated learner state is required. Use --check to verify committed output.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import textwrap
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "site-assets" / "learning-visuals"
RENDERER = "az104-checkpoint-roadmap-svg/1.0.0"
TASK_PATTERN = re.compile(r"^## Task ([1-5]) — (.*?) \{#task-([1-5])\}$", re.MULTILINE)
COLORS = ("#62D7FF", "#AB98FF", "#63E9D0", "#8CACFF", "#D3A3FF")
DOMAIN_LABELS = {
    "foundation": "Foundation",
    "identity-governance": "Identity and governance",
    "storage": "Storage",
    "compute": "Compute",
    "networking": "Networking",
    "monitor-recovery": "Monitoring and recovery",
    "capstone": "Integrated capstone",
}


class VisualError(ValueError):
    """An authoritative source or requested visual is invalid."""


def escaped(value: Any) -> str:
    return html.escape(str(value), quote=True)


def wrapped(value: str, columns: int) -> list[str]:
    """Keep complete wording, including hyphenated service terms."""
    return textwrap.wrap(value, width=columns, break_long_words=False, break_on_hyphens=False)


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def read_labs() -> list[dict[str, Any]]:
    catalog = yaml.safe_load((ROOT / "labs" / "catalog.yml").read_text(encoding="utf-8"))
    entries = catalog.get("labs", [])
    if len(entries) != 28 or catalog.get("expectedLabCount") != 28:
        raise VisualError("The authoritative catalog must contain exactly 28 labs.")
    labs: list[dict[str, Any]] = []
    for entry in entries:
        lab_id = entry["labId"]
        folder = entry["folder"]
        if not re.fullmatch(r"LAB-\d{2}", lab_id) or not re.fullmatch(r"\d{2}-[a-z0-9-]+", folder):
            raise VisualError(f"Invalid lab ID or folder: {lab_id}, {folder}")
        directory = ROOT / "labs" / folder
        readme = (directory / "README.md").read_text(encoding="utf-8")
        metadata_text = (directory / "lab.yml").read_text(encoding="utf-8")
        metadata = yaml.safe_load(metadata_text)
        if metadata["id"] != lab_id or metadata["title"] != entry["title"]:
            raise VisualError(f"{lab_id}: catalog and lab metadata disagree.")
        titles = TASK_PATTERN.findall(readme)
        checkpoints = metadata.get("checkpoints", [])
        if len(titles) != 5 or len(checkpoints) != 5:
            raise VisualError(f"{lab_id}: expected exactly five task headings and checkpoints.")
        tasks = []
        for number, (heading_number, title, anchor_number) in enumerate(titles, start=1):
            checkpoint = checkpoints[number - 1]
            expected_id = f"LAB{lab_id[-2:]}-CP{number:02d}"
            if str(number) != heading_number or heading_number != anchor_number:
                raise VisualError(f"{lab_id}: task ordering or anchors disagree.")
            if checkpoint["title"] != title or checkpoint["id"] != expected_id:
                raise VisualError(f"{lab_id}: Task {number} does not match its checkpoint metadata.")
            if not set(checkpoint.get("objectiveIds", [])).issubset(set(metadata["objectives"])):
                raise VisualError(f"{lab_id}: unmapped checkpoint objective.")
            tasks.append({
                "number": number,
                "id": checkpoint["id"],
                "title": title,
                "anchor": f"#task-{number}",
                "purpose": checkpoint["purpose"],
                "expectedState": checkpoint["expectedState"],
                "objectiveIds": checkpoint["objectiveIds"],
            })
        source_hash = hashlib.sha256(
            (normalized(readme) + normalized(metadata_text) + json.dumps(entry, sort_keys=True)).encode("utf-8")
        ).hexdigest()
        labs.append({
            "labId": lab_id,
            "title": metadata["title"],
            "domain": metadata["domain"],
            "status": metadata["status"],
            "source": f"labs/{folder}/README.md",
            "metadataSource": f"labs/{folder}/lab.yml",
            "sourceSha256": source_hash,
            "tasks": tasks,
        })
    if {lab["labId"] for lab in labs} != {f"LAB-{number:02d}" for number in range(28)}:
        raise VisualError("The catalog must contain each lab from LAB-00 through LAB-27 exactly once.")
    return labs


def icon_kind(title: str) -> str:
    """Choose the visual subject from the actual task, without changing its meaning."""
    text = title.casefold()
    rules = (
        ("tools", ("toolchain", "tooling", "build and lint", "azcopy, identity")),
        ("context", ("sign in", "context", "graph access", "verified upn domain", "resolve the principal")),
        ("manifest", ("safe run id", "deterministic names", "state boundary")),
        ("cost", ("cost gates", "budget", "license capacity", "license denial", "approved sku")),
        ("alert", ("alert", "action group", "action-group", "suppression", "notification")),
        ("dns", ("dns", "hostname", "zone authority", "owned-domain")),
        ("replicate", ("replication", "replica", "source and destination", "paired-region")),
        ("backup", ("backup", "back up", "recovery point", "recover", "restore", "vault", "snapshot")),
        ("key", ("key", "sas", "rbac", "role", "authorization", "permission", "sspr", "assign reader", "access matrix")),
        ("shield", ("policy", "governance", "can not", "cannotdelete", "protection", "hardened", "https", "tls", "encryption")),
        ("network", ("subnet", "vnet", "network", "peering", "routing", "route", "nsg", "asg", "endpoint", "address-space")),
        ("scale", ("scale", "autoscale", "resilien", "availability", "worker count")),
        ("server", ("vm", "disk", "compute", "deallocated")),
        ("container", ("container", "registry", "image", "acr", "aci", "revision")),
        ("web", ("app service", "web app", "deployment slot", "staging", "ingress", "traffic")),
        ("storage", ("blob", "storage", "share", "account", "smb", "data")),
        ("code", ("bicep", "arm", "template", "change set", "deployment")),
        ("monitor", ("telemetry", "kql", "log analytics", "diagnostic", "metric", "monitor")),
        ("users", ("user", "guest", "group", "blair", "alex")),
        ("inspect", ("inventory", "reconcile", "readiness", "report", "matrix", "evidence", "inspect", "verify")),
    )
    for kind, words in rules:
        if any(word in text for word in words):
            return kind
    return "inspect"


def icon(kind: str, color: str, x: int, y: int) -> list[str]:
    """Original geometric symbols on a 100 by 100 local canvas."""
    shapes = {
        "tools": [
            '<rect x="11" y="17" width="78" height="56" rx="8"/>',
            '<path d="M23 33L34 42L23 51M43 52H59M34 84H66M50 73V84"/>',
            '<circle cx="80" cy="77" r="14" fill="#12253A"/>',
            '<path d="M75 77L79 81L86 73"/>',
        ],
        "context": [
            '<path d="M28 65H77C93 65 94 42 79 40C80 20 51 12 43 32C26 26 14 40 20 55C10 61 17 75 28 75"/>',
            '<circle cx="52" cy="49" r="8"/><path d="M39 66V63C39 51 65 51 65 63V66M44 88H64M54 76V88"/>',
        ],
        "manifest": [
            '<path d="M25 9H62L78 25V89H25ZM62 9V25H78"/>',
            '<path d="M38 39H65M38 52H65M38 65H52M38 78H49"/>',
            '<path d="M60 69L69 64L78 69V78L69 86L60 78Z" fill="#12253A"/>',
            '<path d="M65 74L68 77L73 71"/>',
        ],
        "cost": [
            '<path d="M13 65A37 37 0 0 1 87 65M18 62L25 57M29 38L34 45M50 29V38M73 38L67 45M83 60L75 57"/>',
            '<path d="M50 65L70 42M16 78H84"/><circle cx="50" cy="65" r="6"/>',
            '<circle cx="50" cy="88" r="7" fill="#12253A"/>',
        ],
        "users": [
            '<circle cx="50" cy="30" r="13"/><circle cx="20" cy="45" r="9"/><circle cx="80" cy="45" r="9"/>',
            '<path d="M29 82V70C29 44 71 44 71 70V82ZM5 80V70C5 54 25 51 32 64M95 80V70C95 54 75 51 68 64"/>',
        ],
        "key": [
            '<circle cx="35" cy="38" r="23"/><circle cx="35" cy="38" r="8"/>',
            '<path d="M52 54L84 86L94 76L84 66L78 72L71 65L77 59L68 50Z"/>',
        ],
        "shield": [
            '<path d="M50 10L84 25V49C84 71 66 87 50 94C34 87 16 71 16 49V25Z"/>',
            '<path d="M33 49L46 62L70 36M50 12V29"/>',
        ],
        "replicate": [
            '<ellipse cx="22" cy="24" rx="16" ry="7"/><path d="M6 24V68C6 78 38 78 38 68V24M6 46C6 56 38 56 38 46"/>',
            '<ellipse cx="78" cy="24" rx="16" ry="7"/><path d="M62 24V68C62 78 94 78 94 68V24M62 46C62 56 94 56 94 46"/>',
            '<path d="M41 35H59M52 29L59 35L52 41M59 63H41M48 57L41 63L48 69"/>',
        ],
        "backup": [
            '<path d="M19 37A34 34 0 1 1 13 64M18 19V38H37"/>',
            '<rect x="33" y="42" width="41" height="37" rx="7"/>',
            '<path d="M42 42V29C42 14 66 14 66 29V42M44 59L52 67L65 53"/>',
        ],
        "network": [
            '<path d="M24 25L50 50L78 22M50 50L23 79M50 50L80 78"/>',
            '<rect x="37" y="37" width="26" height="26" rx="7"/>',
            '<rect x="10" y="10" width="27" height="27" rx="6"/>',
            '<rect x="66" y="8" width="27" height="27" rx="6"/>',
            '<rect x="9" y="67" width="27" height="27" rx="6"/>',
            '<rect x="66" y="66" width="27" height="27" rx="6"/>',
        ],
        "dns": [
            '<circle cx="50" cy="40" r="30"/><ellipse cx="50" cy="40" rx="13" ry="30"/>',
            '<path d="M21 32H79M21 49H79M50 70V89M25 89H75M26 79V94M74 79V94"/>',
        ],
        "scale": [
            '<rect x="9" y="55" width="21" height="31" rx="4"/><rect x="39" y="39" width="21" height="47" rx="4"/>',
            '<rect x="69" y="21" width="21" height="65" rx="4"/><path d="M12 37L84 8M71 5L85 8L81 23"/>',
        ],
        "server": [
            '<rect x="21" y="10" width="58" height="80" rx="9"/><path d="M21 36H79M21 62H79M49 22H66M49 48H66M49 74H66"/>',
            '<circle cx="33" cy="23" r="3" fill="currentColor"/><circle cx="33" cy="49" r="3" fill="currentColor"/>',
            '<circle cx="33" cy="75" r="3" fill="currentColor"/>',
        ],
        "container": [
            '<path d="M50 8L84 28V71L50 92L16 71V28ZM16 28L50 49L84 28M50 49V92M34 18L68 38V58"/>',
            '<path d="M26 59L40 67M26 70L40 78"/>',
        ],
        "web": [
            '<rect x="7" y="15" width="86" height="67" rx="8"/><path d="M7 33H93M33 51L24 59L33 67M65 51L74 59L65 67M55 48L44 71"/>',
            '<circle cx="20" cy="24" r="2" fill="currentColor"/><circle cx="30" cy="24" r="2" fill="currentColor"/>',
            '<circle cx="40" cy="24" r="2" fill="currentColor"/>',
        ],
        "storage": [
            '<ellipse cx="50" cy="22" rx="35" ry="13"/><path d="M15 22V76C15 94 85 94 85 76V22M15 40C15 58 85 58 85 40M15 58C15 76 85 76 85 58"/>',
            '<circle cx="70" cy="78" r="3" fill="currentColor"/>',
        ],
        "code": [
            '<rect x="8" y="12" width="84" height="77" rx="8"/><path d="M8 30H92M35 47L22 58L35 69M65 47L78 58L65 69M58 41L44 77"/>',
            '<circle cx="20" cy="21" r="2" fill="currentColor"/><circle cx="29" cy="21" r="2" fill="currentColor"/>',
        ],
        "monitor": [
            '<rect x="8" y="14" width="84" height="61" rx="7"/><path d="M18 52H31L39 35L50 61L62 41L68 52H82M50 75V88M32 88H68"/>',
        ],
        "alert": [
            '<path d="M26 61V40C26 12 74 12 74 40V61L84 73H16ZM41 85C44 94 56 94 59 85M50 8V15"/>',
            '<path d="M11 24L5 18M89 24L95 18M50 36V49"/><circle cx="50" cy="59" r="2" fill="currentColor"/>',
        ],
        "inspect": [
            '<path d="M17 9H64L78 23V90H17ZM64 9V23H78M28 32H53M28 45H51M28 61L32 65L38 58M28 77L32 81L38 74"/>',
            '<circle cx="66" cy="57" r="15" fill="#12253A"/><path d="M76 69L91 84M60 57L65 62L73 51"/>',
        ],
    }
    return [
        f'    <g transform="translate({x} {y})" color="{color}" fill="none" stroke="currentColor" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round">',
        *[f"      {shape}" for shape in shapes[kind]],
        "    </g>",
    ]


def render(lab: dict[str, Any]) -> str:
    title_lines = wrapped(lab["title"], 33)
    header_height = 125 + len(title_lines) * 35
    card_height = 226
    gap = 34
    first_y = header_height + 22
    footer_y = first_y + 5 * (card_height + gap) - gap + 35
    height = footer_y + 124
    width = 640
    description = (
        f"{lab['title']}. Follow five checkpoints in lesson order. "
        + " ".join(f"Task {task['number']}, {task['id']}: {task['title']}." for task in lab["tasks"])
        + " Offline-validated curriculum. Consult the lesson for commands, approval gates, and cleanup."
    )
    metadata = {"renderer": RENDERER, **lab}
    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="roadmap-title roadmap-desc" data-lab-id="{escaped(lab["labId"])}">',
        f'  <title id="roadmap-title">{escaped(lab["labId"])} learning roadmap: {escaped(lab["title"])}</title>',
        f'  <desc id="roadmap-desc">{escaped(description)}</desc>',
        f'  <metadata>{escaped(json.dumps(metadata, sort_keys=True, ensure_ascii=False, separators=(",", ":")))}</metadata>',
        '  <defs>',
        '    <linearGradient id="canvas" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07101C"/><stop offset="1" stop-color="#101B30"/></linearGradient>',
        '    <linearGradient id="card" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#142239"/><stop offset="1" stop-color="#0D1727"/></linearGradient>',
        '    <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#4B688C" fill-opacity=".16"/></pattern>',
        '    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1L9 5L1 9" fill="none" stroke="#62D7FF" stroke-width="2"/></marker>',
        '  </defs>',
        '  <style>',
        '    text{font-family:Arial,Helvetica,sans-serif} .eyebrow{font-size:17px;font-weight:700;letter-spacing:1px;fill:#A7B8D1}',
        '    .heading{font-size:30px;font-weight:700;fill:#F1F6FF} .task-title{font-size:24px;font-weight:600;fill:#F1F6FF}',
        '    .checkpoint{font-size:17px;font-weight:700;letter-spacing:1px} .number{font-size:22px;font-weight:700;fill:#F1F6FF}',
        '    .hint{font-size:19px;fill:#B8C9E0} .small{font-size:16px;fill:#B8C9E0}',
        '  </style>',
        '  <rect width="100%" height="100%" rx="24" fill="url(#canvas)"/>',
        '  <rect width="100%" height="100%" rx="24" fill="url(#dots)"/>',
        '  <g aria-hidden="true">',
        '    <rect x="24" y="24" width="92" height="34" rx="10" fill="#29435D" stroke="#62D7FF" stroke-opacity=".6"/>',
        f'    <text x="70" y="47" class="checkpoint" text-anchor="middle" fill="#82E1FF">{escaped(lab["labId"])}</text>',
        '    <text x="133" y="47" class="eyebrow">YOUR CHECKPOINT ROADMAP</text>',
    ]
    for index, line in enumerate(title_lines):
        svg.append(f'    <text x="24" y="{100 + index * 35}" class="heading">{escaped(line)}</text>')
    svg.extend([
        f'    <text x="24" y="{header_height - 13}" class="hint">{escaped(DOMAIN_LABELS[lab["domain"]])} · 5 checkpoints</text>',
        f'    <path d="M24 {header_height + 3}H616" stroke="#2C405C"/>',
    ])
    for index, task in enumerate(lab["tasks"]):
        y = first_y + index * (card_height + gap)
        color = COLORS[index]
        lines = wrapped(task["title"], 28)
        if len(lines) > 5:
            raise VisualError(f"{lab['labId']} Task {task['number']}: title exceeds the readable card bounds.")
        if index:
            previous_y = first_y + (index - 1) * (card_height + gap)
            svg.append(f'    <path d="M42 {previous_y + 73}V{y + 20}" stroke="#62D7FF" stroke-width="2.5" stroke-opacity=".65" marker-end="url(#arrow)"/>')
        svg.extend([
            f'    <circle cx="42" cy="{y + 48}" r="22" fill="#192B43" stroke="{color}" stroke-width="2"/>',
            f'    <text x="42" y="{y + 56}" class="number" text-anchor="middle">{task["number"]}</text>',
            f'    <g data-task="{task["number"]}" data-checkpoint-id="{escaped(task["id"])}">',
            f'      <rect x="78" y="{y}" width="538" height="{card_height}" rx="20" fill="url(#card)" stroke="{color}" stroke-opacity=".47"/>',
            f'      <rect x="78" y="{y + 19}" width="4" height="{card_height - 38}" rx="2" fill="{color}"/>',
            f'      <circle cx="142" cy="{y + 111}" r="55" fill="{color}" fill-opacity=".065"/>',
            f'      <text x="204" y="{y + 34}" class="checkpoint" fill="{color}">{escaped(task["id"])}</text>',
        ])
        svg.extend(icon(icon_kind(task["title"]), color, 92, y + 61))
        for line_index, line in enumerate(lines):
            svg.append(f'      <text x="204" y="{y + 72 + line_index * 28}" class="task-title">{escaped(line)}</text>')
        objective_count = len(task["objectiveIds"])
        objective_label = f"{objective_count} mapped objective" + ("s" if objective_count != 1 else "")
        svg.extend([
            f'      <text x="204" y="{y + 209}" class="small">{escaped(objective_label)} · lesson {escaped(task["anchor"])}</text>',
            '    </g>',
        ])
    svg.extend([
        f'    <path d="M24 {footer_y}H616" stroke="#2C405C"/>',
        f'    <circle cx="36" cy="{footer_y + 29}" r="7" fill="#AB98FF"/>',
        f'    <text x="54" y="{footer_y + 35}" class="hint">Offline-validated · follow the lesson gates.</text>',
        f'    <text x="24" y="{footer_y + 69}" class="hint">Retain checkpoint evidence and verify cleanup.</text>',
        f'    <text x="24" y="{footer_y + 98}" class="small">Source: lab.yml checkpoints and README task headings</text>',
        '  </g>',
        '</svg>',
        '',
    ])
    return "\n".join(svg)


def run(check: bool, only: list[str]) -> int:
    labs = read_labs()
    if only:
        requested = {value.upper() if value.upper().startswith("LAB-") else f"LAB-{int(value):02d}" for value in only}
        unknown = requested - {lab["labId"] for lab in labs}
        if unknown:
            raise VisualError(f"Unknown lab selector: {', '.join(sorted(unknown))}")
        labs = [lab for lab in labs if lab["labId"] in requested]
    failures = 0
    for lab in labs:
        target = OUTPUT / f"{lab['labId']}-roadmap.svg"
        content = render(lab)
        if check:
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                print(f"FAIL  {target.relative_to(ROOT)} is stale; run python tools/render_learning_visuals.py")
                failures += 1
            else:
                print(f"PASS  {target.relative_to(ROOT)}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
            print(f"WRITE {target.relative_to(ROOT)}")
    if not only:
        unexpected = sorted(path.name for path in OUTPUT.glob("*-roadmap.svg") if path.stem.removesuffix("-roadmap") not in {lab["labId"] for lab in labs})
        if unexpected:
            raise VisualError(f"Unexpected roadmap output: {', '.join(unexpected)}")
    print(f"{'Checked' if check else 'Rendered'} {len(labs)} source-aligned checkpoint roadmaps; {failures} stale files.")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify committed SVG output byte for byte.")
    parser.add_argument("--only", action="append", default=[], metavar="LAB", help="Select one lab number or ID; repeat as needed.")
    args = parser.parse_args()
    try:
        return run(args.check, args.only)
    except (VisualError, ValueError, KeyError, OSError, yaml.YAMLError) as exc:
        print(f"FAIL  {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
