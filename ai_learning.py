import json
from datetime import datetime
from models import db, AIKnowledgeBase, RootCause, CapaIssue, ActionPlan


def store_knowledge_on_capa_close(capa_id):
    """
    Stores the final RCA and Action Plan adjustments in the AI knowledge base
    when a CAPA is closed. This creates or updates a single consolidated entry.
    """
    issue = CapaIssue.query.options(
        db.joinedload(CapaIssue.root_cause),
        db.joinedload(CapaIssue.action_plan)
    ).get(capa_id)

    if not issue:
        print(f"Error: CAPA ID {capa_id} not found.")
        return False

    final_whys_json = None
    if issue.root_cause and issue.root_cause.user_adjusted_whys_json:
        final_whys_json = issue.root_cause.user_adjusted_whys_json
    else:
        print(
            f"Warning: No final RCA (user_adjusted_whys_json) found for CAPA ID {capa_id}.")
        # Allow proceeding without RCA if necessary, or return False if RCA is mandatory
        # For now, we'll allow it to proceed and store null for whys.

    temp_action_texts_json = None
    prev_action_texts_json = None
    if issue.action_plan and issue.action_plan.user_adjusted_actions_json:
        try:
            user_adjustment = json.loads(
                issue.action_plan.user_adjusted_actions_json)
            temp_action_texts = [action.get('action_text', '') for action in user_adjustment.get(
                'temp_actions', []) if action.get('action_text')]
            prev_action_texts = [action.get('action_text', '') for action in user_adjustment.get(
                'prev_actions', []) if action.get('action_text')]
            temp_action_texts_json = json.dumps(temp_action_texts)
            prev_action_texts_json = json.dumps(prev_action_texts)
        except json.JSONDecodeError:
            print(
                f"Error: Failed to parse user_adjusted_actions_json for CAPA ID {capa_id}.")
            # Allow proceeding without action plans if parsing fails, or return False
            # For now, we'll allow it to proceed and store null for actions.
    else:
        print(
            f"Warning: No final Action Plan (user_adjusted_actions_json) found for CAPA ID {capa_id}.")

    # If there's neither RCA nor Action Plan data, maybe don't store anything.
    if not final_whys_json and not temp_action_texts_json and not prev_action_texts_json:
        print(
            f"Info: No RCA or Action Plan data to store for CAPA ID {capa_id}. Skipping knowledge entry.")
        return False  # Or True, depending on desired behavior for empty data

    try:
        # Check if an entry already exists for this capa_id
        knowledge_entry = AIKnowledgeBase.query.filter_by(
            capa_id=capa_id).first()

        if knowledge_entry:
            # Update existing entry
            knowledge_entry.machine_name = issue.machine_name
            knowledge_entry.issue_description = issue.issue_description
            knowledge_entry.adjusted_whys_json = final_whys_json
            knowledge_entry.adjusted_temporary_actions_json = temp_action_texts_json
            knowledge_entry.adjusted_preventive_actions_json = prev_action_texts_json
            knowledge_entry.created_at = datetime.utcnow()  # Update timestamp
            knowledge_entry.is_active = True
            print(f"Successfully updated AI knowledge for CAPA ID {capa_id}.")
        else:
            # Create new AI knowledge base entry
            new_knowledge = AIKnowledgeBase(
                capa_id=capa_id,
                machine_name=issue.machine_name,
                issue_description=issue.issue_description,
                adjusted_whys_json=final_whys_json,
                adjusted_temporary_actions_json=temp_action_texts_json,
                adjusted_preventive_actions_json=prev_action_texts_json,
                created_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(new_knowledge)
            print(
                f"Successfully stored new AI knowledge for CAPA ID {capa_id}.")

        db.session.commit()
        return True

    except Exception as e:
        print(
            f"Error storing AI knowledge for CAPA ID {capa_id}: {e}")
        db.session.rollback()
        return False


def get_relevant_action_plan_knowledge(current_capa_issue_description, current_capa_machine_name, current_capa_user_adjusted_whys_json, limit=5):
    """
    Retrieves relevant action plan knowledge (temp/prev action texts) from the knowledge base.
    Filters by:
    1. Matching machine_name.
    2. Matching issue_description (keywords/substrings).
    3. Matching 5 Whys stored in the 'adjusted_whys_json' column.
    Returns max `limit` entries.
    """
    query = AIKnowledgeBase.query.filter_by(
        is_active=True)  # No source_type filter

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

    potential_ap_entries = query.order_by(
        AIKnowledgeBase.created_at.desc()).all()

    results = []
    for entry in potential_ap_entries:
        if len(results) >= limit:
            break

        # Entry must have both whys and at least one type of action plan
        if not entry.adjusted_whys_json or \
           (not entry.adjusted_temporary_actions_json and not entry.adjusted_preventive_actions_json):
            continue

        try:
            past_whys_list = json.loads(entry.adjusted_whys_json)
            if not isinstance(past_whys_list, list):
                continue

            if current_whys_list and past_whys_list and sorted(current_whys_list) == sorted(past_whys_list):
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
        except (json.JSONDecodeError, TypeError):
            continue

    return results


def get_relevant_rca_knowledge(current_capa_issue_description, current_capa_machine_name, limit=5):
    """
    Retrieves relevant RCA knowledge (adjusted 5 whys) from the knowledge base based on:
    1. Matching machine_name.
    2. Matching issue_description (keywords/substrings).
    Returns max `limit` entries.
    """
    query = AIKnowledgeBase.query.filter_by(
        is_active=True)  # No source_type filter

    if current_capa_machine_name:
        query = query.filter(AIKnowledgeBase.machine_name ==
                             current_capa_machine_name)

    if current_capa_issue_description:
        search_term = f"%{current_capa_issue_description.lower()}%"
        query = query.filter(db.func.lower(
            AIKnowledgeBase.issue_description).like(search_term))

    knowledge_entries = query.order_by(
        AIKnowledgeBase.created_at.desc()).limit(limit).all()

    results = []
    for entry in knowledge_entries:
        if entry.adjusted_whys_json:  # Ensure the entry has RCA data
            results.append({
                "adjusted_whys": entry.adjusted_whys_json,
                "context": {
                    "machine_name": entry.machine_name,
                    "issue_description": entry.issue_description,
                    "source_capa_id": entry.capa_id
                }
            })
    return results
