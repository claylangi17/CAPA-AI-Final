import markupsafe
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS

# --- Jinja Filters ---


def from_json_filter(json_string):
    """Safely parse a JSON string for use in templates."""
    if not json_string:
        return {}
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON in template: {json_string}")
        return {"error": "Invalid JSON data stored"}  # Return error dict


def nl2br_filter(s):
    """Converts newlines in a string to HTML line breaks."""
    if s:
        return markupsafe.Markup(str(markupsafe.escape(s)).replace('\n', '<br>\n'))
    return ''

# --- Helper Functions ---


def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, upload_folder, add_timestamp=True):
    """Save an uploaded file to the specified folder and return the saved filename."""
    filename = secure_filename(file.filename)
    os.makedirs(upload_folder, exist_ok=True)

    if add_timestamp:
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    else:
        unique_filename = filename

    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    return unique_filename
