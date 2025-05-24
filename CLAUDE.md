# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- **Install Dependencies**: `pip install -r functions/requirements-dev.txt`
- **Run Functions Locally**: `firebase emulators:start`
- **Run All Tests**: `cd functions && pytest tests/`
- **Run Single Test**: `cd functions && pytest tests/path/to/test_file.py::test_function_name`
- **Test with Coverage**: `cd functions && pytest --cov=. tests/`
- **Linting**: `cd functions && pylint functions/`
- **Type Checking**: `cd functions && mypy functions/`

## Git Workflow
- **Individual File Commits**: When asked to commit changes one by one:
  1. Stage individual files: `git add file_path`
  2. Commit with concise message: `git commit -m "Brief description (< 25 chars)"`
  3. Group related files together when logical
  4. Separate functional changes into different commits

## Code Style Guidelines
- **Imports**: Group by standard library, third-party, local imports
- **Types**: Use type hints for function parameters and return values
- **Formatting**: 4-space indentation, ~100 character line limit
- **Naming**: Classes (PascalCase), functions/variables (snake_case), constants (UPPER_SNAKE_CASE)
- **Documentation**: Use Google-style docstrings with Args/Returns sections
- **Error Handling**: Use specific exceptions with descriptive messages, log exceptions consistently
- **API Responses**: Use helper functions (create_response) for consistent API responses
- **Architecture**: Follow repository/service pattern with clear separation of concerns
