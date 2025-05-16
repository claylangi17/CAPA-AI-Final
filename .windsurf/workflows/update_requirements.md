---
description: Update project dependencies and requirements.txt
---

# Update Project Requirements Workflow

This workflow helps manage and update the project's Python dependencies in `requirements.txt`.

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Git (for version control)

## Steps

1. **Check for outdated packages**
   ```bash
   pip list --outdated
   ```

2. **Update requirements.txt**
   ```bash
   pip freeze > requirements.txt
   ```

3. **Check for unused packages**
   ```bash
   pip install pip-autoremove
   pip-autoremove -L
   ```

4. **Generate hashes for secure installation**
   ```bash
   pip-compile --generate-hashes requirements.txt -o requirements.lock
   ```

5. **Install updated dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Test the application**
   ```bash
   python -m pytest tests/
   ```

7. **Commit changes**
   ```bash
   git add requirements.txt requirements.lock
   git commit -m "chore: update project dependencies"
   git push
   ```

## Best Practices

- Always test the application after updating dependencies
- Use virtual environments to isolate project dependencies
- Document any breaking changes in dependency updates
- Consider using `pip-tools` for better dependency management
- Keep system dependencies (like MySQL, wkhtmltopdf) documented in README.md
