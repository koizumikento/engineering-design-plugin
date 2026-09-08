# Skill behavior evaluation

Each skill has three representative/boundary requests in `skills/<name>/evals/evals.json`.
The prompts are self-contained; `files` is reserved for actual supplied input files,
relative to that skill directory. Assertions describe outcomes rather than exact
wording. Generated artifacts belong in an isolated output directory, not in the
skill or source tree.

## Compare an update

1. Choose the affected cases. Snapshot the baseline skill and its matching runtime
   from the base commit; keep the candidate's skill/runtime separate. A dependency
   change is part of the treatment, so record both lockfile hashes and versions.
2. Run each prompt in a fresh session against the baseline, then the candidate,
   using the same model/settings and available input libraries. Do not give either
   run the assertions, suspected defect, or the other run's answer.
3. Save the final answer, generated files, commands, exit codes, tool versions,
   source/STEP hashes where applicable, and elapsed time. Record tokens only when
   the host supplies them; otherwise use `NOT_EVALUATED`.
4. Grade each assertion with a concrete file, measurement, or output excerpt.
   Use the existing helper CLIs for deterministic evidence. Use human review for
   schematic readability and CAD previews. Report absent tools/data separately
   from assertion failures; do not grant an unsupported PASS.
5. Compare raw pass counts, failures, repair rounds, and time per case. Three cases
   are a starting corpus, not statistical proof of overall quality. Repeat runs
   before claiming reliable improvement or reporting variation.

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

Guidance checked on 2026-09-08. Keep the previous engine benchmark separate from
current production skill results.
