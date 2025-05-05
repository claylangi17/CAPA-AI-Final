from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, make_response
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

from models import db, CapaIssue, RootCause, ActionPlan, Evidence, GembaInvestigation
from ai_service import trigger_rca_analysis, trigger_action_plan_recommendation
from ai_learning import store_rca_learning, store_action_plan_learning
from utils import allowed_file
from config import UPLOAD_FOLDER


def register_routes(app):
    @app.route('/')
    def index():
        issues = CapaIssue.query.order_by(
            CapaIssue.submission_timestamp.desc()).all()
        return render_template('index.html', issues=issues)

    @app.route('/gemba/<int:capa_id>', methods=['GET', 'POST'])
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
            gemba_photos = request.files.getlist('gemba_photos')

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
    def new_capa():
        if request.method == 'POST':
            customer_name = request.form.get('customer_name')
            item_involved = request.form.get('item_involved')
            issue_date_str = request.form.get('issue_date')
            issue_description = request.form.get('issue_description')
            machine_name = request.form.get('machine_name')
            batch_number = request.form.get('batch_number')
            initial_photo = request.files.get('initial_photo')

            # Basic validation
            if not all([customer_name, item_involved, issue_date_str, issue_description]):
                flash('Please fill in all required fields.', 'danger')
                return render_template('new_capa.html')

            try:
                issue_date = datetime.strptime(
                    issue_date_str, '%Y-%m-%d').date()
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
                photo_path = unique_filename  # Store relative path in DB

            # Create new CAPA Issue
            new_issue = CapaIssue(
                customer_name=customer_name,
                item_involved=item_involved,
                issue_date=issue_date,
                issue_description=issue_description,
                machine_name=machine_name,
                batch_number=batch_number,
                initial_photo_path=photo_path,
                status='Open'  # Initial status
            )

            try:
                db.session.add(new_issue)
                # Commit here to get the new_issue.capa_id
                db.session.commit()

                # Update status to Gemba Pending
                new_issue.status = 'Gemba Pending'
                db.session.commit()

                flash(
                    f'New CAPA issue (ID: {new_issue.capa_id}) created successfully! Please complete the Gemba Investigation.', 'success')

                # Redirect to Gemba Investigation page
                return redirect(url_for('gemba_investigation', capa_id=new_issue.capa_id))
            except Exception as e:
                db.session.rollback()  # Rollback issue creation if anything failed
                flash(f'Error creating CAPA issue: {str(e)}', 'danger')
                # Clean up saved photo if DB commit failed
                if photo_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], photo_path)):
                    os.remove(os.path.join(
                        app.config['UPLOAD_FOLDER'], photo_path))

        # GET request: just display the form
        return render_template('new_capa.html')

    @app.route('/view/<int:capa_id>')
    def view_capa(capa_id):
        issue = CapaIssue.query.options(
            db.joinedload(CapaIssue.root_cause),  # Eager load related data
            db.joinedload(CapaIssue.action_plan),
            db.joinedload(CapaIssue.evidence)
        ).get_or_404(capa_id)
        return render_template('view_capa.html', issue=issue)

    @app.route('/edit_rca/<int:capa_id>', methods=['POST'])
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
        if len(why_inputs) > 4:
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

            # Store the user's RCA adjustment for AI learning
            try:
                learning_success = store_rca_learning(capa_id)
                if learning_success:
                    print(
                        f"Successfully stored RCA learning data from CAPA ID {capa_id}")
                    # Don't show this message to user to keep UI clean
            except Exception as learning_error:
                # Log the error but don't show to user to keep UI clean
                print(
                    f"Error storing RCA learning data for CAPA ID {capa_id}: {learning_error}")

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
    def uploaded_file(filename):
        # Route to serve uploaded files (needed to display images in templates)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/edit_action_plan/<int:capa_id>', methods=['POST'])
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

            # Store the user's action plan adjustment for AI learning
            try:
                learning_success = store_action_plan_learning(capa_id)
                if learning_success:
                    print(
                        f"Successfully stored action plan learning data from CAPA ID {capa_id}")
                    # Don't show this message to user to keep UI clean
            except Exception as learning_error:
                # Log the error but don't show to user to keep UI clean
                print(
                    f"Error storing action plan learning data for CAPA ID {capa_id}: {learning_error}")

            flash('Rencana Tindakan berhasil diajukan!', 'success')
            return redirect(url_for('view_capa', capa_id=capa_id))
        except Exception as e:
            db.session.rollback()
            flash(
                f'Error saat mengajukan Rencana Tindakan: {str(e)}', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

    @app.route('/submit_evidence/<int:capa_id>', methods=['POST'])
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
    def close_capa(capa_id):
        issue = CapaIssue.query.get_or_404(capa_id)

        if issue.status != 'Evidence Pending':
            flash('Status CAPA tidak memungkinkan penutupan saat ini.', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))

        # Pastikan semua tindakan memiliki bukti (opsional)
        if issue.action_plan and issue.action_plan.user_adjusted_actions_json:
            action_plan_data = json.loads(
                issue.action_plan.user_adjusted_actions_json)
            temp_actions = action_plan_data.get('temp_actions', [])
            # Removed the logic that automatically flags all actions as completed on close.
            # The 'completed' status should now only be set when evidence is submitted
            # or potentially through manual edits if implemented elsewhere.
            # We still might want to save the JSON if other modifications happened,
            # but for now, we remove the automatic completion flag.
            # issue.action_plan.user_adjusted_actions_json = json.dumps(action_plan_data) # Commented out or remove if no other changes needed here

        # Update status CAPA
        issue.status = 'Closed'
        db.session.commit()

        flash('CAPA telah berhasil ditutup.', 'success')
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
        html_out = render_template(
            'report_template.html', issue=issue, datetime=datetime)

        try:
            # Use WeasyPrint to generate PDF from HTML string
            from weasyprint import HTML  # Import WeasyPrint

            # Pass base_url for relative paths like images
            pdf_bytes = HTML(
                string=html_out, base_url=request.base_url).write_pdf()

            # Create a Flask response object with the PDF data
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            # Or 'attachment;' to force download
            response.headers[
                'Content-Disposition'] = f'inline; filename=capa_report_{capa_id}.pdf'
            return response

        except Exception as e:
            print(f"Error generating PDF for CAPA ID {capa_id}: {e}")
            flash(f'Error generating PDF report: {str(e)}', 'danger')
            return redirect(url_for('view_capa', capa_id=capa_id))
