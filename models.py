from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_login import UserMixin

db = SQLAlchemy()

# --- Database Models ---


class CapaIssue(db.Model):
    __tablename__ = 'capa_issues'
    capa_id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    item_involved = db.Column(db.String(200), nullable=False)
    # Machine information
    machine_name = db.Column(db.String(200))
    # Batch information
    batch_number = db.Column(db.String(100))
    # Paths to initial issue photos (stored as JSON array)
    initial_photos_json = db.Column(db.Text)  # Changed from String(300) to Text
    submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # e.g., 'Open', 'Gemba Pending', 'RCA Pending', 'Action Pending', 'Evidence Pending', 'Closed'
    status = db.Column(db.String(50), default='Open', nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable True for now for existing data

    # Relationships
    company = db.relationship('Company', backref=db.backref('capa_issues', lazy='dynamic'))
    creator = db.relationship('User', backref=db.backref('created_capa_issues', lazy='dynamic'), foreign_keys=[created_by_user_id])
    gemba_investigation = db.relationship('GembaInvestigation', backref='capa_issue',
                                          uselist=False, cascade="all, delete-orphan")  # One-to-one
    root_cause = db.relationship('RootCause', backref='capa_issue',
                                 uselist=False, cascade="all, delete-orphan")  # One-to-one
    action_plan = db.relationship('ActionPlan', backref='capa_issue',
                                  uselist=False, cascade="all, delete-orphan")  # One-to-one
    evidence = db.relationship(
        'Evidence', backref='capa_issue', cascade="all, delete-orphan")  # One-to-many

    @property
    def initial_photos(self):
        if self.initial_photos_json:
            return json.loads(self.initial_photos_json)
        return []

    @initial_photos.setter
    def initial_photos(self, photo_list):
        self.initial_photos_json = json.dumps(photo_list)


class RootCause(db.Model):
    __tablename__ = 'root_causes'
    rc_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey(
        'capa_issues.capa_id'), nullable=False, unique=True)
    # Store AI's 5 Why suggestion as JSON string
    ai_suggested_rc_json = db.Column(db.Text)
    # Store user's adjusted whys as JSON string to support variable number of whys
    user_adjusted_whys_json = db.Column(db.Text)
    # Store the learning examples used by the AI for generating suggestions
    learning_examples_json = db.Column(db.Text)
    # Keep original columns for backward compatibility
    user_adjusted_why1 = db.Column(db.Text)
    user_adjusted_why2 = db.Column(db.Text)
    user_adjusted_why3 = db.Column(db.Text)
    user_adjusted_why4 = db.Column(db.Text)
    user_adjusted_root_cause = db.Column(db.Text)  # Final root cause (Why 5)
    rc_submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def user_adjusted_whys(self):
        """Get the list of user adjusted whys"""
        if self.user_adjusted_whys_json:
            return json.loads(self.user_adjusted_whys_json)
        # For backward compatibility, convert old format to new format
        elif self.user_adjusted_why1:
            whys = []
            if self.user_adjusted_why1:
                whys.append(self.user_adjusted_why1)
            if self.user_adjusted_why2:
                whys.append(self.user_adjusted_why2)
            if self.user_adjusted_why3:
                whys.append(self.user_adjusted_why3)
            if self.user_adjusted_why4:
                whys.append(self.user_adjusted_why4)
            if self.user_adjusted_root_cause:
                whys.append(self.user_adjusted_root_cause)
            return whys
        return []

    @user_adjusted_whys.setter
    def user_adjusted_whys(self, whys_list):
        """Set the list of user adjusted whys"""
        self.user_adjusted_whys_json = json.dumps(whys_list)
        # Also update individual columns for backward compatibility
        if len(whys_list) > 0:
            self.user_adjusted_why1 = whys_list[0]
        if len(whys_list) > 1:
            self.user_adjusted_why2 = whys_list[1]
        if len(whys_list) > 2:
            self.user_adjusted_why3 = whys_list[2]
        if len(whys_list) > 3:
            self.user_adjusted_why4 = whys_list[3]
        if len(whys_list) > 4:
            self.user_adjusted_root_cause = whys_list[4]


