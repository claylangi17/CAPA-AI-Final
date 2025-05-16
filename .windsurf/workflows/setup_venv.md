---
description: How to set up and use a Python virtual environment for the CAPA AI Assistant project
---

# Virtual Environment Setup and Usage

This workflow will guide you through setting up and using a Python virtual environment for the CAPA AI Assistant project.

## 1. Create a Virtual Environment

Open a terminal in the project root directory and run, but please check first, if there is already .venv created in the workspaces:

```bash
# Create a new virtual environment named 'venv'
python -m venv venv
```

## 2. Activate the Virtual Environment

### Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows (Command Prompt):
```cmd
.\venv\Scripts\activate.bat
```

## 3. Install Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

## 4. Run the Application

```bash
# Make sure you're in the project root directory
python app.py
```

## 5. Deactivate the Virtual Environment

When you're done working, you can deactivate the virtual environment:

```bash
deactivate
```

## 6. Updating Dependencies

If you add new packages to the project, update the requirements file with:

```bash
pip freeze > requirements.txt
```

## Notes:
- Always activate the virtual environment before working on the project
- The virtual environment directory (venv/) is in .gitignore and won't be committed to version control
- Each developer should create their own virtual environment