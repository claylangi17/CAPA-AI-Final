from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

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
    # Path to initial issue photo
    initial_photo_path = db.Column(db.String(300))
    submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # e.g., 'Open', 'Gemba Pending', 'RCA Pending', 'Action Pending', 'Evidence Pending', 'Closed'
    status = db.Column(db.String(50), default='Open', nullable=False)

    # Relationships
    gemba_investigation = db.relationship('GembaInvestigation', backref='capa_issue',
                                 uselist=False, cascade="all, delete-orphan")  # One-to-one
    root_cause = db.relationship('RootCause', backref='capa_issue',
                                 uselist=False, cascade="all, delete-orphan")  # One-to-one
    action_plan = db.relationship('ActionPlan', backref='capa_issue',
                                  uselist=False, cascade="all, delete-orphan")  # One-to-one
    evidence = db.relationship(
        'Evidence', backref='capa_issue', cascade="all, delete-orphan")  # One-to-many


class RootCause(db.Model):
    __tablename__ = 'root_causes'
    rc_id = db.Column(db.Integer, primary_key=True)
    capa_id = db.Column(db.Integer, db.ForeignKey(
        'capa_issues.capa_id'), nullable=False, unique=True)
    # Store AI's 5 Why suggestion as JSON string
    ai_suggested_rc_json = db.Column(db.Text)
    user_adjusted_why1 = db.Column(db.Text)
    user_adjusted_why2 = db.Column(db.Text)
    user_adjusted_why3 = db.Column(db.Text)
    user_adjusted_why4 = db.Column(db.Text)
    user_adjusted_root_cause = db.Column(db.Text)  # Final root cause (Why 5)
    rc_submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)


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
    findings = db.Column(db.Text, nullable=False)  # Text of the findings, including suspected causes and factors
    gemba_photos_json = db.Column(db.Text)  # Store photo paths as JSON array
    gemba_submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def gemba_photos(self):
        if self.gemba_photos_json:
            return json.loads(self.gemba_photos_json)
        return []
    
    @gemba_photos.setter
    def gemba_photos(self, photo_list):
        self.gemba_photos_json = json.dumps(photo_list)
