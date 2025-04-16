import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import json # For storing AI suggestions later
from flask import make_response # For sending PDF response
from weasyprint import HTML # Import WeasyPrint
from weasyprint import CSS # Import CSS separately
# FontConfiguration is now imported differently in newer versions

# Load environment variables (especially API Key)
load_dotenv()

# --- Gemini AI Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in .env file. AI features will be disabled.")
    # Optionally raise an error or handle this case as needed
    genai.configure(api_key="DUMMY_KEY_SO_APP_DOESNT_CRASH") # Prevent crash if key missing
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Select the model (adjust if needed, check Gemini documentation for available models)
# Using a model suitable for complex reasoning like 5 Why
gemini_model = genai.GenerativeModel('gemini-1.5-flash') # Or 'gemini-pro' etc.


# --- App Configuration ---
app = Flask(__name__)

# --- Custom Jinja Filters ---
def from_json_filter(json_string):
    """Safely parse a JSON string for use in templates."""
    if not json_string:
        return {}
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON in template: {json_string}")
        return {"error": "Invalid JSON data stored"} # Return error dict

app.jinja_env.filters['fromjson'] = from_json_filter
# Add nl2br filter for displaying text with newlines
import markupsafe
def nl2br_filter(s):
    """Converts newlines in a string to HTML line breaks."""
    if s:
        return markupsafe.Markup(str(markupsafe.escape(s)).replace('\n', '<br>\n'))
    return ''
app.jinja_env.filters['nl2br'] = nl2br_filter


app.config['SECRET_KEY'] = os.urandom(24) # Necessary for flash messages and sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///capa_db.sqlite3' # Use SQLite for development
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads' # Folder to store uploaded images
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limit file upload size (e.g., 16MB)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# --- Database Models ---
class CapaIssue(db.Model):
    __tablename__ = 'capa_issues'
    capa_id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    item_involved = db.Column(db.String(200), nullable=False)
    initial_photo_path = db.Column(db.String(300)) # Path to initial issue photo
    submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Open', nullable=False) # e.g., 'Open', 'RCA Pending', 'Action Pending', 'Evidence Pending', 'Closed'

    # Relationships
    root_cause = db.relationship('RootCause', backref='capa_issue', uselist=False, cascade="all, delete-orphan") # One-to-one
    action_plan = db.relationship('ActionPlan', backref='capa_issue', uselist=False, cascade="all, delete-orphan") # One-to-one
    evidence = db.relationship('Evidence', backref='capa_issue', cascade="all, delete-orphan") # One-to-many

class RootCause(db.Model):
    __tablename__ = 'root_causes'
    rc_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey('capa_issues.capa_id'), nullable=False, unique=True)
    ai_suggested_rc_json = db.Column(db.Text) # Store AI's 5 Why suggestion as JSON string
    user_adjusted_why1 = db.Column(db.Text)
    user_adjusted_why2 = db.Column(db.Text)
    user_adjusted_why3 = db.Column(db.Text)
    user_adjusted_why4 = db.Column(db.Text)
    user_adjusted_root_cause = db.Column(db.Text) # Final root cause (Why 5)
    rc_submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ActionPlan(db.Model):
    __tablename__ = 'action_plans'
    ap_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey('capa_issues.capa_id'), nullable=False, unique=True)
    ai_suggested_actions_json = db.Column(db.Text) # Store AI's action suggestions as JSON string
    user_adjusted_actions_json = db.Column(db.Text) # Store user adjusted actions as JSON string with PIC and due date for each action
    # Jangan hapus kolom lama untuk menjaga kompatibilitas dengan data yang sudah ada
    user_adjusted_temp_action = db.Column(db.Text)
    user_adjusted_prev_action = db.Column(db.Text)
    pic_name = db.Column(db.String(150)) # Person in Charge (legacy)
    due_date = db.Column(db.Date) # Legacy field
    action_submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Evidence(db.Model):
    __tablename__ = 'evidence'
    evidence_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey('capa_issues.capa_id'), nullable=False)
    evidence_photo_path = db.Column(db.String(300), nullable=False) # Path to evidence photo
    evidence_description = db.Column(db.Text)
    evidence_submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/')
def index():
    issues = CapaIssue.query.order_by(CapaIssue.submission_timestamp.desc()).all()
    return render_template('index.html', issues=issues)

