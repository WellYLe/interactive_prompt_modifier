# CLI Interface for Interactive Prompt Modifier (DeepSeek Version)

import click
import os
import sys
import json # For pretty printing

# Adjust import path to reach the core modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # /home/ubuntu/interactive_prompt_modifier
core_path = os.path.join(project_root, "core")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if core_path not in sys.path: # Ensure core is also in path if direct imports from core are needed by controller
    sys.path.insert(0, core_path)

from core.main_controller import MainController

pass_controller = click.make_pass_decorator(MainController)

@click.group()
@click.pass_context
def cli(ctx):
    """An interactive framework for evaluating and modifying LLM prompts (DeepSeek Version)."""
    ctx.obj = MainController()
    # Check for DeepSeek API key early
    controller = ctx.obj
    if not controller.llm_handler.client: # MODIFIED: Check for the unified DeepSeek client
        click.echo(click.style("WARNING: DeepSeek LLM client not initialized.", fg="yellow"))
        click.echo(click.style("Please ensure your DeepSeek API key is correctly set in config.json.", fg="yellow"))
        click.echo(click.style("LLM-dependent features will not work.", fg="yellow"))

@cli.command("new_session")
@click.option("--prompt", "-p", prompt="Enter the initial prompt", help="The initial prompt to start the session with.")
@click.option("--query", "-q", default=None, help="(Optional) The specific target query for the prompt.")
@pass_controller
def new_session(controller: MainController, prompt: str, query: str | None):
    """Starts a new prompt modification session."""
    session_id = controller.start_new_session(initial_prompt=prompt, target_query=query)
    if session_id:
        click.echo(click.style(f"New session created with ID: {session_id}", fg="green"))
        click.echo(f"Current prompt: {controller.current_prompt}")
        if controller.current_target_query:
            click.echo(f"Target query: {controller.current_target_query}")
        # Automatically enter the interaction loop for the new session
        ctx = click.get_current_context()
        ctx.invoke(interact, session_id=session_id)
    else:
        click.echo(click.style("Failed to create a new session.", fg="red"))

@cli.command("load_session")
@click.option("--session_id", "-s", default=None, help="The ID of the session to load.")
@pass_controller
def load_session(controller: MainController, session_id: str | None):
    """Loads an existing prompt modification session."""
    if not session_id:
        sessions = controller.list_sessions()
        if not sessions:
            click.echo("No existing sessions found.")
            return
        click.echo("Available sessions:")
        for i, s in enumerate(sessions):
            click.echo(f"  {i+1}. ID: {s['session_id']} | Created: {s['created_at']} | Prompt: \"{s['initial_prompt_snippet']}\" | Status: {s['status']}")
        choice = click.prompt("Enter the number of the session to load", type=int)
        if 1 <= choice <= len(sessions):
            session_id = sessions[choice-1]["session_id"]
        else:
            click.echo(click.style("Invalid choice.", fg="red"))
            return

    if controller.load_existing_session(session_id):
        click.echo(click.style(f"Session {session_id} loaded successfully.", fg="green"))
        click.echo(f"Current prompt: {controller.current_prompt}")
        if controller.current_target_query:
            click.echo(f"Target query: {controller.current_target_query}")
        # Automatically enter the interaction loop for the loaded session
        ctx = click.get_current_context()
        ctx.invoke(interact, session_id=session_id)
    else:
        click.echo(click.style(f"Failed to load session {session_id}.", fg="red"))

@cli.command("list_sessions")
@pass_controller
def list_sessions_cmd(controller: MainController):
    """Lists all existing prompt modification sessions."""
    sessions = controller.list_sessions()
    if not sessions:
        click.echo("No existing sessions found.")
        return
    click.echo(click.style("Available sessions:", fg="cyan"))
    for s in sessions:
        click.echo(f"- ID: {s['session_id']}")
        click.echo(f"  Created: {s['created_at']}")
        click.echo(f"  Initial Prompt: \"{s['initial_prompt_snippet']}\"")
        click.echo(f"  Rounds: {s['num_rounds']}")
        click.echo(f"  Status: {s['status']}")
        click.echo("---")

