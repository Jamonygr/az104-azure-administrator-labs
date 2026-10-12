#!/usr/bin/env python3
"""Deterministically render original, accessible bootstrap and lifecycle visuals.

These drawings teach the existing lab instructions. They do not execute Azure
commands. Pictograms are original SVG code, not vendor logos or external assets.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "docs/site-assets/learning-visuals"
INK = "#ecf4ff"
MUTED = "#bac9e1"
CYAN = "#68dcff"
PURPLE = "#b9a0ff"
GREEN = "#7ee6b8"
RED = "#ff9cac"


def text(x: int, y: int, label: str, size: int = 28, color: str = INK,
         anchor: str = "middle", weight: int = 650) -> str:
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{html.escape(label)}</text>')


def lines(x: int, y: int, labels: list[str], size: int = 28,
          color: str = INK, anchor: str = "middle", weight: int = 650,
          gap: int = 36) -> str:
    return "".join(text(x, y + i * gap, value, size, color, anchor, weight)
                   for i, value in enumerate(labels))


def icon(name: str, x: int, y: int, color: str = CYAN, scale: float = 1) -> str:
    # Every icon occupies a 100 by 100 view; the caller places its center.
    shapes = {
        "terminal": '<rect x="9" y="16" width="82" height="65" rx="10"/><path d="M10 33H90M23 49l13 11-13 11M47 72H71"/><circle cx="22" cy="25" r="1"/><circle cx="31" cy="25" r="1"/>',
        "powershell": '<path d="M17 20H90L78 79H6Z"/><path d="M28 35l22 15-29 17M48 68H66"/>',
        "code": '<path d="M34 22H25v18L13 50l12 10v18h9M66 22h9v18l12 10-12 10v18h-9M56 29L43 71"/>',
        "transfer": '<path d="M12 33H77l-13-13M77 33L64 46M88 67H23l13 13M23 67l13-13"/><rect x="8" y="15" width="18" height="17" rx="3"/><rect x="74" y="68" width="18" height="17" rx="3"/>',
        "python": '<path d="M22 50V31q0-14 16-14h24q16 0 16 15v18H44q-12 0-12 11v16H21q-13 0-13-15v-3q0-9 14-9ZM78 50v19q0 14-16 14H38q-16 0-16-15V50h34q12 0 12-11V23h11q13 0 13 15v3q0 9-14 9Z"/><circle cx="42" cy="28" r="2"/><circle cx="58" cy="72" r="2"/>',
        "hex": '<path d="M50 8L87 29v42L50 92 13 71V29Z"/><path d="M33 68V32l34 36V32"/>',
        "person": '<circle cx="50" cy="30" r="16"/><path d="M17 84v-9q0-23 33-23t33 23v9Z"/>',
        "identity": '<rect x="7" y="18" width="86" height="66" rx="9"/><path d="M31 18V10h38v8M58 39H80M58 52H80M58 65H72"/><circle cx="31" cy="42" r="10"/><path d="M16 71v-4q0-12 15-12t15 12v4"/>',
        "file": '<path d="M24 9H61l20 20v62H24Z"/><path d="M61 9v21h20M36 44H67M36 57H67M36 70H56"/>',
        "tag": '<path d="M8 45L44 9h40v40L48 85Z"/><circle cx="68" cy="25" r="5"/><path d="M31 47l17 17M42 36l17 17"/>',
        "names": '<rect x="10" y="12" width="80" height="23" rx="5"/><rect x="10" y="42" width="80" height="23" rx="5"/><rect x="10" y="72" width="80" height="16" rx="5"/><path d="M21 24H58M21 54H72M21 80H48"/>',
        "pin": '<path d="M50 92S18 58 18 36a32 32 0 1 1 64 0C82 58 50 92 50 92Z"/><circle cx="50" cy="36" r="12"/>',
        "stack": '<path d="M50 12L9 32l41 20 41-20ZM9 49l41 20 41-20M9 66l41 20 41-20"/>',
        "gauge": '<path d="M12 73a40 40 0 1 1 76 0M50 26v9M23 38l7 7M77 38l-7 7M16 62h10M84 62H74M50 64l20-20"/><circle cx="50" cy="65" r="6"/><path d="M28 84H72"/>',
        "cleanup": '<path d="M16 27H84M28 27V16h44v11M23 28l6 58h42l6-58M40 40v33M59 40v33"/><path d="M83 59l10 7v15q0 11-10 17-10-6-10-17V66Z"/>',
        "checklist": '<rect x="18" y="12" width="65" height="79" rx="7"/><path d="M32 31l5 5 9-11M53 31H70M32 52l5 5 9-11M53 52H70M32 73l5 5 9-11M53 73H70"/>',
        "shield": '<path d="M50 7L85 20v29q0 27-35 44Q15 76 15 49V20Z"/><path d="M31 49l13 13 26-29"/>',
        "search": '<circle cx="43" cy="42" r="28"/><path d="M64 64L88 88M29 41H56M29 31H45M29 51H49"/>',
        "wrench": '<path d="M63 12a24 24 0 0 0-29 29L12 64a13 13 0 0 0 19 19l22-23a24 24 0 0 0 30-28L67 47 52 32Z"/><circle cx="23" cy="73" r="3"/>',
        "play": '<circle cx="50" cy="50" r="39"/><path d="M41 29L72 50 41 71Z"/>',
        "stop": '<path d="M29 10H71l19 19v42L71 90H29L10 71V29Z"/><path d="M33 33l34 34M67 33L33 67"/>',
        "report": '<path d="M19 9H63l18 18v64H19Z"/><path d="M63 9v20h18M32 47l7 7 13-15M58 48H69M32 69l7 7 13-15M58 70H69"/>',
    }
    return (f'<g transform="translate({x - 50 * scale:g} {y - 50 * scale:g}) scale({scale:g})" '
            f'fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" '
            f'stroke-linejoin="round">{shapes[name]}</g>')


def station(name: str, x: int, y: int, color: str = CYAN, radius: int = 65) -> str:
    return (f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#101f36" '
            f'stroke="{color}" stroke-opacity=".38" stroke-width="2"/>'
            + icon(name, x, y, color))


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = CYAN) -> str:
    return (f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" '
            'stroke-width="3" marker-end="url(#arrow)"/>')


def pill(x: int, y: int, width: int, label: str, color: str = CYAN,
         size: int = 26) -> str:
    return (f'<rect x="{x}" y="{y}" width="{width}" height="50" rx="25" '
            f'fill="#122139" stroke="{color}" stroke-opacity=".42"/>'
            + text(x + width // 2, y + 34, label, size, color))


def canvas(title: str, description: str, height: int, body: str,
           heading: list[str], subtitle: str) -> str:
    title_xml = html.escape(title)
    description_xml = html.escape(description)
    header = lines(350, 53, heading, 32, gap=39)
    sub_y = 53 + len(heading) * 39
    header += text(350, sub_y, subtitle, 22, MUTED, weight=400)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="700" '
        f'height="{height}" viewBox="0 0 700 {height}" role="img" '
        'aria-labelledby="title desc">\n'
        f'<title id="title">{title_xml}</title>\n'
        f'<desc id="desc">{description_xml}</desc>\n'
        '<defs><linearGradient id="canvas" x2="1" y2="1">'
        '<stop stop-color="#060c18"/><stop offset="1" stop-color="#0b182c"/>'
        '</linearGradient><marker id="arrow" markerWidth="9" markerHeight="9" '
        'refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0 0L9 4.5L0 9Z" fill="#68dcff"/></marker></defs>\n'
        f'<rect width="700" height="{height}" rx="28" fill="url(#canvas)"/>\n'
        f'<rect x="16" y="16" width="668" height="{height - 32}" rx="22" '
        'fill="none" stroke="#294460" stroke-width="1"/>\n'
        '<g font-family="Segoe UI, Arial, sans-serif">' + header + body + '</g>\n</svg>\n'
    )


def setup_tools() -> str:
    items = [
        ("powershell", "PowerShell", "pwsh", CYAN),
        ("terminal", "Azure CLI", "az version", PURPLE),
        ("code", "Bicep", "az bicep version", CYAN),
        ("transfer", "AzCopy", "azcopy --version", PURPLE),
        ("python", "Python", "python --version", CYAN),
        ("hex", "Node", "node --version", PURPLE),
    ]
    body = ""
    for i, (symbol, label, command, color) in enumerate(items):
        x = 190 if i % 2 == 0 else 510
        y = 220 + (i // 2) * 225
        body += station(symbol, x, y, color)
        body += text(x, y + 104, label)
        body += text(x, y + 140, command, 22, MUTED, weight=400)
    body += pill(60, 852, 580, "Inspect versions and the intended PATH")
    return canvas(
        "Task 1: inspect the local toolchain",
        "Six original tool pictograms represent PowerShell, Azure CLI, Bicep, "
        "AzCopy, Python, and Node. Read their versions from the intended PATH; "
        "version discovery does not install tools or deploy Azure resources.",
        935, body, ["Check your local toolchain"], "Task 1 · discover versions, then record evidence",
    )


def setup_context() -> str:
    body = station("person", 130, 220)
    body += lines(250, 211, ["Sign in deliberately"], anchor="start")
    body += text(250, 249, "az login", 22, MUTED, "start", 400)
    body += arrow(130, 288, 130, 342)
    body += station("identity", 130, 410, PURPLE)
    body += lines(250, 377, ["Inspect cached context"], anchor="start")
    body += lines(250, 417, ["az account show", "Cloud · tenant · subscription"],
                  22, MUTED, "start", 400, 32)
    body += arrow(130, 478, 130, 532)
    body += station("shield", 130, 600)
    body += lines(250, 565, ["Compare the intended", "Azure context"], anchor="start")
    body += text(250, 646, "AzureCloud + approved subscription", 21, MUTED, "start", 400)
    body += '<path d="M130 670V721H510" fill="none" stroke="#68dcff" stroke-width="3"/>'
    body += arrow(190, 721, 190, 765)
    body += arrow(510, 721, 510, 765)
    body += station("shield", 190, 818, GREEN, 50)
    body += station("stop", 510, 818, RED, 50)
    body += lines(190, 900, ["Match: continue"], 26, GREEN)
    body += lines(510, 900, ["Mismatch: stop"], 26, RED)
    body += text(350, 950, "Select the approved context yourself, then recheck.", 23, MUTED, weight=400)
    return canvas(
        "Task 2: deliberately confirm Azure context",
        "Sign in deliberately, read the cached Azure CLI cloud, tenant, and "
        "subscription, and compare the active context with the intended sandbox. "
        "A match allows readiness checks to continue; a mismatch stops before "
        "mutation. Select the approved context yourself and recheck.",
        990, body, ["Know which Azure context", "your commands will use"], "Task 2 · inspect before any change",
    )


def setup_ownership() -> str:
    body = station("tag", 180, 235)
    body += lines(180, 335, ["Unique run ID"], 28)
    body += text(180, 371, "Lowercase + never reused", 21, MUTED, weight=400)
    body += station("names", 520, 235, PURPLE)
    body += lines(520, 335, ["Deterministic names"], 26)
    body += text(520, 371, "Predictable per-run names", 21, MUTED, weight=400)
    body += '<path d="M180 391V432H350M520 391V432H350" fill="none" stroke="#68dcff" stroke-width="3"/>'
    body += arrow(350, 432, 350, 474)
    body += station("file", 350, 545, CYAN, 70)
    body += text(350, 654, "run.json", 32)
    body += text(350, 692, ".state/&lt;run-id&gt;/run.json".replace("&lt;", "<").replace("&gt;", ">"), 26, MUTED, weight=400)
    body += text(350, 739, "Match lab ID + run ID exactly", 27, CYAN)
    body += pill(60, 779, 580, "Ownership tags: purpose · labId · runId", PURPLE, 24)
    body += text(350, 870, "Ignored local state · keep credentials out", 25, MUTED, weight=400)
    return canvas(
        "Task 3: establish a run ownership boundary",
        "A unique lowercase run ID determines names and ownership tags. The "
        "ignored local .state/run-id/run.json manifest must already exist and "
        "match the lab ID and run ID. Tags identify purpose, labId, and runId. "
        "The manifest is a local ownership record, not an Azure deployment.",
        910, body, ["Give this run a safe boundary"], "Task 3 · names, tags, and an ignored manifest",
    )


def setup_cost_cleanup() -> str:
    body = ""
    items = [
        ("pin", 180, 220, ["Approved region"], "Check availability", CYAN),
        ("stack", 520, 220, ["Provider readiness"], "Inspect registration state", PURPLE),
        ("gauge", 180, 485, ["Cost + capacity"], "Review SKU and quota gates", PURPLE),
        ("cleanup", 520, 485, ["Cleanup rehearsal"], "Inspect exact run targets", CYAN),
    ]
    for symbol, x, y, labels, detail, color in items:
        body += station(symbol, x, y, color)
        body += lines(x, y + 103, labels, 27)
        body += text(x, y + 138, detail, 21, MUTED, weight=400)
    body += pill(60, 700, 580, "Run-tag inventory: [ ] for bootstrap", GREEN, 25)
    body += lines(350, 805, ["Inspect only; do not claim or remove", "unrelated Azure resources."], 26, MUTED, weight=400)
    return canvas(
        "Task 4: review cost and cleanup before deployment",
        "Inspect the approved region, provider registration states, SKU and "
        "quota cost gates, and exact run-tag inventory. Lab 00 creates no Azure "
        "resources, so its run-owned inventory should be empty. Do not register "
        "providers or delete a conflicting resource automatically.",
        895, body, ["Rehearse cost and cleanup"], "Task 4 · read-only discovery before billable labs",
    )


def setup_readiness() -> str:
    body = station("checklist", 130, 230)
    body += lines(250, 188, ["Required prerequisites"], 27, anchor="start")
    body += lines(250, 229, ["Tools · CLI sign-in · Bicep", "Extensions · region · lab inputs"],
                  22, MUTED, "start", 400, 34)
    body += arrow(130, 298, 130, 365)
    body += station("terminal", 130, 435, PURPLE)
    body += lines(250, 416, ["Run readiness"], 28, anchor="start")
    body += text(250, 457, "Test-LabEnvironment.ps1", 22, MUTED, "start", 400)
    body += arrow(130, 503, 130, 570)
    body += station("report", 130, 640)
    body += lines(250, 600, ["Inspect every result"], 28, anchor="start")
    body += lines(250, 643, [".state/readiness.json", "Keep the non-secret report"],
                  22, MUTED, "start", 400, 34)
    body += pill(60, 763, 580, "All required checks must pass", GREEN)
    body += lines(350, 861, ["Required failure? Resolve the named", "prerequisite and rerun readiness."], 25, MUTED, weight=400)
    return canvas(
        "Task 5: interpret the blocking readiness report",
        "Check required tools, Azure CLI sign-in, Bicep, extensions, region, "
        "and lab prerequisites. Run Test-LabEnvironment.ps1 and inspect the "
        "ignored .state/readiness.json report. Every required check must pass. "
        "Resolve any named failure deliberately and rerun the readiness check.",
        955, body, ["Read every readiness result"], "Task 5 · a required failure blocks progress",
    )


def safe_run_loop() -> str:
    stages = [
        ("search", "Preview + preflight", ["Inspect context and inputs"], CYAN),
        ("play", "Explicit execution", ["-Execute + required", "acknowledgements"], PURPLE),
        ("checklist", "Read back + validate", ["Check expected live state"], CYAN),
        ("cleanup", "Owned cleanup", ["Exact manifest IDs only"], PURPLE),
        ("report", "Residual audit", ["Record active and retained items"], GREEN),
    ]
    body = ""
    for i, (symbol, label, detail, color) in enumerate(stages):
        y = 210 + i * 185
        body += station(symbol, 125, y, color, 62)
        body += text(235, y - 7, label, 28, INK, "start")
        body += lines(235, y + 34, detail, 22, MUTED, "start", 400, 31)
        if i < len(stages) - 1:
            body += arrow(125, y + 66, 125, y + 117)
    body += lines(350, 1093, ["Read-only labs make no Azure changes.", "Follow the selected lab’s cost and tenant gates."], 24, MUTED, weight=400)
    return canvas(
        "Safe lab lifecycle from preview to residual audit",
        "The learning sequence is preview and preflight, explicit execution "
        "with required cost or tenant acknowledgements, independent readback "
        "and validation, scoped cleanup of manifest-owned targets, and a "
        "residual audit documenting active and retained items. Read-only labs "
        "make no Azure changes. Arrows show learning order, not Azure traffic.",
        1180, body, ["The safe run lifecycle"], "Preview is the default for mutating commands",
    )


def troubleshoot_loop() -> str:
    stages = [
        ("report", "Observe the failure", "Retain redacted evidence", CYAN),
        ("search", "Diagnose one cause", "Compare read-only queries", PURPLE),
        ("wrench", "Apply a small repair", "Resolve one fault at a time", CYAN),
        ("checklist", "Repeat the same check", "Prove before + after state", GREEN),
    ]
    body = ""
    for i, (symbol, label, detail, color) in enumerate(stages):
        y = 210 + i * 190
        body += station(symbol, 125, y, color, 62)
        body += text(235, y - 8, label, 28, INK, "start")
        body += text(235, y + 34, detail, 22, MUTED, "start", 400)
        if i < len(stages) - 1:
            body += arrow(125, y + 66, 125, y + 122)
    body += '<path d="M602 785H652V212H596" fill="none" stroke="#b9a0ff" stroke-width="3" stroke-dasharray="7 7" marker-end="url(#arrow)"/>'
    body += pill(60, 889, 580, "Still failing? Observe and diagnose again", PURPLE, 24)
    return canvas(
        "Troubleshooting loop: observe, diagnose, repair, and reverify",
        "Observe a failed check and retain redacted evidence. Diagnose one "
        "cause with read-only queries, apply a small repair, then repeat the "
        "same check and retain before and after evidence. If it still fails, "
        "return to diagnosis. Do not inject another fault before removing the first.",
        985, body, ["Make the break/fix teach you"], "One symptom, one cause, one verified repair",
    )


def cleanup_boundary() -> str:
    body = station("file", 350, 220, CYAN, 67)
    body += text(350, 326, "Manifest IDs + active context", 28)
    body += arrow(350, 346, 350, 385)
    body += station("shield", 350, 455, PURPLE, 65)
    body += text(350, 559, "Verify exact ownership", 28)
    body += text(350, 596, "Lab ID · run ID · proof for each target", 23, MUTED, weight=400)
    body += '<path d="M350 614V645H170M350 645H530" fill="none" stroke="#68dcff" stroke-width="3"/>'
    body += arrow(170, 645, 170, 685)
    body += arrow(530, 645, 530, 685)
    body += station("cleanup", 170, 750, GREEN, 60)
    body += station("stop", 530, 750, RED, 60)
    body += lines(170, 848, ["This run only"], 28, GREEN)
    body += lines(530, 848, ["Refuse unrelated"], 26, RED)
    body += arrow(170, 869, 170, 916)
    body += '<path d="M170 916H350" fill="none" stroke="#68dcff" stroke-width="3"/>'
    body += arrow(350, 916, 350, 946)
    body += station("report", 350, 1010, CYAN, 59)
    body += text(350, 1107, "Query residuals → cleanup.json", 28)
    body += lines(350, 1162, ["Report active, retained, or soft-deleted items.", "Irreversible purge is never automated."], 24, MUTED, weight=400)
    return canvas(
        "Cleanup boundary: approved run only, with residual evidence",
        "Cleanup compares the manifest identity, active Azure context, exact "
        "target IDs, and each target’s ownership proof before any mutation. "
        "It cleans only the approved run and refuses unrelated targets. "
        "After cleanup it queries residuals and records active, retained, or "
        "soft-deleted items in cleanup.json. It never automates irreversible purge.",
        1250, body, ["Keep cleanup inside", "the owned run boundary"], "Preview targets; use -Execute only after review",
    )


DRAWINGS = {
    "setup-tools.svg": setup_tools,
    "setup-context.svg": setup_context,
    "setup-ownership.svg": setup_ownership,
    "setup-cost-cleanup.svg": setup_cost_cleanup,
    "setup-readiness.svg": setup_readiness,
    "safe-run-loop.svg": safe_run_loop,
    "troubleshoot-loop.svg": troubleshoot_loop,
    "cleanup-boundary.svg": cleanup_boundary,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if an SVG differs from its renderer.")
    args = parser.parse_args()
    stale = []
    if not args.check:
        DESTINATION.mkdir(parents=True, exist_ok=True)
    for name, draw in DRAWINGS.items():
        expected = draw()
        target = DESTINATION / name
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != expected:
                stale.append(name)
        else:
            target.write_text(expected, encoding="utf-8", newline="\n")
    if stale:
        print("Setup/lifecycle SVGs need regeneration: " + ", ".join(stale))
        return 1
    print(f"{'Checked' if args.check else 'Rendered'} {len(DRAWINGS)} setup/lifecycle SVGs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
