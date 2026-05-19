# Python agent work

Use this skill for `apps/agent` changes.

- Keep external SDK handling isolated in small helpers.
- Prefer typed dataclasses or aliases for internal payloads.
- Add tests before or with behavior changes.
- Validate with `npm run validate:agent`.
- Do not require cloud credentials for unit tests.
