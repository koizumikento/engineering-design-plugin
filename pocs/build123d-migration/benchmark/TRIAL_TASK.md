# STR-231 trial task

Generate exactly one first-submission CAD source file for the assigned case and
engine.

Inputs:

- shared contract: `pocs/build123d-migration/benchmark/CONTRACT.md`
- assigned specification: `{SPEC_PATH}`
- assigned engine: `{ENGINE}`
- assigned engine guide: `{ENGINE_GUIDE}`
- required output source: `{OUTPUT_PATH}`

Rules:

1. Read only the shared contract, assigned specification, and assigned engine
   guide. Do not inspect another case, any existing CadQuery/build123d
   implementation, another trial, generated STEP, benchmark result, or repair
   source.
2. Use `{ENGINE}` only. The source must publish the completed engine-native
   geometry as a module-level variable named `result`.
3. Do not export files, invoke a runner, execute the source, inspect geometry,
   or revise the source after observing an error. The benchmark harness performs
   the first execution after submission.
4. Keep dimensions as named parameters and implement every requirement in the
   specification. Do not add unspecified geometry.
5. Edit only `{OUTPUT_PATH}`. Finish immediately after the single source file
   has been written.
