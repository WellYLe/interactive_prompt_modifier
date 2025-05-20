# Main entry point for the Interactive Prompt Modifier application

import os
import sys

# Ensure the project root is in the Python path to allow for absolute imports
# from within the modules (e.g., from core import ...)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from interfaces.cli import cli

if __name__ == "__main__":
    # Create a dummy config.json in the project root if it doesn't exist
    # This helps first-time users or when running in a clean environment.
    config_file_path = os.path.join(current_dir, "config.json")
    if not os.path.exists(config_file_path):
        print(f"Config file not found at {config_file_path}. Creating a default one.")
        print("Please edit config.json to add your API keys for OpenAI and/or Google.")
        default_config = {
            "openai_api_key": "Ysk-e5ca96da010141e383134ca16f03b1cd",
            "google_api_key": "YOUR_GOOGLE_API_KEY_HERE",
            "target_llm_model": "gpt-3.5-turbo",
            "judge_llm_model": "gpt-3.5-turbo",
            "modification_assistant_llm_model": "gpt-3.5-turbo",
            "evaluation_method": "rule_based", # Options: "rule_based", "llm_judge"
            "google_palm_model_test": "models/text-bison-001" # For llm_handler testing
        }
        try:
            with open(config_file_path, "w") as f:
                import json
                json.dump(default_config, f, indent=4)
            print(f"Default config.json created at {config_file_path}. Please update it with your API keys.")
        except Exception as e:
            print(f"Error creating default config.json: {e}")
    
    # Create prompt_sessions directory if it doesn't exist
    sessions_dir = os.path.join(current_dir, "prompt_sessions")
    if not os.path.exists(sessions_dir):
        try:
            os.makedirs(sessions_dir)
            print(f"Created directory for session data: {sessions_dir}")
        except Exception as e:
            print(f"Error creating session directory {sessions_dir}: {e}")
            
    cli()

