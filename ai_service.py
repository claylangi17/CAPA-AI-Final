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


def _parse_action_list(json_str, capa_id_str, action_type_name):
    """Helper to parse action list JSON, handling plain strings and skipping empty/meaningless data."""
    if not json_str or (isinstance(json_str, str) and not json_str.strip()):
        print(
            f"Warning: Empty {action_type_name} data for CAPA ID {capa_id_str}")
        return []

    # Try JSON decode first
    try:
        parsed_data = json.loads(json_str)
        if isinstance(parsed_data, list):
            # Handle list of dictionaries with 'langkah' key
            if parsed_data and isinstance(parsed_data[0], dict) and 'langkah' in parsed_data[0]:
                result = [item.get('langkah', '').strip(
                ) for item in parsed_data if item.get('langkah', '').strip()]
                if result:
                    return result

            # Handle simple list of strings or other values
            result = [str(item).strip()
                      for item in parsed_data if str(item).strip()]
            if result:
                return result

            print(
                f"Warning: List in {action_type_name} for CAPA ID {capa_id_str} contains no meaningful items")
            return []

        elif isinstance(parsed_data, dict):
            # Handle dictionary format
            if 'temporary_action' in parsed_data or 'preventive_action' in parsed_data:
                # Extract from standard format
                key = 'temporary_action' if 'temporary_action' in parsed_data else 'preventive_action'
                actions = parsed_data.get(key, [])
                if isinstance(actions, list):
                    result = []
                    for item in actions:
                        if isinstance(item, dict) and 'langkah' in item:
                            result.append(item.get('langkah', '').strip())
                        else:
                            result.append(str(item).strip())
                    return [item for item in result if item]
            else:
                # Try to extract values from any dictionary
                return [str(value).strip() for value in parsed_data.values() if str(value).strip()]

        elif isinstance(parsed_data, str) and parsed_data.strip():
            return [parsed_data.strip()]

        print(
            f"Warning: Parsed {action_type_name} for CAPA ID {capa_id_str} has unexpected format: {type(parsed_data)}")
        return []

    except (json.JSONDecodeError, TypeError) as e:
        if isinstance(json_str, str) and json_str.strip():
            # Accept any non-empty string
            print(
                f"Info: Accepting non-JSON {action_type_name} for CAPA ID {capa_id_str} as a single action: \"{json_str.strip()}\"")
            return [json_str.strip()]
        else:
            print(
                f"Warning: Could not parse {action_type_name} for CAPA ID {capa_id_str}: {e}")
            return []


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
        """Helper to parse action list JSON, handling plain strings and skipping empty/meaningless data."""
        if not json_str or (isinstance(json_str, str) and not json_str.strip()):
            print(
                f"Warning: Empty {action_type_name} data for CAPA ID {capa_id_str}")
            return []

        # Try JSON decode first
        try:
            parsed_data = json.loads(json_str)
            if isinstance(parsed_data, list):
                # Handle list of dictionaries with 'langkah' key
                if parsed_data and isinstance(parsed_data[0], dict) and 'langkah' in parsed_data[0]:
                    result = [item.get('langkah', '').strip(
                    ) for item in parsed_data if item.get('langkah', '').strip()]
                    if result:
                        return result

                # Handle simple list of strings or other values
                result = [str(item).strip()
                          for item in parsed_data if str(item).strip()]
                if result:
                    return result

                print(
                    f"Warning: List in {action_type_name} for CAPA ID {capa_id_str} contains no meaningful items")
                return []

            elif isinstance(parsed_data, dict):
                # Handle dictionary format
                if 'temporary_action' in parsed_data or 'preventive_action' in parsed_data:
                    # Extract from standard format
                    key = 'temporary_action' if 'temporary_action' in parsed_data else 'preventive_action'
                    actions = parsed_data.get(key, [])
                    if isinstance(actions, list):
                        result = []
                        for item in actions:
                            if isinstance(item, dict) and 'langkah' in item:
                                result.append(item.get('langkah', '').strip())
                            else:
                                result.append(str(item).strip())
                        return [item for item in result if item]
                else:
                    # Try to extract values from any dictionary
                    return [str(value).strip() for value in parsed_data.values() if str(value).strip()]

            elif isinstance(parsed_data, str) and parsed_data.strip():
                return [parsed_data.strip()]

            print(
                f"Warning: Parsed {action_type_name} for CAPA ID {capa_id_str} has unexpected format: {type(parsed_data)}")
            return []

        except (json.JSONDecodeError, TypeError) as e:
            if isinstance(json_str, str) and json_str.strip():
                # Accept any non-empty string
                print(
                    f"Info: Accepting non-JSON {action_type_name} for CAPA ID {capa_id_str} as a single action: \"{json_str.strip()}\"")
                return [json_str.strip()]
            else:
                print(
                    f"Warning: Could not parse {action_type_name} for CAPA ID {capa_id_str}: {e}")
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
    
    PENTING: JANGAN PERNAH menyebutkan frasa seperti "Mengadaptasi dari contoh 1 & 2" atau sejenisnya dalam jawaban Anda.
    Gunakan bahasa Anda sendiri dan integrasikan solusi dari contoh-contoh ini secara alami tanpa mereferensikan nomor contoh.
    
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

                # Only use knowledge items where adjusted_whys_json_str is non-empty and contains at least some meaningful text
                if not adjusted_whys_json_str or (isinstance(adjusted_whys_json_str, str) and not adjusted_whys_json_str.strip()):
                    continue

                # Use improved _parse_action_list to get only meaningful whys
                whys_list = _parse_action_list(
                    adjusted_whys_json_str, source_capa_id_str, "adjusted_whys_json")

                # If _parse_action_list returns nothing but the original string is non-empty, include it as a single why
                if not whys_list and isinstance(adjusted_whys_json_str, str) and adjusted_whys_json_str.strip():
                    whys_list = [adjusted_whys_json_str.strip()]

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
    Berikan semua hasil dalam Bahasa Indonesia, Berikan jawaban yang tegas dan spesifik tanpa keraguan,Hindari penggunaan tanda "/" dalam jawaban, 
    Pilih satu istilah yang paling tepat, jangan memberikan alternatif.
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

    response = None
    try:
        print("\n================ AI RCA ANALYSIS DEBUG ================")
        print(f"[PROMPT SENT to Gemini | CAPA ID {capa_id}]:\n{prompt}\n")
        response = gemini_model.generate_content(prompt)
        print(
            f"[RAW AI RESPONSE]:\n{getattr(response, 'text', str(response))}\n")

        # Attempt to parse the response, handling both JSON and text formats
        try:
            # Gemini might wrap JSON in ```json ... ```, try to extract it
            ai_suggestion_text = response.text.strip()

            # First, try to clean up markdown code blocks if present
            if "```json" in ai_suggestion_text:
                # Extract content between ```json and ``` markers
                import re
                json_block_match = re.search(
                    r'```json\s*(.+?)\s*```', ai_suggestion_text, re.DOTALL)
                if json_block_match:
                    ai_suggestion_text = json_block_match.group(1).strip()
            elif "```" in ai_suggestion_text:
                # Try to extract any code block even if not explicitly marked as JSON
                import re
                code_block_match = re.search(
                    r'```\s*(.+?)\s*```', ai_suggestion_text, re.DOTALL)
                if code_block_match:
                    ai_suggestion_text = code_block_match.group(1).strip()

            # Try to parse as JSON
            try:
                ai_suggestion_json = json.loads(ai_suggestion_text)
                # Basic validation of expected keys
                if all(k in ai_suggestion_json for k in ["why1", "why2", "why3", "why4", "root_cause"]):
                    # If valid JSON with expected keys, use it directly
                    ai_suggestion_str = json.dumps(
                        ai_suggestion_json, indent=2, ensure_ascii=False)
                    print(
                        f"[PARSED AI RCA RESULT | JSON]:\n{ai_suggestion_str}\n")
                else:
                    # JSON format but missing required keys
                    raise ValueError(
                        "JSON response missing expected 5 Why keys")

            except json.JSONDecodeError:
                # If not valid JSON, extract information from text format
                print(
                    f"Response not in JSON format, extracting from text for CAPA ID {capa_id}")

                # Define a structured format to extract from text
                structured_response = {
                    "why1": "",
                    "why2": "",
                    "why3": "",
                    "why4": "",
                    "root_cause": ""
                }

                # Extract each why from the text response
                lines = ai_suggestion_text.split('\n')
                current_why = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Look for why1-why4 and root_cause indicators
                    if "why1" in line.lower() or "1." in line or "why 1" in line.lower():
                        current_why = "why1"
                        # Extract content after the marker
                        content = line.split(':', 1)[1].strip() if ':' in line else line.split(' ', 1)[
                            1].strip() if ' ' in line else ""
                        structured_response["why1"] = content
                    elif "why2" in line.lower() or "2." in line or "why 2" in line.lower():
                        current_why = "why2"
                        content = line.split(':', 1)[1].strip() if ':' in line else line.split(' ', 1)[
                            1].strip() if ' ' in line else ""
                        structured_response["why2"] = content
                    elif "why3" in line.lower() or "3." in line or "why 3" in line.lower():
                        current_why = "why3"
                        content = line.split(':', 1)[1].strip() if ':' in line else line.split(' ', 1)[
                            1].strip() if ' ' in line else ""
                        structured_response["why3"] = content
                    elif "why4" in line.lower() or "4." in line or "why 4" in line.lower():
                        current_why = "why4"
                        content = line.split(':', 1)[1].strip() if ':' in line else line.split(' ', 1)[
                            1].strip() if ' ' in line else ""
                        structured_response["why4"] = content
                    elif "root" in line.lower() or "5." in line or "root cause" in line.lower():
                        current_why = "root_cause"
                        content = line.split(':', 1)[1].strip() if ':' in line else line.split(' ', 1)[
                            1].strip() if ' ' in line else ""
                        structured_response["root_cause"] = content
                    elif current_why and structured_response[current_why] == "":
                        # If we're in a section but haven't captured content yet
                        structured_response[current_why] = line

                # Convert the structured response back to a JSON string
                ai_suggestion_str = json.dumps(
                    structured_response, indent=2, ensure_ascii=False)
                print(
                    f"[PARSED AI RCA RESULT | TEXT-TO-STRUCTURED]:\n{ai_suggestion_str}\n")

        except Exception as parse_error:
            print(
                f"[ERROR] Processing AI response for CAPA ID {capa_id}: {str(parse_error)}")
            if response is not None:
                print(
                    f"[FALLBACK RAW AI RESPONSE]:\n{getattr(response, 'text', str(response))}\n")
                ai_suggestion_str = f'{{"error": "Failed to parse AI response", "raw_response": {json.dumps(getattr(response, 'text', str(response)))} }}'
            else:
                print(
                    "[FALLBACK RAW AI RESPONSE]: Gemini response was not generated due to earlier error.")
                ai_suggestion_str = '{"error": "Failed to parse AI response", "raw_response": null}'
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
        # First check if the JSON string is valid
        if user_adjusted_whys_json_for_current_capa and user_adjusted_whys_json_for_current_capa.strip():
            all_whys_data = json.loads(
                user_adjusted_whys_json_for_current_capa)

            # Handle different expected formats of the WHYs data
            if isinstance(all_whys_data, list):
                # Format expected: List of dictionaries with why_question and why_answer
                for i, why_item in enumerate(all_whys_data, 1):
                    if isinstance(why_item, dict):
                        # Check for different possible key formats
                        if 'why_question' in why_item and 'why_answer' in why_item:
                            why_question = why_item.get(
                                'why_question', f'Why {i}?')
                            why_answer = why_item.get(
                                'why_answer', 'Tidak tersedia')
                        elif 'question' in why_item and 'answer' in why_item:
                            why_question = why_item.get(
                                'question', f'Why {i}?')
                            why_answer = why_item.get(
                                'answer', 'Tidak tersedia')
                        else:
                            # Try to infer from any keys that might contain question/answer
                            keys = list(why_item.keys())
                            if len(keys) >= 2:
                                why_question = why_item.get(
                                    keys[0], f'Why {i}?')
                                why_answer = why_item.get(
                                    keys[1], 'Tidak tersedia')
                            else:
                                why_question = f'Why {i}?'
                                why_answer = next(
                                    iter(why_item.values()), 'Tidak tersedia')

                        all_whys.append({
                            'why_number': i,
                            'question': why_question,
                            'answer': why_answer
                        })
                    else:
                        # If the item is a string, treat it as an answer
                        if isinstance(why_item, str):
                            all_whys.append({
                                'why_number': i,
                                'question': f'Why {i}?',
                                'answer': why_item
                            })
                        else:
                            print(
                                f"Warning: WHY item {i} is not a dictionary or string, skipping")
            elif isinstance(all_whys_data, dict):
                # Alternative format: Dictionary with keys like why1, why2, etc.
                # Map old format to new format
                whys_mapping = {
                    'why1': 1, 'why_1': 1, 'why 1': 1,
                    'why2': 2, 'why_2': 2, 'why 2': 2,
                    'why3': 3, 'why_3': 3, 'why 3': 3,
                    'why4': 4, 'why_4': 4, 'why 4': 4,
                    'why5': 5, 'why_5': 5, 'why 5': 5,
                    'root_cause': 5  # Assuming root_cause is the 5th why
                }

                # Try to find keys that match our patterns
                for key in all_whys_data.keys():
                    # Check if the key is in our mapping
                    if key in whys_mapping:
                        i = whys_mapping[key]
                    else:
                        # Try to extract a number from the key
                        import re
                        match = re.search(r'\d+', key)
                        if match and 1 <= int(match.group()) <= 5:
                            i = int(match.group())
                        else:
                            continue  # Skip keys we can't map

                    all_whys.append({
                        'why_number': i,
                        'question': f'Why {i}?',
                        'answer': all_whys_data[key]
                    })
            else:
                print(
                    f"Warning: Unexpected WHYs data format for CAPA ID {capa_id}")
        else:
            print(f"Warning: Empty WHYs JSON for CAPA ID {capa_id}")

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(
            f"Warning: Could not parse all WHYs JSON for CAPA ID {capa_id}: {e}")
        # Continue with empty list if parsing fails

    # Retrieve relevant knowledge from previous RCAs that match machine, issue desc, and 5 whys
    print(f"\n================ RETRIEVING RELEVANT ACTION PLANS ================\n")
    print(f"Searching for action plans with:")
    print(f"- Issue description: {issue.issue_description}")
    print(f"- Machine name: {issue.machine_name}")
    print(f"- WHYs JSON: {user_adjusted_whys_json_for_current_capa[:100]}..." if len(
        user_adjusted_whys_json_for_current_capa or '') > 100 else user_adjusted_whys_json_for_current_capa)

    relevant_knowledge = get_relevant_action_plan_knowledge(
        current_capa_issue_description=issue.issue_description,
        current_capa_machine_name=issue.machine_name,
        current_capa_user_adjusted_whys_json=user_adjusted_whys_json_for_current_capa,
        limit=10  # Meningkatkan jumlah maksimum referensi yang diambil
    )

    print(f"Found {len(relevant_knowledge)} relevant action plans")
    if not relevant_knowledge:
        print("WARNING: No relevant action plans found. This may affect the quality of AI recommendations.")
    else:
        for i, knowledge_item in enumerate(relevant_knowledge):
            context = knowledge_item.get('context', {})
            print(
                f"Action Plan {i+1} from CAPA ID: {context.get('source_capa_id', 'N/A')}")
            print(f"- Issue: {context.get('issue_description', 'N/A')}")
            print(f"- Machine: {context.get('machine_name', 'N/A')}")
            if 'similarity_score' in context:
                print(f"- Similarity score: {context.get('similarity_score')}")
            print("---")

    # --- Prepare Prompt in Bahasa Indonesia ---
    prompt = f"""
    Berdasarkan masalah pengemasan manufaktur yang dijelaskan di bawah ini, analisis 5 Why, dan akar masalah yang telah ditentukan, rekomendasikan Tindakan Sementara (temporary) dan Tindakan Pencegahan (preventive) yang spesifik dan terukur.

    PENTING: Berikan SEMUA TANGGAPAN dalam BAHASA INDONESIA.

    Detail Masalah:
    Pelanggan: {issue.customer_name}
    Item yang Terlibat: {issue.item_involved}
    Deskripsi Masalah: {issue.issue_description}
    
    Analisis 5 Why Lengkap:"""

    # Debug: Print the raw WHYs data to understand its structure
    print(
        f"DEBUG - Raw WHYs JSON for CAPA ID {capa_id}: {user_adjusted_whys_json_for_current_capa}")
    print(f"DEBUG - Parsed WHYs for CAPA ID {capa_id}: {all_whys}")

    # Always show all 5 WHYs in a consistent format
    if all_whys:
        # First, organize WHYs into a dictionary by number
        whys_by_number = {why['why_number']: why for why in all_whys}

        # Then show all WHYs 1-5, using placeholders for missing ones
        for i in range(1, 6):
            why = whys_by_number.get(i)
            if why:
                prompt += f"""
    Why {i}: {why['question']}
    Jawaban: {why['answer']}"""
            else:
                prompt += f"""
    Why {i}: (Tidak tersedia)
    Jawaban: {final_rc if i == 5 else '(Tidak tersedia)'}"""
    else:
        # If no WHYs available, show all 5 as not available but include final root cause
        for i in range(1, 6):
            prompt += f"""
    Why {i}: (Tidak tersedia)
    Jawaban: {final_rc if i == 5 else '(Tidak tersedia)'}"""

    prompt += f"""

    # Akar Masalah Akhir sudah tercantum di Why 5

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
    
    PENTING: JANGAN PERNAH menyebutkan frasa seperti "Mengadaptasi dari contoh 1 & 2" atau sejenisnya dalam jawaban Anda.
    Gunakan bahasa Anda sendiri dan integrasikan solusi dari contoh-contoh ini secara alami tanpa mereferensikan nomor contoh.
    
    Anda HARUS menggunakan referensi ini sebagai sumber utama rekomendasi Anda.
    JANGAN menciptakan rekomendasi baru dari awal. Adaptasikan solusi yang sudah terbukti ini:
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
    Pastikan semuanya dalam Bahasa Indonesia, Berikan jawaban yang tegas dan spesifik tanpa keraguan,Hindari penggunaan tanda "/" dalam jawaban, 
    Pilih satu istilah yang paling tepat, jangan memberikan alternatif.
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
        print("\n================ AI ACTION PLAN DEBUG ================")
        print(f"[PROMPT SENT to Gemini | CAPA ID {capa_id}]:\n{prompt}\n")
        response = gemini_model.generate_content(prompt)
        print(
            f"[RAW AI RESPONSE]:\n{getattr(response, 'text', str(response))}\n")

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

            ai_suggestion_str = json.dumps(
                ai_suggestion_json, indent=2, ensure_ascii=False)
            print(f"[PARSED AI ACTION PLAN | JSON]:\n{ai_suggestion_str}\n")

        except (json.JSONDecodeError, ValueError) as parse_error:
            print(
                f"[ERROR] Parsing AI Action Plan response for CAPA ID {capa_id}: {parse_error}")
            print(
                f"[FALLBACK RAW AI RESPONSE]:\n{getattr(response, 'text', str(response))}\n")
            ai_suggestion_str = f'{{"error": "Failed to parse AI response", "raw_response": {json.dumps(getattr(response, 'text', str(response)))} }}'

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