class ActionPlan(db.Model):
    __tablename__ = 'action_plans'
    ap_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey(
        'capa_issues.capa_id'), nullable=False, unique=True)
    # Store AI's action suggestions as JSON string
    ai_suggested_actions_json = db.Column(db.Text)
    # Store user adjusted actions as JSON string with PIC and due date for each action
    user_adjusted_actions_json = db.Column(db.Text)
    # Jangan hapus kolom lama untuk menjaga kompatibilitas dengan data yang sudah ada
    user_adjusted_temp_action = db.Column(db.Text)
    user_adjusted_prev_action = db.Column(db.Text)
    pic_name = db.Column(db.String(150))  # Person in Charge (legacy)
    due_date = db.Column(db.Date)  # Legacy field
    action_submission_timestamp = db.Column(
        db.DateTime, default=datetime.utcnow)


class Evidence(db.Model):
    __tablename__ = 'evidence'
    evidence_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey(
        'capa_issues.capa_id'), nullable=False)
    evidence_photo_path = db.Column(
        db.String(300), nullable=False)
    evidence_description = db.Column(db.Text)
    action_type = db.Column(db.String(20))  # 'temporary' atau 'preventive'
    action_index = db.Column(db.Integer)     # Indeks tindakan dalam daftar
    evidence_submission_timestamp = db.Column(
        db.DateTime, default=datetime.utcnow)


class GembaInvestigation(db.Model):
    __tablename__ = 'gemba_investigations'
    gemba_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey(
        'capa_issues.capa_id'), nullable=False, unique=True)
    # Text of the findings, including suspected causes and factors
    findings = db.Column(db.Text, nullable=False)
    gemba_photos_json = db.Column(db.Text)  # Store photo paths as JSON array
    gemba_submission_timestamp = db.Column(
        db.DateTime, default=datetime.utcnow)

    @property
    def gemba_photos(self):
        if self.gemba_photos_json:
            return json.loads(self.gemba_photos_json)
        return []

    @gemba_photos.setter
    def gemba_photos(self, photo_list):
        self.gemba_photos_json = json.dumps(photo_list)


class AIKnowledgeBase(db.Model):
    __tablename__ = 'ai_knowledge_base'
    knowledge_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey(
        'capa_issues.capa_id'), nullable=False)

    # Contextual information duplicated for easier querying and filtering
    machine_name = db.Column(db.String(200), nullable=True)
    issue_description = db.Column(db.Text, nullable=True)

    # User-adjusted data, specific to the source_type
    # For source_type = 'rca_adjustment'
    # Stores JSON array of why strings
    adjusted_whys_json = db.Column(db.Text, nullable=True)

    # For source_type = 'action_plan_adjustment'
    # Stores JSON array of action text strings (simplified, no PIC, due_date etc.)
    adjusted_temporary_actions_json = db.Column(db.Text, nullable=True)
    adjusted_preventive_actions_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Flag to disable/enable knowledge entries
    is_active = db.Column(db.Boolean, default=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Relationship to CapaIssue
    company = db.relationship('Company', backref=db.backref('ai_knowledge_base_entries', lazy='dynamic'))
    capa_issue = db.relationship('CapaIssue', backref=db.backref(
        'knowledge_entries', lazy='dynamic'))


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    company_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)

    users = db.relationship('User', backref='company', lazy='dynamic')

    def __repr__(self):
        return f'<Company {self.name} ({self.company_code})>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Increased length for stronger hashes
    role = db.Column(db.String(50), nullable=False, default='user') # Roles like 'super_admin', 'admin', 'user'
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True) # Link to company
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    # Add a property to easily check if user is super_admin
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