@app.route('/new', methods=['GET', 'POST'])
def new_capa():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        item_involved = request.form.get('item_involved')
        issue_date_str = request.form.get('issue_date')
        issue_description = request.form.get('issue_description')
        initial_photo = request.files.get('initial_photo')

        # Basic validation
        if not all([customer_name, item_involved, issue_date_str, issue_description]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('new_capa.html')

        try:
            issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('new_capa.html')

        photo_path = None
        if initial_photo and allowed_file(initial_photo.filename):
            filename = secure_filename(initial_photo.filename)
            # Ensure uploads directory exists
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_dir, exist_ok=True)
            # Create a unique subfolder for each CAPA ID later? For now, just save.
            # Consider adding timestamp or unique ID to filename to prevent overwrites
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            photo_path = os.path.join(upload_dir, unique_filename)
            initial_photo.save(photo_path)
            photo_path = unique_filename # Store relative path in DB

        # Create new CAPA Issue
        new_issue = CapaIssue(
            customer_name=customer_name,
            item_involved=item_involved,
            issue_date=issue_date,
            issue_description=issue_description,
            initial_photo_path=photo_path,
            status='Open' # Initial status
        )

        try:
            db.session.add(new_issue)
            # Commit here to get the new_issue.capa_id
            db.session.commit()

            flash(f'New CAPA issue (ID: {new_issue.capa_id}) created successfully! Triggering AI Root Cause Analysis...', 'success')

            # --- Trigger AI Root Cause Analysis ---
            try:
                trigger_rca_analysis(new_issue.capa_id)
                # Update status after triggering AI
                new_issue.status = 'RCA Pending' # Update status
                db.session.commit() # Commit status change
            except Exception as ai_error:
                 # Log the error, flash a warning that AI analysis failed
                 print(f"Error triggering AI RCA for CAPA ID {new_issue.capa_id}: {ai_error}")
                 flash(f'Issue {new_issue.capa_id} created, but AI Root Cause Analysis failed: {ai_error}', 'warning')
            # ------------------------------------

            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback() # Rollback issue creation if anything failed
            flash(f'Error creating CAPA issue: {str(e)}', 'danger')
            # Clean up saved photo if DB commit failed
            if photo_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], photo_path)):
                 os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo_path))


    # GET request: just display the form
    return render_template('new_capa.html')

@app.route('/view/<int:capa_id>')
def view_capa(capa_id):
    issue = CapaIssue.query.options(
        db.joinedload(CapaIssue.root_cause), # Eager load related data
        db.joinedload(CapaIssue.action_plan),
        db.joinedload(CapaIssue.evidence)
    ).get_or_404(capa_id)
    return render_template('view_capa.html', issue=issue)

