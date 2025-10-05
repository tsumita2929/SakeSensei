# Repository Guidelines

## Project Structure & Module Organization

Core runtime lives in `agent.py`, the CLI loop that wires Bedrock Sonnet and AgentCore Memory. Tool implementations and AWS integrations reside in `sake_tools.py`; add new utilities by extending `ALL_TOOLS`. Structured sake metadata lives under `data/` as sharded JSON exports that feed Knowledge Base ingestion. Tests are Python `unittest` suites in `tests/`, mirroring memory and preference flows. Shared project config stays in `pyproject.toml`, while local credentials belong in `.env` (see `.env.example`).

## Build, Test, and Development Commands

Always activate the managed virtual environment first: `source .venv/bin/activate`.

- `pip install -e .` — set up an editable install with Python 3.13 dependencies.
- `playwright install chromium` — prepare the headless browser used by pricing tools.
- `python agent.py` — launch the interactive Sake-Sensei console agent.
- `python -m unittest discover tests` — run the current regression suite.

## Coding Style & Naming Conventions

Follow PEP 8 with 4-space indentation, expressive docstrings, and selective inline comments for non-obvious logic (e.g., memory fallbacks). Keep modules and functions snake_case; reserve PascalCase for classes and test fixtures. Prefer type hints for new public helpers and reuse the existing Japanese copy for user-facing strings.

## Testing Guidelines

Extend `unittest.TestCase` in `tests/` and name methods `test_<behavior>` to surface precise failures. Cover both happy paths and error guards when touching memory sessions or AWS calls, and update fakes/stubs to reflect new tool signatures. Run `python -m unittest` locally before pushing and capture any Playwright-dependent flows behind mocks.

## Commit & Pull Request Guidelines

Existing history favors short, imperative messages (e.g., `add data`, `fix web search`); follow that pattern and scope commits narrowly. PRs should summarize intent, link related issues, list manual test results, and include screenshots or logs when UI or agent behavior changes. Flag any infrastructure updates (KB ingest jobs, AWS IDs) in the PR description.

## Security & Configuration Tips

Never commit `.env` or AWS credentials; rely on `.env.example` to document required keys such as `SAKE_AGENT_MEMORY_ID` and `AWS_REGION`. When syncing Knowledge Base data, prefer `aws s3 sync data/ s3://<kb-bucket>/` from a vetted profile, and verify ingestion with the Bedrock console before live demos. When updating Strands or AgentCore integrations, always route requests through the MCP server to pull the latest information and verify specifications.