@cli.command("interact")
@click.option("--session_id", "-s", help="The ID of the session to interact with. Will use current if already loaded.")
@pass_controller
def interact(controller: MainController, session_id: str | None):
    """Interactive loop for an active session."""
    if session_id and (not controller.current_session_id or controller.current_session_id != session_id):
        if not controller.load_existing_session(session_id):
            click.echo(click.style(f"Cannot start interaction: Failed to load session {session_id}.", fg="red"))
            return
    elif not controller.current_session_id:
        click.echo(click.style("No active session. Please start with `new_session` or `load_session` first.", fg="yellow"))
        return
    
    click.echo(click.style(f"Interacting with session: {controller.current_session_id}", fg="blue"))

    last_response = None
    last_evaluation = None

    while True:
        click.echo("\n--- Current State ---")
        click.echo(f"Session ID: {controller.current_session_id}")
        click.echo(f"Current Prompt:\n{click.style(controller.current_prompt, fg='magenta')}")
        if controller.current_target_query:
            click.echo(f"Target Query: {click.style(controller.current_target_query, fg='magenta')}")
        if last_response:
            click.echo(f"Last LLM Response:\n{click.style(last_response, fg='yellow')}")
        if last_evaluation:
            click.echo(f"Last Evaluation:\n{click.style(json.dumps(last_evaluation, indent=2), fg='yellow')}")

        click.echo("\n--- Actions ---")
        click.echo("1. Process current prompt with Target LLM")
        click.echo("2. Get modification suggestion (requires last response & evaluation)")
        click.echo("3. Manually edit current prompt")
        click.echo("4. View full session history")
        click.echo("5. End current session")
        click.echo("0. Exit interaction (back to main menu)")

        choice = click.prompt("Choose an action", type=click.IntRange(0, 5))

        if choice == 1: # Process current prompt
            if not controller.llm_handler.client: # MODIFIED: Check for the unified DeepSeek client
                click.echo(click.style("Cannot process prompt: DeepSeek client not initialized. Check API key in config.json.", fg="red"))
                continue
            # Model is now fetched from config by default in llm_handler, no need to prompt here unless we want to override
            # For simplicity, we'll use the configured default target_llm_model
            click.echo("Processing...")
            response, evaluation = controller.process_current_prompt() # Removed target_model argument
            if response is not None and evaluation is not None:
                last_response = response
                last_evaluation = evaluation
                controller.record_rejection_or_continuation(last_response, last_evaluation, "processed_prompt")
            else:
                click.echo(click.style("Failed to process prompt with LLM.", fg="red"))
        
        elif choice == 2: # Get modification suggestion
            if not last_response or not last_evaluation:
                click.echo(click.style("Please process the prompt first (action 1) to get a response and evaluation.", fg="yellow"))
                continue
            if not controller.llm_handler.client: # MODIFIED: Check for the unified DeepSeek client
                click.echo(click.style("Cannot get suggestion: DeepSeek client for modifier LLM not initialized. Check API key.", fg="red"))
                continue
            
            click.echo("Getting suggestion...")
            suggestion = controller.get_modification_suggestion(last_response, last_evaluation)
            if suggestion:
                click.echo(f"Suggested New Prompt:\n{click.style(suggestion, fg='green')}")
                if click.confirm("Do you want to apply this suggestion?"):
                    controller.apply_suggestion(suggestion, last_response, last_evaluation)
                    last_response, last_evaluation = None, None 
                    click.echo("Suggestion applied. Process the new prompt (action 1) to see its effect.")
                else:
                    controller.record_rejection_or_continuation(last_response, last_evaluation, "rejected_suggestion_kept_old")
                    click.echo("Suggestion not applied. Current prompt remains unchanged.")
            else:
                click.echo(click.style("Modifier did not provide a suggestion.", fg="yellow"))

        elif choice == 3: # Manually edit current prompt
            edited_prompt = click.edit(controller.current_prompt)
            if edited_prompt is not None and edited_prompt.strip() != controller.current_prompt.strip():
                controller.apply_manual_edit(edited_prompt.strip(), last_response, last_evaluation)
                click.echo("Prompt manually updated. Process it (action 1) to see its effect.")
                last_response, last_evaluation = None, None 
            else:
                click.echo("Prompt not changed.")

        elif choice == 4: # View full session history
            session_data = controller.prompt_manager.load_session(controller.current_session_id)
            if session_data:
                click.echo(click.style("--- Full Session History ---", fg="cyan"))
                click.echo(json.dumps(session_data, indent=2))
            else:
                click.echo(click.style("Could not load session data for history view.", fg="red"))

        elif choice == 5: # End current session
            status = click.prompt("End session status (e.g., completed, aborted)", default="completed")
            session_id_to_end = controller.current_session_id # Capture before it's cleared
            controller.end_session(status)
            click.echo(f"Session {session_id_to_end} ended.") 
            return 

        elif choice == 0: # Exit interaction
            click.echo("Exiting interaction mode.")
            return

if __name__ == '__main__':
    cli()