@app.route('/edit_rca/<int:capa_id>', methods=['POST'])
def edit_rca(capa_id):
    issue = CapaIssue.query.options(db.joinedload(CapaIssue.root_cause)).get_or_404(capa_id)
    rc = issue.root_cause

    if not rc:
        flash('Root Cause Analysis data not found for this issue.', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))

    # Get adjusted values from form
    rc.user_adjusted_why1 = request.form.get('user_adjusted_why1')
    rc.user_adjusted_why2 = request.form.get('user_adjusted_why2')
    rc.user_adjusted_why3 = request.form.get('user_adjusted_why3')
    rc.user_adjusted_why4 = request.form.get('user_adjusted_why4')
    rc.user_adjusted_root_cause = request.form.get('user_adjusted_root_cause')
    rc.rc_submission_timestamp = datetime.utcnow() # Update timestamp

    # Update issue status
    issue.status = 'Action Pending' # Move to next stage

    try:
        db.session.commit()
        flash('Adjusted Root Cause submitted successfully! Triggering AI Action Plan recommendation...', 'success')

        # --- Trigger AI Action Plan Recommendation ---
        try:
            trigger_action_plan_recommendation(capa_id)
            # Status remains 'Action Pending' until user submits the plan details
        except Exception as ai_error:
            # Log the error, flash a warning that AI action plan failed
            print(f"Error triggering AI Action Plan for CAPA ID {capa_id}: {ai_error}")
            flash(f'Adjusted Root Cause submitted, but AI Action Plan recommendation failed: {ai_error}', 'warning')
        # -----------------------------------------

        return redirect(url_for('view_capa', capa_id=capa_id))
    except Exception as e:
        db.session.rollback() # Rollback RCA submission if anything failed before redirect
        flash(f'Error submitting adjusted Root Cause: {str(e)}', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Route to serve uploaded files (needed to display images in templates)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- AI Integration ---
def trigger_rca_analysis(capa_id):
    """Fetches issue details, calls Gemini for 5 Why analysis, and stores the result."""
    if not GOOGLE_API_KEY:
        print(f"Skipping AI RCA for CAPA ID {capa_id}: API Key not configured.")
        return # Don't proceed if API key is missing

    issue = CapaIssue.query.get(capa_id)
    if not issue:
        print(f"Error: Could not find CAPA Issue with ID {capa_id} for AI analysis.")
        return

    # --- Prepare Prompt in Bahasa Indonesia ---
    prompt = f"""
    Analisis masalah pengemasan manufaktur berikut menggunakan teknik 5 Whys untuk menentukan akar masalah.
    Berikan output dalam bentuk objek JSON dengan kunci "why1", "why2", "why3", "why4", dan "root_cause" (untuk why ke-5).
    PENTING: Berikan SEMUA TANGGAPAN dalam BAHASA INDONESIA.

    Detil Masalah:
    Pelanggan: {issue.customer_name}
    Item yang Terlibat: {issue.item_involved}
    Deskripsi Masalah: {issue.issue_description}

    Contoh Format Output JSON:
    {{
      "why1": "Alasan tingkat pertama",
      "why2": "Alasan tingkat kedua yang dibangun dari yang pertama",
      "why3": "Alasan tingkat ketiga",
      "why4": "Alasan tingkat keempat",
      "root_cause": "Akar masalah yang mendasar"
    }}

    Lakukan analisis 5 Why sekarang berdasarkan *hanya* pada Detail Masalah yang diberikan. Berikan semua hasil dalam Bahasa Indonesia.
    """

    try:
        print(f"Sending prompt to Gemini for CAPA ID {capa_id}...")
        response = gemini_model.generate_content(prompt)

        # Attempt to parse the response as JSON
        try:
            # Gemini might wrap JSON in ```json ... ```, try to extract it
            ai_suggestion_text = response.text.strip()
            if ai_suggestion_text.startswith("```json"):
                ai_suggestion_text = ai_suggestion_text[7:]
            if ai_suggestion_text.endswith("```"):
                ai_suggestion_text = ai_suggestion_text[:-3]

            ai_suggestion_json = json.loads(ai_suggestion_text.strip())
            # Basic validation of expected keys
            if not all(k in ai_suggestion_json for k in ["why1", "why2", "why3", "why4", "root_cause"]):
                 raise ValueError("AI response missing expected 5 Why keys.")
            ai_suggestion_str = json.dumps(ai_suggestion_json) # Store validated JSON string
            print(f"AI RCA Suggestion received for CAPA ID {capa_id}")

        except (json.JSONDecodeError, ValueError) as parse_error:
            print(f"Error parsing AI response for CAPA ID {capa_id}: {parse_error}")
            print(f"Raw AI Response:\n{response.text}")
            # Store the raw text if JSON parsing fails, maybe update status differently?
            ai_suggestion_str = f'{{"error": "Failed to parse AI response", "raw_response": {json.dumps(response.text)}}}'
            # Consider flashing a specific warning to the user later

        # Store the result in the database
        existing_rc = RootCause.query.filter_by(capa_id=capa_id).first()
        if existing_rc:
            existing_rc.ai_suggested_rc_json = ai_suggestion_str
            existing_rc.rc_submission_timestamp = datetime.utcnow() # Update timestamp
        else:
            new_rc = RootCause(
                capa_id=capa_id,
                ai_suggested_rc_json=ai_suggestion_str
            )
            db.session.add(new_rc)

        db.session.commit()
        print(f"AI RCA Suggestion stored for CAPA ID {capa_id}.")

    except Exception as e:
        # Handle potential API errors (rate limits, connection issues, etc.)
        print(f"Error calling Gemini API for CAPA ID {capa_id}: {e}")
        # Re-raise the exception so the calling function can handle it (e.g., flash message)
        raise e

def trigger_action_plan_recommendation(capa_id):
    """Fetches issue and final RCA, calls Gemini for action plan, stores result."""
    if not GOOGLE_API_KEY:
        print(f"Skipping AI Action Plan for CAPA ID {capa_id}: API Key not configured.")
        return

    issue = CapaIssue.query.options(db.joinedload(CapaIssue.root_cause)).get(capa_id)
    if not issue or not issue.root_cause or not issue.root_cause.user_adjusted_root_cause:
        print(f"Error: Cannot trigger Action Plan AI for CAPA ID {capa_id}. Missing issue or final root cause.")
        return

    final_rc = issue.root_cause.user_adjusted_root_cause

    # --- Prepare Prompt in Bahasa Indonesia ---
    prompt = f"""
    Berdasarkan masalah pengemasan manufaktur yang dijelaskan di bawah ini dan akar masalah yang telah ditentukan, rekomendasikan Tindakan Sementara (temporary) dan Tindakan Pencegahan (preventive) yang spesifik dan terukur.
    
    PENTING: Berikan SEMUA TANGGAPAN dalam BAHASA INDONESIA.

    Detail Masalah:
    Pelanggan: {issue.customer_name}
    Item yang Terlibat: {issue.item_involved}
    Deskripsi Masalah: {issue.issue_description}
    Akar Masalah Akhir: {final_rc}

    Berikan output dalam format JSON berikut (tanpa nested JSON yang kompleks):
    {{
      "temporary_action": [
        {{
          "langkah": "Deskripsi langkah tindakan sementara 1 (hanya deskripsi langkah, tidak perlu properti lain)"
        }},
        {{
          "langkah": "Deskripsi langkah tindakan sementara 2 (hanya deskripsi langkah, tidak perlu properti lain)"
        }}
      ],
      "preventive_action": [
        {{
          "langkah": "Deskripsi langkah tindakan pencegahan 1 (hanya deskripsi langkah, tidak perlu properti lain)"
        }},
        {{
          "langkah": "Deskripsi langkah tindakan pencegahan 2 (hanya deskripsi langkah, tidak perlu properti lain)"
        }}
      ]
    }}
    
    Perhatikan! Berikan HANYA langkah tindakan untuk setiap item, tanpa indikator keberhasilan, penanggung jawab, atau deadline - itu akan ditambahkan oleh pengguna aplikasi.
    
    OUTPUT harus merupakan JSON yang valid dan sederhana. Hanya berisi array langkah-langkah tindakan yang perlu dilakukan.
    Buat 3-4 langkah tindakan sementara dan 2-3 langkah tindakan pencegahan yang spesifik dan relevan dengan masalah tersebut.
    Pastikan semuanya dalam Bahasa Indonesia.
    """

    try:
        print(f"Sending Action Plan prompt to Gemini for CAPA ID {capa_id}...")
        response = gemini_model.generate_content(prompt)

        # Attempt to parse JSON
        try:
            ai_suggestion_text = response.text.strip()
            if ai_suggestion_text.startswith("```json"): ai_suggestion_text = ai_suggestion_text[7:]
            if ai_suggestion_text.endswith("```"): ai_suggestion_text = ai_suggestion_text[:-3]
            
            ai_suggestion_json = json.loads(ai_suggestion_text.strip())
            if not all(k in ai_suggestion_json for k in ["temporary_action", "preventive_action"]):
                raise ValueError("AI response missing expected action plan keys.")
                
            # Validasi bahwa temporary_action dan preventive_action adalah array
            temp_actions = ai_suggestion_json["temporary_action"]
            prev_actions = ai_suggestion_json["preventive_action"]
            
            if not isinstance(temp_actions, list) or not isinstance(prev_actions, list):
                # Jika masih dalam string, coba parse lagi
                if isinstance(temp_actions, str):
                    try:
                        temp_actions = json.loads(temp_actions)
                    except:
                        temp_actions = [{"langkah": temp_actions}]
                
                if isinstance(prev_actions, str):
                    try:
                        prev_actions = json.loads(prev_actions)
                    except:
                        prev_actions = [{"langkah": prev_actions}]
                        
                ai_suggestion_json["temporary_action"] = temp_actions
                ai_suggestion_json["preventive_action"] = prev_actions
            
            # Pastikan setiap item memiliki properti langkah
            for action_list in [temp_actions, prev_actions]:
                for i, action in enumerate(action_list):
                    if not isinstance(action, dict):
                        action_list[i] = {"langkah": str(action)}
                    elif "langkah" not in action:
                        action["langkah"] = "Tindakan " + str(i+1)
            
            ai_suggestion_str = json.dumps(ai_suggestion_json)
            print(f"AI Action Plan Suggestion received for CAPA ID {capa_id}")

        except (json.JSONDecodeError, ValueError) as parse_error:
            print(f"Error parsing AI Action Plan response for CAPA ID {capa_id}: {parse_error}")
            print(f"Raw AI Response:\n{response.text}")
            ai_suggestion_str = f'{{"error": "Failed to parse AI response", "raw_response": {json.dumps(response.text)}}}'

        # Store the result
        existing_ap = ActionPlan.query.filter_by(capa_id=capa_id).first()
        if existing_ap:
            existing_ap.ai_suggested_actions_json = ai_suggestion_str
            # Don't update timestamp here, wait for user submission
        else:
            new_ap = ActionPlan(
                capa_id=capa_id,
                ai_suggested_actions_json=ai_suggestion_str
            )
            db.session.add(new_ap)

        # Don't update issue status here, wait for user submission of action plan details
        db.session.commit()
        print(f"AI Action Plan Suggestion stored for CAPA ID {capa_id}.")

    except Exception as e:
        print(f"Error calling Gemini API for Action Plan (CAPA ID {capa_id}): {e}")
        # Re-raise the exception so the calling function flashes a warning
        raise e

@app.route('/edit_action_plan/<int:capa_id>', methods=['POST'])
def edit_action_plan(capa_id):
    issue = CapaIssue.query.options(db.joinedload(CapaIssue.action_plan)).get_or_404(capa_id)
    ap = issue.action_plan

    if not ap:
        flash('Data Rencana Tindakan tidak ditemukan untuk masalah ini.', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))
    
    # --- Mengambil data dari form baru ---
    # Temp Actions
    temp_action_texts = request.form.getlist('temp_action_text[]')
    temp_action_indicators = request.form.getlist('temp_action_indicator[]')
    temp_action_pics = request.form.getlist('temp_action_pic[]')
    temp_action_due_dates = request.form.getlist('temp_action_due_date[]')
    temp_action_completed = request.form.getlist('temp_action_completed[]')
    
    # Prev Actions
    prev_action_texts = request.form.getlist('prev_action_text[]')
    prev_action_indicators = request.form.getlist('prev_action_indicator[]')
    prev_action_pics = request.form.getlist('prev_action_pic[]')
    prev_action_due_dates = request.form.getlist('prev_action_due_date[]')
    prev_action_completed = request.form.getlist('prev_action_completed[]')
    
    # Validasi data
    if not temp_action_texts or not prev_action_texts:
        flash('Silakan isi setidaknya satu tindakan sementara dan tindakan pencegahan.', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))
    
    if not all(temp_action_pics) or not all(prev_action_pics):
        flash('Setiap tindakan harus memiliki Penanggung Jawab (PIC).', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))
    
    if not all(temp_action_due_dates) or not all(prev_action_due_dates):
        flash('Setiap tindakan harus memiliki Tanggal Jatuh Tempo.', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))
    
    # Menyiapkan struktur data JSON
    temp_actions = []
    for i, text in enumerate(temp_action_texts):
        try:
            due_date = datetime.strptime(temp_action_due_dates[i], '%Y-%m-%d').date() if i < len(temp_action_due_dates) else None
            due_date_str = due_date.strftime('%Y-%m-%d') if due_date else ''
        except ValueError:
            flash(f'Format Tanggal Jatuh Tempo tidak valid untuk Tindakan Sementara #{i+1}. Gunakan format YYYY-MM-DD.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))
        
        is_completed = str(i) in temp_action_completed
        
        temp_actions.append({
            'action_text': text,
            'indicator': temp_action_indicators[i] if i < len(temp_action_indicators) else '',
            'pic': temp_action_pics[i] if i < len(temp_action_pics) else '',
            'due_date': due_date_str,
            'completed': is_completed
        })
    
    prev_actions = []
    for i, text in enumerate(prev_action_texts):
        try:
            due_date = datetime.strptime(prev_action_due_dates[i], '%Y-%m-%d').date() if i < len(prev_action_due_dates) else None
            due_date_str = due_date.strftime('%Y-%m-%d') if due_date else ''
        except ValueError:
            flash(f'Format Tanggal Jatuh Tempo tidak valid untuk Tindakan Pencegahan #{i+1}. Gunakan format YYYY-MM-DD.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))
        
        is_completed = str(i) in prev_action_completed
        
        prev_actions.append({
            'action_text': text,
            'indicator': prev_action_indicators[i] if i < len(prev_action_indicators) else '',
            'pic': prev_action_pics[i] if i < len(prev_action_pics) else '',
            'due_date': due_date_str,
            'completed': is_completed
        })
    
    # Simpan data terstruktur ke kolom user_adjusted_actions_json
    adjusted_actions = {
        'temp_actions': temp_actions,
        'prev_actions': prev_actions,
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    ap.user_adjusted_actions_json = json.dumps(adjusted_actions)
    
    # Untuk kompatibilitas dengan versi lama
    ap.user_adjusted_temp_action = request.form.get('user_adjusted_temp_action')
    ap.user_adjusted_prev_action = request.form.get('user_adjusted_prev_action')
    ap.pic_name = request.form.get('pic_name')
    due_date_str = request.form.get('due_date')
    
    try:
        if due_date_str:
            ap.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    except ValueError:
        # Gunakan tanggal jatuh tempo dari tindakan pertama jika format tidak valid
        if temp_actions and temp_actions[0]['due_date']:
            ap.due_date = datetime.strptime(temp_actions[0]['due_date'], '%Y-%m-%d').date()
    
    ap.action_submission_timestamp = datetime.utcnow() # Update timestamp
    
    # Update issue status
    issue.status = 'Evidence Pending' # Move to next stage
    
    try:
        db.session.commit()
        flash('Rencana Tindakan berhasil diajukan!', 'success')
        return redirect(url_for('view_capa', capa_id=capa_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error saat mengajukan Rencana Tindakan: {str(e)}', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))

@app.route('/submit_evidence/<int:capa_id>', methods=['POST'])
def submit_evidence(capa_id):
    issue = CapaIssue.query.get_or_404(capa_id)

    if issue.status != 'Evidence Pending':
        flash(f'Cannot submit evidence for issue in status "{issue.status}".', 'warning')
        return redirect(url_for('view_capa', capa_id=capa_id))

    evidence_photo = request.files.get('evidence_photo')
    evidence_description = request.form.get('evidence_description')

    # Validate file upload
    if not evidence_photo or evidence_photo.filename == '':
        flash('Evidence photo is required.', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))

    if not allowed_file(evidence_photo.filename):
        flash('Invalid file type for evidence photo. Allowed types: png, jpg, jpeg, gif.', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))

    # Save the file
    filename = secure_filename(evidence_photo.filename)
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir, exist_ok=True) # Ensure directory exists
    unique_filename = f"evidence_{capa_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    photo_path = os.path.join(upload_dir, unique_filename)

    try:
        evidence_photo.save(photo_path)
        photo_relative_path = unique_filename # Store relative path

        # Create Evidence record
        new_evidence = Evidence(
            capa_id=capa_id,
            evidence_photo_path=photo_relative_path,
            evidence_description=evidence_description
        )
        db.session.add(new_evidence)

        # Update issue status to Closed
        issue.status = 'Closed'

        db.session.commit()
        flash('Evidence submitted and CAPA issue closed successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting evidence: {str(e)}', 'danger')
        # Clean up saved photo if DB commit failed
        if os.path.exists(photo_path):
             os.remove(photo_path)

    return redirect(url_for('view_capa', capa_id=capa_id))

@app.route('/report/<int:capa_id>/pdf')
def generate_pdf_report(capa_id):
    issue = CapaIssue.query.options(
        db.joinedload(CapaIssue.root_cause),
        db.joinedload(CapaIssue.action_plan),
        db.joinedload(CapaIssue.evidence)
    ).get_or_404(capa_id)

    # Render the HTML template with the issue data
    # Pass datetime to template context for footer generation
    html_out = render_template('report_template.html', issue=issue, datetime=datetime)

    try:
        # Use WeasyPrint to generate PDF from HTML string
        # font_config = FontConfiguration() # Optional: configure fonts if needed
        # css = CSS(string='@page { size: A4; margin: 1cm; }', font_config=font_config) # Example CSS
        pdf_bytes = HTML(string=html_out, base_url=request.base_url).write_pdf() # Pass base_url for relative paths like images

        # Create a Flask response object with the PDF data
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=capa_report_{capa_id}.pdf' # Or 'attachment;' to force download
        return response

    except Exception as e:
        print(f"Error generating PDF for CAPA ID {capa_id}: {e}")
        flash(f'Error generating PDF report: {str(e)}', 'danger')
        return redirect(url_for('view_capa', capa_id=capa_id))


# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables if they don't exist
    app.run(debug=True) # Run in debug mode for development