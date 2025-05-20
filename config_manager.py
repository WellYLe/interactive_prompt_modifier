# Configuration Module for Interactive Prompt Modifier (DeepSeek Version)

import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        # Ensure config_file path is relative to the project root if this script is in utils/
        if not os.path.isabs(config_file):
            self.config_file = os.path.join(os.path.dirname(__file__), "..", config_file)
        else:
            self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from {self.config_file}. Starting with empty config.")
                    return self._create_default_config_content() # Return default if file is corrupt
        else:
            print(f"Warning: Config file {self.config_file} not found. Creating with default values.")
            default_cfg = self._create_default_config_content()
            self.config = default_cfg # Set self.config before saving
            self._save_config() # Save the new default config
            return default_cfg

    def _create_default_config_content(self):
        return {
            "deepseek_api_key": "YOUR_DEEPSEEK_API_KEY_HERE",
            "deepseek_base_url": "https://api.deepseek.com/v1",
            "target_llm_model": "deepseek-chat",
            "judge_llm_model": "deepseek-chat",
            "modification_assistant_llm_model": "deepseek-chat",
            "evaluation_method": "rule_based" # Options: "rule_based", "llm_judge"
        }

    def _save_config(self):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_deepseek_api_key(self):
        api_key = self.config.get("deepseek_api_key")
        if not api_key or api_key == "YOUR_DEEPSEEK_API_KEY_HERE":
            print(f"DeepSeek API key not found or not set in {self.config_file}.")
            # In a real CLI app, we might prompt, but for backend, better to require it in config.
            # For this tool, let's make it clear it needs to be set.
            print("Please set your DeepSeek API key in the config.json file.")
            return None
        return api_key

    def set_deepseek_api_key(self, api_key):
        self.config["deepseek_api_key"] = api_key
        self._save_config()
        print(f"DeepSeek API key saved to {self.config_file}")

    def get_deepseek_base_url(self):
        return self.config.get("deepseek_base_url", "https://api.deepseek.com/v1")

    def set_deepseek_base_url(self, base_url):
        self.config["deepseek_base_url"] = base_url
        self._save_config()
        print(f"DeepSeek base URL saved to {self.config_file}")

    def get_setting(self, setting_name, default_value=None):
        return self.config.get(setting_name, default_value)

    def set_setting(self, setting_name, value):
        self.config[setting_name] = value
        self._save_config()
        print(f"Setting \'{setting_name}\' saved to {self.config_file}")

if __name__ == '__main__':
    # Example Usage, assuming this script is in utils/ and config.json is in project root
    project_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_config_path = os.path.join(project_root_path, "config.json")
    
    print(f"Config manager expects config file at: {test_config_path}")
    config_manager = ConfigManager(config_file=test_config_path)

    # DeepSeek API Key
    ds_key = config_manager.get_deepseek_api_key()
    if ds_key:
        print(f"DeepSeek API Key: {ds_key}")
    else:
        print("DeepSeek API Key: Not set or using placeholder.")

    # DeepSeek Base URL
    ds_base_url = config_manager.get_deepseek_base_url()
    print(f"DeepSeek Base URL: {ds_base_url}")
    # Example of changing a setting
    # config_manager.set_deepseek_base_url("https://api.deepseek.com/other_v1") 

    # Target LLM Model
    target_llm = config_manager.get_setting("target_llm_model", "deepseek-chat")
    print(f"Target LLM Model: {target_llm}")
    config_manager.set_setting("target_llm_model", "deepseek-chat") # Ensure it's set
    target_llm_updated = config_manager.get_setting("target_llm_model")
    print(f"Updated Target LLM Model: {target_llm_updated}")

    print("\nCurrent full config:")
    print(json.dumps(config_manager.config, indent=2))

