import json
from datetime import datetime
from models import db, AIKnowledgeBase, RootCause, CapaIssue, ActionPlan


def store_rca_learning(capa_id):
    """
    Stores the user's RCA adjustments in the AI knowledge base for future learning.
    This function extracts the AI-suggested RCA and the user-adjusted RCA,
    then stores the comparison in the knowledge base.
    """
    # Get the issue and its root cause analysis
    issue = CapaIssue.query.options(
        db.joinedload(CapaIssue.root_cause),
        db.joinedload(CapaIssue.gemba_investigation)
    ).get(capa_id)

    if not issue or not issue.root_cause:
        print(
            f"Error: Cannot store learning for CAPA ID {capa_id}. Missing issue or root cause.")
        return False

    rc = issue.root_cause

    # Check if we have both AI suggestion and user adjustment
    if not rc.ai_suggested_rc_json or not rc.user_adjusted_root_cause:
        print(
            f"Warning: Missing AI suggestion or user adjustment for CAPA ID {capa_id}.")
        return False

    try:
        # Parse AI suggestion
        ai_suggestion = json.loads(rc.ai_suggested_rc_json)

        # Prepare data for new structured columns
        ai_suggestion_data = {
            "why1": ai_suggestion.get("why1", ""),
            "why2": ai_suggestion.get("why2", ""),
            "why3": ai_suggestion.get("why3", ""),
            "why4": ai_suggestion.get("why4", ""),
            "root_cause": ai_suggestion.get("root_cause", "")
        }

        # Get the list of user-adjusted whys
        # This uses the property that returns a list
        user_whys_list = rc.user_adjusted_whys

        # Create new AI knowledge base entry
        new_knowledge = AIKnowledgeBase(
            capa_id=capa_id,
            source_type="rca_adjustment",
            machine_name=issue.machine_name,
            issue_description=issue.issue_description,
            # Store the list of whys directly in the new column
            adjusted_whys_json=json.dumps(user_whys_list),
            created_at=datetime.utcnow(),
            is_active=True
            # No adjusted_temporary_actions_json or adjusted_preventive_actions_json for RCA
        )

        db.session.add(new_knowledge)
        db.session.commit()

        print(f"Successfully stored RCA learning from CAPA ID {capa_id}.")
        return True

    except json.JSONDecodeError:
        print(
            f"Error: Failed to parse AI suggestion JSON for CAPA ID {capa_id}.")
        return False
    except Exception as e:
        print(f"Error storing RCA learning from CAPA ID {capa_id}: {e}")
        db.session.rollback()
        return False


def store_action_plan_learning(capa_id):
    """
    Stores the user's action plan adjustments in the AI knowledge base for future learning.
    This function extracts the AI-suggested actions and the user-adjusted actions,
    then stores the comparison in the knowledge base.
    """
    # Get the issue and its action plan
    issue = CapaIssue.query.options(
        db.joinedload(CapaIssue.action_plan),
        db.joinedload(CapaIssue.root_cause)
    ).get(capa_id)

    if not issue or not issue.action_plan:
        print(
            f"Error: Cannot store learning for CAPA ID {capa_id}. Missing issue or action plan.")
        return False

    ap = issue.action_plan

    # Check if we have both AI suggestion and user adjustment
    if not ap.ai_suggested_actions_json or not ap.user_adjusted_actions_json:
        print(
            f"Warning: Missing AI suggestion or user adjustment for CAPA ID {capa_id}.")
        return False

    try:
        # Parse AI suggestion and user adjustments
        ai_suggestion = json.loads(ap.ai_suggested_actions_json)
        user_adjustment = json.loads(ap.user_adjusted_actions_json)

        # Prepare data for new structured columns
        ai_suggestion_data = {
            "temporary_actions": ai_suggestion.get("temporary_action", []),
            "preventive_actions": ai_suggestion.get("preventive_action", [])
        }

        # user_adjustment is already a dict from json.loads(ap.user_adjusted_actions_json)
        # It contains 'temp_actions' and 'prev_actions' lists of dictionaries.

        # Extract only the action text strings as requested
        temp_action_texts = [action.get('action_text', '') for action in user_adjustment.get(
            'temp_actions', []) if action.get('action_text')]
        prev_action_texts = [action.get('action_text', '') for action in user_adjustment.get(
            'prev_actions', []) if action.get('action_text')]

        # Fetch the corresponding adjusted 5 Whys for this CAPA
        final_whys_json = None
        if issue.root_cause:
            # Directly use the stored JSON string from RootCause model
            final_whys_json = issue.root_cause.user_adjusted_whys_json

        # Create new AI knowledge base entry
        new_knowledge = AIKnowledgeBase(
            capa_id=capa_id,
            source_type="action_plan_adjustment",
            machine_name=issue.machine_name,
            issue_description=issue.issue_description,
            # Store the simplified lists of action texts in the new columns
            adjusted_temporary_actions_json=json.dumps(temp_action_texts),
            adjusted_preventive_actions_json=json.dumps(prev_action_texts),
            # Store the associated 5 Whys JSON
            adjusted_whys_json=final_whys_json,
            created_at=datetime.utcnow(),
            is_active=True
        )

        db.session.add(new_knowledge)
        db.session.commit()

        print(
            f"Successfully stored action plan learning from CAPA ID {capa_id}.")
        return True

    except json.JSONDecodeError:
        print(
            f"Error: Failed to parse action plan JSON for CAPA ID {capa_id}.")
        return False
    except Exception as e:
        print(
            f"Error storing action plan learning from CAPA ID {capa_id}: {e}")
        db.session.rollback()
        return False


