import json
from datetime import datetime
from models import db, AIKnowledgeBase, RootCause, CapaIssue, ActionPlan
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Initialize the embedding model globally at the module level
embedding_model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
embedding_model = None
try:
    embedding_model = SentenceTransformer(embedding_model_name)
    print(
        f"Successfully initialized SentenceTransformer model: {embedding_model_name}")
except Exception as e:
    print(
        f"Error initializing SentenceTransformer model {embedding_model_name} at module level: {e}")
    # embedding_model remains None, fallback mechanisms should handle this.


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


def get_embedding_st_rca(text_list):
    if not text_list or not all(isinstance(t, str) and t.strip() != "" for t in text_list):
        return [None] * len(text_list) if text_list else []
    try:
        embeddings = embedding_model.encode(
            text_list, convert_to_tensor=False)
        print(
            f"[RCA DEBUG get_embedding_st_rca] Input text_list: {text_list}")
        print(
            f"[RCA DEBUG get_embedding_st_rca] Raw embeddings from model: {embeddings}")
        print(
            f"[RCA DEBUG get_embedding_st_rca] Type of embeddings from model: {type(embeddings)}")
        if isinstance(embeddings, np.ndarray):
            print(
                f"[RCA DEBUG get_embedding_st_rca] Embeddings dtype: {embeddings.dtype}")
        return embeddings
    except Exception as e:
        print(
            f"Error getting embedding with SentenceTransformer for RCA: {e}")
        return [None] * len(text_list)


def cosine_similarity_rca(vec1, vec2):
    """Calculates the cosine similarity between two vectors."""
    logging.debug(
        f"[RCA DEBUG cosine_similarity_rca ENTRY] vec1 type: {type(vec1)}, vec2 type: {type(vec2)}")
    # logging.debug(f"[RCA DEBUG cosine_similarity_rca ENTRY] vec1 content: {vec1}") # Can be very verbose
    # logging.debug(f"[RCA DEBUG cosine_similarity_rca ENTRY] vec2 content: {vec2}") # Can be very verbose

    # Ensure both vectors are not None and are numpy arrays before proceeding
    if vec1 is not None and vec2 is not None and isinstance(vec1, np.ndarray) and isinstance(vec2, np.ndarray):
        # Reshape a 1D array to a 2D array with one row
        vec1_reshaped = vec1.reshape(1, -1)
        vec2_reshaped = vec2.reshape(1, -1)
        similarity = cosine_similarity(
            vec1_reshaped, vec2_reshaped)[0][0]
        logging.debug(
            f"[RCA DEBUG cosine_similarity_rca] Calculated similarity: {similarity}")
        return similarity
    else:
        logging.debug(
            f"[RCA DEBUG cosine_similarity_rca] Invalid input for cosine similarity (vec1 type: {type(vec1)}, vec2 type: {type(vec2)}). Returning 0.0")
        return 0.0  # Return 0.0 if inputs are not valid to prevent errors


def _extract_text_from_whys_json_str(whys_json_str):
    """Extracts concatenated 'why' and 'cause' text from a 5 Whys JSON string."""
    if not whys_json_str:
        return ""
    try:
        whys_data = json.loads(whys_json_str)
        text_parts = []
        for item in whys_data:
            if isinstance(item, dict):
                text_parts.append(item.get('why', ''))
                text_parts.append(item.get('cause', ''))
        return " ".join(filter(None, text_parts)).strip()
    except json.JSONDecodeError as e:
        logging.error(
            f"Error decoding WHYs JSON: {e} - JSON string: {whys_json_str}")
        return ""


