---
name: enforce-test-standards
description: Use this skill to ensure that all tests adhere to established standards and guidelines.
---
- Verify that no original test files are modified; only new test files should be created.
- Ensure that all public functions have type annotations for parameters and return values.
- Create a regression test file for each bug fixed, ensuring it contains at least three test functions.
- Document all changes in the CHANGELOG.md under the '## Unreleased' section, with a bullet point for each fix.
- Confirm that all tests pass before finalizing any changes to the codebase.