# Contributing to Velvet AI Core

Thank you for your interest in contributing to Velvet AI Core!

---

## Code of Conduct

This project adheres to a standard code of conduct. By participating, you agree to uphold professional and respectful communication.

---

## How to Contribute

### Reporting Bugs

1. Check existing [Issues](https://github.com/velvet-ai/velvet-ai-core/issues) to avoid duplicates
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Relevant logs or error messages

### Proposing Features

1. Open a [Discussion](https://github.com/velvet-ai/velvet-ai-core/discussions) first
2. Describe the use case and proposed solution
3. Wait for maintainer feedback before implementing
4. Large features may require design review

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with clear messages
7. Push to your fork
8. Open a PR against `main` branch

---

## Development Setup

### Clone the Repository

```bash
git clone https://github.com/velvet-ai/velvet-ai-core.git
cd velvet-ai-core
```

### Install in Development Mode

```bash
pip install -e .[dev]
```

This installs the package in editable mode with development dependencies.

### Run Tests

```bash
pytest
```

### Type Checking (Optional)

```bash
mypy velvet
```

---

## Coding Standards

### Style Guide

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use descriptive variable names

### Code Structure

- Keep functions focused and small
- Avoid circular imports
- Use `__all__` in `__init__.py` to control exports
- Document public APIs with docstrings

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Keep first line under 72 characters
- Reference issues: "Fix #123: Description"

---

## Testing Guidelines

### Writing Tests

- Use `pytest` framework
- Place tests in `tests/` directory
- Name test files: `test_*.py`
- Name test functions: `test_*`

### Test Coverage

- Aim for >80% code coverage
- Test both success and failure paths
- Include edge cases

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=velvet

# Run specific test file
pytest tests/test_runtime.py
```

---

## Documentation

### Updating Docs

- Keep `README.md` up to date
- Add architecture docs to `docs/` for major features
- Use Markdown format
- Include code examples where helpful

### Docstrings

```python
def example_function(param: str) -> int:
    """
    Brief description of function.
    
    Args:
        param: Description of parameter
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When input is invalid
    """
    pass
```

---

## Pull Request Process

1. **Create PR** with clear title and description
2. **Reference issue** if applicable
3. **Wait for CI** to pass (automated tests)
4. **Address review feedback** from maintainers
5. **Squash commits** if requested
6. **Merge** — Maintainers will merge after approval

### PR Checklist

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear
- [ ] Code follows style guidelines

---

## Release Process

Releases are handled by maintainers:

1. Version bump in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Tag release: `git tag v0.x.0`
4. Push tag: `git push origin v0.x.0`
5. GitHub Actions publishes to PyPI

---

## Questions?

- Open a [Discussion](https://github.com/velvet-ai/velvet-ai-core/discussions)
- Check existing [Issues](https://github.com/velvet-ai/velvet-ai-core/issues)

---

Thank you for contributing!
