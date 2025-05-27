# Standard Library
import calendar
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# Third-Party Imports
import pdfkit
import pytz
from flask import (
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from flask_mail import Message
from flask_wtf import FlaskForm
from sqlalchemy import distinct
from werkzeug.utils import secure_filename
from wtforms import (
    PasswordField,
    SelectField,
    StringField,
    SubmitField
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError
)

# Local Application Imports
from ai_learning import store_knowledge_on_capa_close
from ai_service import (
    trigger_action_plan_recommendation,
    trigger_rca_analysis
)
from config import UPLOAD_FOLDER
from models import (
    AIKnowledgeBase,
    CapaIssue,
    Company,
    db,
    Evidence,
    GembaInvestigation,
    User
)
from utils import allowed_file

# Define your local timezone
LOCAL_TIMEZONE = pytz.timezone('Asia/Jakarta')  # Or your specific timezone for +07:00

def register_routes(app):

    @app.context_processor
    def inject_company_context():
        available_companies = []
        selected_company_id = None
        selected_company_name = "All Companies" # Default for super_user if nothing is selected

        if current_user.is_authenticated:
            if current_user.role == 'super_admin':
                available_companies = Company.query.order_by(Company.name).all()
                # Try to get selected company from session
                session_company_id = session.get('selected_company_id')
                if session_company_id and session_company_id != 'all':
                    company = Company.query.get(session_company_id)
                    if company:
                        selected_company_id = company.id
                        selected_company_name = company.name
                elif session_company_id == 'all':
                    selected_company_id = 'all'
                    selected_company_name = "All Companies"
                # If nothing in session for super_admin, default to their own company or 'All Companies'
                elif current_user.company_id: # Super admin has an assigned company
                    company = Company.query.get(current_user.company_id)
                    if company:
                        session['selected_company_id'] = current_user.company_id
                        session['selected_company_name'] = company.name
                        selected_company_id = current_user.company_id
                        selected_company_name = company.name
                    else: # Assigned company not found, default to 'all'
                        session['selected_company_id'] = 'all'
                        session['selected_company_name'] = "All Companies"
                        selected_company_id = 'all'
                        selected_company_name = "All Companies"
                        app.logger.warning(f"Super admin {current_user.username} assigned company ID {current_user.company_id} not found during context injection. Defaulting to 'All Companies'.")
                else: # Super user not tied to a company, defaults to all
                    session['selected_company_id'] = 'all'
                    session['selected_company_name'] = "All Companies"
                    selected_company_id = 'all'
                    selected_company_name = "All Companies"

            else: # Regular user
                if current_user.company_id:
                    company = Company.query.get(current_user.company_id)
                    if company:
                        available_companies = [company] # Only their own company
                        selected_company_id = company.id
                        selected_company_name = company.name
                        session['selected_company_id'] = company.id
                        session['selected_company_name'] = company.name
                    else:
                        # Should not happen if data is consistent
                        flash('Error: Your assigned company is not found. Please contact support.', 'danger')
                        selected_company_name = "Error: Company Not Found"
                else:
                    # User not assigned to any company - critical issue
                    flash('Critical Error: You are not assigned to any company. Please contact support.', 'danger')
                    selected_company_name = "Error: No Company Assigned"
        
        return dict(
            available_companies=available_companies, 
            selected_company_id=selected_company_id,
            selected_company_name=selected_company_name
        )


    class RequestPasswordResetForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired(), Email()])
        submit = SubmitField('Request Password Reset')

    class ResetPasswordForm(FlaskForm):
        password = PasswordField('Password', validators=[DataRequired()])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
        submit = SubmitField('Reset Password')

    class RegistrationForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
        email = StringField('Email', validators=[DataRequired(), Email()])
        company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
        submit = SubmitField('Register')

        def validate_username(self, username):
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

        def validate_email(self, email):
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered. Please choose a different one.')

    class LoginForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)

                # Set initial company context in session after login
                if user.role == 'super_admin':
                    if user.company_id:
                        company = Company.query.get(user.company_id)
                        if company: # Ensure company exists
                            session['selected_company_id'] = user.company_id
                            session['selected_company_name'] = company.name
                        else: # Super admin's assigned company not found, default to 'all'
                            session['selected_company_id'] = 'all'
                            session['selected_company_name'] = "All Companies"
                            app.logger.warning(f"Super admin {user.username} assigned company ID {user.company_id} not found. Defaulting to 'All Companies'.")
                    else: # Super admin not tied to a specific company
                        session['selected_company_id'] = 'all'
                        session['selected_company_name'] = "All Companies"
                else: # Regular user
                    if user.company_id:
                        company = Company.query.get(user.company_id)
                        if company: # Ensure company exists
                            session['selected_company_id'] = user.company_id
                            session['selected_company_name'] = company.name
                        else: # Should not happen if data is consistent
                            session.pop('selected_company_id', None)
                            session.pop('selected_company_name', None)
                            flash('Error: Your assigned company could not be loaded. Please contact support.', 'danger')
                            app.logger.error(f"User {user.username} assigned company ID {user.company_id} not found.")
                    else: # Regular user without a company_id - data integrity issue
                        session.pop('selected_company_id', None)
                        session.pop('selected_company_name', None)
                        flash('Critical Error: You are not assigned to a company. Please contact support.', 'danger')
                        app.logger.error(f"User {user.username} has no company_id assigned.")
                
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    @login_required
    def register():
        if current_user.role != 'super_admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))

        form = RegistrationForm()
        # Populate company choices - ensuring it's done before validation if needed, or on GET
        form.company_id.choices = [
            (c.id, c.name) for c in Company.query.filter(
                Company.name.notin_(['Sansico Group (all company combine)', 'Unassigned'])
            ).order_by(Company.name).all()
        ]
        if not form.company_id.choices:
             flash('No companies available for registration. Please contact an administrator.', 'warning')
             # Potentially disable form or handle differently

        if form.validate_on_submit():
            try:
                user = User(
                    username=form.username.data, 
                    email=form.email.data, 
                    company_id=form.company_id.data,
                    role='user' # Default role for new registrations
                )
                user.set_password(form.password.data) # Hash password
                db.session.add(user)
                db.session.commit()
                flash('Your account has been created! You are now able to log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error during registration: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
        else:
            # Log validation errors for debugging if POST request fails validation
            if request.method == 'POST':
                app.logger.warning(f"Registration form validation errors: {form.errors}")

        return render_template('register.html', title='Register', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    def send_reset_email(user):
        token = user.get_reset_token()
        msg = Message('Password Reset Request',
                      sender=current_app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[user.email])
        msg.html = render_template('reset_email.html', user=user, token=token)
        try:
            # Print mail configuration for debugging
            print(f"Mail Server: {current_app.config['MAIL_SERVER']}")
            print(f"Mail Port: {current_app.config['MAIL_PORT']}")
            print(f"Mail Use TLS: {current_app.config['MAIL_USE_TLS']}")
            print(f"Mail Username: {current_app.config['MAIL_USERNAME']}")
            print(f"Mail Default Sender: {current_app.config['MAIL_DEFAULT_SENDER']}")
            
            # Try to send the email
            current_app.extensions['mail'].send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Error sending password reset email: {e}")
            # More detailed error printing
            import traceback
            traceback.print_exc()
            return False

    @app.route('/request_reset_token', methods=['GET', 'POST'])
    def request_reset_token():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = RequestPasswordResetForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                if send_reset_email(user):
                    flash('An email has been sent with instructions to reset your password.', 'info')
                else:
                    flash('There was an error sending the password reset email. Please try again later or contact support.', 'danger')
            else:
                # Still flash info to prevent user enumeration
                flash('If an account exists with that email, an email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        return render_template('request_reset_token.html', title='Reset Password', form=form)

    @app.route('/reset_token/<token>', methods=['GET', 'POST'])
    def reset_token(token):
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        user = User.verify_reset_token(token)
        if user is None:
            flash('That is an invalid or expired token.', 'warning')
            return redirect(url_for('request_reset_token'))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.set_password(form.password.data)
            db.session.commit()
            flash('Your password has been updated! You are now able to log in.', 'success')
            return redirect(url_for('login'))
        return render_template('reset_token.html', title='Reset Password', form=form)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/select_company', methods=['POST'])
    @login_required
    def select_company():
        if current_user.role != 'super_admin':
            flash('You do not have permission to switch companies.', 'danger')
            return redirect(request.referrer or url_for('index'))

        selected_id = request.form.get('company_id')
        
        if selected_id == 'all':
            session['selected_company_id'] = 'all'
            session['selected_company_name'] = "All Companies"
            flash('Viewing data for All Companies.', 'info')
        else:
            try:
                company_id_int = int(selected_id)
                company = Company.query.get(company_id_int)
                if company:
                    session['selected_company_id'] = company.id
                    session['selected_company_name'] = company.name
                    flash(f'Switched to company: {company.name}', 'success')
                else:
                    flash('Invalid company selected.', 'danger')
            except ValueError:
                flash('Invalid company ID format.', 'danger')
        
        return redirect(request.referrer or url_for('index'))


    @app.route('/dashboard/data')
    @login_required
    def dashboard_data():
        s_company_id = session.get('selected_company_id')
        capa_issue_query = CapaIssue.query.filter(CapaIssue.is_deleted == False)
        ai_kb_query = AIKnowledgeBase.query # Assuming you might want to filter this too

        if current_user.role == 'super_admin' and s_company_id == 'all':
            pass # No company filter for super_admin viewing all
        elif s_company_id is not None and s_company_id != 'all':
            try:
                company_id_int = int(s_company_id)
                capa_issue_query = capa_issue_query.filter(CapaIssue.company_id == company_id_int)
                ai_kb_query = ai_kb_query.filter(AIKnowledgeBase.company_id == company_id_int)
            except ValueError:
                app.logger.error(f"Invalid company_id '{s_company_id}' in session for dashboard_data for user {current_user.username}.")
                capa_issue_query = capa_issue_query.filter(CapaIssue.company_id == -1)
                ai_kb_query = ai_kb_query.filter(AIKnowledgeBase.company_id == -1)
        elif current_user.role != 'super_admin' and s_company_id is None:
            app.logger.warning(f"User {current_user.username} (role: {current_user.role}) has no selected_company_id in session for dashboard_data.")
            capa_issue_query = capa_issue_query.filter(CapaIssue.company_id == -1)
            ai_kb_query = ai_kb_query.filter(AIKnowledgeBase.company_id == -1)
        elif current_user.role == 'super_admin' and s_company_id is None:
            app.logger.warning(f"Super admin {current_user.username} has no selected_company_id in session for dashboard_data. Defaulting to all.")
            # No filter, effectively 'all'
            pass 
        else:
            app.logger.error(f"Unexpected company session state for dashboard_data user {current_user.username}, role {current_user.role}, session company ID {s_company_id}.")
            capa_issue_query = capa_issue_query.filter(CapaIssue.company_id == -1)
            ai_kb_query = ai_kb_query.filter(AIKnowledgeBase.company_id == -1)

        # The capa_issue_query and ai_kb_query are already filtered by company context at the beginning of this function.
        # We will use capa_issue_query for all CapaIssue related aggregations.

        try:
            from_date_obj = None
            to_date_obj = None
            today = date.today()

            filter_type = request.args.get('filter_type')
            time_range = request.args.get('range') # For predefined/default

            print(f"Dashboard data request: filter_type='{filter_type}', range='{time_range}', year='{request.args.get('year')}', month='{request.args.get('month')}', week='{request.args.get('week')}', start_date='{request.args.get('start_date')}', end_date='{request.args.get('end_date')}'")

            if filter_type == 'custom':
                start_date_str = request.args.get('start_date')
                end_date_str = request.args.get('end_date') # RESTORED
                if start_date_str:
                    try:
                        from_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        app.logger.warning(f"Invalid start_date format: {start_date_str}")
                if end_date_str:
                    try:
                        to_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        app.logger.warning(f"Invalid end_date format: {end_date_str}")
            elif filter_type == 'ymw': # RESTORED BLOCK
                year_str = request.args.get('year')
                month_str = request.args.get('month') # Can be 'all' or number
                week_str = request.args.get('week')   # Can be 'all' or number

                if year_str:
                    try:
                        year = int(year_str)
                        if month_str and month_str != 'all':
                            month = int(month_str)
                            if 1 <= month <= 12:
                                num_days_in_month = calendar.monthrange(year, month)[1]
                                if week_str and week_str != 'all':
                                    week = int(week_str)
                                    # Simple week definition: week 1 = days 1-7, week 2 = days 8-14, etc.
                                    start_day_of_week = (week - 1) * 7 + 1
                                    end_day_of_week = week * 7
                                    if start_day_of_week <= num_days_in_month:
                                        from_date_obj = date(year, month, start_day_of_week)
                                        to_date_obj = date(year, month, min(end_day_of_week, num_days_in_month))
                                    else:
                                        app.logger.warning(f"Invalid week '{week_str}' for {year}-{month}. Defaulting to whole month.")
                                        from_date_obj = date(year, month, 1)
                                        to_date_obj = date(year, month, num_days_in_month)
                                else: # Year and Month selected, all weeks
                                    from_date_obj = date(year, month, 1)
                                    to_date_obj = date(year, month, num_days_in_month)
                            else:
                                app.logger.warning(f"Invalid month value: {month_str}. Defaulting to whole year {year}.")
                                from_date_obj = date(year, 1, 1)
                                to_date_obj = date(year, 12, 31)
                        else: # Year selected, all months
                            from_date_obj = date(year, 1, 1)
                            to_date_obj = date(year, 12, 31)
                    except ValueError:
                        app.logger.warning(f"Invalid year/month/week format: Y='{year_str}', M='{month_str}', W='{week_str}'. No YMW filter applied.")
            
            elif time_range: # Handles predefined ranges
                if time_range == '12m':
                    from_date_obj = today - timedelta(days=365)
                    to_date_obj = today
                elif time_range == '6m':
                    from_date_obj = today - timedelta(days=180)
                    to_date_obj = today
                elif time_range == '3m':
                    from_date_obj = today - timedelta(days=90)
                    to_date_obj = today
                elif time_range == '1m':
                    from_date_obj = today - timedelta(days=30)
                    to_date_obj = today
                elif time_range == 'all':
                    from_date_obj = None
                    to_date_obj = None # No date filtering for 'all'
                else:
                    app.logger.warning(f"Unknown time_range: {time_range}. Defaulting to 'Last 12 Months'.")
                    from_date_obj = today - timedelta(days=365)
                    to_date_obj = today
            else: # Default if no filter_type and no range (e.g. initial load or unexpected params)
                app.logger.info("No specific date filter parameters, defaulting to 'Last 12 Months'.")
                from_date_obj = today - timedelta(days=365)
                to_date_obj = today

            # Apply date filters to the company-filtered query
            # capa_issue_query is already company-filtered at this point.
            query_after_date_filter = capa_issue_query
            if from_date_obj:
                query_after_date_filter = query_after_date_filter.filter(CapaIssue.issue_date >= from_date_obj)
            # For 'all' time_range, to_date_obj will be None, so this condition won't apply, which is correct.
            # For other ranges, to_date_obj is set to 'today'.
            # For custom range, to_date_obj is the selected end date.
            if to_date_obj:
                query_after_date_filter = query_after_date_filter.filter(CapaIssue.issue_date <= to_date_obj)

            # --- Status Distribution ---
            status_query_aggregated = query_after_date_filter.with_entities(CapaIssue.status, db.func.count(CapaIssue.status)) \
                                               .group_by(CapaIssue.status) \
                                               .order_by(db.func.count(CapaIssue.status).desc())
        
            status_distribution = status_query_aggregated.all()
            status_labels = [row[0] for row in status_distribution]
            status_values = [row[1] for row in status_distribution]
            print(f"Status Distribution: {status_distribution}")

            # --- Top Customers ---
            top_customers_query = query_after_date_filter.with_entities(CapaIssue.customer_name, db.func.count(CapaIssue.customer_name))
            top_customers = top_customers_query.group_by(CapaIssue.customer_name).order_by(db.func.count(CapaIssue.customer_name).desc()).limit(5).all()
            customer_labels = [row[0] for row in top_customers]
            customer_values = [row[1] for row in top_customers]
            print(f"Top Customers: {top_customers}")

            # --- Area Distribution ---
            area_distribution_query = query_after_date_filter.with_entities(CapaIssue.item_involved, db.func.count(CapaIssue.item_involved))
            area_distribution = area_distribution_query.group_by(CapaIssue.item_involved).order_by(db.func.count(CapaIssue.item_involved).desc()).limit(5).all()
            area_labels = [row[0] for row in area_distribution]
            area_values = [row[1] for row in area_distribution]
            print(f"Area Distribution: {area_distribution}")

            # --- Repeated Issues (by description/count) ---
            repeated_issues_query = query_after_date_filter.with_entities(CapaIssue.issue_description, db.func.count(CapaIssue.issue_description))
            repeated_issues = repeated_issues_query.group_by(CapaIssue.issue_description).having(db.func.count(CapaIssue.issue_description) > 1).order_by(db.func.count(CapaIssue.issue_description).desc()).limit(5).all()
            repeated_issues_labels = [row[0] for row in repeated_issues]
            repeated_issues_values = [row[1] for row in repeated_issues]
            print(f"Repeated Issues: {repeated_issues}")

            # --- Top Machines with Most Issues ---
            top_machines_query = query_after_date_filter.with_entities(CapaIssue.machine_name, db.func.count(CapaIssue.machine_name))
            top_machines = top_machines_query.group_by(CapaIssue.machine_name).order_by(db.func.count(CapaIssue.machine_name).desc()).limit(5).all()
            top_machines_labels = [row[0] for row in top_machines]
            top_machines_values = [row[1] for row in top_machines]
            print(f"Top Machines: {top_machines}")

            # --- Issue Trends Over Time (monthly) ---
            issue_trends_query = query_after_date_filter.with_entities(db.func.date_format(CapaIssue.issue_date, '%Y-%m'), db.func.count(CapaIssue.capa_id))
            issue_trends = issue_trends_query.group_by(db.func.date_format(CapaIssue.issue_date, '%Y-%m')).order_by(db.func.date_format(CapaIssue.issue_date, '%Y-%m')).all()
            issue_trends_labels = [row[0] for row in issue_trends]
            issue_trends_values = [row[1] for row in issue_trends]
            print(f"Issue Trends: {issue_trends}")

            return jsonify({
                'status_distribution': {'labels': status_labels, 'values': status_values},
                'top_customers': {'labels': customer_labels, 'values': customer_values},
                'area_distribution': {'labels': area_labels, 'values': area_values},
                'repeated_issues': {'labels': repeated_issues_labels, 'values': repeated_issues_values},
                'top_machines': {'labels': top_machines_labels, 'values': top_machines_values},
                'issue_trends': {'labels': issue_trends_labels, 'values': issue_trends_values}
            })

        except Exception as e:
            print(f"Error in dashboard_data: {str(e)}")
            return jsonify({
                'error': str(e)
            }), 500

    @app.route('/')
    @login_required
    def index():
        s_company_id = session.get('selected_company_id')
        query = CapaIssue.query.filter(CapaIssue.is_deleted == False)

        if current_user.role == 'super_admin' and s_company_id == 'all':
            # Super admin viewing all companies, no company filter
            pass
        elif s_company_id is not None and s_company_id != 'all':
            try:
                company_id_int = int(s_company_id)
                query = query.filter(CapaIssue.company_id == company_id_int)
            except ValueError:
                flash("Invalid company selection in session. Displaying no issues.", "danger")
                app.logger.error(f"Invalid company_id '{s_company_id}' in session for user {current_user.username}.")
                query = query.filter(CapaIssue.company_id == -1) # Effectively no results
        elif current_user.role != 'super_admin' and s_company_id is None:
            # Regular user with no company_id in session (should be set at login)
            flash("Your company context is not set. Please re-login or contact support.", "warning")
            app.logger.warning(f"User {current_user.username} (role: {current_user.role}) has no selected_company_id in session.")
            query = query.filter(CapaIssue.company_id == -1) # Effectively no results
        elif current_user.role == 'super_admin' and s_company_id is None:
            # Super admin with no company_id in session (should be 'all' or a specific ID)
            flash("Company context not fully initialized for admin. Defaulting to all companies view. Please re-select if needed.", "info")
            app.logger.warning(f"Super admin {current_user.username} has no selected_company_id in session. Defaulting to all.")
            # No filter, effectively 'all'
            pass 
        else:
            # Fallback for any other unexpected state
            app.logger.error(f"Unexpected company session state for user {current_user.username}, role {current_user.role}, session company ID {s_company_id}. Displaying no issues.")
            query = query.filter(CapaIssue.company_id == -1) # Effectively no results

        issues = query.order_by(CapaIssue.submission_timestamp.desc()).all()
        return render_template('index.html', issues=issues)


    @app.route('/capa/<int:capa_id>/soft_delete', methods=['POST'])
    @login_required
    def soft_delete_capa(capa_id):
        if current_user.role != 'super_admin':
            flash('You do not have permission to perform this action.', 'danger')
            return redirect(url_for('index'))
        capa_to_delete = CapaIssue.query.get_or_404(capa_id)
        capa_to_delete.is_deleted = True
        capa_to_delete.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('CAPA issue successfully soft-deleted.', 'success')
        return redirect(url_for('index'))

    @app.route('/api/machine_names')
    @login_required
    def api_machine_names():
        s_company_id = session.get('selected_company_id')
        query = db.session.query(distinct(CapaIssue.machine_name)).filter(CapaIssue.machine_name.isnot(None), CapaIssue.machine_name != '')

        if current_user.role == 'super_admin' and s_company_id == 'all':
            # Super admin viewing all companies, no additional company filter needed on query
            pass
        elif s_company_id is not None and s_company_id != 'all':
            try:
                company_id_int = int(s_company_id)
                query = query.filter(CapaIssue.company_id == company_id_int)
            except ValueError:
                app.logger.error(f"Invalid company_id '{s_company_id}' in session for api_machine_names for user {current_user.username}.")
                flash('Invalid company selection for machine names.', 'danger') # User-facing message
                return jsonify([]) # Return empty list on error
        elif current_user.role != 'super_admin': # Regular user
            if current_user.company_id:
                query = query.filter(CapaIssue.company_id == current_user.company_id)
            else:
                app.logger.warning(f"User {current_user.username} (role: {current_user.role}) has no company_id for api_machine_names.")
                flash('Your user profile is not associated with a company.', 'warning')
                return jsonify([])
        elif current_user.role == 'super_admin' and s_company_id is None:
            # Super admin with no company_id in session (should be 'all' or a specific ID after login)
            # This case implies an issue with session initialization, but we'll default to 'all' for safety.
            app.logger.warning(f"Super admin {current_user.username} has no selected_company_id in session for api_machine_names. Defaulting to all.")
            pass # No filter, effectively 'all'
        else:
            # Fallback for any other unexpected state or if a regular user somehow has s_company_id == 'all'
            app.logger.error(f"Unexpected company session state for api_machine_names user {current_user.username}, role {current_user.role}, session company ID {s_company_id}.")
            flash('Could not determine company context for machine names.', 'danger')
            return jsonify([])

        try:
            machine_names_result = query.order_by(CapaIssue.machine_name).all()
            machine_names = [item[0] for item in machine_names_result if item[0]] # Ensure name is not None/empty before adding
            return jsonify(machine_names)
        except Exception as e:
            app.logger.error(f"Error executing query for machine names: {e}")
            return jsonify({'error': 'Could not fetch machine names due to a server error.'}), 500

    @app.route('/gemba/<int:capa_id>', methods=['GET', 'POST'])
    @login_required
    def gemba_investigation(capa_id):
        # Get the CAPA issue
        issue = CapaIssue.query.get_or_404(capa_id)

        # Check if CAPA is closed
        if issue.status == 'Closed':
            flash(
                'CAPA sudah ditutup. Tidak dapat melakukan input atau edit lagi.', 'warning')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Check if already completed gemba
        if issue.gemba_investigation:
            flash('Gemba investigation already completed for this issue.', 'info')
            return redirect(url_for('view_capa', capa_id=capa_id))

        if request.method == 'POST':
            # Get form data with findings and multiple photos
            findings = request.form.get('gemba_findings')
            gemba_photos = request.files.getlist('gemba_photos[]')

            # Basic validation
            if not findings or not gemba_photos:
                flash('Silakan isi temuan dan unggah minimal satu foto bukti.', 'danger')
                return render_template('gemba_investigation.html', issue=issue)

            # Process and save all photos
            photo_paths = []
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_dir, exist_ok=True)

            for photo in gemba_photos:
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    unique_filename = f"gemba_{capa_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    photo.save(os.path.join(upload_dir, unique_filename))
                    photo_paths.append(unique_filename)

            # Create new Gemba Investigation record
            new_gemba = GembaInvestigation(
                capa_id=capa_id,
                findings=findings
            )
            # Set photos using the property setter
            new_gemba.gemba_photos = photo_paths

            try:
                db.session.add(new_gemba)
                db.session.commit()

                # Update issue status and trigger AI RCA
                issue.status = 'RCA Pending'
                db.session.commit()

                flash(
                    'Gemba investigation submitted successfully! Triggering AI Root Cause Analysis...', 'success')

                # Trigger AI RCA with Gemba data
                try:
                    trigger_rca_analysis(capa_id)
                except Exception as ai_error:
                    print(
                        f"Error triggering AI RCA for CAPA ID {capa_id}: {ai_error}")
                    flash(
                        f'Gemba investigation submitted, but AI Root Cause Analysis failed: {ai_error}', 'warning')

                return redirect(url_for('view_capa', capa_id=capa_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving Gemba investigation: {str(e)}', 'danger')

        # GET request or form submission failed
        return render_template('gemba_investigation.html', issue=issue)

    @app.route('/new', methods=['GET', 'POST'])
    @login_required
    def new_capa():
        if request.method == 'POST':
            customer_name = request.form.get('customer_name')
            item_involved = request.form.get('item_involved')
            issue_date_str = request.form.get('issue_date')
            issue_description = request.form.get('issue_description')
            machine_name = request.form.get('machine_name')
            batch_number = request.form.get('batch_number')
            initial_photos_files = request.files.getlist('initial_photos[]')
            saved_photo_filenames = []  # For temporary storage before capa_id is known
            final_photo_filenames = []   # For filenames with capa_id prefix
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'])
            # Ensure upload directory exists
            Path(upload_dir).mkdir(parents=True, exist_ok=True)

            # Basic validation for required text fields
            if not all([customer_name, item_involved, issue_date_str, issue_description]):
                flash('Please fill in all required fields.', 'danger')
                return render_template('new_capa.html')

            # Photo validation (at least one photo if input is required by HTML)
            if not initial_photos_files or not any(f for f in initial_photos_files if f.filename):
                flash('Please upload at least one initial issue photo.', 'danger')
                return render_template('new_capa.html')

            try:
                issue_date = datetime.strptime(
                    issue_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('new_capa.html')

            # Process and save uploaded photos temporarily
            for photo_file in initial_photos_files:
                if photo_file and allowed_file(photo_file.filename):
                    filename = secure_filename(photo_file.filename)
                    timestamp_prefix = datetime.now().strftime(
                        '%Y%m%d%H%M%S%f')  # Microseconds for better uniqueness
                    unique_filename_temp = f"{timestamp_prefix}_{filename}"
                    temp_photo_path = os.path.join(
                        upload_dir, unique_filename_temp)
                    try:
                        photo_file.save(temp_photo_path)
                        saved_photo_filenames.append(unique_filename_temp)
                    except Exception as e_save:
                        flash(
                            f'Error saving photo {filename}: {str(e_save)}', 'danger')
                        for sf_name in saved_photo_filenames:  # Clean up already saved photos in this batch
                            sf_path = os.path.join(upload_dir, sf_name)
                            if os.path.exists(sf_path):
                                try:
                                    os.remove(sf_path)
                                except OSError as e_remove_cleanup:
                                    app.logger.error(
                                        f"Error removing photo {sf_path} during save error cleanup: {e_remove_cleanup}")
                        return render_template('new_capa.html')
                elif photo_file and photo_file.filename:  # If file exists but not allowed
                    flash(
                        f'File type not allowed for {secure_filename(photo_file.filename)}.', 'danger')
                    for sf_name in saved_photo_filenames:  # Clean up already saved photos
                        sf_path = os.path.join(upload_dir, sf_name)
                        if os.path.exists(sf_path):
                            try:
                                os.remove(sf_path)
                            except OSError as e_remove_cleanup:
                                app.logger.error(
                                    f"Error removing photo {sf_path} during type error cleanup: {e_remove_cleanup}")
                    return render_template('new_capa.html')

            # Determine company_id for the new CAPA
            company_id_to_assign = None
            if current_user.role == 'super_admin':
                s_company_id = session.get('selected_company_id')
                if not s_company_id or s_company_id == 'all':
                    flash('Super admins must select a specific company from the dropdown before creating a new CAPA.', 'danger')
                    return redirect(url_for('new_capa')) # Or perhaps url_for('index')
                try:
                    company_id_to_assign = int(s_company_id)
                    # Optional: Verify company_id_to_assign exists in Company table
                    company_exists = Company.query.get(company_id_to_assign)
                    if not company_exists:
                        flash(f'Selected company (ID: {company_id_to_assign}) does not exist. Please select a valid company.', 'danger')
                        return redirect(url_for('new_capa'))
                except ValueError:
                    flash('Invalid company ID selected in session. Please re-select a company.', 'danger')
                    return redirect(url_for('new_capa'))
            else: # Regular user
                if not current_user.company_id:
                    flash('Your user profile is not associated with a company. Cannot create CAPA. Please contact an administrator.', 'danger')
                    return redirect(url_for('index')) # Or a more appropriate page
                company_id_to_assign = current_user.company_id

            # Create new CAPA Issue (without photo paths initially)
            new_issue = CapaIssue(
                customer_name=customer_name,
                item_involved=item_involved,
                issue_date=issue_date,
                issue_description=issue_description,
                machine_name=machine_name,
                batch_number=batch_number,
                status='Open',
                company_id=company_id_to_assign
            )

            try:
                db.session.add(new_issue)
                db.session.commit()  # First commit to get new_issue.capa_id

                # Now, rename photos with capa_id prefix and finalize list
                for temp_filename in saved_photo_filenames:
                    final_filename = f"initial_{new_issue.capa_id}_{temp_filename}"
                    original_path = os.path.join(upload_dir, temp_filename)
                    final_path = os.path.join(upload_dir, final_filename)
                    try:
                        os.rename(original_path, final_path)
                        final_photo_filenames.append(final_filename)
                    except OSError as e_rename:
                        app.logger.error(
                            f"Error renaming photo {temp_filename} to {final_filename}: {e_rename}. Keeping temp name.")
                        # Keep temp name, will lack capa_id prefix but photo isn't lost
                        final_photo_filenames.append(temp_filename)

                if final_photo_filenames:
                    new_issue.initial_photos = final_photo_filenames  # Uses property setter

                new_issue.status = 'Gemba Pending'
                db.session.commit()  # Second commit to save photo paths and status update

                flash(
                    f'New CAPA issue (ID: {new_issue.capa_id}) created successfully with {len(final_photo_filenames)} photo(s)! Please complete the Gemba Investigation.', 'success')
                return redirect(url_for('gemba_investigation', capa_id=new_issue.capa_id))

            except Exception as e:
                db.session.rollback()
                flash(f'Error creating CAPA issue: {str(e)}', 'danger')
                # Clean up all potentially saved photos (temp or final names)
                cleanup_candidates = set(
                    saved_photo_filenames + final_photo_filenames)
                for p_filename in cleanup_candidates:
                    full_p_path = os.path.join(upload_dir, p_filename)
                    if os.path.exists(full_p_path):
                        try:
                            os.remove(full_p_path)
                        except OSError as e_remove:
                            app.logger.error(
                                f"Error removing photo {full_p_path} during rollback: {e_remove}")

        # GET request: just display the form
        return render_template('new_capa.html')

    @app.route('/view/<int:capa_id>')
    @login_required
    def view_capa(capa_id):
        issue = CapaIssue.query.options(
            db.joinedload(CapaIssue.root_cause),  # Eager load related data
            db.joinedload(CapaIssue.action_plan),
            db.joinedload(CapaIssue.evidence)
        ).get_or_404(capa_id)
        return render_template('view_capa.html', issue=issue)

    @app.route('/edit_rca/<int:capa_id>', methods=['POST'])
    @login_required
    def edit_rca(capa_id):
        issue = CapaIssue.query.options(db.joinedload(
            CapaIssue.root_cause)).get_or_404(capa_id)

        # Check if CAPA is closed
        if issue.status == 'Closed':
            flash(
                'CAPA sudah ditutup. Tidak dapat melakukan input atau edit lagi.', 'warning')
            return redirect(url_for('view_capa', capa_id=capa_id))

        rc = issue.root_cause

        if not rc:
            flash('Root Cause Analysis data not found for this issue.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Get all why inputs from the form
        why_inputs = []
        i = 1
        while True:
            why_key = f'why_{i}'
            why_value = request.form.get(why_key)
            if why_value is None or i > 100:  # Safety limit
                break
            if why_value.strip():  # Only add non-empty whys
                why_inputs.append(why_value)
            i += 1

        # Make sure we have at least one why
        if not why_inputs:
            flash('Silakan isi minimal satu analisis why.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Set the whys using our new property
        rc.user_adjusted_whys = why_inputs
        rc.rc_submission_timestamp = datetime.utcnow()  # Update timestamp

        # For backward compatibility, also set the individual fields
        # (This is redundant with our property setter, but keeping for clarity)
        if len(why_inputs) > 0:
            rc.user_adjusted_why1 = why_inputs[0]
        if len(why_inputs) > 1:
            rc.user_adjusted_why2 = why_inputs[1]
        if len(why_inputs) > 2:
            rc.user_adjusted_why3 = why_inputs[2]
        if len(why_inputs) > 3:
            rc.user_adjusted_why4 = why_inputs[3]
        # Always set the root cause to the last entered 'why'
        if why_inputs:  # Ensure there is at least one why
            rc.user_adjusted_root_cause = why_inputs[-1]
        # The following line is now redundant if why_inputs has 5 or more items, but harmless
        if len(why_inputs) > 4:
            # Keeps explicit 5th why logic if needed, but covered above
            rc.user_adjusted_root_cause = why_inputs[4]

        # Update issue status
        issue.status = 'Action Pending'  # Move to next stage

        # Reset any existing user-adjusted action plan to use the new AI suggestions
        if issue.action_plan:
            # Clear any user adjustments but keep the AI suggestions
            issue.action_plan.user_adjusted_actions_json = None
            issue.action_plan.user_adjusted_temp_action = None
            issue.action_plan.user_adjusted_prev_action = None

        try:
            db.session.commit()
            flash(
                'Akar Masalah disesuaikan berhasil! Memicu rekomendasi Rencana Tindakan AI baru...', 'success')

            # --- Trigger AI Action Plan Recommendation ---
            try:
                trigger_action_plan_recommendation(capa_id)
                # Status remains 'Action Pending' until user submits the plan details
            except Exception as ai_error:
                # Log the error, flash a warning that AI action plan failed
                print(
                    f"Error triggering AI Action Plan for CAPA ID {capa_id}: {ai_error}")
                flash(
                    f'Adjusted Root Cause submitted, but AI Action Plan recommendation failed: {ai_error}', 'warning')
            # -----------------------------------------

            return redirect(url_for('view_capa', capa_id=capa_id))
        except Exception as e:
            db.session.rollback()  # Rollback RCA submission if anything failed before redirect
            flash(f'Error submitting adjusted Root Cause: {str(e)}', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

    @app.route('/uploads/<filename>')
    @login_required
    def uploaded_file(filename):
        # Route to serve uploaded files (needed to display images in templates)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/edit_action_plan/<int:capa_id>', methods=['POST'])
    @login_required
    def edit_action_plan(capa_id):
        issue = CapaIssue.query.options(db.joinedload(
            CapaIssue.action_plan)).get_or_404(capa_id)

        # Check if CAPA is closed
        if issue.status == 'Closed':
            flash(
                'CAPA sudah ditutup. Tidak dapat melakukan input atau edit lagi.', 'warning')
            return redirect(url_for('view_capa', capa_id=capa_id))

        ap = issue.action_plan

        if not ap:
            flash('Data Rencana Tindakan tidak ditemukan untuk masalah ini.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # --- Mengambil data dari form baru ---
        # Temp Actions
        temp_action_texts = request.form.getlist('temp_action_text[]')
        temp_action_indicators = request.form.getlist(
            'temp_action_indicator[]')
        temp_action_pics = request.form.getlist('temp_action_pic[]')
        temp_action_due_dates = request.form.getlist('temp_action_due_date[]')
        temp_action_completed = request.form.getlist('temp_action_completed[]')

        # Prev Actions
        prev_action_texts = request.form.getlist('prev_action_text[]')
        prev_action_indicators = request.form.getlist(
            'prev_action_indicator[]')
        prev_action_pics = request.form.getlist('prev_action_pic[]')
        prev_action_due_dates = request.form.getlist('prev_action_due_date[]')
        prev_action_completed = request.form.getlist('prev_action_completed[]')

        # Validasi data
        if not temp_action_texts or not prev_action_texts:
            flash(
                'Silakan isi setidaknya satu tindakan sementara dan tindakan pencegahan.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Check that all items have the required fields
        for i, text in enumerate(temp_action_texts):
            if not text.strip():  # Skip empty items (may happen if JS cleanup fails)
                continue

            if i >= len(temp_action_pics) or not temp_action_pics[i].strip():
                flash(
                    'Setiap tindakan sementara harus memiliki Penanggung Jawab (PIC).', 'danger')
                return redirect(url_for('view_capa', capa_id=capa_id))

            if i >= len(temp_action_due_dates) or not temp_action_due_dates[i].strip():
                flash(
                    'Setiap tindakan sementara harus memiliki Tanggal Jatuh Tempo.', 'danger')
                return redirect(url_for('view_capa', capa_id=capa_id))

        for i, text in enumerate(prev_action_texts):
            if not text.strip():  # Skip empty items (may happen if JS cleanup fails)
                continue

            if i >= len(prev_action_pics) or not prev_action_pics[i].strip():
                flash(
                    'Setiap tindakan pencegahan harus memiliki Penanggung Jawab (PIC).', 'danger')
                return redirect(url_for('view_capa', capa_id=capa_id))

            if i >= len(prev_action_due_dates) or not prev_action_due_dates[i].strip():
                flash(
                    'Setiap tindakan pencegahan harus memiliki Tanggal Jatuh Tempo.', 'danger')
                return redirect(url_for('view_capa', capa_id=capa_id))

        # Menyiapkan struktur data JSON
        temp_actions = []
        for i, text in enumerate(temp_action_texts):
            # Skip empty items
            if not text.strip():
                continue

            try:
                due_date = datetime.strptime(
                    temp_action_due_dates[i], '%Y-%m-%d').date() if i < len(temp_action_due_dates) else None
                due_date_str = due_date.strftime(
                    '%Y-%m-%d') if due_date else ''
            except ValueError:
                flash(
                    f'Format Tanggal Jatuh Tempo tidak valid untuk Tindakan Sementara #{i+1}. Gunakan format YYYY-MM-DD.', 'danger')
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
            # Skip empty items
            if not text.strip():
                continue

            try:
                due_date = datetime.strptime(
                    prev_action_due_dates[i], '%Y-%m-%d').date() if i < len(prev_action_due_dates) else None
                due_date_str = due_date.strftime(
                    '%Y-%m-%d') if due_date else ''
            except ValueError:
                flash(
                    f'Format Tanggal Jatuh Tempo tidak valid untuk Tindakan Pencegahan #{i+1}. Gunakan format YYYY-MM-DD.', 'danger')
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
        ap.user_adjusted_temp_action = request.form.get(
            'user_adjusted_temp_action')
        ap.user_adjusted_prev_action = request.form.get(
            'user_adjusted_prev_action')
        ap.pic_name = request.form.get('pic_name')
        due_date_str = request.form.get('due_date')

        try:
            if due_date_str:
                ap.due_date = datetime.strptime(
                    due_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Gunakan tanggal jatuh tempo dari tindakan pertama jika format tidak valid
            if temp_actions and temp_actions[0]['due_date']:
                ap.due_date = datetime.strptime(
                    temp_actions[0]['due_date'], '%Y-%m-%d').date()

        ap.action_submission_timestamp = datetime.utcnow()  # Update timestamp

        # Update issue status
        issue.status = 'Evidence Pending'  # Move to next stage

        try:
            db.session.commit()

            flash('Rencana Tindakan berhasil diajukan!', 'success')
            return redirect(url_for('view_capa', capa_id=capa_id))
        except Exception as e:
            db.session.rollback()
            flash(
                f'Error saat mengajukan Rencana Tindakan: {str(e)}', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

    @app.route('/submit_evidence/<int:capa_id>', methods=['POST'])
    @login_required
    def submit_evidence(capa_id):
        issue = CapaIssue.query.get_or_404(capa_id)

        if issue.status == 'Closed':
            flash(
                'CAPA sudah ditutup. Tidak dapat melakukan input atau edit lagi.', 'warning')
            return redirect(url_for('view_capa', capa_id=capa_id))

        if issue.status != 'Evidence Pending':
            flash(
                f'Cannot submit evidence for issue in status "{issue.status}".', 'warning')
            return redirect(url_for('view_capa', capa_id=capa_id))

        evidence_photo = request.files.get('evidence_photo')
        evidence_description = request.form.get('evidence_description')

        # Validate file upload
        if not evidence_photo or evidence_photo.filename == '':
            flash('Evidence photo is required.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Menangani upload foto
        evidence_photo = request.files['evidence_photo']
        if evidence_photo and allowed_file(evidence_photo.filename):
            filename = secure_filename(evidence_photo.filename)
            unique_filename = f'{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{filename}'
            evidence_photo.save(os.path.join(UPLOAD_FOLDER, unique_filename))

            # Ambil deskripsi bila ada
            evidence_description = request.form.get('evidence_description', '')

            # Ambil informasi tindakan terkait
            # 'temporary' atau 'preventive'
            action_type = request.form.get('action_type')
            action_index = request.form.get('action_index')

            if action_index and action_index.isdigit():
                action_index = int(action_index)

                # Periksa apakah tindakan yang akan diberi bukti sudah ditandai sebagai selesai
                if issue.action_plan and issue.action_plan.user_adjusted_actions_json:
                    try:
                        action_plan_data = json.loads(
                            issue.action_plan.user_adjusted_actions_json)

                        # Periksa apakah tindakan yang dipilih sudah selesai
                        if action_type == 'temporary' and len(action_plan_data.get('temp_actions', [])) > action_index:
                            if action_plan_data['temp_actions'][action_index].get('completed', False):
                                flash(
                                    'Tindakan ini sudah ditandai selesai. Tidak dapat menambahkan bukti baru.', 'warning')
                                return redirect(url_for('view_capa', capa_id=capa_id))
                        elif action_type == 'preventive' and len(action_plan_data.get('prev_actions', [])) > action_index:
                            if action_plan_data['prev_actions'][action_index].get('completed', False):
                                flash(
                                    'Tindakan ini sudah ditandai selesai. Tidak dapat menambahkan bukti baru.', 'warning')
                                return redirect(url_for('view_capa', capa_id=capa_id))
                    except Exception as e:
                        print(f"Error checking action status: {str(e)}")
                        # Biarkan proses berlanjut jika terjadi kesalahan
            else:
                action_index = None

            # Simpan evidence
            new_evidence = Evidence(
                capa_id=capa_id,
                evidence_photo_path=unique_filename,
                evidence_description=evidence_description,
                action_type=action_type,
                action_index=action_index
            )

            db.session.add(new_evidence)
            db.session.commit()

            # Perbarui status tindakan jika terkait dengan tindakan tertentu
            if action_type and action_index is not None and issue.action_plan and issue.action_plan.user_adjusted_actions_json:
                try:
                    action_plan_data = json.loads(
                        issue.action_plan.user_adjusted_actions_json)

                    if action_type == 'temporary' and len(action_plan_data.get('temp_actions', [])) > action_index:
                        action_plan_data['temp_actions'][action_index]['completed'] = True
                    elif action_type == 'preventive' and len(action_plan_data.get('prev_actions', [])) > action_index:
                        action_plan_data['prev_actions'][action_index]['completed'] = True

                    issue.action_plan.user_adjusted_actions_json = json.dumps(
                        action_plan_data)
                    db.session.commit()
                except Exception as e:
                    print(f"Error updating action plan status: {str(e)}")

            flash('Bukti telah berhasil diupload.', 'success')
        else:
            flash('Gagal mengupload bukti. Format file tidak valid.', 'danger')

        # Redirect with fragment to keep position at Pengajuan Bukti section
        return redirect(url_for('view_capa', capa_id=capa_id) + '#pengajuan-bukti')

    @app.route('/edit_evidence/<int:capa_id>', methods=['POST'])
    @login_required
    def edit_evidence(capa_id):
        issue = CapaIssue.query.get_or_404(capa_id)

        if issue.status == 'Closed':
            flash(
                'CAPA sudah ditutup. Tidak dapat melakukan input atau edit lagi.', 'warning')
            return redirect(url_for('view_capa', capa_id=capa_id))

        if issue.status != 'Evidence Pending':
            flash(
                f'Tidak dapat mengedit bukti untuk CAPA dengan status "{issue.status}".', 'warning')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Get evidence ID from form
        evidence_id = request.form.get('evidence_id')
        if not evidence_id or not evidence_id.isdigit():
            flash('ID bukti tidak valid.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Find the evidence
        evidence = Evidence.query.filter_by(
            evidence_id=int(evidence_id), capa_id=capa_id).first()
        if not evidence:
            flash('Bukti tidak ditemukan.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Get form data
        evidence_description = request.form.get('evidence_description', '')
        evidence_photo = request.files.get('evidence_photo')

        # Update description
        evidence.evidence_description = evidence_description

        # Update photo if provided
        if evidence_photo and evidence_photo.filename:
            if allowed_file(evidence_photo.filename):
                # Delete old photo if exists
                if evidence.evidence_photo_path and os.path.exists(os.path.join(UPLOAD_FOLDER, evidence.evidence_photo_path)):
                    try:
                        os.remove(os.path.join(UPLOAD_FOLDER,
                                  evidence.evidence_photo_path))
                    except Exception as e:
                        print(f"Error deleting old photo: {str(e)}")

                # Save new photo
                filename = secure_filename(evidence_photo.filename)
                unique_filename = f'{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{filename}'
                evidence_photo.save(os.path.join(
                    UPLOAD_FOLDER, unique_filename))
                evidence.evidence_photo_path = unique_filename
            else:
                flash('Format file tidak valid.', 'danger')
                return redirect(url_for('view_capa', capa_id=capa_id))

        try:
            db.session.commit()
            flash('Bukti berhasil diperbarui.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saat memperbarui bukti: {str(e)}', 'danger')

        # Redirect with fragment to keep position at Pengajuan Bukti section
        return redirect(url_for('view_capa', capa_id=capa_id) + '#pengajuan-bukti')

    @app.route('/close_capa/<int:capa_id>', methods=['POST'])
    @login_required
    def close_capa(capa_id):
        issue = CapaIssue.query.get_or_404(capa_id)

        if issue.status != 'Evidence Pending':
            flash('Status CAPA tidak memungkinkan penutupan saat ini.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Pastikan semua tindakan memiliki bukti (opsional)
        if issue.action_plan and issue.action_plan.user_adjusted_actions_json:
            action_plan_data = json.loads(
                issue.action_plan.user_adjusted_actions_json)
            # Removed the logic that automatically flags all actions as completed on close.
            # The 'completed' status should now only be set when evidence is submitted
            # or potentially through manual edits if implemented elsewhere.
            # We still might want to save the JSON if other modifications happened,
            # but for now, we remove the automatic completion flag.
            # issue.action_plan.user_adjusted_actions_json = json.dumps(action_plan_data) # Commented out or remove if no other changes needed here

        # Update status CAPA
        issue.status = 'Closed'
        db.session.commit()  # Commit status change first

        # Store final knowledge when CAPA is closed
        try:
            knowledge_stored = store_knowledge_on_capa_close(capa_id)
            if knowledge_stored:
                print(
                    f"Successfully stored consolidated AI knowledge for CAPA ID {capa_id} upon closure.")
            else:
                print(
                    f"Failed to store or no data to store for AI knowledge for CAPA ID {capa_id} upon closure.")
        except Exception as e:
            print(
                f"Error storing AI knowledge upon closing CAPA ID {capa_id}: {e}")
            # Optionally, flash a warning to the user, but for now, just log it.

        flash('CAPA telah berhasil ditutup.', 'success')
        return redirect(url_for('view_capa', capa_id=capa_id))

    @app.route('/report/<int:capa_id>/pdf')
    @login_required
    def generate_pdf_report(capa_id):
        issue = CapaIssue.query.options(
            db.joinedload(CapaIssue.gemba_investigation),
            db.joinedload(CapaIssue.root_cause),
            db.joinedload(CapaIssue.action_plan),
            db.joinedload(CapaIssue.evidence)
        ).get_or_404(capa_id)

        # Convert timestamps to local timezone
        if issue.submission_timestamp:
            issue.submission_timestamp = pytz.utc.localize(issue.submission_timestamp).astimezone(LOCAL_TIMEZONE)
        if issue.gemba_investigation and issue.gemba_investigation.gemba_submission_timestamp:
            issue.gemba_investigation.gemba_submission_timestamp = pytz.utc.localize(issue.gemba_investigation.gemba_submission_timestamp).astimezone(LOCAL_TIMEZONE)
        if issue.root_cause and issue.root_cause.rc_submission_timestamp:
            issue.root_cause.rc_submission_timestamp = pytz.utc.localize(issue.root_cause.rc_submission_timestamp).astimezone(LOCAL_TIMEZONE)
        if issue.action_plan and issue.action_plan.action_submission_timestamp:
            issue.action_plan.action_submission_timestamp = pytz.utc.localize(issue.action_plan.action_submission_timestamp).astimezone(LOCAL_TIMEZONE)
        
        for ev in issue.evidence:
            if ev.evidence_submission_timestamp:
                ev.evidence_submission_timestamp = pytz.utc.localize(ev.evidence_submission_timestamp).astimezone(LOCAL_TIMEZONE)

        # Render the HTML template with the issue data
        initial_photo_abs_paths = []
        if issue.initial_photos:
            for photo_filename in issue.initial_photos:
                abs_path = os.path.join(
                    current_app.root_path, current_app.config['UPLOAD_FOLDER'], photo_filename)
                initial_photo_abs_paths.append(abs_path)

        gemba_findings = None
        gemba_photo_abs_paths = []
        if issue.gemba_investigation:
            gemba_findings = issue.gemba_investigation.findings
            if issue.gemba_investigation.gemba_photos:
                for photo_filename in issue.gemba_investigation.gemba_photos:
                    abs_path = os.path.join(
                        current_app.root_path, current_app.config['UPLOAD_FOLDER'], photo_filename)
                    gemba_photo_abs_paths.append(abs_path)

        html_out = render_template(
            'report_template.html',
            issue=issue,
            datetime=datetime,
            initial_photo_abs_paths=initial_photo_abs_paths,
            gemba_findings=gemba_findings,
            gemba_photo_abs_paths=gemba_photo_abs_paths
        )

        try:
            # Import required modules (pdfkit and Path are now imported at the top)
            # wkhtmltopdf is expected to be in system PATH. pdfkit will find it.

            # Options for the PDF
            options = {
                'page-size': 'A4',
                'margin-top': '1.5cm',
                'margin-right': '1.5cm',
                'margin-bottom': '1.5cm',
                'margin-left': '1.5cm',
                'encoding': 'UTF-8',
                'enable-local-file-access': '',  # Allow local file access for images
                'no-outline': None,
                'print-media-type': '',  # Use print media type for better rendering
                'disable-smart-shrinking': '',  # Prevent text size adjustment
                'dpi': 300,  # Higher DPI for better quality
                'zoom': 1.0,  # No zoom
                # Include custom CSS if needed
                'user-style-sheet': str(Path('static/css/custom.css').absolute())
            }

            # Add additional CSS for PDF
            css = '''
            @page {
                margin: 1.5cm;
                size: A4;
            }
            body {
                font-family: 'Poppins', Arial, sans-serif;
                margin: 0;
                padding: 0;
                font-size: 10pt;
                line-height: 1.6;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            '''

            # Generate PDF using pdfkit with additional CSS
            pdf_bytes = pdfkit.from_string(
                html_out,
                False,
                options=options,
                css=os.path.join('static', 'css', 'custom.css') if os.path.exists(
                    os.path.join('static', 'css', 'custom.css')) else None
            )

            # Create and return the response
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers[
                'Content-Disposition'] = f'inline; filename=capa_report_{capa_id}.pdf'
            return response

        except Exception as e:
            print(f"Error generating PDF for CAPA ID {capa_id}: {e}")
            flash(f'Error generating PDF report: {str(e)}', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))
