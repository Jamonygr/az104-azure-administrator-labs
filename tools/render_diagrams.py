#!/usr/bin/env python3
"""Render the repository's Mermaid flowcharts as deterministic accessible SVG.

The curriculum deliberately uses a small, documented Mermaid subset: left-to-right
flowcharts, labelled directed edges, class definitions, and class assignments.  A
repository-owned renderer keeps generated SVG byte-for-byte stable without a
browser, network access, fonts, or an unpinned JavaScript dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import html
import json
import re
import sys
import textwrap
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB_PATTERN = re.compile(r"^\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
RENDERER_ID = "az104-mermaid-flowchart-svg/2.0.0"


class DiagramError(ValueError):
    """Raised when a diagram uses syntax outside the deterministic subset."""


@dataclass
class Node:
    identifier: str
    label: str
    shape: str = "rect"
    class_name: str | None = None
    order: int = 0
    rank: int = 0
    x: float = 0
    y: float = 0
    width: float = 260
    height: float = 68
    lines: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    label: str = ""


@dataclass
class Diagram:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    styles: dict[str, dict[str, str]] = field(default_factory=dict)


def normalized_source(text: str) -> str:
    """Normalize only transport-level differences before hashing the source."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def clean_label(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def parse_node(expression: str, diagram: Diagram) -> str:
    expression = expression.strip().rstrip(";").strip()
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*)(.*)", expression)
    if not match:
        raise DiagramError(f"unsupported node expression: {expression!r}")
    identifier, descriptor = match.groups()
    label = identifier
    shape = "rect"
    descriptor = descriptor.strip()
    if descriptor:
        if descriptor.startswith("([") and descriptor.endswith("])"):
            label = descriptor[2:-2]
            shape = "stadium"
        elif descriptor.startswith("[(") and descriptor.endswith(")]"):
            label = descriptor[2:-2]
            shape = "database"
        elif descriptor.startswith("[") and descriptor.endswith("]"):
            label = descriptor[1:-1]
        else:
            raise DiagramError(f"unsupported shape for node {identifier}: {descriptor!r}")
        label = clean_label(label)
    existing = diagram.nodes.get(identifier)
    if existing is None:
        diagram.nodes[identifier] = Node(
            identifier=identifier,
            label=label,
            shape=shape,
            order=len(diagram.nodes),
        )
    elif descriptor:
        existing.label = label
        existing.shape = shape
    return identifier


def parse_mermaid(text: str) -> Diagram:
    source = normalized_source(text)
    lines = source.splitlines()
    first_index = next(
        (index for index, line in enumerate(lines) if line.strip() and not line.lstrip().startswith("%%")),
        None,
    )
    if first_index is None or not re.fullmatch(r"flowchart\s+LR", lines[first_index].strip(), re.I):
        raise DiagramError("architecture diagrams must begin with 'flowchart LR'")

    diagram = Diagram()
    class_assignments: list[tuple[list[str], str]] = []
    edge_pattern = re.compile(r"^(.*?)\s*-->\s*(?:\|([^|]*)\|\s*)?(.*?)\s*;?$")
    for number, raw_line in enumerate(lines[first_index + 1 :], start=first_index + 2):
        line = raw_line.strip()
        if not line or line.startswith("%%"):
            continue
        if line.startswith("classDef "):
            match = re.fullmatch(r"classDef\s+([A-Za-z_][\w-]*)\s+(.+?)\s*;?", line)
            if not match:
                raise DiagramError(f"line {number}: invalid classDef")
            name, declarations = match.groups()
            style: dict[str, str] = {}
            for declaration in declarations.rstrip(";").split(","):
                if ":" not in declaration:
                    raise DiagramError(f"line {number}: invalid style declaration {declaration!r}")
                key, value = declaration.split(":", 1)
                key = key.strip()
                if key not in {"fill", "stroke", "color"}:
                    raise DiagramError(f"line {number}: unsupported style property {key!r}")
                style[key] = value.strip()
            diagram.styles[name] = style
            continue
        if line.startswith("class "):
            match = re.fullmatch(r"class\s+([A-Za-z0-9_,-]+)\s+([A-Za-z_][\w-]*)\s*;?", line)
            if not match:
                raise DiagramError(f"line {number}: invalid class assignment")
            class_assignments.append((match.group(1).split(","), match.group(2)))
            continue
        edge_match = edge_pattern.fullmatch(line)
        if edge_match:
            source_expression, label, target_expression = edge_match.groups()
            source_id = parse_node(source_expression, diagram)
            target_id = parse_node(target_expression, diagram)
            diagram.edges.append(Edge(source_id, target_id, clean_label(label or "")))
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*(?:\(\[.*\]\)|\[\(.*\)\]|\[.*\])", line):
            parse_node(line, diagram)
            continue
        raise DiagramError(f"line {number}: unsupported Mermaid syntax: {line!r}")

    if not diagram.nodes or not diagram.edges:
        raise DiagramError("a diagram must contain at least one node and one directed edge")
    for identifiers, class_name in class_assignments:
        if class_name not in diagram.styles:
            raise DiagramError(f"class {class_name!r} has no classDef")
        for identifier in identifiers:
            if identifier not in diagram.nodes:
                raise DiagramError(f"class assignment references unknown node {identifier!r}")
            diagram.nodes[identifier].class_name = class_name
    return diagram


