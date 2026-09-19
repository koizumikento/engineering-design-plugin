# Skill behavior evaluation

The four skills have 16 representative/boundary requests in `skills/<name>/evals/evals.json`:
the original 12 plus read-only STEP inspection, repair through completion,
BOM/ERC-only work, and partial specification updates.
The prompts are self-contained; `files` is reserved for actual supplied input files,
relative to that skill directory. Assertions describe outcomes rather than exact
wording. Generated artifacts belong in an isolated output directory, not in the
skill or source tree.

The inspection fixture is a 40 x 20 x 6 mm solid with bottom centre at the origin,
created with OCCT's box primitive and STEP writer. Supply it at the case's `files`
path and compare its SHA-256 before/after inspection. The fixture itself is not
an evaluation result.

## Routing comparison

Use [skill-routing-cases.json](skill-routing-cases.json) for the nine routing
boundaries. `expect` is an ordered list; an empty list with `no_skill: true`
intentionally selects no skill. `reject` names nearby skills that must not be selected. Each skill has
positive and rejection coverage. The release validator checks these invariants.

For a description-only comparison, give a fresh model session just the visible
name/description catalog and one case prompt. Ask for a minimal ordered selection;
do not give it `expect`, `reject`, assertions, or another trial's answer. Record
the actual catalog text/hash, model/settings, selections, and result for each
case/version. This is a classifier comparison, not proof that a host will load
the right references or finish the task. Do not assume a fixed truncation length.

For end-to-end routing, let the host discover the isolated local skills without
an explicit skill invocation. Record actual skill/reference reads separately
from the expected inventory and from output-quality assertions.

## Compare an update

1. Choose the affected cases. Snapshot the baseline skill and its matching runtime
   from the base commit; keep the candidate's skill/runtime separate. A dependency
   change is part of the treatment, so record both lockfile hashes and versions.
2. Run each prompt in a fresh session against the baseline, then the candidate,
   using the same model/settings and available input libraries. Do not give either
   run the assertions, suspected defect, or the other run's answer.
3. Save the final answer, generated files, commands, exit codes, tool versions,
   source/STEP hashes where applicable, actual skill/reference reads, unnecessary
   questions or stops, repair/recheck rounds, and elapsed time. Record tokens only when
   the host supplies them; otherwise use `NOT_EVALUATED`.
4. Grade each assertion with a concrete file, measurement, or output excerpt.
   Use the existing helper CLIs for deterministic evidence. Use human review for
   schematic readability and CAD previews. Report absent tools/data separately
   from assertion failures; do not grant an unsupported PASS.
5. Compare raw pass counts, failures, repair rounds, and time per case. The corpus
   is a starting point, not statistical proof of overall quality. Repeat runs
   before claiming reliable improvement or reporting variation.

Keep model/settings and runtime fixed for prompt-only changes. Baseline failures
are not candidate regressions. A successful agent process exit is not proof of
task completion: grade the actual files, commands, and answers. If policy prevents
even reading the skill, stop affected trials and report output quality as
`NOT_EVALUATED`; do not change permissions to manufacture a passing comparison.
Evaluate other models separately when compatibility claims require them.

Suggested result shape (one file per case/version):

```json
{
  "skill": "integration",
  "case_id": "bottom-interference",
  "revision": "record exact git commit and any uncommitted diff hash",
  "runtime": "record Python, package versions, and lockfile hash",
  "assertions": [
    {"index": 0, "status": "PASS", "evidence": "report path and bottom_gap_mm = -2"}
  ],
  "duration_seconds": 0,
  "tokens": "NOT_EVALUATED",
  "unverified": []
}
```

The values above illustrate the schema; they are not a recorded evaluation run.
The existing `scripts/validate_release.py` checks case structure, unique IDs,
nonempty prompts/assertions, and file references. Unit tests separately exercise
the reproduced ERC, bottom-clearance, and solid-gap failures and native schematic
generation. Neither replaces an actual old/new agent comparison.

## Sources

- [Agent Skills: evaluating output quality](https://agentskills.io/skill-creation/evaluating-skills)
- [Agent Skills: optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
- Existing repository comparison: [STR-231](decisions/STR-231-agent-generation-benchmark.md)
- [OpenAI: Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) — reviewed 2026-09-19.

Guidance checked on 2026-09-08. Keep the previous engine benchmark separate from
current production skill results.
