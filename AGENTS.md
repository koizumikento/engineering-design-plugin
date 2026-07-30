# AGENTS.md

## Purpose

This repository is the source-of-truth for the engineering design agent skills. The primary assets are the skill folders under `skills/`.

## Repository structure

- Each skill lives in `skills/<skill-name>/`.
- `SKILL.md` is the authoritative workflow and trigger definition.
- `references/` stores documents that should only be loaded when the skill is actually in use.
- `agents/openai.yaml` stores OpenAI/Codex-facing metadata such as display name, short description, default prompt, and invocation policy.
- `scripts/` contains shared execution helpers used by the skills.
- `templates/` contains reusable specification templates.
- `.claude-plugin/` is kept only for Claude Code installation metadata. It is not the source of truth for skill behavior.

## Editing rules

- Keep `skills/` as the source of truth. The installable Codex package under
  `plugins/engineering-design/` is generated with
  `scripts/sync_codex_plugin_package.py`; do not edit its copied runtime files
  directly.
- Prefer repository-relative paths like `scripts/...`, `templates/...`, and `references/...` in skill docs.
- If you rename or move referenced files, update `README.md`, `docs/engineering-design-plugin-spec.md`, and any affected templates or examples in the same change.
- Keep skill descriptions narrow and explicit so implicit invocation behaves predictably.
- Prefer focused `references/` documents over adding large amounts of text directly into `SKILL.md`.

## OpenAI/Codex notes

- This repository exposes a repo-local Codex plugin from `plugins/engineering-design/.codex-plugin/plugin.json`.
- Use `.agents/plugins/marketplace.json` for repo-local Codex installation metadata instead of repo-local skill symlinks.
- Keep `skills/` as the authoring source of truth. Regenerate the self-contained
  Codex package after changing skills, runtime scripts, templates, or Python
  dependency files.
- Use `agents/openai.yaml` only for metadata and invocation behavior. Keep operational instructions in `SKILL.md`.

## Validation

- For documentation-only changes, verify references and example commands still point to existing paths.
- For workflow changes that mention scripts, prefer validating the documented entrypoints that already exist in `scripts/`.
- Before release validation, run
  `uv run python scripts/sync_codex_plugin_package.py`.
