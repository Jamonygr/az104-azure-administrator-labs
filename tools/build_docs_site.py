#!/usr/bin/env python3
"""Stage authoritative repository content for the Material for MkDocs site."""

# cspell:ignore labelledby

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from collections import defaultdict
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml
import markdown as markdown_library


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / ".site-docs"
SITE_SOURCE = REPO_ROOT / "docs" / "site"
SITE_ASSETS = REPO_ROOT / "docs" / "site-assets"
CATALOG_PATH = REPO_ROOT / "labs" / "catalog.yml"
BLUEPRINT_PATH = REPO_ROOT / "curriculum" / "blueprint.yml"

EXAM_DOMAINS = {
    "identity-governance": ("IG", "identity-governance", "Govern with confidence", "Manage identities, access, policy, and costs.", "Identity shield with users and governance controls"),
    "storage": ("ST", "storage", "Protect your data", "Secure storage, move data, and manage lifecycle.", "Storage cylinders and protected data connections"),
    "compute": ("CP", "compute", "Build resilient workloads", "Deploy infrastructure, virtual machines, and apps.", "Virtual machines, containers, and an application platform"),
    "networking": ("NW", "networking", "Connect securely", "Design networks, control traffic, and isolate services.", "Connected network nodes and a secure boundary"),
    "monitor-recovery": ("MR", "monitor-recovery", "Operate and recover", "Observe, alert, back up, and restore workloads.", "Monitoring signals beside a backup and recovery shield"),
}

DOMAIN_LABELS = {
    "foundation": "Foundation",
    "identity-governance": "Identity and governance",
    "storage": "Storage",
    "compute": "Compute",
    "networking": "Networking",
    "monitor-recovery": "Monitoring and recovery",
    "capstone": "Capstones",
}

ALLOWED_LAB_SUFFIXES = {
    ".bicep",
    ".json",
    ".kql",
    ".md",
    ".mmd",
    ".ps1",
    ".svg",
    ".yaml",
    ".yml",
}


class SiteBuildError(RuntimeError):
    """Raised when authoritative site inputs violate the staging contract."""


