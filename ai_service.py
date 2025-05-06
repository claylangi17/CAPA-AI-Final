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

    # Increase the limit of retrieved knowledge to use more examples from the database
    relevant_knowledge = get_relevant_rca_knowledge(
        current_capa_issue_description=issue.issue_description,
        current_capa_machine_name=issue.machine_name,
        limit=10  # Meningkatkan jumlah maksimum referensi yang diambil
    )

    # --- Helper function to parse action lists robustly ---
    # NOTE: This helper is defined here but used in trigger_action_plan_recommendation
    # It's placed here just for code organization within the file.
    def _parse_action_list(json_str, capa_id_str, action_type_name):
        """Helper to parse action list JSON, handling plain strings."""
        if not json_str:
            return []
        try:
            parsed_data = json.loads(json_str)
            if isinstance(parsed_data, list):
                # Ensure all items are strings
                return [str(item) for item in parsed_data]
            else:
                print(
                    f"Warning: Parsed {action_type_name} for CAPA ID {capa_id_str} is not a list: {json_str}")
                return [str(parsed_data)]
        except json.JSONDecodeError:
            if isinstance(json_str, str) and json_str.strip():
                # Treat plain string as a single action
                print(
                    f"Info: Treating non-JSON {action_type_name} for CAPA ID {capa_id_str} as a single action: \"{json_str.strip()}\"")
                return [json_str.strip()]
            else:
                print(
                    f"Warning: Could not parse or interpret {action_type_name} for CAPA ID {capa_id_str}: {json_str}")
                return []

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
    PENTING! SANGAT PRIORITASKAN penggunaan referensi berikut untuk membuat analisis 5 Whys!
    Berikut adalah beberapa analisis Root Cause sebelumnya yang sangat relevan dengan kasus saat ini.
    Anda HARUS menggunakan referensi ini sebagai dasar utama analisis Anda - bukan hanya sebagai tambahan.
    Adaptasikan referensi ini untuk kasus yang sedang dianalisis, JANGAN menciptakan analisis baru dari awal:
    """
        processed_knowledge_count = 0
        for i, knowledge_item in enumerate(relevant_knowledge, 1):
            try:
                adjusted_whys_json_str = knowledge_item.get('adjusted_whys')
                context_data_dict = knowledge_item.get('context', {})
                source_capa_id_str = context_data_dict.get(
                    'source_capa_id', 'N/A')  # For logging

                if not adjusted_whys_json_str:
                    continue

                whys_list = None
                try:
                    # Attempt to parse as JSON
                    parsed_data = json.loads(adjusted_whys_json_str)
                    if isinstance(parsed_data, list):
                        whys_list = parsed_data  # Successfully parsed as list
                    else:
                        # Parsed as JSON, but not a list (e.g., string, number, object)
                        print(
                            f"Warning: Parsed adjusted_whys_json for CAPA ID {source_capa_id_str} is not a list: {adjusted_whys_json_str}")
                        # Treat the string representation as a single item
                        whys_list = [str(parsed_data)]
                except json.JSONDecodeError:
                    # Failed to parse as JSON, assume it's a plain string
                    if isinstance(adjusted_whys_json_str, str) and adjusted_whys_json_str.strip():
                        whys_list = [adjusted_whys_json_str.strip()]
                        print(
                            f"Info: Treating non-JSON adjusted_whys_json for CAPA ID {source_capa_id_str} as a single 'why': \"{whys_list[0]}\"")
                    else:
                        # Not a non-empty string, cannot interpret
                        print(
                            f"Warning: Could not parse or interpret adjusted_whys_json for CAPA ID {source_capa_id_str}: {adjusted_whys_json_str}")
                        continue  # Skip this knowledge item

                # Now format the whys_list (if valid) into the prompt
                if whys_list:  # Ensure we have a list (even if single item)
                    prompt += f"""
    Contoh Pembelajaran {i} (dari CAPA ID: {source_capa_id_str}):
    Konteks Masalah Sebelumnya:
      Deskripsi: {context_data_dict.get('issue_description', 'Tidak tersedia')}
      Mesin: {context_data_dict.get('machine_name', 'Tidak tersedia')}
    Pembelajaran RCA (5 Whys yang disesuaikan pengguna):
    """
                    for idx, why_text in enumerate(whys_list):
                        prompt += f"      Why {idx + 1}: {why_text}\n"
                    prompt += "\n"
                    processed_knowledge_count += 1  # Count successfully processed items
                else:
                    # This case should ideally not be reached if logic above is correct, but as fallback:
                    prompt += f"""
    Contoh Pembelajaran {i} (dari CAPA ID: {source_capa_id_str}):
    Konteks Masalah Sebelumnya:
      Deskripsi: {context_data_dict.get('issue_description', 'Tidak tersedia')}
      Mesin: {context_data_dict.get('machine_name', 'Tidak tersedia')}
    Pembelajaran RCA (5 Whys yang disesuaikan pengguna):
          (Data 'why' tidak dapat diproses)\n
    """
                    prompt += "\n"

            except Exception as e:  # Catch any other unexpected errors during processing
                print(
                    f"Unexpected error processing RCA knowledge item {i} for prompt: {e}")
                continue

    prompt += """

    Lakukan analisis 5 Why berdasarkan Detail Masalah yang diberikan DAN hasil investigasi Gemba dari lapangan.
    PENTING: Gunakan informasi hasil Gemba (terutama akar masalah yang dicurigai) sebagai masukan utama untuk analisis Anda,
    tapi pastikan bahwa Anda melakukan analisis 5 Why yang logis dan mendalam.
    Berikan semua hasil dalam Bahasa Indonesia.
    """

    # Log the knowledge enhancement using the count of successfully processed items
    if processed_knowledge_count > 0:
        print(
            f"Enhanced RCA prompt with {processed_knowledge_count} relevant knowledge entries.")
    else:
        # Check if relevant_knowledge was initially found but none could be processed
        if relevant_knowledge:
            print(
                "Relevant prior knowledge was found, but none could be successfully processed for the prompt.")
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
    """Fetches issue and RCA with all WHYs, calls Gemini for action plan, stores result."""
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

    # Parse all WHYs from JSON to incorporate in prompt
    all_whys = []
    try:
        all_whys_data = json.loads(user_adjusted_whys_json_for_current_capa)

        # Handle different expected formats of the WHYs data
        if isinstance(all_whys_data, list):
            # Format expected: List of dictionaries with why_question and why_answer
            for i, why_item in enumerate(all_whys_data, 1):
                if isinstance(why_item, dict):
                    why_question = why_item.get('why_question', f'Why {i}?')
                    why_answer = why_item.get('why_answer', 'Tidak tersedia')
                    all_whys.append({
                        'why_number': i,
                        'question': why_question,
                        'answer': why_answer
                    })
                else:
                    print(
                        f"Warning: WHY item {i} is not a dictionary, skipping")
        elif isinstance(all_whys_data, dict):
            # Alternative format: Dictionary with keys like why1, why2, etc.
            # Map old format to new format
            whys_mapping = {
                'why1': 1,
                'why2': 2,
                'why3': 3,
                'why4': 4,
                'root_cause': 5  # Assuming root_cause is the 5th why
            }

            for key, i in whys_mapping.items():
                if key in all_whys_data:
                    all_whys.append({
                        'why_number': i,
                        'question': f'Why {i}?',
                        'answer': all_whys_data[key]
                    })
        else:
            print(
                f"Warning: Unexpected WHYs data format for CAPA ID {capa_id}")

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(
            f"Warning: Could not parse all WHYs JSON for CAPA ID {capa_id}: {e}")
        # Continue with empty list if parsing fails

    # Retrieve relevant knowledge from previous RCAs that match machine, issue desc, and 5 whys
    relevant_knowledge = get_relevant_action_plan_knowledge(
        current_capa_issue_description=issue.issue_description,
        current_capa_machine_name=issue.machine_name,
        current_capa_user_adjusted_whys_json=user_adjusted_whys_json_for_current_capa,
        limit=10  # Meningkatkan jumlah maksimum referensi yang diambil
    )

    # --- Prepare Prompt in Bahasa Indonesia ---
    prompt = f"""
    Berdasarkan masalah pengemasan manufaktur yang dijelaskan di bawah ini, analisis 5 Why, dan akar masalah yang telah ditentukan, rekomendasikan Tindakan Sementara (temporary) dan Tindakan Pencegahan (preventive) yang spesifik dan terukur.

    PENTING: Berikan SEMUA TANGGAPAN dalam BAHASA INDONESIA.

    Detail Masalah:
    Pelanggan: {issue.customer_name}
    Item yang Terlibat: {issue.item_involved}
    Deskripsi Masalah: {issue.issue_description}
    
    Analisis 5 Why Lengkap:"""

    # Add all WHYs to the prompt if available
    if all_whys:
        for why in all_whys:
            prompt += f"""
    Why {why['why_number']}: {why['question']}   
    Jawaban: {why['answer']}"""
    else:
        prompt += f"""
    (Analisis 5 Why tidak tersedia secara lengkap)
    Akar Masalah Akhir: {final_rc}"""

    prompt += f"""

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
    # Initialize counter *before* checking relevant_knowledge
    processed_ap_knowledge_count = 0
    if relevant_knowledge:
        prompt += """

    PEMBELAJARAN DARI RENCANA TINDAKAN SEBELUMNYA YANG SERUPA:
    PERHATIAN! SANGAT PRIORITASKAN dan GUNAKAN referensi berikut sebagai solusi utama!
    Berikut adalah beberapa Rencana Tindakan dari kasus sebelumnya yang sangat serupa dengan kasus ini.
    Anda HARUS menggunakan referensi ini sebagai sumber utama rekomendasi Anda.
    JANGAN menciptakan rekomendasi baru dari awal. Cukup adaptasikan solusi yang sudah terbukti ini:
    """
        # relevant_knowledge now contains past Action Plan adjustments
        for i, knowledge_item in enumerate(relevant_knowledge, 1):
            temp_actions_list = []  # Initialize lists for this item
            prev_actions_list = []
            try:
                # knowledge_item contains 'adjusted_temporary_actions', 'adjusted_preventive_actions' (JSON strings of lists), and 'context'
                temp_actions_json_str = knowledge_item.get(
                    'adjusted_temporary_actions')
                prev_actions_json_str = knowledge_item.get(
                    'adjusted_preventive_actions')
                context_data_dict = knowledge_item.get('context', {})
                source_capa_id_str = context_data_dict.get(
                    'source_capa_id', 'N/A')  # Get source ID for logging

                # Use the helper function (defined in trigger_rca_analysis) for robust parsing
                temp_actions_list = _parse_action_list(
                    temp_actions_json_str, source_capa_id_str, "temporary actions")
                prev_actions_list = _parse_action_list(
                    prev_actions_json_str, source_capa_id_str, "preventive actions")

                # Only add to prompt if we successfully parsed something
                if temp_actions_list or prev_actions_list:
                    prompt += f"""
    Contoh Pembelajaran Rencana Tindakan {i} (dari CAPA ID: {source_capa_id_str}):
    Konteks Masalah Sebelumnya:
      Deskripsi: {context_data_dict.get('issue_description', 'Tidak tersedia')}
      Mesin: {context_data_dict.get('machine_name', 'Tidak tersedia')}

    Tindakan Sementara yang telah disesuaikan pengguna sebelumnya:
    """
                    if temp_actions_list:
                        for j, action_text in enumerate(temp_actions_list, 1):
                            prompt += f"      {j}. {action_text}\n"
                    else:
                        prompt += "      (Tidak ada tindakan sementara yang tersimpan)\n"

                    prompt += f"""
    Tindakan Pencegahan yang telah disesuaikan pengguna sebelumnya:
    """
                    if prev_actions_list:
                        for j, action_text in enumerate(prev_actions_list, 1):
                            prompt += f"      {j}. {action_text}\n"
                    else:
                        # Corrected placeholder
                        prompt += "      (Tidak ada tindakan pencegahan yang tersimpan)\n"
                    prompt += "\n"
                    processed_ap_knowledge_count += 1  # Increment count here
                else:
                    # Optional: Log if an item was retrieved but parsing resulted in empty lists for both
                    print(
                        f"Info: Skipping knowledge item {i} for Action Plan prompt as parsing yielded no actions.")

            except Exception as e:  # This except catches errors for the whole item processing
                print(
                    f"Error processing Action Plan knowledge item {i} for prompt: {e}")
                continue  # Continue to next knowledge_item
    # This else corresponds to 'if relevant_knowledge:'
    else:
        prompt += """
    (Tidak ada pembelajaran dari Rencana Tindakan sebelumnya yang cocok ditemukan untuk kasus ini.)
    """
    prompt += """

    Perhatikan! Berikan HANYA langkah tindakan untuk setiap item, tanpa indikator keberhasilan, penanggung jawab, atau deadline - itu akan ditambahkan oleh pengguna aplikasi.

    OUTPUT harus merupakan JSON yang valid dan sederhana. Hanya berisi array langkah-langkah tindakan yang perlu dilakukan.
    Buat 3-4 langkah tindakan sementara dan 2-3 langkah tindakan pencegahan yang spesifik dan relevan dengan masalah tersebut.
    Pastikan semuanya dalam Bahasa Indonesia.
    """

    # Log the knowledge enhancement using the count of successfully processed items
    if processed_ap_knowledge_count > 0:
        print(
            f"Enhanced Action Plan prompt with {processed_ap_knowledge_count} relevant knowledge entries.")
    else:
        # Check if relevant_knowledge was initially found but none could be processed
        if relevant_knowledge:
            print("Relevant prior Action Plan knowledge was found, but none could be successfully processed for the prompt.")
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