def get_relevant_action_plan_knowledge(current_capa_issue_description, current_capa_machine_name, current_capa_user_adjusted_whys_json, limit=5):
    """
    Retrieves relevant action plan knowledge (temp/prev action texts) from the knowledge base using semantic search.
    Uses a two-stage semantic process:
    1. Filter top N (e.g., 5) entries by issue description similarity.
    2. From these N, filter top M (e.g., 3) by 5 Whys similarity.
    Also considers exact machine_name matching (if provided).
    Returns max `limit` entries, sorted by the final stage's relevance score.
    """
    logging.info(
        f"Starting get_relevant_action_plan_knowledge for machine: {current_capa_machine_name}, limit: {limit}")
    logging.debug(
        f"Current CAPA Issue Description: {current_capa_issue_description}")

    query = AIKnowledgeBase.query
    if current_capa_machine_name and current_capa_machine_name.lower() != 'all':
        query = query.filter_by(machine_name=current_capa_machine_name)

    potential_ap_entries = query.filter(
        (AIKnowledgeBase.adjusted_temporary_actions_json != None) |
        (AIKnowledgeBase.adjusted_preventive_actions_json != None)
    ).all()

    logging.info(
        f"Found {len(potential_ap_entries)} potential AP entries from DB (machine: {current_capa_machine_name}).")

    results = []

    if embedding_model and potential_ap_entries:
        # STAGE 0: Filter by exact Machine Name
        if current_capa_machine_name:
            machine_filtered_entries = [
                entry for entry in potential_ap_entries if entry.machine_name == current_capa_machine_name]
            logging.info(
                f"Filtered down to {len(machine_filtered_entries)} entries matching machine name: '{current_capa_machine_name}'.")
            if not machine_filtered_entries:
                logging.info(
                    f"No action plan knowledge base entries found for machine name '{current_capa_machine_name}'. Skipping semantic search for this machine.")
                # Optionally, could proceed with all entries if no machine match, or return empty, or fallback to keyword on all.
                # For now, we will only proceed with machine-matched entries if a machine name is provided.
                # Effectively stops further semantic processing for this specific request if no machine match
                potential_ap_entries = []
            else:
                # Continue with machine-filtered entries
                potential_ap_entries = machine_filtered_entries
        else:
            logging.info(
                "No current_capa_machine_name provided, proceeding with all potential AP entries for semantic search.")
            # potential_ap_entries remains as all entries

        # Proceed only if there are entries after machine filtering (or if no machine name was specified)
        if not potential_ap_entries:
            logging.info(
                "No entries to process after machine name filtering (if applicable). Skipping semantic search stages.")
        else:
            # Get embedding for current issue description
            current_issue_embedding_list = get_embedding_st_rca(
                [current_capa_issue_description])
            current_issue_embedding = None
            if current_issue_embedding_list is not None:
                if isinstance(current_issue_embedding_list, np.ndarray) and current_issue_embedding_list.ndim == 2 and current_issue_embedding_list.shape[0] > 0:
                    current_issue_embedding = current_issue_embedding_list[0]
                elif isinstance(current_issue_embedding_list, list) and len(current_issue_embedding_list) > 0 and isinstance(current_issue_embedding_list[0], np.ndarray):
                    current_issue_embedding = current_issue_embedding_list[0]

            if current_issue_embedding is None:
                logging.warning(
                    "Could not generate embedding for current issue description. Proceeding without issue-based semantic search for action plans.")

            # Get embedding for current 5 WHYs
            current_whys_text = _extract_text_from_whys_json_str(
                current_capa_user_adjusted_whys_json)
            current_whys_embedding = None
            # Only proceed if issue embedding was successful
            if current_whys_text and current_issue_embedding is not None:
                current_whys_embedding_list = get_embedding_st_rca(
                    [current_whys_text])
                if current_whys_embedding_list is not None:
                    if isinstance(current_whys_embedding_list, np.ndarray) and current_whys_embedding_list.ndim == 2 and current_whys_embedding_list.shape[0] > 0:
                        current_whys_embedding = current_whys_embedding_list[0]
                    elif isinstance(current_whys_embedding_list, list) and len(current_whys_embedding_list) > 0 and isinstance(current_whys_embedding_list[0], np.ndarray):
                        current_whys_embedding = current_whys_embedding_list[0]

            if not current_whys_text:
                logging.info(
                    "No current WHYs text provided for action plan semantic search.")
            elif current_whys_embedding is None and current_issue_embedding is not None:
                logging.warning(
                    "Could not generate embedding for current WHYs text, but issue embedding exists.")

            # STAGE 1: Filter by Issue Description Similarity (Top 5)
            stage1_candidates = []

            if current_issue_embedding is not None:
                # Prepare batch for entry issue descriptions from (potentially machine-filtered) potential_ap_entries
                entry_issue_descriptions = [
                    entry.issue_description for entry in potential_ap_entries]
                if entry_issue_descriptions:  # Ensure there are descriptions to process
                    entry_issue_embeddings = get_embedding_st_rca(
                        entry_issue_descriptions)

                    logging.info(
                        f"Calculating Stage 1 (Issue Sim.) scores for {len(potential_ap_entries)} potential APs (post machine filter) using SentenceTransformer...")

                    for idx, entry in enumerate(potential_ap_entries):
                        # Skip entries without action plans (already filtered by DB query, but good to double check structure)
                        if not entry.adjusted_temporary_actions_json and not entry.adjusted_preventive_actions_json:
                            continue  # Should not happen due to DB query filter

                        entry_issue_embedding = entry_issue_embeddings[idx] if entry_issue_embeddings is not None and idx < len(
                            entry_issue_embeddings) else None

                        issue_similarity = 0.0
                        if entry_issue_embedding is not None:
                            issue_similarity = cosine_similarity_rca(
                                current_issue_embedding, entry_issue_embedding)

                        # Store all entries with their issue similarity for now
                        stage1_candidates.append({
                            'entry': entry,
                            'issue_similarity': issue_similarity
                        })
            else:  # current_issue_embedding is None, skip stage 1 and stage 2 logic
                logging.info(
                    "Skipping semantic stages for action plans as current issue embedding is not available.")

            # Sort stage1_candidates by issue_similarity descending and take top N
            TOP_N_ISSUE_SIMILARITY = 5
            stage1_top_n = sorted(
                stage1_candidates,
                key=lambda x: x['issue_similarity'],
                reverse=True
            )[:TOP_N_ISSUE_SIMILARITY]

            logging.info(
                f"Stage 1 (Issue Sim.) selected top {len(stage1_top_n)} candidates.")
            for cand in stage1_top_n:
                logging.debug(
                    f"  S1 Candidate: CAPA ID {cand['entry'].capa_id}, Issue Sim: {cand['issue_similarity']:.4f}")

            # STAGE 2: Filter by 5 WHYs Similarity (Top M from Stage 1's Top N)
            stage2_candidates = []
            if current_whys_embedding is not None and stage1_top_n:
                logging.info("Calculating Stage 2 (WHYs Sim.) scores...")
                # Prepare batch for historical WHYs text embeddings
                historical_whys_texts = [_extract_text_from_whys_json_str(
                    cand['entry'].adjusted_whys_json) for cand in stage1_top_n]
                historical_whys_embeddings_list = get_embedding_st_rca(
                    historical_whys_texts)

                for idx, candidate_s1 in enumerate(stage1_top_n):
                    entry = candidate_s1['entry']
                    issue_similarity = candidate_s1['issue_similarity']

                    historical_whys_embedding = None
                    if historical_whys_embeddings_list is not None and idx < len(historical_whys_embeddings_list):
                        # Check if the specific embedding is not None (it could be if _extract_text_from_whys_json_str returned empty)
                        if isinstance(historical_whys_embeddings_list[idx], np.ndarray):
                            historical_whys_embedding = historical_whys_embeddings_list[idx]

                    whys_similarity = 0.0
                    if historical_whys_embedding is not None:
                        whys_similarity = cosine_similarity_rca(
                            current_whys_embedding, historical_whys_embedding)

                    logging.debug(
                        f"  S2 Candidate: CAPA ID {entry.capa_id}, Issue Sim: {issue_similarity:.4f}, WHYs Sim: {whys_similarity:.4f}")
                    stage2_candidates.append({
                        'entry': entry,
                        'issue_similarity': issue_similarity,
                        'whys_similarity': whys_similarity
                    })
            elif stage1_top_n:  # Current WHYs embedding is None, but we have Stage 1 results. Use Stage 1 results with 0 WHYs score.
                logging.info(
                    "Current WHYs embedding not available. Using Stage 1 issue similarity for ranking, WHYs similarity will be 0.")
                for candidate_s1 in stage1_top_n:
                    stage2_candidates.append({
                        'entry': candidate_s1['entry'],
                        'issue_similarity': candidate_s1['issue_similarity'],
                        'whys_similarity': 0.0
                    })

            # Sort stage2_candidates by whys_similarity descending and take top M
            TOP_M_WHYS_SIMILARITY = 3
            stage2_top_m = sorted(
                stage2_candidates,
                key=lambda x: x['whys_similarity'],
                reverse=True
            )[:TOP_M_WHYS_SIMILARITY]

            logging.info(
                f"Stage 2 (WHYs Sim.) selected top {len(stage2_top_m)} candidates to form final results.")

            # Format final results, respecting the overall 'limit'
            for candidate_s2 in stage2_top_m:
                if len(results) >= limit:
                    break
                entry = candidate_s2['entry']
                temp_actions = entry.adjusted_temporary_actions_json or "[]"
                prev_actions = entry.adjusted_preventive_actions_json or "[]"
                results.append({
                    # Primary score is WHYs similarity
                    "score": candidate_s2['whys_similarity'],
                    "adjusted_temporary_actions": temp_actions,
                    "adjusted_preventive_actions": prev_actions,
                    "context": {
                        "machine_name": entry.machine_name,
                        "issue_description": entry.issue_description,
                        "source_capa_id": entry.capa_id,
                        "issue_similarity_score": round(candidate_s2['issue_similarity'], 4),
                        "whys_similarity_score": round(candidate_s2['whys_similarity'], 4),
                        "match_type": "semantic_issue_then_whys"
                    }
                })

            if results:
                logging.info(
                    f"Found {len(results)} semantically similar action plans using two-stage process.")
                for i, res_item in enumerate(results):
                    logging.info(
                        f"  {i+1}. CAPA ID: {res_item['context']['source_capa_id']}, Final Score (Whys Sim): {res_item['score']:.4f}, Issue Sim: {res_item['context']['issue_similarity_score']:.4f}, Machine: {res_item['context']['machine_name']}")

    # Fallback to keyword based search if semantic search yielded no results or was skipped
    if not results and potential_ap_entries:  # Check 'results' not 'scored_entries'
        logging.info(
            "Semantic search for action plans yielded no results or was skipped, trying keyword based search...")
        # Use traditional keyword search as fallback
        if current_capa_issue_description:
            # Try with more flexible keyword matching
            keywords = [word.lower()
                        for word in current_capa_issue_description.split() if len(word) > 3]

            for entry in potential_ap_entries:
                if len(results) >= limit:
                    break

                # Skip entries without action plans
                if not entry.adjusted_temporary_actions_json and not entry.adjusted_preventive_actions_json:
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