def wrap_label(label: str, width: int = 20) -> list[str]:
    """Respect source line breaks while keeping every source word readable."""
    return [line for paragraph in label.splitlines() for line in textwrap.wrap(
        paragraph, width=width, break_long_words=False, break_on_hyphens=False
    )] or [label]


def assign_layout(diagram: Diagram) -> tuple[int, int]:
    """Lay out the original LR ranks in bands of at most four columns."""
    adjacency: dict[str, list[str]] = {identifier: [] for identifier in diagram.nodes}
    incoming = {identifier: 0 for identifier in diagram.nodes}
    for edge in diagram.edges:
        adjacency[edge.source].append(edge.target)
        incoming[edge.target] += 1
    ordered = sorted(diagram.nodes.values(), key=lambda node: node.order)
    roots = [node.identifier for node in ordered if incoming[node.identifier] == 0] or [ordered[0].identifier]
    distance: dict[str, int] = {}
    queue: deque[str] = deque()
    for root in roots:
        distance[root] = 0
        queue.append(root)
    while queue:
        source = queue.popleft()
        for target in adjacency[source]:
            candidate = distance[source] + 1
            if target not in distance or candidate < distance[target]:
                distance[target] = candidate
                queue.append(target)
    for node in ordered:
        if node.identifier not in distance:
            distance[node.identifier] = 0
            queue.append(node.identifier)
            while queue:
                source = queue.popleft()
                for target in adjacency[source]:
                    if target not in distance:
                        distance[target] = distance[source] + 1
                        queue.append(target)

    columns: dict[int, list[Node]] = {}
    for node in ordered:
        node.rank = distance[node.identifier]
        node.lines = wrap_label(node.label)
        node.width = 330
        node.height = max(124, len(node.lines) * 24 + 40)
        columns.setdefault(node.rank, []).append(node)
    row_gap, column_gap = 96, 180
    y_offset = 176
    maximum_rank = max(columns)
    for band in range(maximum_rank // 4 + 1):
        band_columns = {rank: nodes for rank, nodes in columns.items() if rank // 4 == band}
        band_height = max(sum(node.height for node in nodes) + row_gap * (len(nodes) - 1)
                          for nodes in band_columns.values())
        for rank, nodes in sorted(band_columns.items()):
            group_height = sum(node.height for node in nodes) + row_gap * (len(nodes) - 1)
            y = y_offset + (band_height - group_height) / 2
            for node in nodes:
                node.x = 88 + (rank % 4) * (node.width + column_gap)
                node.y = y
                y += node.height + row_gap
        y_offset += band_height + 144
    used_columns = min(4, maximum_rank + 1)
    width = int(176 + used_columns * 330 + (used_columns - 1) * column_gap)
    height = int(y_offset - 144 + 104)
    return width, height


# Original small vector forms rather than Microsoft product logos. These are
# decorative symbols; source labels and accessible descriptions retain meaning.
ICON_FORMS = {
    'person': '<circle cx="32" cy="18" r="9"/><path d="M14 54v-8a18 18 0 0 1 36 0v8z"/><path d="M32 37v17"/>',
    'identity': '<rect x="8" y="9" width="48" height="45" rx="8"/><circle cx="25" cy="25" r="6"/><path d="M15 43a10 10 0 0 1 20 0M41 23h7M41 32h7M41 41h7"/>',
    'group': '<circle cx="22" cy="22" r="7"/><circle cx="45" cy="24" r="6"/><path d="M8 53V43a14 14 0 0 1 28 0v10M40 39a11 11 0 0 1 17 10v4"/>',
    'scope': '<path d="M8 20h18l6 7h24v27H8z"/><path d="M8 20V10h21l6 7h21v10M20 39h24M20 46h15"/>',
    'storage': '<ellipse cx="32" cy="13" rx="22" ry="8"/><path d="M10 13v37c0 11 44 11 44 0V13M10 27c0 11 44 11 44 0M10 40c0 11 44 11 44 0"/>',
    'files': '<path d="M10 20h18l6 7h22v27H10z"/><path d="M17 13h25l10 10M29 36h17M29 44h17"/><rect x="18" y="34" width="5" height="13" rx="2"/>',
    'vm': '<rect x="7" y="9" width="50" height="35" rx="5"/><path d="M24 44v9M40 44v9M16 54h32M14 17h36M14 24h22M14 31h14"/><circle cx="47" cy="36" r="2"/>',
    'scale': '<rect x="6" y="22" width="19" height="28" rx="3"/><rect x="27" y="14" width="19" height="36" rx="3"/><path d="M48 9h9v41h-9M11 32h9M11 39h9M32 24h9M32 32h9M32 40h9"/>',
    'container': '<path d="M32 7L55 20v26L32 59 9 46V20zM9 20l23 14 23-14M32 34v25"/><path d="M20 14l23 13M43 14L20 27"/>',
    'app': '<rect x="7" y="9" width="50" height="46" rx="6"/><path d="M7 21h50M15 15h1M22 15h1M19 32l-7 7 7 7M45 32l7 7-7 7M36 28l-8 23"/>',
    'network': '<rect x="24" y="25" width="16" height="14" rx="3"/><circle cx="12" cy="12" r="6"/><circle cx="52" cy="12" r="6"/><circle cx="12" cy="52" r="6"/><circle cx="52" cy="52" r="6"/><path d="M17 17l8 8M47 17l-8 8M17 47l8-8M47 47l-8-8"/>',
    'route': '<path d="M9 17h33l10 10M42 17l-8-8M42 17l-8 8M55 47H22L12 37M22 47l8-8M22 47l8 8"/><circle cx="8" cy="17" r="3"/><circle cx="56" cy="47" r="3"/>',
    'dns': '<circle cx="32" cy="32" r="24"/><ellipse cx="32" cy="32" rx="11" ry="24"/><path d="M9 25h46M9 39h46M32 8v48"/>',
    'balance': '<rect x="23" y="6" width="18" height="14" rx="3"/><rect x="5" y="44" width="18" height="14" rx="3"/><rect x="41" y="44" width="18" height="14" rx="3"/><path d="M32 20v10H14v14M32 30h18v14M10 52h8M46 52h8"/>',
    'shield': '<path d="M32 6l22 9v17c0 13-9 23-22 29C19 55 10 45 10 32V15z"/><path d="M22 33l7 7 15-17"/>',
    'key': '<circle cx="23" cy="23" r="13"/><circle cx="23" cy="23" r="4"/><path d="M33 33l23 23M43 43l7-7M50 50l7-7"/>',
    'lock': '<rect x="13" y="28" width="38" height="30" rx="5"/><path d="M21 28V19a11 11 0 0 1 22 0v9"/><circle cx="32" cy="40" r="3"/><path d="M32 43v7"/>',
    'monitor': '<rect x="6" y="10" width="52" height="40" rx="5"/><path d="M11 34h10l5-13 10 23 5-10h12M24 50v7M40 50v7M18 58h28"/>',
    'alert': '<path d="M17 43V27a15 15 0 0 1 30 0v16l6 7H11zM26 55a6 6 0 0 0 12 0M32 12V6"/><path d="M7 23l5-5M57 23l-5-5"/>',
    'recovery': '<path d="M14 21a23 23 0 1 1-3 24M14 21V8M14 21H2"/><path d="M32 18v16l11 7"/>',
    'vault': '<rect x="8" y="7" width="48" height="50" rx="7"/><circle cx="32" cy="32" r="14"/><circle cx="32" cy="32" r="4"/><path d="M32 18v10M32 36v10M18 32h10M36 32h10M12 19h3M12 45h3"/>',
    'cost': '<path d="M10 54V35h10v19M27 54V24h10v30M44 54V12h10v42"/><path d="M9 18l18-7 14 4 13-9"/>',
    'code': '<path d="M22 18L8 32l14 14M42 18l14 14-14 14M37 9L27 55"/>',
    'check': '<circle cx="32" cy="32" r="24"/><path d="M18 32l9 10 20-23"/>',
    'cleanup': '<path d="M14 18h36M25 11h14M18 18l3 38h22l3-38M27 26v22M37 26v22"/>',
    'manifest': '<path d="M15 6h25l10 10v42H15zM40 6v13h10M23 29h19M23 38h19M23 47h11"/>',
    'cloud': '<path d="M18 48h29a13 13 0 0 0 1-26A18 18 0 0 0 14 25a12 12 0 0 0 4 23z"/>',
}


def service_icon(node: Node) -> tuple[str, str]:
    """Choose a symbolic form from the unmodified service label."""
    label = node.label.casefold().replace('\n', ' ')
    choices = [
        ('cleanup', ('cleanup', 'residual audit')),
        ('check', ('assert', 'validation', 'required tools', 'version and dependency')),
        ('manifest', ('run.json', 'run manifest', 'matrix', 'report', 'evidence')),
        ('lock', ('lock',)),
        ('key', (' key', 'sas', 'kerberos', 'encryption', 'certificate', 'tls')),
        ('vault', ('vault',)),
        ('recovery', ('backup', 'restore', 'recovery', 'replication', 'failover', 'soft delete', 'snapshot')),
        ('balance', ('load balan', 'backend pool', 'frontend', 'health probe', 'outbound rule')),
        ('dns', ('dns', ' a record', 'cname', 'hostname', 'public ip', ' ns delegation')),
        ('shield', ('nsg', 'firewall', 'policy', 'role definition', 'reader definition', 'denial', 'denied', 'acrpull', 'consent', 'rbac', 'role matrix', 'share contributor', 'contributor assignment')),
        ('alert', ('alert', 'action group', 'receiver', 'budget email', 'processing rule')),
        ('cost', ('budget', 'advisor', 'cost')),
        ('scale', ('scale set', 'autoscale', 'scale assertions', 'availability set')),
        ('vm', (' vm', 'vm ', 'virtual machine', 'workload vm', 'os disk', 'data disk', 'source vm')),
        ('container', ('container instance', 'container apps', 'acr ', 'registry', 'image', 'revision')),
        ('app', ('app service', 'slot', 'externally ingressed app')),
        ('monitor', ('log analytics', 'kql', 'metric', 'diagnostic', 'monitor', 'transaction')),
        ('files', ('file share', 'smb', 'blob container', 'source container', 'destination container', 'uploaded blob')),
        ('storage', ('storage', 'storagev2', 'account', 'cache ', 'redundancy', 'sku inventory')),
        ('route', ('peering', 'route', 'mapping', 'move', 'resize', 'swap')),
        ('network', ('vnet', 'virtual network', 'subnet', 'nic', 'endpoint', 'asg', 'fabric', 'bastion', 'network')),
        ('scope', ('resource group', 'subscription', 'management group', 'tenant root', 'tags')),
        ('group', ('security group',)),
        ('identity', ('graph', 'identity', 'principal', 'guest', 'cloud user', 'registration', 'sku capacity')),
        ('code', ('bicep', 'build', 'source', 'export', 'deployment', 'cli', 'initializer', 'what-if')),
        ('person', ('operator', 'administrator', 'learner', 'client', 'workstation')),
    ]
    kind = next((kind for kind, terms in choices if any(term in label for term in terms)), 'cloud')
    purple = {'identity', 'group', 'shield', 'key', 'lock', 'vault', 'recovery', 'scope', 'code'}
    cyan = {'network', 'route', 'dns', 'balance', 'monitor', 'alert', 'check', 'storage', 'files'}
    accent = '#B8A4FF' if kind in purple else '#5BE1EF' if kind in cyan else '#69AFFF'
    return kind, accent


def node_shape(node: Node, style: dict[str, str]) -> list[str]:
    kind, accent = service_icon(node)
    center_y = node.y + node.height / 2
    text_y = center_y - (len(node.lines) - 1) * 12
    output = [
        f'    <g id="node-{node.identifier}" data-service-icon="{kind}">',
        f'      <rect x="{node.x:g}" y="{node.y:g}" width="{node.width:g}" height="{node.height:g}" rx="20" fill="url(#card-fill)" stroke="{accent}" stroke-opacity=".64"/>',
        f'      <rect x="{node.x + 16:g}" y="{center_y - 39:g}" width="78" height="78" rx="20" fill="{accent}" fill-opacity=".10"/>',
        f'      <g transform="translate({node.x + 23:g} {center_y - 32:g})" fill="none" stroke="{accent}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">{ICON_FORMS[kind]}</g>',
    ]
    for index, line in enumerate(node.lines):
        output.append(f'      <text x="{node.x + 110:g}" y="{text_y + index * 24:g}" class="node-label">{html.escape(line)}</text>')
    output.append('    </g>')
    return output


def segment_clear(a: tuple[float, float], b: tuple[float, float], nodes: list[Node]) -> bool:
    """Reject orthogonal segments that cross a card or its breathing room."""
    for node in nodes:
        left, right = node.x - 12, node.x + node.width + 12
        top, bottom = node.y - 12, node.y + node.height + 12
        if a[1] == b[1] and top < a[1] < bottom:
            if max(min(a[0], b[0]), left) < min(max(a[0], b[0]), right):
                return False
        elif a[0] == b[0] and left < a[0] < right:
            if max(min(a[1], b[1]), top) < min(max(a[1], b[1]), bottom):
                return False
    return True


def compact_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result = []
    for point in points:
        if result and result[-1] == point:
            continue
        while len(result) >= 2 and ((result[-2][0] == result[-1][0] == point[0]) or
                                    (result[-2][1] == result[-1][1] == point[1])):
            result.pop()
        result.append(point)
    return result


def rounded_path(points: list[tuple[float, float]]) -> str:
    chunks = [f'M {points[0][0]:g} {points[0][1]:g}']
    for index in range(1, len(points) - 1):
        previous, corner, following = points[index - 1:index + 2]
        before = abs(corner[0] - previous[0]) + abs(corner[1] - previous[1])
        after = abs(following[0] - corner[0]) + abs(following[1] - corner[1])
        radius = min(12, before / 2, after / 2)
        enter = (corner[0] + (previous[0] - corner[0]) / before * radius,
                 corner[1] + (previous[1] - corner[1]) / before * radius)
        leave = (corner[0] + (following[0] - corner[0]) / after * radius,
                 corner[1] + (following[1] - corner[1]) / after * radius)
        chunks.extend([f'L {enter[0]:g} {enter[1]:g}',
                       f'Q {corner[0]:g} {corner[1]:g} {leave[0]:g} {leave[1]:g}'])
    chunks.append(f'L {points[-1][0]:g} {points[-1][1]:g}')
    return ' '.join(chunks)


def route_edges(diagram: Diagram, width: int, height: int) -> list[list[tuple[float, float]]]:
    """Route graph edges through a deterministic obstacle-aware channel grid."""
    nodes = list(diagram.nodes.values())
    xs = sorted({36.0, float(width - 36), *[value for node in nodes for value in (node.x - 24, node.x + node.width + 24)]})
    ys = sorted({138.0, float(height - 66), *[value for node in nodes for value in
                  (node.y - 24, node.y + node.height / 2, node.y + node.height + 24)]})
    free = {(xi, yi) for xi, x in enumerate(xs) for yi, y in enumerate(ys)
            if not any(node.x - 12 < x < node.x + node.width + 12 and
                       node.y - 12 < y < node.y + node.height + 12 for node in nodes)}
    adjacency: dict[tuple[int, int], list[tuple[tuple[int, int], float, int]]] = {}
    for point in sorted(free):
        xi, yi = point
        neighbors = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            other = (xi + dx, yi + dy)
            if other in free:
                a, b = (xs[xi], ys[yi]), (xs[other[0]], ys[other[1]])
                if segment_clear(a, b, nodes):
                    neighbors.append((other, abs(a[0] - b[0]) + abs(a[1] - b[1]), 1 if dx else 2))
        adjacency[point] = neighbors
    occupancy: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}
    output = []
    for edge in diagram.edges:
        source, target = diagram.nodes[edge.source], diagram.nodes[edge.target]
        start = (xs.index(source.x + source.width + 24), ys.index(source.y + source.height / 2))
        end = (xs.index(target.x - 24), ys.index(target.y + target.height / 2))
        initial = (start, 1)
        distances = {initial: 0.0}
        previous = {}
        frontier = [(0.0, 0.0, start, 1)]
        found = None
        while frontier:
            _, cost, point, direction = heapq.heappop(frontier)
            state = (point, direction)
            if cost != distances.get(state):
                continue
            if point == end:
                found = state
                break
            for other, length, new_direction in adjacency[point]:
                segment = tuple(sorted((point, other)))
                penalty = 38 if new_direction != direction else 0
                candidate = cost + length + penalty + occupancy.get(segment, 0) * 20
                new_state = (other, new_direction)
                if candidate < distances.get(new_state, float('inf')):
                    distances[new_state] = candidate
                    previous[new_state] = state
                    heuristic = abs(xs[other[0]] - xs[end[0]]) + abs(ys[other[1]] - ys[end[1]])
                    heapq.heappush(frontier, (candidate + heuristic, candidate, other, new_direction))
        if found is None:
            raise DiagramError(f'cannot route {edge.source} to {edge.target}')
        chain = [found[0]]
        while found != initial:
            found = previous[found]
            chain.append(found[0])
        chain.reverse()
        for a, b in zip(chain, chain[1:]):
            segment = tuple(sorted((a, b)))
            occupancy[segment] = occupancy.get(segment, 0) + 1
        points = [(source.x + source.width, source.y + source.height / 2),
                  *[(xs[xi], ys[yi]) for xi, yi in chain],
                  (target.x, target.y + target.height / 2)]
        output.append(compact_points(points))
    return output


def intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def place_edge_labels(diagram: Diagram, routes: list[list[tuple[float, float]]], width: int, height: int) -> list[tuple[list[str], float, float, float, float, float, float]]:
    labels = []
    occupied = [(node.x - 10, node.y - 10, node.x + node.width + 10, node.y + node.height + 10)
                for node in diagram.nodes.values()]
    for edge, points in sorted(zip(diagram.edges, routes), key=lambda pair: -len(pair[0].label)):
        if not edge.label:
            continue
        lines = wrap_label(edge.label, 16)
        box_width = max(62, max(len(line) for line in lines) * 7.4 + 22)
        box_height = len(lines) * 18 + 14
        candidates = []
        for a, b in zip(points, points[1:]):
            length = abs(a[0] - b[0]) + abs(a[1] - b[1])
            if a[1] == b[1] and length >= box_width + 20:
                center = (a[0] + b[0]) / 2
                candidates.extend((length, center + shift, a[1], center + shift, a[1]) for shift in (0, -24, 24, -48, 48))
            elif a[0] == b[0] and length >= box_height + 20:
                center = (a[1] + b[1]) / 2
                candidates.extend((length / 2, a[0], center + shift, a[0], center + shift) for shift in (0, -24, 24))
            # Short leaders keep captions beside crowded branching channels.
            center_x, center_y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            for shift in (0, *[sign * value for value in range(12, 133, 12) for sign in (-1, 1)]):
                if a[1] == b[1]:
                    if not min(a[0], b[0]) <= center_x + shift <= max(a[0], b[0]):
                        continue
                    for sign in (-1, 1):
                        candidates.append((length / 4, center_x + shift,
                                           center_y + sign * (box_height / 2 + 12),
                                           center_x + shift, center_y))
                else:
                    if not min(a[1], b[1]) <= center_y + shift <= max(a[1], b[1]):
                        continue
                    for sign in (-1, 1):
                        candidates.append((length / 4, center_x + sign * (box_width / 2 + 12),
                                           center_y + shift, center_x, center_y + shift))
        selected = None
        for _, x, y, anchor_x, anchor_y in sorted(candidates, key=lambda item: -item[0]):
            bounds = (x - box_width / 2, y - box_height / 2, x + box_width / 2, y + box_height / 2)
            if bounds[0] < 16 or bounds[2] > width - 16 or bounds[1] < 112 or bounds[3] > height - 42:
                continue
            if not segment_clear((x, y), (anchor_x, anchor_y), list(diagram.nodes.values())):
                continue
            if not any(intersects(bounds, other) for other in occupied):
                selected = (lines, x, y, box_width, box_height, anchor_x, anchor_y)
                occupied.append((bounds[0] - 6, bounds[1] - 6, bounds[2] + 6, bounds[3] + 6))
                break
        if selected is None:
            raise DiagramError(f'no unclipped label position for {edge.source} to {edge.target}: {edge.label}')
        labels.append(selected)
    return labels


def read_lab_title(lab_dir: Path) -> tuple[str, str]:
    metadata = (lab_dir / "lab.yml").read_text(encoding="utf-8", errors="replace")
    lab_id = re.search(r"(?m)^id:\s*['\"]?(LAB-\d{2})['\"]?\s*$", metadata)
    title = re.search(r"(?m)^title:\s*(.+?)\s*$", metadata)
    if not lab_id or not title:
        raise DiagramError(f"{lab_dir.name}/lab.yml must declare id and title")
    clean_title = title.group(1).strip().strip("'\"")
    return lab_id.group(1), clean_title


def render_lab_svg(lab_dir: Path) -> str:
    source_path = lab_dir / 'diagrams' / 'architecture.mmd'
    source = normalized_source(source_path.read_text(encoding='utf-8', errors='strict'))
    diagram = parse_mermaid(source)
    width, height = assign_layout(diagram)
    routes = route_edges(diagram, width, height)
    edge_labels = place_edge_labels(diagram, routes, width, height)
    lab_id, title = read_lab_title(lab_dir)
    prefix = lab_id.casefold().replace('-', '')
    digest = hashlib.sha256(source.encode('utf-8')).hexdigest()
    labels = ', '.join(node.label.replace('\n', ' ') for node in sorted(diagram.nodes.values(), key=lambda item: item.order))
    relationships = '; '.join(
        f"{diagram.nodes[edge.source].label.replace(chr(10), ' ')} to "
        f"{diagram.nodes[edge.target].label.replace(chr(10), ' ')}"
        + (f' ({edge.label})' if edge.label else '') for edge in diagram.edges
    )
    description = (
        f'Illustrated service topology with {len(diagram.nodes)} components and '
        f'{len(diagram.edges)} directed relationships. Original left-to-right ranks '
        f'continue on the next row when necessary. Components: {labels}. '
        f'Relationships: {relationships}.'
    )
    metadata = json.dumps({'renderer': RENDERER_ID, 'source': 'architecture.mmd', 'sourceSha256': digest},
                          sort_keys=True, separators=(',', ':'))
    output = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{prefix}-title {prefix}-desc">',
        f'  <title id="{prefix}-title">{html.escape(lab_id)} architecture: {html.escape(title)}</title>',
        f'  <desc id="{prefix}-desc">{html.escape(description)}</desc>',
        f'  <metadata id="{prefix}-metadata">{html.escape(metadata)}</metadata>',
        '  <defs>',
        '    <linearGradient id="canvas-fill" x2="1" y2="1"><stop stop-color="#090D19"/><stop offset="1" stop-color="#111B30"/></linearGradient>',
        '    <linearGradient id="card-fill" x2="0" y2="1"><stop stop-color="#18253C"/><stop offset="1" stop-color="#111B2E"/></linearGradient>',
        '    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#72A6E8" opacity=".10"/></pattern>',
        '    <marker id="arrow" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0 0L9 4L0 8z" fill="#59D6E8"/></marker>',
        '    <style>',
        '      .edge { fill: none; stroke: #59D6E8; stroke-width: 2; stroke-opacity: .8; marker-end: url(#arrow); }',
        "      .node-label { fill: #F6F8FF; font: 600 18px 'Segoe UI', Arial, sans-serif; dominant-baseline: central; }",
        "      .edge-label { fill: #D9F8FD; font: 13px 'Segoe UI', Arial, sans-serif; text-anchor: middle; dominant-baseline: central; }",
        "      .heading { fill: #F6F8FF; font: 700 27px 'Segoe UI', Arial, sans-serif; }",
        "      .eyebrow { fill: #87C9FF; font: 600 14px 'Segoe UI', Arial, sans-serif; letter-spacing: 2px; }",
        "      .footer { fill: #ACC0DC; font: 13px 'Segoe UI', Arial, sans-serif; }",
        '    </style>',
        '  </defs>',
        '  <rect width="100%" height="100%" fill="url(#canvas-fill)"/>',
        '  <rect width="100%" height="100%" fill="url(#grid)"/>',
        '  <g aria-hidden="true">',
        f'    <rect x="36" y="35" width="72" height="34" rx="10" fill="#6366F1" fill-opacity=".23" stroke="#A295F9" stroke-opacity=".55"/>',
        f'    <text x="72" y="58" class="eyebrow" text-anchor="middle">{html.escape(lab_id[4:])}</text>',
        '    <text x="126" y="58" class="eyebrow">AZURE ADMINISTRATOR · SERVICE TOPOLOGY</text>',
        f'    <text x="36" y="102" class="heading">{html.escape(title)}</text>',
    ]
    for index, (edge, points) in enumerate(zip(diagram.edges, routes)):
        output.append(f'    <path id="edge-{index}" data-source="{edge.source}" data-target="{edge.target}" class="edge" d="{rounded_path(points)}"/>')
    for node in sorted(diagram.nodes.values(), key=lambda item: item.order):
        output.extend(node_shape(node, diagram.styles.get(node.class_name or '', {})))
    for index, (lines, x, y, box_width, box_height, anchor_x, anchor_y) in enumerate(edge_labels):
        output.append(f'    <g class="edge-caption" id="edge-caption-{index}">')
        if x != anchor_x or y != anchor_y:
            output.append(f'      <path d="M{x:g} {y:g}L{anchor_x:g} {anchor_y:g}" stroke="#6AA0B2" stroke-width="1.5" stroke-dasharray="3 3" fill="none"/>')
        output.append(f'      <rect x="{x - box_width / 2:g}" y="{y - box_height / 2:g}" width="{box_width:g}" height="{box_height:g}" rx="9" fill="#0D1728" stroke="#3E7189"/>')
        first_y = y - (len(lines) - 1) * 9
        for line_index, line in enumerate(lines):
            output.append(f'      <text class="edge-label" x="{x:g}" y="{first_y + line_index * 18:g}">{html.escape(line)}</text>')
        output.append('    </g>')
    output.extend([
        f'    <path d="M36 {height - 40}H{width - 36}" stroke="#29405D"/>',
        f'    <text x="36" y="{height - 17}" class="footer">{len(diagram.nodes)} components · {len(diagram.edges)} directed connections · Original source: architecture.mmd</text>',
        '  </g>', '</svg>', '',
    ])
    return '\n'.join(output)


