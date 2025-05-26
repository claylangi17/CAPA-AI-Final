# run_production.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This is crucial for production settings
project_home = os.path.dirname(__file__)
dotenv_path = os.path.join(project_home, '.env')

# Check if .env file exists and load it
if os.path.exists(dotenv_path):
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}. Production settings might be missing. The server might not start correctly.")

# Now import your app AFTER .env is loaded
try:
    from app import app  # Assuming your Flask app instance is named 'app' in 'app.py'
except ImportError as e:
    print(f"Critical Error: Could not import 'app' from app.py. Ensure app.py exists and is correct. Details: {e}")
    print("The Waitress server cannot start without the Flask app.")
    exit() # Exit if app cannot be imported

from waitress import serve

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0') # Get host from .env or default
    port = int(os.getenv('FLASK_RUN_PORT', 5000)) # Get port from .env or default
    threads = int(os.getenv('WAITRESS_THREADS', 4)) # Get threads from .env or default

    # Ensure FLASK_ENV is set to 'production' in your .env file for security and performance
    flask_env = os.getenv('FLASK_ENV', 'not_set')
    if flask_env != 'production':
        print(f"Warning: FLASK_ENV is '{flask_env}'. It should be 'production' for a production deployment.")

    print(f"Attempting to start production server with Waitress...")
    print(f"Serving Flask app on http://{host}:{port} with {threads} threads.")
    
    try:
        # THIS IS THE LINE THAT ACTUALLY STARTS THE SERVER
        serve(app, host=host, port=port, threads=threads)
    except Exception as e:
        print(f"Critical Error starting Waitress server: {e}")
        print("Please check your .env configuration, Flask app, and ensure the port is not in use.")
