# CAPA AI Assistant

![CAPA AI Assistant](https://img.shields.io/badge/Status-Active-brightgreen)

A comprehensive Corrective and Preventive Action (CAPA) management system powered by AI to help track, analyze, and resolve quality issues in manufacturing environments.

## ✨ Features

- 📝 Create and track CAPA issues with detailed metadata
- 🤖 AI-powered root cause analysis and solution suggestions
- 📊 Interactive dashboards for issue tracking and reporting
- 🔍 Advanced search and filtering capabilities
- 🔄 Workflow automation for CAPA processes
- 📱 Responsive design for desktop and mobile use

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL Server
- Git (optional)
- wkhtmltopdf (for PDF generation)
  - **Windows**: Download and install from [wkhtmltopdf downloads](https://wkhtmltopdf.org/downloads.html), then add to system PATH
  - **macOS**: `brew install --cask wkhtmltopdf`
  - **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install -y wkhtmltopdf`
  - **Other Linux**: Check your distribution's package manager or build from source

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/CAPA-AI-Final.git
   cd CAPA-AI-Final
   ```

2. **Set up a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   DB_USERNAME=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_HOST=localhost
   DB_NAME=capa_ai_system

   # Google Gemini AI API Key (Optional)
   GOOGLE_API_KEY=your_google_api_key_here
   ```

5. **Initialize the database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

### Running the Application

**Development mode:**
```bash
python app.py
```

**Production mode (using Gunicorn):**
```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

The application will be available at: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 📂 Project Structure

```
CAPA-AI-Final/
├── app.py                 # Main application entry point
├── config.py             # Application configuration
├── models.py             # Database models
├── routes.py             # Application routes
├── ai_service.py         # AI service implementation
├── ai_learning.py        # AI learning and processing
├── requirements.txt      # Python dependencies
├── .env.example         # Example environment variables
├── uploads/             # Directory for uploaded files
├── static/              # Static files (CSS, JS, images)
└── templates/           # HTML templates
```

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please open an issue in the repository or contact the development team.

---

*Last Updated: May 2025*