def get_relevant_action_plan_knowledge(current_capa_issue_description, current_capa_machine_name, current_capa_user_adjusted_whys_json, limit=5):
    """
    Retrieves relevant action plan knowledge (temp/prev action texts) from the knowledge base.
    Filters by:
    1. source_type = 'action_plan_adjustment'.
    2. Matching machine_name.
    3. Matching issue_description (keywords/substrings).
    4. Matching 5 Whys stored in the 'adjusted_whys_json' column of the action plan entry.
    Returns max `limit` entries.
    """
    query = AIKnowledgeBase.query.filter_by(
        source_type="action_plan_adjustment", is_active=True)

    if current_capa_machine_name:
        query = query.filter(AIKnowledgeBase.machine_name ==
                             current_capa_machine_name)

    if current_capa_issue_description:
        search_term = f"%{current_capa_issue_description.lower()}%"
        query = query.filter(db.func.lower(
            AIKnowledgeBase.issue_description).like(search_term))

    # Deserialize current CAPA's 5 Whys for comparison
    try:
        current_whys_list = json.loads(current_capa_user_adjusted_whys_json)
        if not isinstance(current_whys_list, list):
            current_whys_list = []
    except (json.JSONDecodeError, TypeError):
        current_whys_list = []

    # Get potential action plan matches first, then filter by 5 whys in Python
    potential_ap_entries = query.order_by(
        AIKnowledgeBase.created_at.desc()).all()

    results = []
    for entry in potential_ap_entries:
        if len(results) >= limit:
            break

        if not entry.adjusted_whys_json:  # Check if the action plan entry has associated whys
            continue

        try:
            # Compare current whys with the whys stored in this action plan entry
            past_whys_list = json.loads(entry.adjusted_whys_json)
            if not isinstance(past_whys_list, list):
                continue  # Skip if the stored JSON is not a list

            # Simple 5 Why matching (exact list match, order-agnostic)
            if current_whys_list and past_whys_list and sorted(current_whys_list) == sorted(past_whys_list):
                # If whys match, add the action plan data to results
                temp_actions = entry.adjusted_temporary_actions_json or "[]"
                prev_actions = entry.adjusted_preventive_actions_json or "[]"
                results.append({
                    "adjusted_temporary_actions": temp_actions,
                    "adjusted_preventive_actions": prev_actions,
                    "context": {
                        "machine_name": entry.machine_name,
                        "issue_description": entry.issue_description,
                        "source_capa_id": entry.capa_id
                    }
                })
        # Add the except block back to handle potential errors during JSON parsing or comparison
        except (json.JSONDecodeError, TypeError):
            continue  # Skip entries with malformed JSON or unexpected types

    return results  # Return the list of action plan results


def get_relevant_rca_knowledge(current_capa_issue_description, current_capa_machine_name, limit=5):
    """
    Retrieves relevant RCA knowledge (adjusted 5 whys) from the knowledge base based on:
    1. Matching machine_name.
    2. Matching issue_description (keywords/substrings).
    Returns max `limit` entries.
    """
    query = AIKnowledgeBase.query.filter_by(
        source_type="rca_adjustment", is_active=True)

    if current_capa_machine_name:
        query = query.filter(AIKnowledgeBase.machine_name ==
                             current_capa_machine_name)

    # Issue description matching (case-insensitive substring)
    if current_capa_issue_description:
        # Simple keyword matching: split description and search for each word
        # More robust: use LIKE for substring matching
        search_term = f"%{current_capa_issue_description.lower()}%"
        query = query.filter(db.func.lower(
            AIKnowledgeBase.issue_description).like(search_term))

    knowledge_entries = query.order_by(
        AIKnowledgeBase.created_at.desc()).limit(limit).all()

    results = []
    for entry in knowledge_entries:
        # Return the adjusted whys JSON and the context
        if entry.adjusted_whys_json:  # Ensure the data exists
            results.append({
                "adjusted_whys": entry.adjusted_whys_json,  # JSON string of the 5 whys list
                "context": {
                    "machine_name": entry.machine_name,
                    "issue_description": entry.issue_description,
                    "source_capa_id": entry.capa_id  # ID of the CAPA this knowledge came from
                }
            })
    return results
