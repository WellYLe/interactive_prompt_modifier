# Prompt Management Module for Interactive Prompt Modifier

import json
import os
import uuid
from datetime import datetime

class PromptManager:
    def __init__(self, storage_dir="prompt_sessions"):
        self.storage_dir = os.path.join(os.path.dirname(__file__), "..", storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_session_filepath(self, session_id):
        return os.path.join(self.storage_dir, f"session_{session_id}.json")

    def create_session(self, initial_prompt: str, target_query: str | None = None):
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        session_data = {
            "session_id": session_id,
            "created_at": timestamp,
            "initial_prompt": initial_prompt,
            "target_query": target_query,
            "rounds": [],
            "status": "active" # active, completed, aborted
        }
        self.save_session(session_id, session_data)
        return session_id, session_data

    def save_session(self, session_id: str, session_data: dict):
        filepath = self._get_session_filepath(session_id)
        with open(filepath, "w") as f:
            json.dump(session_data, f, indent=4)
        # print(f"Session {session_id} saved to {filepath}")

    def load_session(self, session_id: str):
        filepath = self._get_session_filepath(session_id)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON from {filepath}")
                    return None
        else:
            # print(f"Error: Session file {filepath} not found.")
            return None

    def add_round_to_session(self, session_id: str, prompt_used: str, llm_response: str, 
                               evaluation_result: dict, modification_suggestion: str | None = None, 
                               user_action: str | None = None):
        session_data = self.load_session(session_id)
        if not session_data:
            print(f"Error: Cannot add round, session {session_id} not found.")
            return False

        round_data = {
            "round_number": len(session_data["rounds"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "prompt_used": prompt_used,
            "llm_response": llm_response,
            "evaluation_result": evaluation_result, # e.g., {"score": 0.8, "details": "..."}
            "modification_suggestion": modification_suggestion,
            "user_action": user_action # e.g., "accepted_suggestion", "manual_edit", "rejected_suggestion"
        }
        session_data["rounds"].append(round_data)
        self.save_session(session_id, session_data)
        # print(f"Round {round_data['round_number']} added to session {session_id}")
        return True
    
    def update_session_status(self, session_id: str, status: str):
        session_data = self.load_session(session_id)
        if not session_data:
            print(f"Error: Cannot update status, session {session_id} not found.")
            return False
        session_data["status"] = status
        self.save_session(session_id, session_data)
        # print(f"Session {session_id} status updated to {status}")
        return True

    def list_sessions(self):
        session_files = [f for f in os.listdir(self.storage_dir) if f.startswith("session_") and f.endswith(".json")]
        sessions_summary = []
        for sf in session_files:
            session_id = sf.replace("session_", "").replace(".json", "")
            session_data = self.load_session(session_id)
            if session_data:
                sessions_summary.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "initial_prompt_snippet": session_data.get("initial_prompt", "")[:50] + "...",
                    "num_rounds": len(session_data.get("rounds", [])),
                    "status": session_data.get("status")
                })
        return sessions_summary

if __name__ == '__main__':
    # Example Usage
    # Assumes this script is in /core/
    # storage_dir will be created in project_root/prompt_sessions
    project_root = os.path.dirname(os.path.dirname(__file__))
    pm_storage_path = os.path.join(project_root, "prompt_sessions_test")
    
    # Clean up old test sessions if any
    if os.path.exists(pm_storage_path):
        for f_name in os.listdir(pm_storage_path):
            os.remove(os.path.join(pm_storage_path, f_name))
        os.rmdir(pm_storage_path)
        
    pm = PromptManager(storage_dir=pm_storage_path)

    # Create a new session
    print("Creating new session...")
    session_id_1, session_data_1 = pm.create_session("This is my first initial prompt.", "Tell me a joke.")
    print(f"Created session ID: {session_id_1}")
    print(f"Initial session data: {json.dumps(session_data_1, indent=2)}")

    # Add a round to the session
    print("\nAdding round 1...")
    pm.add_round_to_session(
        session_id_1,
        prompt_used="This is my first initial prompt. Tell me a joke.",
        llm_response="Why did the scarecrow win an award? Because he was outstanding in his field!",
        evaluation_result={"score": 0.9, "category": "good_joke", "is_safe": True},
        modification_suggestion="Try asking for a funnier joke.",
        user_action="accepted_suggestion"
    )
    
    print("\nAdding round 2...")
    pm.add_round_to_session(
        session_id_1,
        prompt_used="Tell me a funnier joke.",
        llm_response="I told my wife she was drawing her eyebrows too high. She seemed surprised.",
        evaluation_result={"score": 0.95, "category": "better_joke", "is_safe": True},
        modification_suggestion=None, # No suggestion this time
        user_action="completed"
    )

    # Load the session to see changes
    print("\nLoading session...")
    loaded_session = pm.load_session(session_id_1)
    if loaded_session:
        print(f"Loaded session data: {json.dumps(loaded_session, indent=2)}")

    # Update session status
    print("\nUpdating session status...")
    pm.update_session_status(session_id_1, "completed")
    updated_session = pm.load_session(session_id_1)
    if updated_session:
        print(f"Updated session status: {updated_session.get('status')}")

    # Create another session for listing
    session_id_2, _ = pm.create_session("Another prompt for testing list.", "What is the capital of France?")
    pm.add_round_to_session(session_id_2, "What is the capital of France?", "Paris", {"correct": True}, None, "completed")
    pm.update_session_status(session_id_2, "completed")

    # List all sessions
    print("\nListing all sessions...")
    all_sessions = pm.list_sessions()
    print(f"All sessions summary: {json.dumps(all_sessions, indent=2)}")

    print("\nPromptManager example usage complete.")
    print(f"Test session files are stored in: {pm_storage_path}")

