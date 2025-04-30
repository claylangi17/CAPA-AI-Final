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

        # Prepare knowledge entry
        knowledge_entry = {
            "issue_context": {
                "customer_name": issue.customer_name,
                "item_involved": issue.item_involved,
                "issue_description": issue.issue_description,
                "gemba_findings": issue.gemba_investigation.findings if issue.gemba_investigation else None
            },
            "ai_suggestion": {
                "why1": ai_suggestion.get("why1", ""),
                "why2": ai_suggestion.get("why2", ""),
                "why3": ai_suggestion.get("why3", ""),
                "why4": ai_suggestion.get("why4", ""),
                "root_cause": ai_suggestion.get("root_cause", "")
            },
            "user_adjustment": {
                "why1": rc.user_adjusted_why1 or "",
                "why2": rc.user_adjusted_why2 or "",
                "why3": rc.user_adjusted_why3 or "",
                "why4": rc.user_adjusted_why4 or "",
                "root_cause": rc.user_adjusted_root_cause or ""
            },
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Create new AI knowledge base entry
        new_knowledge = AIKnowledgeBase(
            source_type="rca_adjustment",
            source_id=capa_id,
            knowledge_data=json.dumps(knowledge_entry),
            created_at=datetime.utcnow()
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

        # Prepare knowledge entry
        knowledge_entry = {
            "issue_context": {
                "customer_name": issue.customer_name,
                "item_involved": issue.item_involved,
                "issue_description": issue.issue_description,
                "root_cause": issue.root_cause.user_adjusted_root_cause if issue.root_cause else None
            },
            "ai_suggestion": {
                "temporary_actions": ai_suggestion.get("temporary_action", []),
                "preventive_actions": ai_suggestion.get("preventive_action", [])
            },
            "user_adjustment": {
                "temporary_actions": user_adjustment.get("temp_actions", []),
                "preventive_actions": user_adjustment.get("prev_actions", [])
            },
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Create new AI knowledge base entry
        new_knowledge = AIKnowledgeBase(
            source_type="action_plan_adjustment",
            source_id=capa_id,
            knowledge_data=json.dumps(knowledge_entry),
            created_at=datetime.utcnow()
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


def get_relevant_action_plan_knowledge(issue_description, root_cause=None, limit=5):
    """
    Retrieves relevant action plan knowledge from the knowledge base based on the issue description
    and root cause. Currently uses a simple keyword matching approach.

    In a production environment, you would use a more sophisticated similarity search,
    vector embeddings, or semantic search.
    """
    knowledge_entries = AIKnowledgeBase.query.filter_by(source_type="action_plan_adjustment").order_by(
        AIKnowledgeBase.created_at.desc()).limit(20).all()

    # Simple keyword matching (could be improved with embeddings/vector search)
    relevant_entries = []
    search_text = (issue_description + " " + (root_cause or "")).lower()

    for entry in knowledge_entries:
        try:
            knowledge_data = json.loads(entry.knowledge_data)
            context = knowledge_data.get("issue_context", {})

            # Calculate a simple matching score based on keyword overlap
            context_text = (
                (context.get("issue_description", "") or "") + " " +
                (context.get("root_cause", "") or "")
            ).lower()

            # Very simple similarity score (would be replaced by better methods)
            words1 = set(search_text.split())
            words2 = set(context_text.split())
            common_words = words1.intersection(words2)

            if len(common_words) > 0:
                similarity = len(common_words) / (len(words1) +
                                                  len(words2) - len(common_words))

                relevant_entries.append({
                    "entry": knowledge_data,
                    "score": similarity
                })
        except:
            continue

    # Sort by score and get top entries
    relevant_entries.sort(key=lambda x: x["score"], reverse=True)
    return [entry["entry"] for entry in relevant_entries[:limit]]


def get_relevant_rca_knowledge(issue_description, gemba_findings=None, limit=5):
    """
    Retrieves relevant RCA knowledge from the knowledge base based on the issue description 
    and gemba findings. Currently uses a simple keyword matching approach.

    In a production environment, you would use a more sophisticated similarity search,
    vector embeddings, or semantic search.
    """
    knowledge_entries = AIKnowledgeBase.query.filter_by(source_type="rca_adjustment").order_by(
        AIKnowledgeBase.created_at.desc()).limit(20).all()

    # Simple keyword matching (could be improved with embeddings/vector search)
    relevant_entries = []
    search_text = (issue_description + " " + (gemba_findings or "")).lower()

    for entry in knowledge_entries:
        try:
            knowledge_data = json.loads(entry.knowledge_data)
            context = knowledge_data.get("issue_context", {})

            # Calculate a simple matching score based on keyword overlap
            context_text = (
                (context.get("issue_description", "") or "") + " " +
                (context.get("gemba_findings", "") or "")
            ).lower()

            # Very simple similarity score (would be replaced by better methods)
            words1 = set(search_text.split())
            words2 = set(context_text.split())
            common_words = words1.intersection(words2)

            if len(common_words) > 0:
                similarity = len(common_words) / (len(words1) +
                                                  len(words2) - len(common_words))

                relevant_entries.append({
                    "entry": knowledge_data,
                    "score": similarity
                })
        except:
            continue

    # Sort by score and get top entries
    relevant_entries.sort(key=lambda x: x["score"], reverse=True)
    return [entry["entry"] for entry in relevant_entries[:limit]]
