import json
from datetime import datetime
import google.generativeai as genai
from models import db, RootCause, ActionPlan
from config import GOOGLE_API_KEY
from ai_learning import get_relevant_rca_knowledge, get_relevant_action_plan_knowledge

# Initialize Gemini AI
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in .env file. AI features will be disabled.")
    # Prevent crash if key missing
    genai.configure(api_key="DUMMY_KEY_SO_APP_DOESNT_CRASH")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Select the model (adjust if needed, check Gemini documentation for available models)
gemini_model = genai.GenerativeModel('models/gemini-2.5-flash-preview-04-17')


def trigger_rca_analysis(capa_id):
    """Fetches issue details, gemba findings, calls Gemini for 5 Why analysis, and stores the result."""
    from models import CapaIssue, GembaInvestigation  # Import here to avoid circular imports

    if not GOOGLE_API_KEY:
        print(
            f"Skipping AI RCA for CAPA ID {capa_id}: API Key not configured.")
        return  # Don't proceed if API key is missing

    # Get issue with gemba investigation data
    issue = CapaIssue.query.options(db.joinedload(
        CapaIssue.gemba_investigation)).get(capa_id)
    if not issue:
        print(
            f"Error: Could not find CAPA Issue with ID {capa_id} for AI analysis.")
        return

    # Check if Gemba investigation exists
    gemba_data = issue.gemba_investigation
    if not gemba_data:
        print(
            f"Warning: No Gemba investigation found for CAPA ID {capa_id}. This is unusual.")

    # Retrieve relevant knowledge from previous RCAs
    relevant_knowledge = get_relevant_rca_knowledge(
        current_capa_issue_description=issue.issue_description,
        current_capa_machine_name=issue.machine_name,
        limit=3
    )

    # --- Prepare Prompt in Bahasa Indonesia ---
    prompt = f"""
    Analisis masalah pengemasan manufaktur berikut menggunakan teknik 5 Whys untuk menentukan akar masalah.
    Berikan output dalam bentuk objek JSON dengan kunci "why1", "why2", "why3", "why4", dan "root_cause" (untuk why ke-5).
    PENTING: Berikan SEMUA TANGGAPAN dalam BAHASA INDONESIA.

    Detil Masalah:
    Pelanggan: {issue.customer_name}
    Item yang Terlibat: {issue.item_involved}
    Mesin: {issue.machine_name or 'Tidak diketahui'}
    Batch: {issue.batch_number or 'Tidak diketahui'}
    Deskripsi Masalah: {issue.issue_description}
    
    Hasil Investigasi Gemba (Data dari Lapangan):
    {gemba_data.findings if gemba_data else 'Tidak ada data gemba'}

    Contoh Format Output JSON:
    {{
      "why1": "Alasan tingkat pertama",
      "why2": "Alasan tingkat kedua yang dibangun dari yang pertama",
      "why3": "Alasan tingkat ketiga",
      "why4": "Alasan tingkat keempat",
      "root_cause": "Akar masalah yang mendasar"
    }}
    """

    # Add knowledge from previous relevant RCAs if available
    if relevant_knowledge:
        prompt += """
        
    PEMBELAJARAN DARI RCA SEBELUMNYA:
    Berikut adalah beberapa analisis Root Cause sebelumnya yang mungkin relevan. Gunakan ini sebagai referensi tambahan untuk memperbaiki analisis Anda, tetapi tetap fokus pada masalah saat ini:
    """
        for i, knowledge_item in enumerate(relevant_knowledge, 1):
            try:
                # knowledge_item now contains 'adjusted_whys' (JSON string of list) and 'context'
                adjusted_whys_json_str = knowledge_item.get('adjusted_whys')
                context_data_dict = knowledge_item.get('context', {})

                if not adjusted_whys_json_str:
                    continue  # Skip if no whys data

                prompt += f"""
    Contoh Pembelajaran {i} (dari CAPA ID: {context_data_dict.get('source_capa_id', 'N/A')}):
    Konteks Masalah Sebelumnya:
      Deskripsi: {context_data_dict.get('issue_description', 'Tidak tersedia')}
      Mesin: {context_data_dict.get('machine_name', 'Tidak tersedia')}
    Pembelajaran RCA (5 Whys yang disesuaikan pengguna):
    """
                # Parse the JSON string list of whys
                whys_list = json.loads(adjusted_whys_json_str)
                if isinstance(whys_list, list) and whys_list:
                    for idx, why_text in enumerate(whys_list):
                        prompt += f"      Why {idx + 1}: {why_text}\n"
                else:
                    prompt += "      (Tidak ada detail 'why' yang tersimpan)\n"
                prompt += "\n"
            except Exception as e:
                print(f"Error processing RCA knowledge item for prompt: {e}")
                continue

    prompt += """

    Lakukan analisis 5 Why berdasarkan Detail Masalah yang diberikan DAN hasil investigasi Gemba dari lapangan.
    PENTING: Gunakan informasi hasil Gemba (terutama akar masalah yang dicurigai) sebagai masukan utama untuk analisis Anda,
    tapi pastikan bahwa Anda melakukan analisis 5 Why yang logis dan mendalam.
    Berikan semua hasil dalam Bahasa Indonesia.
    """

    # Log the knowledge enhancement
    if relevant_knowledge:
        print(
            f"Enhanced RCA prompt with {len(relevant_knowledge)} relevant knowledge entries.")
    else:
        print("No relevant prior knowledge found for enhancing RCA.")

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
            # Store validated JSON string
            ai_suggestion_str = json.dumps(ai_suggestion_json)
            print(f"AI RCA Suggestion received for CAPA ID {capa_id}")

        except (json.JSONDecodeError, ValueError) as parse_error:
            print(
                f"Error parsing AI response for CAPA ID {capa_id}: {parse_error}")
            print(f"Raw AI Response:\n{response.text}")
            # Store the raw text if JSON parsing fails, maybe update status differently?
            ai_suggestion_str = f'{{"error": "Failed to parse AI response", "raw_response": {json.dumps(response.text)}}}'
            # Consider flashing a specific warning to the user later

        # Store the result in the database
        existing_rc = RootCause.query.filter_by(capa_id=capa_id).first()
        if existing_rc:
            existing_rc.ai_suggested_rc_json = ai_suggestion_str
            existing_rc.rc_submission_timestamp = datetime.utcnow()  # Update timestamp
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
    from models import CapaIssue  # Import here to avoid circular imports

    if not GOOGLE_API_KEY:
        print(
            f"Skipping AI Action Plan for CAPA ID {capa_id}: API Key not configured.")
        return

    issue = CapaIssue.query.options(
        db.joinedload(CapaIssue.root_cause)).get(capa_id)
    if not issue or not issue.root_cause or not issue.root_cause.user_adjusted_root_cause:
        print(
            f"Error: Cannot trigger Action Plan AI for CAPA ID {capa_id}. Missing issue or final root cause.")
        return

    # This is the final "why" string
    final_rc = issue.root_cause.user_adjusted_root_cause
    # This is the JSON string of all whys
    user_adjusted_whys_json_for_current_capa = issue.root_cause.user_adjusted_whys_json

    # Retrieve relevant knowledge from previous RCAs that match machine, issue desc, and 5 whys
    relevant_knowledge = get_relevant_action_plan_knowledge(
        current_capa_issue_description=issue.issue_description,
        current_capa_machine_name=issue.machine_name,
        current_capa_user_adjusted_whys_json=user_adjusted_whys_json_for_current_capa,
        limit=3
    )

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
    """

    # Add knowledge from previous relevant action plans if available
    if relevant_knowledge:
        prompt += """
        
    PEMBELAJARAN DARI RENCANA TINDAKAN SEBELUMNYA YANG SERUPA:
    Berikut adalah beberapa Rencana Tindakan dari kasus sebelumnya yang serupa (berdasarkan kecocokan mesin, deskripsi masalah, dan 5 Why). 
    Gunakan ini sebagai referensi untuk membantu Anda merumuskan Rencana Tindakan yang lebih baik untuk masalah saat ini.
    """
        # relevant_knowledge now contains past Action Plan adjustments
        for i, knowledge_item in enumerate(relevant_knowledge, 1):
            try:
                # knowledge_item contains 'adjusted_temporary_actions', 'adjusted_preventive_actions' (JSON strings of lists), and 'context'
                temp_actions_json_str = knowledge_item.get(
                    'adjusted_temporary_actions')
                prev_actions_json_str = knowledge_item.get(
                    'adjusted_preventive_actions')
                context_data_dict = knowledge_item.get('context', {})

                prompt += f"""
    Contoh Pembelajaran Rencana Tindakan {i} (dari CAPA ID: {context_data_dict.get('source_capa_id', 'N/A')}):
    Konteks Masalah Sebelumnya:
      Deskripsi: {context_data_dict.get('issue_description', 'Tidak tersedia')}
      Mesin: {context_data_dict.get('machine_name', 'Tidak tersedia')}
      
    Tindakan Sementara yang telah disesuaikan pengguna sebelumnya:
    """
                temp_actions_list = json.loads(
                    temp_actions_json_str) if temp_actions_json_str else []
                if isinstance(temp_actions_list, list) and temp_actions_list:
                    for j, action_text in enumerate(temp_actions_list, 1):
                        prompt += f"      {j}. {action_text}\n"
                else:
                    prompt += "      (Tidak ada tindakan sementara yang tersimpan)\n"

                prompt += f"""
    Tindakan Pencegahan yang telah disesuaikan pengguna sebelumnya:
    """
                prev_actions_list = json.loads(
                    prev_actions_json_str) if prev_actions_json_str else []
                if isinstance(prev_actions_list, list) and prev_actions_list:
                    for j, action_text in enumerate(prev_actions_list, 1):
                        prompt += f"      {j}. {action_text}\n"
                else:
                    prompt += "      (Tidak ada detail 'why' yang tersimpan untuk RCA ini)\n"
                prompt += "\n"
            except Exception as e:
                print(
                    f"Error processing similar RCA knowledge item for Action Plan prompt: {e}")
                continue
    else:
        prompt += """
    (Tidak ada pembelajaran dari RCA sebelumnya yang cocok ditemukan untuk kasus ini.)
    """
    prompt += """
    
    Perhatikan! Berikan HANYA langkah tindakan untuk setiap item, tanpa indikator keberhasilan, penanggung jawab, atau deadline - itu akan ditambahkan oleh pengguna aplikasi.
    
    OUTPUT harus merupakan JSON yang valid dan sederhana. Hanya berisi array langkah-langkah tindakan yang perlu dilakukan.
    Buat 3-4 langkah tindakan sementara dan 2-3 langkah tindakan pencegahan yang spesifik dan relevan dengan masalah tersebut.
    Pastikan semuanya dalam Bahasa Indonesia.
    """

    # Log the knowledge enhancement
    if relevant_knowledge:
        print(
            f"Enhanced Action Plan prompt with {len(relevant_knowledge)} relevant knowledge entries.")
    else:
        print("No relevant prior knowledge found for enhancing Action Plan.")

    try:
        print(f"Sending Action Plan prompt to Gemini for CAPA ID {capa_id}...")
        response = gemini_model.generate_content(prompt)

        # Attempt to parse JSON
        try:
            ai_suggestion_text = response.text.strip()
            if ai_suggestion_text.startswith("```json"):
                ai_suggestion_text = ai_suggestion_text[7:]
            if ai_suggestion_text.endswith("```"):
                ai_suggestion_text = ai_suggestion_text[:-3]

            ai_suggestion_json = json.loads(ai_suggestion_text.strip())
            if not all(k in ai_suggestion_json for k in ["temporary_action", "preventive_action"]):
                raise ValueError(
                    "AI response missing expected action plan keys.")

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
            print(
                f"Error parsing AI Action Plan response for CAPA ID {capa_id}: {parse_error}")
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
        print(
            f"Error calling Gemini API for Action Plan (CAPA ID {capa_id}): {e}")
        # Re-raise the exception so the calling function flashes a warning
        raise e
