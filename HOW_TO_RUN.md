# How to Run the CAPA AI Assistant Application

This document provides step-by-step instructions to set up and run the CAPA AI Assistant web application locally.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Python 3.x:** Download and install Python from [python.org](https://www.python.org/downloads/). Make sure to add Python to your system's PATH.
*   **pip:** Python's package installer. It usually comes with Python 3.x installations.
*   **MySQL Database Server:** You need a running MySQL server instance. You can download it from [dev.mysql.com/downloads/mysql/](https://dev.mysql.com/downloads/mysql/) or use a managed service.

## 2. Setup Environment

Follow these steps to set up your project environment:

1.  **Clone the Repository (if you haven't already):**
    If you're working from a fresh copy, clone the project repository to your local machine.
    ```bash
    git clone <repository_url>
    cd <repository_folder_name>
    ```

2.  **Create a Virtual Environment (Recommended):**
    It's best practice to use a virtual environment to manage project dependencies.
    Open your terminal or command prompt in the project's root directory and run:
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    *   **Windows (Command Prompt/PowerShell):**
        ```bash
        .venv\Scripts\activate
        ```
    *   **macOS/Linux (bash/zsh):**
        ```bash
        source .venv/bin/activate
        ```
    You should see `(.venv)` at the beginning of your command prompt, indicating the virtual environment is active.

4.  **Create the `.env` Configuration File:**
    In the root directory of the project, create a file named `.env`.
    Copy the following content into it and replace the placeholder values with your actual MySQL database credentials and Google API Key:

    ```plaintext
    DB_USERNAME=your_mysql_username
    DB_PASSWORD=your_mysql_password
    DB_HOST=localhost
    DB_NAME=capa_ai_system
    GOOGLE_API_KEY=your_google_api_key_here
    ```
    *   `DB_USERNAME`: Your MySQL username.
    *   `DB_PASSWORD`: Your MySQL password.
    *   `DB_HOST`: The host where your MySQL server is running (e.g., `localhost` or `127.0.0.1`).
    *   `DB_NAME`: The name of the database the application will use (e.g., `capa_ai_system`). The application will attempt to create this database if it doesn't exist, but your MySQL user needs appropriate permissions.
    *   `GOOGLE_API_KEY`: Your API key for Google Generative AI services. While the primary embedding model has been switched to `sentence-transformers` (which doesn't require this key for embeddings), the key is still used for other AI-powered text generation features within the application.

## 3. Install Dependencies

With your virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

This command will read the `requirements.txt` file and install all listed dependencies.

## 4. Run the Application

Once the setup is complete and dependencies are installed, you can run the Flask application:

```bash
python app.py
```

*   On the first run, the application should automatically create the necessary database tables in the MySQL database specified in your `.env` file.
*   If successful, you'll see output similar to:
    ```
     * Serving Flask app 'app'
     * Debug mode: on
    INFO:werkzeug:Warning: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
     * Running on http://127.0.0.1:5000
    INFO:werkzeug:Press CTRL+C to quit
    ```

5.  **Access the Application:**
    Open your web browser and navigate to the URL shown in the terminal (usually `http://127.0.0.1:5000` or `http://localhost:5000`).

## Troubleshooting

*   **MySQL Connection Issues:**
    *   Ensure your MySQL server is running.
    *   Double-check your credentials (`DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`) in the `.env` file.
    *   Verify that the MySQL user has permissions to create databases and tables, or that the `DB_NAME` database already exists and the user has access to it.
*   **Dependency Installation Errors:**
    *   Make sure your virtual environment is activated.
    *   Ensure `pip` is up to date: `pip install --upgrade pip`.
*   **`ModuleNotFoundError`:**
    *   Ensure you've installed dependencies using `pip install -r requirements.txt` within the activated virtual environment.

If you encounter other issues, check the terminal output for error messages, which can provide clues to the problem.
