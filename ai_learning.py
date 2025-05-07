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
    Retrieves relevant action plan knowledge (temp/prev action texts) from the knowledge base using semantic search.
    Uses a combination of:
    1. Exact machine_name matching (if provided)
    2. Semantic similarity for issue descriptions
    3. Semantic similarity for WHYs content
    Returns max `limit` entries, sorted by relevance score.
    """
    import os
    from sqlalchemy import func

    # First, filter by machine name and ensure we have action plans
    query = AIKnowledgeBase.query.filter_by(is_active=True)

    # Only include entries with valid action plans
    query = query.filter(
        (func.length(func.replace(AIKnowledgeBase.adjusted_temporary_actions_json, ' ', '')) >= 5) |
        (func.length(func.replace(
            AIKnowledgeBase.adjusted_preventive_actions_json, ' ', '')) >= 5)
    )

    # Filter by machine name if provided
    if current_capa_machine_name:
        query = query.filter(AIKnowledgeBase.machine_name ==
                             current_capa_machine_name)

    # Get all potential matches
    potential_ap_entries = query.order_by(
        AIKnowledgeBase.created_at.desc()).all()

    # If no entries found, return empty list
    if not potential_ap_entries:
        print("No potential action plan entries found in database.")
        return []

    # Try to use embeddings for semantic search if available
    try:
        # Check if we have access to an embedding model (Google's text-embedding-gecko model)
        # If GOOGLE_API_KEY is available, use it for embeddings
        from ai_service import GOOGLE_API_KEY
        if GOOGLE_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)

            # Initialize the embedding model
            embedding_model = genai.get_model("models/embedding-001")

            # Function to get embedding
            def get_embedding(text):
                if not text or not isinstance(text, str) or text.strip() == "":
                    return None
                try:
                    # Use the correct embedding method based on the Gemini API
                    result = genai.embed_content(
                        model="models/embedding-001",
                        content=text,
                        task_type="retrieval_document"
                    )
                    return result["embedding"]
                except Exception as e:
                    print(f"Error getting embedding: {e}")
                    return None

            # Function to calculate cosine similarity between two vectors
            def cosine_similarity(vec1, vec2):
                import numpy as np
                if vec1 is None or vec2 is None:
                    return 0.0
                dot_product = np.dot(vec1, vec2)
                norm_a = np.linalg.norm(vec1)
                norm_b = np.linalg.norm(vec2)
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                return dot_product / (norm_a * norm_b)

            # Get embeddings for current issue description and WHYs
            current_issue_embedding = get_embedding(
                current_capa_issue_description)

            # Extract WHYs text for embedding
            current_whys_text = ""
            try:
                current_whys_list = json.loads(
                    current_capa_user_adjusted_whys_json)
                if isinstance(current_whys_list, list):
                    # Extract text from WHYs list
                    for why_item in current_whys_list:
                        if isinstance(why_item, dict):
                            # Try different key patterns
                            for key in ['why_answer', 'answer']:
                                if key in why_item:
                                    current_whys_text += why_item[key] + " "
                        elif isinstance(why_item, str):
                            current_whys_text += why_item + " "
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing current WHYs: {e}")
                current_whys_list = []

            current_whys_embedding = get_embedding(current_whys_text)

            # Calculate similarity scores
            print(
                f"Calculating similarity scores for {len(potential_ap_entries)} potential action plans...")
            scored_entries = []
            for idx, entry in enumerate(potential_ap_entries):
                # Skip entries without action plans
                if not entry.adjusted_whys_json or \
                   (not entry.adjusted_temporary_actions_json and not entry.adjusted_preventive_actions_json):
                    print(
                        f"Skipping entry {idx+1} (CAPA ID: {entry.capa_id}) - Missing WHYs or action plans")
                    continue

                # Get embeddings for this entry
                entry_issue_embedding = get_embedding(entry.issue_description)

                # Extract WHYs text for embedding
                entry_whys_text = ""
                try:
                    past_whys_list = json.loads(entry.adjusted_whys_json)
                    if isinstance(past_whys_list, list):
                        for why_item in past_whys_list:
                            if isinstance(why_item, dict):
                                for key in ['why_answer', 'answer']:
                                    if key in why_item:
                                        entry_whys_text += why_item[key] + " "
                            elif isinstance(why_item, str):
                                entry_whys_text += why_item + " "
                except (json.JSONDecodeError, TypeError):
                    continue

                entry_whys_embedding = get_embedding(entry_whys_text)

                # Calculate similarity scores
                issue_similarity = cosine_similarity(
                    current_issue_embedding, entry_issue_embedding) if current_issue_embedding else 0
                whys_similarity = cosine_similarity(
                    current_whys_embedding, entry_whys_embedding) if current_whys_embedding else 0

                # Combined score (weighted average)
                # Give more weight to WHYs similarity as it's more important for action plan relevance
                combined_score = (0.3 * issue_similarity) + (0.7 *
                                                             whys_similarity) if whys_similarity > 0 else issue_similarity

                # Debug output for similarity scores
                print(f"Entry {idx+1} (CAPA ID: {entry.capa_id}) - Issue similarity: {issue_similarity:.2f}, WHYs similarity: {whys_similarity:.2f}, Combined: {combined_score:.2f}")

                # Add to scored entries if score is above threshold (lowered for better recall)
                if combined_score > 0.3:  # Lowered threshold for better recall
                    temp_actions = entry.adjusted_temporary_actions_json or "[]"
                    prev_actions = entry.adjusted_preventive_actions_json or "[]"
                    scored_entries.append({
                        "score": combined_score,
                        "data": {
                            "adjusted_temporary_actions": temp_actions,
                            "adjusted_preventive_actions": prev_actions,
                            "context": {
                                "machine_name": entry.machine_name,
                                "issue_description": entry.issue_description,
                                "source_capa_id": entry.capa_id,
                                "similarity_score": round(combined_score, 2)
                            }
                        }
                    })

            # Sort by score and take top 'limit' entries
            scored_entries.sort(key=lambda x: x["score"], reverse=True)
            results = [entry["data"] for entry in scored_entries[:limit]]

            if results:
                print(
                    f"Found {len(results)} semantically similar action plans with scores above threshold.")
                for i, result in enumerate(results):
                    context = result.get('context', {})
                    print(
                        f"  {i+1}. CAPA ID: {context.get('source_capa_id')}, Score: {context.get('similarity_score')}, Machine: {context.get('machine_name')}")
                return results
            else:
                print("No semantically similar action plans found above threshold.")
    except Exception as e:
        print(f"Error using semantic search for action plans: {e}")

    # Fallback to traditional search if semantic search fails or finds no results
    print("Falling back to traditional keyword search for action plans.")

    # Reset results for fallback method
    results = []

    # Use traditional keyword search as fallback
    if current_capa_issue_description:
        # Try with more flexible keyword matching
        keywords = [word.lower()
                    for word in current_capa_issue_description.split() if len(word) > 3]

        for entry in potential_ap_entries:
            if len(results) >= limit:
                break

            # Skip entries without action plans
            if not entry.adjusted_whys_json or \
               (not entry.adjusted_temporary_actions_json and not entry.adjusted_preventive_actions_json):
                continue

            # Check if any keyword matches in the issue description
            issue_desc_lower = entry.issue_description.lower()
            keyword_match = any(
                keyword in issue_desc_lower for keyword in keywords)

            if keyword_match:
                temp_actions = entry.adjusted_temporary_actions_json or "[]"
                prev_actions = entry.adjusted_preventive_actions_json or "[]"
                results.append({
                    "adjusted_temporary_actions": temp_actions,
                    "adjusted_preventive_actions": prev_actions,
                    "context": {
                        "machine_name": entry.machine_name,
                        "issue_description": entry.issue_description,
                        "source_capa_id": entry.capa_id,
                        "match_type": "keyword"
                    }
                })

    return results

    return results


def get_relevant_rca_knowledge(current_capa_issue_description, current_capa_machine_name, limit=5):
    """
    Retrieves relevant RCA knowledge (adjusted 5 whys) from the knowledge base using semantic search.
    Uses a combination of:
    1. Exact machine_name matching (if provided)
    2. Semantic similarity for issue descriptions
    Returns max `limit` entries, sorted by relevance score.
    """
    from sqlalchemy import func

    # First, filter by machine name and ensure we have valid WHYs data
    query = AIKnowledgeBase.query.filter_by(is_active=True)

    # Only include entries with at least 10 non-whitespace characters in adjusted_whys_json
    query = query.filter(
        func.length(func.replace(
            AIKnowledgeBase.adjusted_whys_json, ' ', '')) >= 10
    )

    # Filter by machine name if provided
    if current_capa_machine_name:
        query = query.filter(AIKnowledgeBase.machine_name ==
                             current_capa_machine_name)

    # Get all potential matches
    potential_rca_entries = query.order_by(
        AIKnowledgeBase.created_at.desc()).all()

    # If no entries found, return empty list
    if not potential_rca_entries:
        print("No potential RCA entries found in database.")
        return []

    # Try to use embeddings for semantic search if available
    try:
        # Check if we have access to an embedding model (Google's text-embedding-gecko model)
        # If GOOGLE_API_KEY is available, use it for embeddings
        from ai_service import GOOGLE_API_KEY
        if GOOGLE_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)

            # Initialize the embedding model
            embedding_model = genai.get_model("models/embedding-001")

            # Function to get embedding
            def get_embedding(text):
                if not text or not isinstance(text, str) or text.strip() == "":
                    return None
                try:
                    # Use the correct embedding method based on the Gemini API
                    result = genai.embed_content(
                        model="models/embedding-001",
                        content=text,
                        task_type="retrieval_document"
                    )
                    return result["embedding"]
                except Exception as e:
                    print(f"Error getting embedding: {e}")
                    return None

            # Function to calculate cosine similarity between two vectors
            def cosine_similarity(vec1, vec2):
                import numpy as np
                if vec1 is None or vec2 is None:
                    return 0.0
                dot_product = np.dot(vec1, vec2)
                norm_a = np.linalg.norm(vec1)
                norm_b = np.linalg.norm(vec2)
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                return dot_product / (norm_a * norm_b)

            # Get embeddings for current issue description
            current_issue_embedding = get_embedding(
                current_capa_issue_description)

            # Calculate similarity scores for each potential entry
            scored_entries = []
            for entry in potential_rca_entries:
                # Skip entries without valid WHYs data
                if not entry.adjusted_whys_json:
                    continue

                # Get embeddings for this entry's issue description
                entry_issue_embedding = get_embedding(entry.issue_description)

                # Calculate similarity score
                issue_similarity = cosine_similarity(
                    current_issue_embedding, entry_issue_embedding) if current_issue_embedding else 0

                # Add to scored entries if score is above threshold (lowered for better recall)
                if issue_similarity > 0.3:  # Lowered threshold for better recall
                    scored_entries.append({
                        "score": issue_similarity,
                        "data": {
                            "adjusted_whys": entry.adjusted_whys_json,
                            "context": {
                                "machine_name": entry.machine_name,
                                "issue_description": entry.issue_description,
                                "source_capa_id": entry.capa_id,
                                "similarity_score": round(issue_similarity, 2)
                            }
                        }
                    })

            # Sort by score and take top 'limit' entries
            scored_entries.sort(key=lambda x: x["score"], reverse=True)
            results = [entry["data"] for entry in scored_entries[:limit]]

            if results:
                print(
                    f"Found {len(results)} semantically similar RCA entries.")
                return results
            else:
                print("No semantically similar RCA entries found.")
    except Exception as e:
        print(f"Error using semantic search for RCA knowledge: {e}")

    # Fallback to traditional search if semantic search fails or finds no results
    print("Falling back to traditional keyword search for RCA knowledge.")

    # Reset results for fallback method
    results = []

    # Use traditional keyword search as fallback
    if current_capa_issue_description:
        # Try with more flexible keyword matching
        keywords = [word.lower()
                    for word in current_capa_issue_description.split() if len(word) > 3]

        for entry in potential_rca_entries:
            if len(results) >= limit:
                break

            # Skip entries without valid WHYs data
            if not entry.adjusted_whys_json:
                continue

            # Check if any keyword matches in the issue description
            issue_desc_lower = entry.issue_description.lower()
            keyword_match = any(
                keyword in issue_desc_lower for keyword in keywords)

            if keyword_match:
                results.append({
                    "adjusted_whys": entry.adjusted_whys_json,
                    "context": {
                        "machine_name": entry.machine_name,
                        "issue_description": entry.issue_description,
                        "source_capa_id": entry.capa_id,
                        "match_type": "keyword"
                    }
                })

    return results
