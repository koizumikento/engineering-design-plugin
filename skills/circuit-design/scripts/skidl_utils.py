#!/usr/bin/env python3
"""Shared helpers for loading SKiDL scripts consistently."""

from __future__ import annotations

import builtins
import importlib.util
import sys
import types
from pathlib import Path


def stabilize_hierarchy_tags(circuit, script_path: Path) -> None:
    """Normalize hierarchy tag checks for importlib-loaded SKiDL scripts.

    SKiDL creates an anonymous top-level node whose source line points into
    frozen importlib when a script is loaded with importlib. The hierarchy is
    still stable because the root node is represented by the empty string, but
    the default `check_tags()` implementation warns anyway. Override the check
    on this circuit so stable named nodes pass without warning while genuinely
    anonymous non-root nodes still warn.
    """

    def check_tags_without_root_warning(self):
        for part in self.parts:
            part.check_tag(create_if_missing=True)
        for node in self.nodes:
            if getattr(node, "tag", None):
                continue
            if getattr(node, "name", None):
                continue
            if getattr(node, "parent", None) is None:
                continue
            node.check_tag(create_if_missing=False)

    circuit.check_tags = types.MethodType(check_tags_without_root_warning, circuit)


def load_skidl_circuit(script_path: Path, module_name: str = "skidl_script"):
    """Load a SKiDL script and return the default circuit after normalization."""

    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    circuit = builtins.default_circuit
    stabilize_hierarchy_tags(circuit, script_path)
    return circuit
