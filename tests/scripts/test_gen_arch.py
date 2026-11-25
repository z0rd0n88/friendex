"""Tests for ``.githooks/gen_arch.py`` — the ARCH.md file-tree generator.

These pin the root-label contract: the label on the first line of the
generated tree (``friendex/``) is part of the committed document, so it must
not depend on what a particular clone's folder happens to be called. Before
this was pinned, a checkout named ``Friendex`` and one named ``friendex``
rewrote the label back and forth on every commit.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_GEN_ARCH_PATH = Path(__file__).resolve().parents[2] / ".githooks" / "gen_arch.py"


def _load_gen_arch() -> ModuleType:
    """Import the hook script by path — ``.githooks`` is not a package."""
    spec = importlib.util.spec_from_file_location("gen_arch", _GEN_ARCH_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen_arch = _load_gen_arch()


def _make_repo(parent: Path, folder_name: str) -> Path:
    """Create a one-file git repository in ``parent / folder_name``."""
    root = parent / folder_name
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    return root


def _root_label(document: str) -> str:
    """Return the first line inside the generated tree's code fence."""
    after_marker = document.split(gen_arch.TREE_START, 1)[1]
    return str(after_marker.splitlines()[2])


def test_new_document_labels_root_after_checkout_folder(tmp_path: Path) -> None:
    """With no ARCH.md yet, the label is seeded from the repository folder."""
    root = _make_repo(tmp_path, "SomeProject")

    document = gen_arch.build_document(root, None)

    assert _root_label(document) == "SomeProject/"


def test_existing_root_label_survives_differently_named_checkout(
    tmp_path: Path,
) -> None:
    """A clone under another folder name must not rewrite the committed label."""
    original = _make_repo(tmp_path, "friendex")
    committed = gen_arch.build_document(original, None)
    clone = _make_repo(tmp_path, "Friendex-renamed-clone")

    regenerated = gen_arch.build_document(clone, committed)

    assert _root_label(regenerated) == "friendex/"
    assert gen_arch.normalize(regenerated) == gen_arch.normalize(committed)


@pytest.mark.parametrize(
    "existing",
    ["", "# ARCH\n\nNo generated tree block in here.\n"],
)
def test_existing_root_label_is_none_without_a_tree_block(existing: str) -> None:
    assert gen_arch.existing_root_label(existing) is None


def test_tree_entry_in_the_label_position_is_not_adopted(tmp_path: Path) -> None:
    """A hand-deleted root line must not turn the first tree entry into the label."""
    root = _make_repo(tmp_path, "SomeProject")
    damaged = f"# ARCH\n\n{gen_arch.TREE_START}\n```\n└── README.md\n```\n"

    assert gen_arch.existing_root_label(damaged) is None
    assert _root_label(gen_arch.build_document(root, damaged)) == "SomeProject/"


def test_existing_root_label_reads_the_committed_label() -> None:
    document = f"# ARCH\n\n{gen_arch.TREE_START}\n```\nfriendex/\n└── a.py\n```\n"

    assert gen_arch.existing_root_label(document) == "friendex"


@pytest.mark.parametrize(
    "label_line",
    [
        "README.md",
        "|-- README.md",
        "friendex/  — the bot",
        "a/b/",
        "/",
    ],
)
def test_hand_damaged_label_line_is_not_adopted(
    tmp_path: Path, label_line: str
) -> None:
    """Only the form the generator writes — ``<name>/`` — counts as a label."""
    root = _make_repo(tmp_path, "SomeProject")
    damaged = f"# ARCH\n\n{gen_arch.TREE_START}\n```\n{label_line}\n└── a.py\n```\n"

    assert gen_arch.existing_root_label(damaged) is None
    assert _root_label(gen_arch.build_document(root, damaged)) == "SomeProject/"


def test_root_label_with_a_space_is_kept() -> None:
    document = f"# ARCH\n\n{gen_arch.TREE_START}\n```\nMy Project/\n└── a.py\n```\n"

    assert gen_arch.existing_root_label(document) == "My Project"
