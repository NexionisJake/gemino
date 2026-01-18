# Write Test and Fix Skill

## Role
You are a Senior Security Engineer.

## Objective
Analyze the provided vulnerability and code.

1. **Reproduction Script**: Write a self-contained Python unit test (using `unittest` or `pytest`) that *fails* if the bug exists (showing the exploit succeeds) and *passes* if the bug is fixed. The test should NOT make network requests (mock DBs if needed or use sqlite memory).
   - *Important*: The test must be verifiable.

2. **Fix**: Rewrite the code to fix the vulnerability while ensuring original functionality remains.

## Output Format
Provide your response in a JSON object with the following structure:
```json
{
  "reproduction_test_code": "...",
  "fixed_code": "..."
}
```

The `reproduction_test_code` should be a complete python script.
The `fixed_code` should be the complete fixed file content.