def get_relevant_rca_knowledge(current_capa_issue_description, current_capa_machine_name, limit=5):
    """
    Retrieves relevant RCA knowledge (adjusted 5 whys) from the knowledge base using semantic search.
    Uses a combination of:
    1. Exact machine_name matching (if provided)
    2. Semantic similarity for issue descriptions
    Returns max `limit` entries, sorted by relevance score.
    """
    from sqlalchemy import func
    # SentenceTransformer and numpy are imported at the top of the module.
    # embedding_model is initialized globally at the module level.

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

    # Use sentence-transformers for semantic search
    if embedding_model:
        try:
            # Get embeddings for current issue description
            current_issue_embedding_list = get_embedding_st_rca(
                [current_capa_issue_description])
            print(
                f"[RCA DEBUG POST get_embed_current] current_issue_embedding_list type: {type(current_issue_embedding_list)}")
            print(
                f"[RCA DEBUG POST get_embed_current] current_issue_embedding_list content: {current_issue_embedding_list}")

            # current_issue_embedding_list is either np.ndarray (shape (1,D)) from successful encode of one item,
            # or a Python list [None] if get_embedding_st_rca failed internally for that one item.
            if isinstance(current_issue_embedding_list, np.ndarray):
                # Successful embedding, current_issue_embedding_list is ndarray (1,D)
                # We want the 1D vector itself.
                if current_issue_embedding_list.ndim == 2 and current_issue_embedding_list.shape[0] == 1:
                    current_issue_embedding = current_issue_embedding_list[0]
                # Should not happen if model.encode returns (1,D) for single text
                elif current_issue_embedding_list.ndim == 1:
                    current_issue_embedding = current_issue_embedding_list
                else:
                    print(
                        f"[RCA WARNING] Unexpected ndarray shape for current_issue_embedding_list: {current_issue_embedding_list.shape}")
                    current_issue_embedding = None
            elif isinstance(current_issue_embedding_list, list) and current_issue_embedding_list and current_issue_embedding_list[0] is None:
                # get_embedding_st_rca failed and returned [None]
                current_issue_embedding = None
            else:
                # Fallback for any other unexpected structure
                print(
                    f"[RCA WARNING] Unexpected structure for current_issue_embedding_list. Type: {type(current_issue_embedding_list)}, Content: {current_issue_embedding_list}")
                current_issue_embedding = None

            print(
                f"[RCA DEBUG POST current_issue_assign] current_issue_embedding type: {type(current_issue_embedding)}")
            print(
                f"[RCA DEBUG POST current_issue_assign] current_issue_embedding content: {current_issue_embedding}")

            # Prepare batch for entry issue descriptions
            entry_issue_descriptions_rca = [
                entry.issue_description for entry in potential_rca_entries]
            entry_issue_embeddings_rca = get_embedding_st_rca(
                entry_issue_descriptions_rca)
            print(
                f"[RCA DEBUG POST get_embed_batch] entry_issue_embeddings_rca type: {type(entry_issue_embeddings_rca)}")
            print(
                f"[RCA DEBUG POST get_embed_batch] entry_issue_embeddings_rca content: {entry_issue_embeddings_rca}")

            scored_entries = []
            for idx, entry in enumerate(potential_rca_entries):
                if not entry.adjusted_whys_json:
                    continue

                entry_issue_embedding = entry_issue_embeddings_rca[idx]

                print(
                    f"[RCA DEBUG PRE-SIMILARITY CHECK] current_issue_embedding type: {type(current_issue_embedding)}")
                print(
                    f"[RCA DEBUG PRE-SIMILARITY CHECK] current_issue_embedding content: {current_issue_embedding}")
                print(
                    f"[RCA DEBUG PRE-SIMILARITY CHECK] entry_issue_embedding type: {type(entry_issue_embedding)}")
                print(
                    f"[RCA DEBUG PRE-SIMILARITY CHECK] entry_issue_embedding content: {entry_issue_embedding}")

                issue_similarity = 0
                if current_issue_embedding is not None and entry_issue_embedding is not None:
                    issue_similarity = cosine_similarity_rca(
                        current_issue_embedding, entry_issue_embedding)

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

            scored_entries.sort(key=lambda x: x["score"], reverse=True)
            results = [entry["data"] for entry in scored_entries[:limit]]

            if results:
                print(
                    f"Found {len(results)} semantically similar RCA entries using SentenceTransformer.")
                return results
            else:
                print(
                    "No semantically similar RCA entries found using SentenceTransformer.")
        except Exception as e:
            print(
                f"Error using SentenceTransformer for semantic search for RCA knowledge: {e}")
    else:
        print("SentenceTransformer model not initialized for RCA. Falling back.")

    # Fallback to traditional search if semantic search fails or finds no results or model not loaded
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
