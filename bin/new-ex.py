#!/usr/bin/env python3
"""
Exercise generator and utilities.

Commands:
  new <slug> [--from-registry] [--title ... --prompt ... --tags ... --difficulty ...] [--template exercise-java]
  list [--filter-by-tag TAG]
  validate [--run-build]

Idempotent and safe: refuses to overwrite existing exercises and suggests a -v2 slug.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "questions.yaml"
TEMPLATES = ROOT / "templates"
EXERCISES = ROOT / "exercises"


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def suggest_collision_free_slug(slug: str) -> str:
    base = slug
    m = re.match(r"^(.*?)-v(\d+)$", slug)
    if m:
        base = m.group(1)
        start = int(m.group(2)) + 1
    else:
        start = 2
    i = start
    while (EXERCISES / f"{base}-v{i}").exists():
        i += 1
    return f"{base}-v{i}"


def slug_to_pkg_segment(slug: str) -> str:
    # remove non-alnum and dashes; ensure starts with letter
    seg = re.sub(r"[^A-Za-z0-9]", "", slug)
    if not seg or not seg[0].isalpha():
        seg = f"x{seg}"
    return seg.lower()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_questions_yaml(path: Path) -> List[Dict[str, object]]:
    """A tiny YAML parser for the limited format we use.
    Supports:
      - top-level list of items starting with '- '
      - key: value pairs
      - multi-line 'prompt: |' with indented lines
      - checklist: followed by indented '- ' items
      - tags as comma-separated string
    Comments (# ...) and blank lines are ignored.
    """
    items: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None
    collecting_prompt = False
    prompt_lines: List[str] = []
    prompt_indent = 0
    checklist_mode = False
    checklist_indent = 0

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if collecting_prompt:
            if indent > prompt_indent:
                prompt_lines.append(line[prompt_indent + 2 :])  # strip two spaces beyond base and key
                continue
            else:
                # finish prompt
                if current is not None:
                    current["prompt"] = "\n".join(prompt_lines).rstrip("\n")
                collecting_prompt = False
                prompt_lines = []
                prompt_indent = 0
                # fall-through to normal parsing of this line

        if checklist_mode:
            if indent >= checklist_indent and line.strip().startswith("- "):
                item = line.strip()[2:]
                assert current is not None
                current.setdefault("checklist", []).append(item)
                continue
            else:
                checklist_mode = False
                checklist_indent = 0

        if line.startswith("- ") and indent == 0:
            # start new item
            if current:
                items.append(current)
            current = {}
            tail = line[2:].strip()
            if tail:
                if ":" in tail:
                    k, v = tail.split(":", 1)
                    current[k.strip()] = v.strip()
            continue

        # normal key: value or key: |
        if ":" in line:
            key, val = line.strip().split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "|":
                collecting_prompt = True
                prompt_indent = indent
                prompt_lines = []
                continue
            if key == "checklist":
                checklist_mode = True
                checklist_indent = indent + 2
                assert current is not None
                current["checklist"] = []
                continue
            assert current is not None
            current[key] = val

    if collecting_prompt and current is not None:
        current["prompt"] = "\n".join(prompt_lines).rstrip("\n")
    if current:
        items.append(current)

    # normalize fields
    for it in items:
        if isinstance(it.get("tags"), str):
            tags = [t.strip() for t in str(it["tags"]).split(",") if t.strip()]
            it["tags"] = tags
        if isinstance(it.get("checklist"), list):
            it["checklist"] = [str(x) for x in it["checklist"]]
    return items


def find_question_by_slug(slug: str) -> Optional[Dict[str, object]]:
    if not REGISTRY.exists():
        return None
    for q in parse_questions_yaml(REGISTRY):
        if q.get("slug") == slug:
            return q
    return None


def render_checklist_bullets(items: List[str]) -> str:
    return "\n".join(f"- {s}" for s in items)


def replace_tokens_in_text(content: str, tokens: Dict[str, str]) -> str:
    for k, v in tokens.items():
        content = content.replace(f"${{{k}}}", v)
    return content


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".java", ".kt", ".kts", ".gradle", ".txt"}


def move_exercise_pkg_dirs(base: Path, pkg_segment: str) -> None:
    # For both src/main/java and src/test/java
    for src_root in base.rglob("src/*/java/com/learn/ood/EXERCISE_PKG"):
        new_dir = src_root.parent / "exercises" / pkg_segment
        new_dir.mkdir(parents=True, exist_ok=True)
        # Move all children
        for p in src_root.rglob("*"):
            rel = p.relative_to(src_root)
            dest = new_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(dest))
        # Remove the old placeholder directory
        try:
            shutil.rmtree(src_root)
        except Exception:
            pass


def create_exercise(slug: str, meta: Dict[str, object], template: str = "exercise-java") -> Path:
    dest = EXERCISES / slug
    if dest.exists():
        suggestion = suggest_collision_free_slug(slug)
        eprint(f"Error: exercise '{slug}' already exists at {dest}")
        eprint(f"Suggestion: use '{suggestion}'")
        sys.exit(2)

    src = TEMPLATES / template
    if not src.exists():
        eprint(f"Error: template '{template}' not found under {TEMPLATES}")
        sys.exit(1)

    shutil.copytree(src, dest)

    # Token substitution
    title = str(meta.get("title", slug)).strip() or slug
    prompt = str(meta.get("prompt", "")).strip()
    tags_list = meta.get("tags", [])
    if isinstance(tags_list, str):
        tags_list = [t.strip() for t in tags_list.split(",") if t.strip()]
    tags_str = ", ".join(tags_list)
    difficulty = str(meta.get("difficulty", "unknown")).strip()
    checklist = meta.get("checklist", [])
    if isinstance(checklist, str):
        checklist = [s.strip() for s in checklist.split("\n") if s.strip()]
    checklist_md = render_checklist_bullets(list(checklist)) if checklist else "- [ ] Define your plan"

    tokens = {
        "TITLE": title,
        "PROMPT": prompt,
        "TAGS": tags_str,
        "DIFFICULTY": difficulty,
        "CHECKLIST": checklist_md,
    }

    for p in dest.rglob("*"):
        if p.is_file() and is_text_file(p):
            try:
                content = read_text(p)
                content = replace_tokens_in_text(content, tokens)
                # Replace package placeholder in java source
                pkg_seg = slug_to_pkg_segment(slug)
                content = content.replace(
                    "com.learn.ood.EXERCISE_PKG", f"com.learn.ood.exercises.{pkg_seg}"
                )
                write_text(p, content)
            except UnicodeDecodeError:
                # skip binary or non-text
                pass

    # Move EXERCISE_PKG dirs to exercises/<slugpkg>
    move_exercise_pkg_dirs(dest, slug_to_pkg_segment(slug))

    # Ensure a build file exists (template already provides one)
    build_file = dest / "build.gradle.kts"
    if not build_file.exists():
        write_text(
            build_file,
            (
                "plugins { id(\"java\") }\n\n"
                "dependencies {\n"
                "  implementation(project(\":common\"))\n"
                "  testImplementation(platform(\"org.junit:junit-bom:5.10.2\"))\n"
                "  testImplementation(\"org.junit.jupiter:junit-jupiter\")\n"
                "}\n\n"
                "tasks.test { useJUnitPlatform() }\n"
            ),
        )

    return dest


def cmd_new(args: argparse.Namespace) -> None:
    slug = args.slug
    meta: Dict[str, object] = {}
    if args.from_registry:
        q = find_question_by_slug(slug)
        if not q:
            eprint(f"Error: slug '{slug}' not found in registry {REGISTRY}")
            sys.exit(1)
        meta = q.copy()
    else:
        meta = {
            "slug": slug,
            "title": args.title or slug.replace("-", " ").title(),
            "prompt": args.prompt or "",
            "tags": [t.strip() for t in (args.tags or "").split(",") if t.strip()],
            "difficulty": args.difficulty or "unknown",
            "checklist": [],
        }

    dest = create_exercise(slug, meta, template=args.template)
    print(str(dest))


def cmd_list(args: argparse.Namespace) -> None:
    items = parse_questions_yaml(REGISTRY) if REGISTRY.exists() else []
    tag = args.filter_by_tag
    count = 0
    for it in items:
        tags = [str(t) for t in it.get("tags", [])]
        if tag and tag not in tags:
            continue
        count += 1
        print(f"{it.get('slug')} | {it.get('title')} | {it.get('difficulty')} | {', '.join(tags)}")
    if tag:
        print(f"-- {count} question(s) matched tag '{tag}'")
    else:
        print(f"-- {count} total question(s)")


def which(cmd: str) -> Optional[str]:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        fp = Path(p) / cmd
        if fp.exists() and os.access(fp, os.X_OK):
            return str(fp)
    return None


def cmd_validate(args: argparse.Namespace) -> None:
    required_paths = [
        ROOT / "settings.gradle.kts",
        ROOT / "build.gradle.kts",
        ROOT / "gradle.properties",
        ROOT / ".editorconfig",
        ROOT / "registry" / "questions.yaml",
        ROOT / "templates" / "exercise-java" / "build.gradle.kts",
        ROOT / "common" / "src" / "main" / "java" / "com" / "learn" / "ood" / "common" / "ConsoleIO.java",
        ROOT / "common" / "src" / "test" / "java" / "com" / "learn" / "ood" / "common" / "CommonSmokeTest.java",
    ]
    missing = [str(p) for p in required_paths if not p.exists()]
    if missing:
        eprint("Missing required files:")
        for m in missing:
            eprint(f" - {m}")
        sys.exit(1)

    print("Structure OK")

    if args.run_build:
        gradle_cmd = which("gradle") or which("./gradlew")
        if not gradle_cmd:
            eprint("Gradle not found on PATH. Install Gradle or add a wrapper to run builds.")
            sys.exit(1)
        try:
            subprocess.check_call([gradle_cmd, "test"], cwd=str(ROOT))
        except subprocess.CalledProcessError as e:
            eprint(f"Gradle build failed with exit code {e.returncode}")
            sys.exit(e.returncode)
        print("Build OK")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="OOD Exercise generator and utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new exercise")
    p_new.add_argument("slug", help="Exercise slug, e.g., strategy-pattern-basics")
    p_new.add_argument("--from-registry", action="store_true", help="Create from registry entry")
    p_new.add_argument("--title")
    p_new.add_argument("--prompt")
    p_new.add_argument("--tags", help="Comma-separated tags")
    p_new.add_argument("--difficulty", choices=["easy", "medium", "hard", "unknown"], default="unknown")
    p_new.add_argument("--template", default="exercise-java")
    p_new.set_defaults(func=cmd_new)

    p_list = sub.add_parser("list", help="List questions in registry")
    p_list.add_argument("--filter-by-tag")
    p_list.set_defaults(func=cmd_list)

    p_val = sub.add_parser("validate", help="Validate repository structure (and optionally build)")
    p_val.add_argument("--run-build", action="store_true")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