def lab_directories(only: list[str]) -> list[Path]:
    directories = sorted(
        path for path in (ROOT / "labs").iterdir() if path.is_dir() and LAB_PATTERN.fullmatch(path.name)
    )
    if not only:
        return directories
    requested = {value.casefold() for value in only}
    selected = [
        path
        for path in directories
        if path.name.casefold() in requested or path.name[:2] in requested or f"lab-{path.name[:2]}" in requested
    ]
    missing = requested - {
        key
        for path in selected
        for key in (path.name.casefold(), path.name[:2], f"lab-{path.name[:2]}")
        if key in requested
    }
    if missing:
        raise DiagramError(f"unknown lab selector(s): {', '.join(sorted(missing))}")
    return selected


def run(check: bool, only: list[str]) -> int:
    failures = 0
    directories = lab_directories(only)
    if not directories:
        print("FAIL  no lab directories found")
        return 1
    for lab_dir in directories:
        relative = lab_dir.relative_to(ROOT)
        svg_path = lab_dir / "diagrams" / "architecture.svg"
        try:
            expected = render_lab_svg(lab_dir)
        except (DiagramError, OSError, UnicodeError) as exc:
            failures += 1
            print(f"FAIL  {relative}: {exc}")
            continue
        if check:
            actual = svg_path.read_text(encoding="utf-8", errors="replace") if svg_path.exists() else ""
            if actual != expected:
                failures += 1
                print(f"FAIL  {relative}/diagrams/architecture.svg is stale; run python tools/render_diagrams.py")
            else:
                print(f"PASS  {relative}/diagrams/architecture.svg")
        else:
            svg_path.parent.mkdir(parents=True, exist_ok=True)
            with svg_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(expected)
            print(f"WRITE {relative}/diagrams/architecture.svg")
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if a committed SVG differs from deterministic output.")
    parser.add_argument("--only", action="append", default=[], metavar="LAB", help="Render one lab ID or folder; repeat as needed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return run(args.check, args.only)
    except DiagramError as exc:
        print(f"FAIL  {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
