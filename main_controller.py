# Main Controller for Interactive Prompt Modifier (DeepSeek Version)

import os
import sys
import json # for printing dicts neatly

# Ensure project root is in sys.path for consistent imports
if __name__ == '__main__': # Adjust path for direct execution for testing
    current_dir_controller = os.path.dirname(os.path.abspath(__file__))
    project_root_controller = os.path.dirname(current_dir_controller)
    if project_root_controller not in sys.path:
        sys.path.insert(0, project_root_controller)

from utils.config_manager import ConfigManager
from core.llm_handler import LLMHandler
from core.prompt_manager import PromptManager
from core.automatic_evaluator import AutomaticEvaluator
from core.prompt_modifier import PromptModifier

class MainController:
    def __init__(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file_path = os.path.join(project_root, "config.json")

        self.config_manager = ConfigManager(config_file=config_file_path)
        self.llm_handler = LLMHandler(self.config_manager)
        self.prompt_manager = PromptManager(storage_dir=os.path.join(project_root, "prompt_sessions"))
        self.evaluator = AutomaticEvaluator(self.config_manager, self.llm_handler)
        self.modifier = PromptModifier(self.config_manager, self.llm_handler)
        self.current_session_id = None
        self.current_prompt = ""
        self.current_target_query = ""

    def start_new_session(self, initial_prompt: str, target_query: str | None = None):
        self.current_prompt = initial_prompt
        self.current_target_query = target_query if target_query else ""
        self.current_session_id, session_data = self.prompt_manager.create_session(initial_prompt, target_query)
        print(f"New session started with ID: {self.current_session_id}")
        print(f"Initial prompt: {initial_prompt}")
        if target_query:
            print(f"Target query: {target_query}")
        return self.current_session_id

    def load_existing_session(self, session_id: str):
        session_data = self.prompt_manager.load_session(session_id)
        if session_data:
            self.current_session_id = session_id
            if session_data["rounds"]:
                self.current_prompt = session_data["rounds"][-1]["prompt_used"]
            else:
                self.current_prompt = session_data["initial_prompt"]
            self.current_target_query = session_data.get("target_query", "")
            print(f"Successfully loaded session {session_id}.")
            print(f"Current prompt for this session: {self.current_prompt}")
            if self.current_target_query:
                print(f"Target query: {self.current_target_query}")
            return True
        else:
            print(f"Failed to load session {session_id}.")
            return False

    def process_current_prompt(self, target_llm_model: str | None = None):
        if not self.current_session_id:
            print("Error: No active session. Please start or load a session.")
            return None, None

        print(f"\nProcessing prompt for session {self.current_session_id}...")
        print(f"Using prompt: {self.current_prompt}")
        if self.current_target_query:
            print(f"With target query: {self.current_target_query}")
        
        full_prompt_to_send = self.current_prompt
        if self.current_target_query:
            if "{query}" in self.current_prompt:
                full_prompt_to_send = self.current_prompt.replace("{query}", self.current_target_query)
            else:
                full_prompt_to_send = f"{self.current_prompt}\n\nRegarding the query: {self.current_target_query}"

        # Model name will be fetched from config by llm_handler if target_llm_model is None
        effective_model_name = target_llm_model if target_llm_model else self.config_manager.get_setting("target_llm_model")
        print(f"Sending to target LLM ({effective_model_name}):\n{full_prompt_to_send}")

        llm_response = self.llm_handler.send_prompt(
            prompt_text=full_prompt_to_send,
            model_name=effective_model_name 
        )

        if llm_response is None:
            print("Failed to get response from LLM.")
            self.prompt_manager.add_round_to_session(
                self.current_session_id,
                prompt_used=self.current_prompt,
                llm_response="ERROR: No response from LLM",
                evaluation_result={"error": "LLM communication failure"},
                user_action="llm_error"
            )
            return None, None

        print(f"\nTarget LLM Response:\n{llm_response}")

        evaluation = self.evaluator.evaluate_response(llm_response, self.current_prompt, self.current_target_query)
        print(f"\nEvaluation Result:\n{json.dumps(evaluation, indent=2)}")
        
        return llm_response, evaluation

    def get_modification_suggestion(self, last_response: str, evaluation: dict):
        if not self.current_session_id:
            print("Error: No active session.")
            return None
        
        print("\nRequesting modification suggestion...")
        suggestion = self.modifier.suggest_modification(
            current_prompt=self.current_prompt,
            target_query=self.current_target_query,
            last_response=last_response,
            evaluation_result=evaluation
        )

        if suggestion:
            print(f"\nSuggested New Prompt:\n{suggestion}")
        else:
            print("No modification suggestion was provided by the assistant.")
        return suggestion

    def apply_suggestion(self, suggested_prompt: str, llm_response: str, evaluation: dict):
        if not self.current_session_id:
            print("Error: No active session.")
            return False
        self.prompt_manager.add_round_to_session(
            self.current_session_id,
            prompt_used=self.current_prompt,
            llm_response=llm_response,
            evaluation_result=evaluation,
            modification_suggestion=suggested_prompt,
            user_action="accepted_suggestion"
        )
        self.current_prompt = suggested_prompt
        print(f"Suggestion applied. Current prompt updated for session {self.current_session_id}.")
        return True

    def apply_manual_edit(self, manually_edited_prompt: str, llm_response: str | None, evaluation: dict | None):
        if not self.current_session_id:
            print("Error: No active session.")
            return False
        self.prompt_manager.add_round_to_session(
            self.current_session_id,
            prompt_used=self.current_prompt, 
            llm_response=llm_response if llm_response else "N/A (Prompt manually edited before processing)",
            evaluation_result=evaluation if evaluation else {"notes": "Prompt manually edited"},
            modification_suggestion=None, 
            user_action="manual_edit"
        )
        self.current_prompt = manually_edited_prompt
        print(f"Manual edit applied. Current prompt updated for session {self.current_session_id}.")
        return True
    
    def record_rejection_or_continuation(self, llm_response: str, evaluation: dict, user_action: str):
        if not self.current_session_id:
            print("Error: No active session.")
            return False
        self.prompt_manager.add_round_to_session(
            self.current_session_id,
            prompt_used=self.current_prompt,
            llm_response=llm_response,
            evaluation_result=evaluation,
            modification_suggestion=None, 
            user_action=user_action
        )
        return True

    def end_session(self, status="completed"):
        if self.current_session_id:
            self.prompt_manager.update_session_status(self.current_session_id, status)
            print(f"Session {self.current_session_id} ended with status: {status}.")
            self.current_session_id = None
            self.current_prompt = ""
            self.current_target_query = ""
        else:
            print("No active session to end.")

    def list_sessions(self):
        return self.prompt_manager.list_sessions()

if __name__ == '__main__':
    # This is a very basic test sequence.
    # Ensure dummy config exists for testing (ConfigManager now creates one if not found)
    project_root_mc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dummy_config_path_mc = os.path.join(project_root_mc, "config.json")
    
    print(f"MainController test expects config at: {dummy_config_path_mc}")
    controller = MainController()
    
    if not controller.llm_handler.client: # Check if DeepSeek client is initialized
        print("\nWARNING: DeepSeek LLM client not initialized in LLMHandler.")
        print("Please ensure your DeepSeek API key is correctly set in config.json.")
        print("LLM-dependent tests will be skipped or may fail.")
    
    print("\n--- MainController Test (DeepSeek Version) --- ")
    session_id = controller.start_new_session("What is the capital of France?", "A city name.")

    if controller.llm_handler.client:
        response, evaluation = controller.process_current_prompt()

        if response and evaluation:
            suggestion = controller.get_modification_suggestion(response, evaluation)
            if suggestion:
                controller.apply_suggestion(suggestion, response, evaluation)
                print("\n--- Processing suggested prompt ---")
                controller.process_current_prompt()
            else:
                print("No suggestion, or modifier LLM not available.")
                controller.record_rejection_or_continuation(response, evaluation, "continued_with_current_no_suggestion")
        else:
            print("Could not process initial prompt (check API key and network).")
    else:
        print("Skipping LLM processing tests as DeepSeek client is not initialized.")

    controller.end_session()

    print("\nListing sessions:")
    sessions = controller.list_sessions()
    print(json.dumps(sessions, indent=2))
    print("\nMainController (DeepSeek Version) test sequence finished.")