class AccessibilityParser(HTMLParser):
    """Collect a small set of deterministic accessibility signals from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.has_language = False
        self.has_viewport = False
        self.main_count = 0
        self.h1_count = 0
        self.images_without_alt = 0
        self.external_active_resources: list[str] = []
        self.links: list[str] = []
        self.home_card_count = 0
        self.domain_card_count = 0
        self.code_blocks = 0
        self.skip_target = None
        self.document_title = ""
        self.in_document_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "html" and attributes.get("lang"):
            self.has_language = True
        elif tag == "title":
            self.in_document_title = True
        elif tag == "meta" and attributes.get("name", "").lower() == "viewport":
            self.has_viewport = True
        elif tag == "main":
            self.main_count += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "img" and "alt" not in attributes:
            self.images_without_alt += 1
        elif tag == "pre":
            self.code_blocks += 1
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
            if "md-skip" in attributes.get("class", "").split():
                self.skip_target = attributes["href"]
        classes = attributes.get("class", "").split()
        if "az104-lab-card" in classes:
            self.home_card_count += 1
        if "az104-domain-card" in classes:
            self.domain_card_count += 1
        active_resource = None
        if tag in {"img", "script", "source"}:
            active_resource = attributes.get("src")
        elif tag == "link" and attributes.get("rel"):
            relationships = set(attributes["rel"].casefold().split())
            if relationships & {"icon", "manifest", "modulepreload", "preload", "stylesheet"}:
                active_resource = attributes.get("href")
        if active_resource and re.match(r"^https?://", active_resource, re.IGNORECASE):
            self.external_active_resources.append(active_resource)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_document_title = False

    def handle_data(self, data: str) -> None:
        if self.in_document_title:
            self.document_title += data


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SiteBuildError(f"Cannot read {path.relative_to(REPO_ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise SiteBuildError(f"Expected a mapping in {path.relative_to(REPO_ROOT)}")
    return value


def normalized_lab_id(value: Any) -> str:
    text = str(value)
    if not re.fullmatch(r"\d{1,2}", text):
        raise SiteBuildError(f"Invalid catalog lab ID: {value!r}")
    number = int(text)
    if not 0 <= number <= 27:
        raise SiteBuildError(f"Catalog lab ID is outside 00-27: {value!r}")
    return f"{number:02d}"


def load_labs() -> list[dict[str, Any]]:
    catalog = load_yaml(CATALOG_PATH)
    entries = catalog.get("labs")
    if not isinstance(entries, list) or len(entries) != 28:
        raise SiteBuildError("labs/catalog.yml must declare exactly 28 labs")

    labs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in entries:
        if not isinstance(raw, dict):
            raise SiteBuildError("Every catalog lab entry must be a mapping")
        lab_id = normalized_lab_id(raw.get("id"))
        if lab_id in seen:
            raise SiteBuildError(f"Duplicate catalog lab ID: {lab_id}")
        seen.add(lab_id)
        slug = raw.get("slug")
        domain = raw.get("domain")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]+", slug):
            raise SiteBuildError(f"LAB-{lab_id} has an invalid slug")
        if domain not in DOMAIN_LABELS:
            raise SiteBuildError(f"LAB-{lab_id} has an unsupported domain: {domain!r}")
        estimated_minutes = raw.get("estimatedMinutes")
        if (
            not isinstance(estimated_minutes, int)
            or isinstance(estimated_minutes, bool)
            or estimated_minutes <= 0
        ):
            raise SiteBuildError(f"LAB-{lab_id} has an invalid estimatedMinutes value")
        question_count = raw.get("questionCount")
        expected_question_count = 0 if lab_id in {"00", "26", "27"} else 50
        if question_count != expected_question_count:
            raise SiteBuildError(
                f"LAB-{lab_id} must declare questionCount {expected_question_count}"
            )
        folder = REPO_ROOT / "labs" / f"{lab_id}-{slug}"
        metadata_path = folder / "lab.yml"
        readme_path = folder / "README.md"
        if not folder.is_dir() or not metadata_path.is_file() or not readme_path.is_file():
            raise SiteBuildError(f"LAB-{lab_id} is missing its folder, lab.yml, or README.md")
        metadata = load_yaml(metadata_path)
        title = metadata.get("title")
        if not isinstance(title, str) or not title.strip():
            raise SiteBuildError(f"LAB-{lab_id} has no title in lab.yml")
        labs.append(
            {
                **raw,
                "id": lab_id,
                "labId": f"LAB-{lab_id}",
                "folder": folder,
                "folderName": folder.name,
                "title": title.strip(),
            }
        )

    expected = {f"{number:02d}" for number in range(28)}
    if seen != expected:
        missing = ", ".join(sorted(expected - seen))
        raise SiteBuildError(f"Catalog IDs must be contiguous from 00 through 27; missing: {missing}")
    return sorted(labs, key=lambda item: item["id"])


def copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise SiteBuildError(
            f"Refusing to stage symbolic link: {source.relative_to(REPO_ROOT)}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def homepage_sections(labs: list[dict[str, Any]]) -> dict[str, str]:
    """Render compact, escaped HTML from the authoritative catalog and blueprint."""
    blueprint = load_yaml(BLUEPRINT_PATH)
    domains = blueprint.get("domains", [])
    objective_count = sum(
        len(group.get("objectives", []))
        for domain in domains
        for group in domain.get("groups", [])
    )
    question_count = sum(lab["questionCount"] for lab in labs)
    if objective_count != 82 or objective_count != blueprint["exam"]["officialObjectiveCount"]:
        raise SiteBuildError("Homepage must use all 82 official objectives from the blueprint")
    if question_count != 1250:
        raise SiteBuildError("Homepage must use exactly 1,250 catalog questions")
    stats = '<div class="az104-stats" aria-label="Curriculum at a glance">' + "".join(
        f'<div><strong>{value:,}</strong><span>{label}</span></div>'
        for value, label in ((len(labs), "guided labs"), (question_count, "practice questions"), (objective_count, "exam objectives"))
    ) + '</div>'
    domain_cards: list[str] = []
    for domain, (domain_id, illustration, headline, description, alt) in EXAM_DOMAINS.items():
        authoritative = next((item for item in domains if item["id"] == domain_id), None)
        if not authoritative:
            raise SiteBuildError(f"Blueprint is missing exam domain {domain_id}")
        selected_labs = [lab for lab in labs if lab["domain"] == domain]
        visual = f"assets/illustrations/domain-{illustration}.svg"
        domain_cards.append(
            f'<article class="az104-domain-card"><figure><a href="{visual}" aria-label="Open {escape(DOMAIN_LABELS[domain])} illustration at full size"><img src="{visual}" alt="{escape(alt)}" loading="lazy" width="640" height="400"></a>'
            f'<figcaption>{escape(DOMAIN_LABELS[domain])} · <a href="{visual}">Full size</a></figcaption></figure>'
            f'<div class="az104-card-body"><span class="az104-eyebrow">{escape(authoritative["weight"])} of the exam</span><h3><a href="domains/{domain}/">{escape(headline)}</a></h3>'
            f'<p>{escape(description)}</p><p class="az104-card-meta">{len(selected_labs)} labs · {sum(lab["questionCount"] for lab in selected_labs)} questions</p></div></article>'
        )
    lab_cards: list[str] = []
    for lab in labs:
        path_url = f'labs/{lab["folderName"]}/'
        visual = f'{path_url}diagrams/architecture.svg'
        lab_cards.append(
            f'<article class="az104-lab-card" data-lab-id="{lab["labId"]}"><figure><a href="{visual}" aria-label="Open {lab["labId"]} architecture at full size"><img src="{visual}" alt="{escape(lab["title"])}: service topology and connections" loading="lazy" width="960" height="600"></a>'
            f'<figcaption>{lab["labId"]} architecture · <a href="{visual}">Full size</a></figcaption></figure>'
            f'<div class="az104-card-body"><span class="az104-eyebrow">{lab["labId"]} · {escape(DOMAIN_LABELS[lab["domain"]])}</span><h3><a href="{path_url}">{escape(lab["title"])}</a></h3>'
            f'<ul class="az104-card-tags" aria-label="Lab details"><li>{lab["estimatedMinutes"]} min</li><li>{escape(lab["difficulty"])}</li><li>Cost: {escape(lab["costClass"])}</li><li>{lab["questionCount"]} questions</li></ul>'
            f'<p class="az104-card-status">{escape(lab["status"])}</p><a class="az104-card-link" href="{path_url}">Open lab <span aria-hidden="true">→</span></a></div></article>'
        )
    return {
        "AZ104_STATS": stats,
        "AZ104_DOMAINS": '<div class="az104-domain-grid">' + "\n".join(domain_cards) + '</div>',
        "AZ104_LAB_CARDS": '<div class="az104-lab-grid">' + "\n".join(lab_cards) + '</div>',
    }


def validate_homepage(content: str) -> None:
    rendered = markdown_library.markdown(content, extensions=["attr_list", "tables", "admonition"])
    parser = AccessibilityParser()
    parser.feed(rendered)
    if parser.h1_count != 1 or 'id="home-title"' not in rendered:
        raise SiteBuildError("Homepage must render one native Markdown H1 with the home-title anchor")
    if parser.code_blocks or "&lt;article" in rendered or "&lt;section" in rendered:
        raise SiteBuildError("Homepage HTML must not render as indented code or escaped markup")
    if parser.home_card_count != 28 or parser.domain_card_count != 5:
        raise SiteBuildError("Homepage must render exactly 28 lab cards and five domain cards")
    if parser.images_without_alt:
        raise SiteBuildError("Homepage images must have descriptive alternative text")


def copy_site_sources(output: Path, labs: list[dict[str, Any]]) -> None:
    required_pages = {
        "index.md": "index.md",
        "learning-pathways.md": "learning-pathways.md",
        "environment-readiness.md": "environment-readiness.md",
        "learner-progress.md": "learner-progress.md",
        "glossary.md": "glossary.md",
        "practice.md": "practice.md",
    }
    for source_name, destination_name in required_pages.items():
        source = SITE_SOURCE / source_name
        if not source.is_file():
            raise SiteBuildError(f"Missing site source: {source.relative_to(REPO_ROOT)}")
        content = source.read_text(encoding="utf-8")
        if source_name == "index.md":
            for marker, value in homepage_sections(labs).items():
                token = f"<!-- {marker} -->"
                if content.count(token) != 1:
                    raise SiteBuildError(f"Homepage must contain exactly one {marker} marker")
                content = content.replace(token, value)
            validate_homepage(content)
        link_rewrites = {
            "../../labs/": "labs/",
            "../objective-map.md": "docs/objective-map.md",
            "../study-plan.md": "docs/study-plan.md",
            "../assessment-guide.md": "docs/assessment-guide.md",
            "../cost-and-cleanup.md": "docs/cost-and-cleanup.md",
            "../../learner.config.example.yml": "downloads/learner.config.example.yml",
            "../../curriculum/progress-schema.json": "contracts/progress-schema.json",
        }
        for source_link, staged_link in link_rewrites.items():
            content = content.replace(source_link, staged_link)
        destination = output / destination_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)

    if not SITE_ASSETS.is_dir():
        raise SiteBuildError("docs/site-assets is missing")
    shutil.copytree(SITE_ASSETS, output / "assets", dirs_exist_ok=True)


def copy_repository_docs(output: Path) -> None:
    docs_root = REPO_ROOT / "docs"
    for source in sorted(docs_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(docs_root)
        # Authoritative site art is staged separately from site-assets; legacy
        # branding sources under visuals remain downloadable in the repository.
        if relative.parts[0] in {"site", "site-assets", "visuals"}:
            continue
        copy_file(source, output / "docs" / relative)

    curriculum_root = REPO_ROOT / "curriculum"
    for source in sorted(curriculum_root.iterdir()):
        if source.is_file() and source.suffix.lower() in {".json", ".yml", ".yaml"}:
            copy_file(source, output / "contracts" / source.name)
    copy_file(
        REPO_ROOT / "learner.config.example.yml",
        output / "downloads" / "learner.config.example.yml",
    )


def navigation_line(labs: list[dict[str, Any]], index: int) -> str:
    parts: list[str] = []
    if index > 0:
        previous = labs[index - 1]
        parts.append(f"[← {previous['labId']}](../{previous['folderName']}/README.md)")
    parts.append("[Lab catalog](../README.md)")
    if index + 1 < len(labs):
        following = labs[index + 1]
        parts.append(f"[{following['labId']} →](../{following['folderName']}/README.md)")
    return " · ".join(parts)


def add_staged_navigation(markdown: str, navigation: str) -> str:
    lines = markdown.splitlines()
    heading_index = next((index for index, line in enumerate(lines) if line.startswith("# ")), None)
    if heading_index is None:
        raise SiteBuildError("Every staged lab README must contain one H1 heading")
    if re.search(r"\[(?:Lab )?Catalog\]\(", markdown, re.IGNORECASE):
        return markdown if markdown.endswith("\n") else f"{markdown}\n"
    body = [*lines[: heading_index + 1], "", navigation, "", *lines[heading_index + 1 :]]
    while len(body) > 1 and body[-1] == "":
        body.pop()
    body.extend(["", "---", "", navigation, ""])
    return "\n".join(body)


def validate_svg(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    required = ("role=\"img\"", "<title", "<desc", "aria-labelledby=")
    missing = [token for token in required if token not in content]
    if missing:
        relative = path.relative_to(REPO_ROOT)
        raise SiteBuildError(f"{relative} is missing accessible SVG markup: {', '.join(missing)}")


def copy_labs(output: Path, labs: list[dict[str, Any]]) -> None:
    copy_file(REPO_ROOT / "labs" / "README.md", output / "labs" / "README.md")
    copy_file(CATALOG_PATH, output / "labs" / "catalog.yml")
    for index, lab in enumerate(labs):
        source_root: Path = lab["folder"]
        destination_root = output / "labs" / lab["folderName"]
        for source in sorted(source_root.rglob("*")):
            if not source.is_file() or source.suffix.lower() not in ALLOWED_LAB_SUFFIXES:
                continue
            relative = source.relative_to(source_root)
            destination = destination_root / relative
            if relative == Path("README.md"):
                content = source.read_text(encoding="utf-8")
                staged = add_staged_navigation(content, navigation_line(labs, index))
                # The generated comment preceding the original H1 makes MkDocs
                # fall back to "Index". Metadata gives search and page titles a
                # meaningful label without rewriting authoritative lesson text.
                page_metadata = yaml.safe_dump(
                    {"title": f"Lab {lab['id']}: {lab['title']}"},
                    allow_unicode=True,
                    sort_keys=False,
                )
                staged = f"---\n{page_metadata}---\n\n{staged}"
                diagram_alt = f"{lab['labId']}: {lab['title']}; service topology and connections"
                diagram_figure = (
                    f'<figure class="az104-teaching-visual"><a href="diagrams/architecture.svg" aria-label="Open {lab["labId"]} architecture at full size">'
                    f'<img src="diagrams/architecture.svg" alt="{escape(diagram_alt)}" loading="lazy"></a>'
                    f'<figcaption>{escape(lab["title"])} — topology for this lab. <a href="diagrams/architecture.svg">Open at full size</a>.</figcaption></figure>'
                )
                staged, replacements = re.subn(
                    r"!\[[^\]]+\]\(diagrams/architecture\.svg\)",
                    lambda _: diagram_figure,
                    staged,
                )
                if replacements != 1:
                    raise SiteBuildError(f"{lab['labId']} must contain exactly one instructional architecture image")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("w", encoding="utf-8", newline="\n") as handle:
                    handle.write(staged)
            elif relative.as_posix() == "assessment/ANSWERS.md":
                content = source.read_text(encoding="utf-8")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("w", encoding="utf-8", newline="\n") as handle:
                    handle.write("---\nsearch:\n  exclude: true\n---\n\n" + content)
            else:
                copy_file(source, destination)
            if source.name == "architecture.svg":
                validate_svg(source)


def domain_page(domain: str, labs: list[dict[str, Any]]) -> str:
    label = DOMAIN_LABELS[domain]
    lab_ids = ",".join(lab["labId"] for lab in labs)
    lines = [
        f"# {label}",
        "",
        f"This generated dashboard lists the authoritative {label.lower()} labs in catalog order.",
        "",
        f'<div class="az104-progress-card" data-az104-domain-labs="{lab_ids}"></div>',
        "",
        "| Lab | Guided time | Questions |",
        "|---|---:|---:|",
    ]
    for lab in labs:
        minutes = int(lab.get("estimatedMinutes", 0))
        count = int(lab["questionCount"])
        lines.append(
            f"| [{lab['labId']}: {lab['title']}](../labs/{lab['folderName']}/README.md) | "
            f"{minutes} minutes | {count} |"
        )
    lines.extend(
        [
            "",
            "Completion requires successful deployment validation and post-cleanup validation.",
            "Assessment scores are learning signals rather than claims about the certification exam.",
            "",
        ]
    )
    return "\n".join(lines)


def write_domain_pages(output: Path, labs: list[dict[str, Any]]) -> None:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for lab in labs:
        grouped[lab["domain"]].append(lab)
    domain_root = output / "domains"
    domain_root.mkdir(parents=True, exist_ok=True)
    for domain in DOMAIN_LABELS:
        path = domain_root / f"{domain}.md"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(domain_page(domain, grouped[domain]))


def write_quiz_banks(output: Path, labs: list[dict[str, Any]]) -> None:
    """Add route information to exact YAML question records without rewriting them."""
    quiz_root = output / "assets" / "quiz"
    quiz_root.mkdir(parents=True, exist_ok=True)
    entries = []
    total_questions = 0
    for lab in labs:
        if not lab["questionCount"]:
            continue
        path = lab["folder"] / "assessment" / "questions.yml"
        try:
            questions = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise SiteBuildError(f"Cannot load quiz bank {path}: {exc}") from exc
        if not isinstance(questions, list) or len(questions) != 50:
            raise SiteBuildError(f"{lab['labId']} must stage 50 questions")
        path_url = f'labs/{lab["folderName"]}/'
        readme = (lab["folder"] / "README.md").read_text(encoding="utf-8")
        anchors = set(re.findall(r"\{#([a-z0-9-]+)\}", readme))
        staged_questions = []
        for question in questions:
            if not isinstance(question, dict):
                raise SiteBuildError(f"{lab['labId']} has a non-mapping quiz question")
            anchor = question.get("remediationAnchor", "")
            if not isinstance(anchor, str) or not anchor.startswith("#") or anchor[1:] not in anchors:
                raise SiteBuildError(f"{question.get('id')} has an invalid remediation anchor")
            if set(question.get("options", {})) != {"A", "B", "C", "D"} or question.get("correctOption") not in {"A", "B", "C", "D"}:
                raise SiteBuildError(f"{question.get('id')} has invalid quiz options")
            if set(question.get("optionExplanations", {})) != {"A", "B", "C", "D"}:
                raise SiteBuildError(f"{question.get('id')} needs four quiz explanations")
            staged_questions.append({**question, "reviewUrl": f"{path_url}{anchor}"})
        bank_name = f'{lab["labId"]}.json'
        document = {"schemaVersion": "1.0.0", "labId": lab["labId"], "title": lab["title"], "pathUrl": path_url, "questions": staged_questions}
        (quiz_root / bank_name).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        entries.append({"labId": lab["labId"], "title": lab["title"], "pathUrl": path_url, "questionCount": len(questions), "bankUrl": bank_name})
        total_questions += len(questions)
    if len(entries) != 25 or total_questions != 1250:
        raise SiteBuildError("Staged quizzes must contain 25 banks and exactly 1,250 unchanged questions")
    (quiz_root / "index.json").write_text(json.dumps({"schemaVersion": "1.0.0", "labs": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def check_artwork(output: Path, labs: list[dict[str, Any]]) -> None:
    hero = output / "assets" / "illustrations" / "az104-cloud-cover.png"
    if not hero.is_file() or hero.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise SiteBuildError("Original AZ-104 cover artwork must be a local PNG")
    for _, illustration, _, _, _ in EXAM_DOMAINS.values():
        source = SITE_ASSETS / "illustrations" / f"domain-{illustration}.svg"
        if not source.is_file():
            raise SiteBuildError(f"Missing original domain illustration {source.name}")
        validate_svg(source)
    for lab in labs:
        diagram = output / "labs" / lab["folderName"] / "diagrams" / "architecture.svg"
        if not diagram.is_file():
            raise SiteBuildError(f"Missing architecture visual for {lab['labId']}")


def write_manifest(output: Path) -> None:
    files: list[dict[str, Any]] = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name == ".stage-manifest.json":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": path.relative_to(output).as_posix(), "sha256": digest})
    manifest = {
        "schemaVersion": "1.0.0",
        "generatedFrom": "authoritative repository sources",
        "fileCount": len(files),
        "files": files,
    }
    with (output / ".stage-manifest.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2) + "\n")


def populate_staging_tree(output: Path, labs: list[dict[str, Any]]) -> None:
    """Create one complete site source tree from authoritative inputs."""

    copy_site_sources(output, labs)
    copy_repository_docs(output)
    copy_labs(output, labs)
    write_domain_pages(output, labs)
    write_quiz_banks(output, labs)
    check_artwork(output, labs)
    write_manifest(output)


def stage(output: Path) -> None:
    labs = load_labs()
    output = output.resolve()
    repository = REPO_ROOT.resolve()
    if (
        output.parent != repository
        or not re.fullmatch(r"\.site-docs(?:-[a-z0-9][a-z0-9-]*)?", output.name)
    ):
        raise SiteBuildError(
            "The site staging directory must be the repository's .site-docs "
            "directory or a direct .site-docs-<name> sibling"
        )

    temporary = output.with_name(f"{output.name}.tmp")
    for target in (temporary,):
        if target.exists():
            shutil.rmtree(target)
    temporary.mkdir(parents=True)
    try:
        populate_staging_tree(temporary, labs)
        if output.exists():
            shutil.rmtree(output)
        temporary.replace(output)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def check() -> None:
    with tempfile.TemporaryDirectory(prefix="az104-site-check-") as temp_dir:
        first_output = Path(temp_dir) / "site-docs-first"
        second_output = Path(temp_dir) / "site-docs-second"
        labs = load_labs()
        populate_staging_tree(first_output, labs)
        populate_staging_tree(second_output, labs)
        if not (first_output / "index.md").is_file():
            raise SiteBuildError("Site staging check did not produce index.md")
        if len(list((first_output / "labs").glob("[0-2][0-9]-*/README.md"))) != 28:
            raise SiteBuildError("Site staging check did not produce all 28 lab guides")
        first_manifest = (first_output / ".stage-manifest.json").read_bytes()
        second_manifest = (second_output / ".stage-manifest.json").read_bytes()
        if first_manifest != second_manifest:
            raise SiteBuildError("Two consecutive staging passes produced different manifests")


def check_built_site(site_root: Path) -> None:
    site_root = site_root.resolve()
    labs = load_labs()
    representative = (
        site_root / "index.html",
        site_root / "learner-progress" / "index.html",
        site_root / "practice" / "index.html",
        site_root / "labs" / "00-safe-bootstrap" / "index.html",
        site_root / "labs" / "14-container-apps" / "index.html",
        site_root / "labs" / "27-capstone-operate-recover" / "index.html",
    )
    for page in representative:
        if not page.is_file():
            raise SiteBuildError(f"Built site is missing representative page: {page}")
        parser = AccessibilityParser()
        parser.feed(page.read_text(encoding="utf-8"))
        failures: list[str] = []
        if not parser.has_language:
            failures.append("document language")
        if not parser.has_viewport:
            failures.append("responsive viewport")
        if parser.main_count != 1:
            failures.append(f"one main landmark (found {parser.main_count})")
        if parser.h1_count != 1:
            failures.append(f"one H1 (found {parser.h1_count})")
        if parser.images_without_alt:
            failures.append(f"alt text for {parser.images_without_alt} image(s)")
        if parser.external_active_resources:
            failures.append(
                "no externally hosted runtime assets "
                f"(found {len(parser.external_active_resources)})"
            )
        if failures:
            raise SiteBuildError(f"{page} failed static accessibility checks: {', '.join(failures)}")
        if page == site_root / "index.html":
            if parser.home_card_count != 28 or parser.domain_card_count != 5 or parser.code_blocks:
                raise SiteBuildError("Built homepage must contain 28 lab cards, five domain cards, and no code blocks")
            if parser.skip_target != "#home-title":
                raise SiteBuildError("Built homepage must retain the native skip-to-content target")
            for href in parser.links:
                if href.startswith(("labs/", "domains/", "assets/illustrations/", "practice/")):
                    target = site_root / href.split("#", 1)[0]
                    if not target.is_file() and not (target / "index.html").is_file():
                        raise SiteBuildError(f"Built homepage link is missing: {href}")

    quiz_root = site_root / "assets" / "quiz"
    try:
        quiz_index = json.loads((quiz_root / "index.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SiteBuildError(f"Built quiz index is unavailable: {exc}") from exc
    if len(quiz_index.get("labs", [])) != 25:
        raise SiteBuildError("Built quiz index must offer exactly 25 labs")
    total_questions = 0
    for entry in quiz_index["labs"]:
        bank = json.loads((quiz_root / entry["bankUrl"]).read_text(encoding="utf-8"))
        if len(bank["questions"]) != 50 or bank["labId"] != entry["labId"]:
            raise SiteBuildError(f"Built quiz {entry['labId']} has invalid question count or identity")
        lab_page = site_root / entry["pathUrl"] / "index.html"
        if not lab_page.is_file():
            raise SiteBuildError(f"Built quiz lesson route is missing: {entry['pathUrl']}")
        lesson_html = lab_page.read_text(encoding="utf-8")
        for question in bank["questions"]:
            anchor = question["reviewUrl"].split("#", 1)[1]
            if f'id="{anchor}"' not in lesson_html:
                raise SiteBuildError(f"Built quiz remediation is missing for {question['id']}")
        total_questions += len(bank["questions"])
    if total_questions != 1250:
        raise SiteBuildError("Built quiz assets must contain all 1,250 questions")
    for asset in ("learning.css", "quiz.js", "illustrations/az104-cloud-cover.png"):
        if not (site_root / "assets" / asset).is_file():
            raise SiteBuildError(f"Built site is missing local learning asset: {asset}")

    progress_script = site_root / "assets" / "progress.js"
    progress_styles = site_root / "assets" / "progress.css"
    if not progress_script.is_file() or not progress_styles.is_file():
        raise SiteBuildError("Built site is missing local progress assets")
    styles = progress_styles.read_text(encoding="utf-8")
    if "prefers-reduced-motion" not in styles or "auto-fit" not in styles:
        raise SiteBuildError("Progress styles must retain reduced-motion and responsive-grid behavior")

    search_index = site_root / "search" / "search_index.json"
    if not search_index.is_file():
        raise SiteBuildError("Built site is missing the client-side search index")
    try:
        search_document = json.loads(search_index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SiteBuildError(f"Client-side search index is invalid: {exc}") from exc
    indexed_documents = search_document.get("docs", [])
    if search_document.get("config", {}).get("separator") != r"[\s\-\.]+":
        raise SiteBuildError("Search separator must split whitespace, hyphens, and periods with single regex escapes")
    if not isinstance(indexed_documents, list) or not indexed_documents:
        raise SiteBuildError("Client-side search index contains no documents")
    answer_hits = [
        item.get("location", "")
        for item in indexed_documents
        if isinstance(item, dict)
        and "/assessment/answers/" in str(item.get("location", "")).casefold()
    ]
    if answer_hits:
        raise SiteBuildError(
            "Assessment answer keys must be excluded from learner search; found "
            + ", ".join(answer_hits[:3])
        )
    indexed_locations = {
        str(item.get("location", ""))
        for item in indexed_documents
        if isinstance(item, dict)
    }
    indexed_lab_roots = {
        match.group(1)
        for location in indexed_locations
        if (
            match := re.match(
                r"^(labs/(?:0[0-9]|1[0-9]|2[0-7])-[a-z0-9-]+/)",
                location,
            )
        )
    }
    if len(indexed_lab_roots) != 28:
        raise SiteBuildError(
            "Client-side search must include every lab guide; "
            f"found {len(indexed_lab_roots)} of 28"
        )
    for lab in labs:
        location = f'labs/{lab["folderName"]}/'
        page_path = site_root / location / "index.html"
        if not page_path.is_file():
            raise SiteBuildError(f"Built site is missing lab guide: {location}")
        parser = AccessibilityParser()
        parser.feed(page_path.read_text(encoding="utf-8"))
        expected_title = f"Lab {lab['id']}: {lab['title']}"
        if not parser.document_title.startswith(expected_title) or parser.document_title.startswith("Index"):
            raise SiteBuildError(f"{lab['labId']} must have its meaningful lab title rather than Index")
        root_documents = [item for item in indexed_documents if isinstance(item, dict) and item.get("location") == location]
        if len(root_documents) != 1 or root_documents[0].get("title") != expected_title:
            raise SiteBuildError(f"Search must use the meaningful {lab['labId']} title at {location}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument(
        "--check",
        action="store_true",
        help="Validate a temporary staging tree without changing the local staging directory.",
    )
    operation.add_argument(
        "--check-built-site",
        type=Path,
        metavar="SITE_DIR",
        help="Check representative built pages for deterministic accessibility signals.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Site staging directory (default: .site-docs).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.check_built_site:
            check_built_site(args.check_built_site)
            print("PASS  representative built pages satisfy static accessibility checks")
        elif args.check:
            check()
            print("PASS  documentation site sources stage cleanly")
        else:
            stage(args.output)
            print(f"PASS  staged documentation site at {args.output}")
    except SiteBuildError as exc:
        print(f"FAIL  {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
