# LLM Handler Module for Interactive Prompt Modifier (DeepSeek Version)

import openai
import os
import sys # Required for sys.path manipulation in __main__
import json # Required for json.dump in __main__

# Adjust import path for ConfigManager if this script is in core/
# and ConfigManager is in utils/
# This assumes the main script (main.py) or test execution handles the project root in sys.path
if __name__ == '__main__': # Only adjust path for direct execution for testing
    current_dir_llm_handler = os.path.dirname(os.path.abspath(__file__))
    project_root_llm_handler = os.path.dirname(current_dir_llm_handler)
    if project_root_llm_handler not in sys.path:
        sys.path.insert(0, project_root_llm_handler)

from utils.config_manager import ConfigManager

class LLMHandler:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.client = None
        self._initialize_deepseek_client()

    def _initialize_deepseek_client(self):
        api_key = self.config_manager.get_deepseek_api_key()
        base_url = self.config_manager.get_deepseek_base_url()

        if not api_key or api_key == "YOUR_DEEPSEEK_API_KEY_HERE":
            print("Warning: DeepSeek API key not configured. LLM calls will fail.")
            print("Please set your DeepSeek API key in config.json.")
            return
        
        if not base_url:
            print("Warning: DeepSeek base URL not configured. Using default.")
            # The config_manager should provide a default, but double-check.
            base_url = "https://api.deepseek.com/v1" # Fallback default

        try:
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            # Test connectivity (optional, or handle first error gracefully)
            # try:
            #     self.client.models.list() # A simple call to check if auth works
            #     print("Successfully connected to DeepSeek API.")
            # except openai.AuthenticationError:
            #     print("Error: DeepSeek API Authentication Failed. Check your API key and base_url.")
            #     self.client = None # Invalidate client
            # except Exception as e:
            #     print(f"Error connecting to DeepSeek API: {e}")
            #     self.client = None # Invalidate client

        except Exception as e:
            print(f"Error initializing DeepSeek client: {e}")
            self.client = None

    def send_prompt(
        self, 
        prompt_text: str, 
        system_message: str | None = None, 
        model_name: str | None = None, 
        max_tokens: int = 1500,
        temperature: float = 0.7,
        top_p: float = 0.95,
        n_responses: int = 1
    ):
        """Sends a prompt to the configured DeepSeek LLM and returns the response(s)."""
        
        if not self.client:
            print("Error: DeepSeek client not initialized. Cannot send prompt.")
            print("Please ensure your DeepSeek API key and base URL are correctly set in config.json.")
            return None

        if model_name is None:
            model_name = self.config_manager.get_setting("target_llm_model", "deepseek-chat")
            # print(f"No model specified, using default target LLM from config: {model_name}")

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt_text})
        
        try:
            # print(f"Sending prompt to DeepSeek model: {model_name} with temperature: {temperature}")
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                n=n_responses,
                # stream=False # DeepSeek API docs show this for non-streaming
            )
            if n_responses == 1:
                return response.choices[0].message.content.strip()
            else:
                return [choice.message.content.strip() for choice in response.choices]
        
        except openai.AuthenticationError as e:
            print(f"DeepSeek API Authentication Error: {e}. Please check your API key and base_url in config.json.")
            return None
        except openai.APIConnectionError as e:
            print(f"DeepSeek API Connection Error: {e}. Check your network and the base_url.")
            return None
        except openai.RateLimitError as e:
            print(f"DeepSeek API Rate Limit Error: {e}. Please check your usage and limits.")
            return None
        except openai.APIStatusError as e:
            print(f"DeepSeek API Status Error: Status Code {e.status_code}, Response: {e.response}")
            return None
        except Exception as e:
            print(f"An error occurred while sending prompt to DeepSeek model {model_name}: {e}")
            return None

if __name__ == '__main__':
    # Create a dummy config.json for testing if it doesn't exist
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dummy_config_path = os.path.join(project_root, "config.json")

    # Ensure the dummy config is created by the ConfigManager if not present
    # The ConfigManager's __init__ now handles creating a default if not found.
    print(f"Attempting to load or create config at: {dummy_config_path}")
    config = ConfigManager(config_file=dummy_config_path)
    
    # Manually ensure API key is set for testing if it's the placeholder
    # In a real scenario, the user must edit config.json
    if config.get_deepseek_api_key() is None or config.get_deepseek_api_key() == "YOUR_DEEPSEEK_API_KEY_HERE":
        print("WARNING: DeepSeek API key is not set in config.json or is a placeholder.")
        print("LLMHandler tests will likely fail without a valid API key.")
        # For automated testing, you might inject a test key via environment or a test-specific config.
        # For this example, we'll proceed and let it fail if the key isn't set by the user.

    handler = LLMHandler(config)

    if handler.client:
        print("\nTesting DeepSeek model...")
        # Using the model from config, which should default to "deepseek-chat"
        ds_response = handler.send_prompt("Hello, who are you?") 
        if ds_response:
            print(f"DeepSeek Response: {ds_response}")
        else:
            print("Failed to get response from DeepSeek.")
        
        print("\nTesting DeepSeek model for 2 responses...")
        ds_responses_multi = handler.send_prompt("Suggest two creative names for a new AI assistant.", n_responses=2)
        if ds_responses_multi:
            for i, r in enumerate(ds_responses_multi):
                print(f"DeepSeek Response {i+1}: {r}")
        else:
            print("Failed to get multiple responses from DeepSeek.")
    else:
        print("Skipping DeepSeek tests as client is not initialized (likely API key or base_url issue).")

    print("\nLLMHandler (DeepSeek Version) example usage complete.")

