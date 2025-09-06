import streamlit as st
import subprocess
import re
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
import time

load_dotenv()

NRP_API_KEY = os.getenv("NRP_API_KEY")
client = OpenAI(
    api_key=NRP_API_KEY,
    base_url="https://llm.nrp-nautilus.io/"
)

# System prompt that the chatbot will never forget
SYSTEM_PROMPT = """You are a specialized assistant for generating redbiom commands. 
Always provide valid, executable redbiom commands based on the user's request.
Your responses should be properly formatted commands that can be executed directly."""

def format_and_display_output(output, key_suffix):
    """Format and display command output in a more readable way"""
    
    # Check if output looks like tabular data (TSV/CSV)
    lines = output.strip().split('\n')
    
    # If it looks like a table (has tabs or multiple consistent separators)
    if len(lines) > 1 and ('\t' in output or ',' in output):
        try:
            # Try to detect if it's tab-separated
            if '\t' in lines[0]:
                # Parse as TSV
                headers = lines[0].split('\t')
                data = []
                for line in lines[1:]:
                    if line.strip():  # Skip empty lines
                        data.append(line.split('\t'))
                
                # Display as a nice table
                if data and len(data[0]) == len(headers):
                    st.markdown("**📋 Formatted Output:**")
                    
                    # Create a dataframe for better display
                    import pandas as pd
                    df = pd.DataFrame(data, columns=headers)
                    st.dataframe(df, use_container_width=True)
                    
                    # Show summary stats
                    st.markdown(f"**📊 Summary:** {len(data)} rows, {len(headers)} columns")
                    
                    # Also show raw output in expandable section
                    with st.expander("🔍 View Raw Output"):
                        st.code(output, language='text')
                    return
            
            # Try comma-separated if tab didn't work
            elif ',' in lines[0] and len(lines[0].split(',')) > 2:
                headers = lines[0].split(',')
                data = []
                for line in lines[1:]:
                    if line.strip():
                        data.append(line.split(','))
                
                if data and len(data[0]) == len(headers):
                    st.markdown("**📋 Formatted Output:**")
                    import pandas as pd
                    df = pd.DataFrame(data, columns=headers)
                    
                    # Check for study IDs in CSV data too
                    study_column = None
                    for col in df.columns:
                        if any(str(val).split('.')[0].isdigit() for val in df[col] if str(val).strip()):
                            study_column = col
                            break
                    
                    if study_column:
                        def make_study_link(val):
                            if str(val).strip():
                                parts = str(val).split('.')
                                if parts and parts[0].isdigit():
                                    study_id = parts[0]
                                    return f"[{val}](https://qiita.ucsd.edu/study/description/{study_id})"
                            return val
                        
                        display_df = df.copy()
                        display_df[study_column] = df[study_column].apply(make_study_link)
                        st.markdown(display_df.to_markdown(index=False), unsafe_allow_html=True)
                    else:
                        st.dataframe(df, use_container_width=True)
                    
                    st.markdown(f"**📊 Summary:** {len(data)} rows, {len(headers)} columns")
                    
                    if study_ids:
                        st.markdown("---")
                        st.markdown("**🔗 Qiita Studies Found:**")
                        cols = st.columns(min(4, len(study_ids)))
                        for idx, study_id in enumerate(study_ids):
                            col_idx = idx % len(cols)
                            with cols[col_idx]:
                                qiita_url = f"https://qiita.ucsd.edu/study/description/{study_id}"
                                st.markdown(f"[📊 {study_id}]({qiita_url})")
                    
                    with st.expander("🔍 View Raw Output"):
                        st.code(output, language='text')
                    return
                    
        except Exception as e:
            # If parsing fails, fall back to raw display
            pass
    
    # Check if it's a simple list (one item per line)
    elif len(lines) > 3 and all(len(line.strip()) > 0 for line in lines[:10]):
        st.markdown("**📋 Output List:**")
        
        # Show first few items with numbering
        display_limit = min(20, len(lines))
        for i, line in enumerate(lines[:display_limit], 1):
            if line.strip():
                st.markdown(f"{i}. `{line.strip()}`")
        
        if len(lines) > display_limit:
            st.markdown(f"*... and {len(lines) - display_limit} more items*")
            
        st.markdown(f"**📊 Summary:** {len([l for l in lines if l.strip()])} items total")
        
        # Show raw output in expandable section
        with st.expander("🔍 View Raw Output"):
            st.code(output, language='text')
        return
    
    # Check if it's JSON-like output
    elif output.strip().startswith('{') or output.strip().startswith('['):
        try:
            import json
            parsed = json.loads(output)
            st.markdown("**📋 JSON Output:**")
            st.json(parsed)
            
            with st.expander("🔍 View Raw Output"):
                st.code(output, language='json')
            return
        except:
            pass
    
    # For short outputs, display nicely formatted
    if len(lines) <= 10 and len(output) < 1000:
        st.markdown("**📋 Output:**")
        if len(lines) == 1:
            # Single line output
            st.code(output.strip(), language='text')
        else:
            # Multi-line but short output
            for line in lines:
                if line.strip():
                    st.markdown(f"• `{line.strip()}`")
    else:
        # Large output - show in scrollable text area
        st.markdown("**📋 Output:**")
        st.text_area(
            f"Large output ({len(lines)} lines):", 
            output, 
            height=300,
            key=f"formatted_output_{key_suffix}"
        )
        
        # Show summary
        st.markdown(f"**📊 Summary:** {len(lines)} lines, {len(output)} characters")

def clean_qwen_output(text):
    """Remove thinking tokens and other unwanted content from Qwen output"""
    # Remove <think>...</think> blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    
    # Remove other common thinking patterns
    patterns_to_remove = [
        r"<thinking>.*?</thinking>",
        r"```thinking.*?```",
        r"Assistant:",
        r"Human:",
        r"\.\.\.+",
        r"---+",
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text, flags=re.DOTALL)
    
    return text.strip()

def validate_redbiom_command(command):
    """
    Validate if the generated command looks like a valid redbiom command
    Returns: (is_valid, issues, suggestions)
    """
    issues = []
    suggestions = []
    
    # Clean the command
    command = command.strip()
    
    # Check if command starts with redbiom
    if not command.startswith('redbiom'):
        issues.append("Command doesn't start with 'redbiom'")
        suggestions.append("Add 'redbiom' at the beginning")
        return False, issues, suggestions
    
    # Define valid subcommands and their required parameters
    required_subcommands = {
        'search': {
            "features": ["--context"], 
            "samples": ["--context"], 
            "taxon": ["--context"],
            "metadata": []  # metadata search doesn't require context
        },
        'fetch': {
            "tags-contained": ["--context"],
            "samples-contained": [], 
            "features-contained": [], 
            "sample-metadata": ["--output"], 
            "features": ["--context", "--output"], 
            "samples": ["--context", "--output"], 
            "qiita-study": ["--context", "--study-id", "--output-basename"]
        },
        'summarize': {
            "contexts": [],
            "metadata-category": ["--category"],
            "metadata": [],
            "table": ["--category", "--context", "--table"],
            "features": ["--category", "--context"],
            "samples": ["--category"],
            "taxonomy": ["--context"],
        },
        'select': {
            "samples-from-metadata": ["--context"],
            "features-from-samples": ["--context"],
        }
    }
    
    valid_subcommands = list(required_subcommands.keys()) + ['stat', 'feature-table', 'tree', 'context', 'admin']
    
    command_parts = command.split()
    if len(command_parts) < 2:
        issues.append("Command appears incomplete - missing subcommand")
        suggestions.append(f"Add a subcommand like: {', '.join(list(required_subcommands.keys()))}")
        return False, issues, suggestions
    
    subcommand = command_parts[1]
    
    # Check if subcommand is valid
    if subcommand not in valid_subcommands:
        issues.append(f"Unknown subcommand: '{subcommand}'")
        suggestions.append(f"Use one of: {', '.join(valid_subcommands)}")
        return False, issues, suggestions
    
    # If we have detailed validation rules for this subcommand
    if subcommand in required_subcommands:
        if len(command_parts) < 3:
            actions = list(required_subcommands[subcommand].keys())
            issues.append(f"Missing action for '{subcommand}' subcommand")
            suggestions.append(f"Add an action like: {', '.join(actions[:3])}")
            return False, issues, suggestions
        
        action = command_parts[2]
        
        # Check if the action is valid for this subcommand
        if action not in required_subcommands[subcommand]:
            valid_actions = list(required_subcommands[subcommand].keys())
            issues.append(f"Unknown action '{action}' for subcommand '{subcommand}'")
            suggestions.append(f"Use one of: {', '.join(valid_actions)}")
        else:
            # Check required parameters for this subcommand-action combination
            required_params = required_subcommands[subcommand][action]
            
            for param in required_params:
                if param not in command:
                    issues.append(f"Missing required parameter '{param}' for '{subcommand} {action}'")
                    suggestions.append(f"Add {param} parameter with appropriate value")
    
    # Check for common flags and syntax
    output_flags = ['--output-file', '--output', '--output-basename']
    has_output_flag = any(flag in command for flag in output_flags)
    
    if has_output_flag:
        # Check if there's a filename with proper extension
        valid_extensions = ['.txt', '.tsv', '.csv', '.biom', '.qza', '.json']
        has_valid_extension = any(x.endswith(tuple(valid_extensions)) for x in command_parts)
        
        if not has_valid_extension:
            issues.append("Output file specified but no valid file extension found")
            suggestions.append(f"Specify output file with proper extension: {', '.join(valid_extensions)}")
    
    # Additional validation for specific patterns
    
    # Check for study-id format when required
    if '--study-id' in command:
        study_id_idx = None
        try:
            study_id_idx = command_parts.index('--study-id')
            if study_id_idx + 1 < len(command_parts):
                study_id = command_parts[study_id_idx + 1]
                if not study_id.isdigit():
                    issues.append("Study ID should be a number")
                    suggestions.append("Use a numeric study ID (e.g., --study-id 12345)")
        except (ValueError, IndexError):
            pass
    
    # Check for category format
    if '--category' in command:
        try:
            cat_idx = command_parts.index('--category')
            if cat_idx + 1 < len(command_parts):
                category = command_parts[cat_idx + 1]
                if len(category.strip()) == 0:
                    issues.append("Category parameter cannot be empty")
                    suggestions.append("Provide a valid metadata category name")
        except (ValueError, IndexError):
            pass
    
    # Check for context format (should not be empty if specified)
    if '--context' in command:
        try:
            ctx_idx = command_parts.index('--context')
            if ctx_idx + 1 < len(command_parts):
                context = command_parts[ctx_idx + 1]
                if len(context.strip()) == 0 or context.startswith('-'):
                    issues.append("Context parameter appears to be missing or invalid")
                    suggestions.append("Provide a valid context name after --context")
        except (ValueError, IndexError):
            issues.append("--context flag found but no context name provided")
            suggestions.append("Add a context name after --context flag")
    
    # Check for dangerous patterns
    dangerous_patterns = [';', '&&', '||', '>', '<', '`']

def dry_run_command(command):
    """
    Perform a dry run check by running redbiom --help or similar safe commands
    """
    try:
        # Check if redbiom is available
        result = subprocess.run(['redbiom', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False, "redbiom command not found or not working"
        
        # For certain commands, we can do syntax validation
        if '--help' not in command:
            # Try to get help for the subcommand to validate it exists
            command_parts = command.split()
            if len(command_parts) >= 2:
                help_result = subprocess.run(
                    ['redbiom', command_parts[1], '--help'], 
                    capture_output=True, text=True, timeout=10
                )
                if help_result.returncode != 0:
                    return False, f"Subcommand '{command_parts[1]}' not found"
        
        return True, "Basic syntax validation passed"
    
    except subprocess.TimeoutExpired:
        return False, "Command validation timed out"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def initialize_session_state():
    """Initialize session state variables"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'generated_command' not in st.session_state:
        st.session_state.generated_command = ''
    
    if 'command_outputs' not in st.session_state:
        st.session_state.command_outputs = []
    
    if 'streaming_enabled' not in st.session_state:
        st.session_state.streaming_enabled = True

def build_conversation_messages():
    """Build the full conversation history including system prompt"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add all conversation history
    for entry in st.session_state.conversation_history:
        messages.append({"role": "user", "content": entry['user_message']})
        messages.append({"role": "assistant", "content": entry['assistant_response']})
    
    return messages

def generate_command_streaming(user_query):
    """Generate a redbiom command with streaming output"""
    messages = build_conversation_messages()
    messages.append({"role": "user", "content": user_query})
    
    try:
        # Create streaming placeholder
        streaming_placeholder = st.empty()
        full_response = ""
        
        # Make streaming request
        stream = client.chat.completions.create(
            model="qwen3",
            messages=messages,
            stream=True
        )
        
        # Process stream
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                
                # Update display with current response
                streaming_placeholder.code(full_response, language='bash')
                
                # Add small delay to make streaming visible
                time.sleep(0.01)
        
        cleaned_command = clean_qwen_output(full_response)
        return cleaned_command
        
    except Exception as e:
        st.error(f"Error generating command: {str(e)}")
        return None

def generate_command_regular(user_query):
    """Generate a redbiom command using regular (non-streaming) method"""
    messages = build_conversation_messages()
    messages.append({"role": "user", "content": user_query})
    
    try:
        llama_response = client.chat.completions.create(
            model="qwen3",
            messages=messages,
        )
        
        raw_command = llama_response.choices[0].message.content
        cleaned_command = clean_qwen_output(raw_command)
        
        return cleaned_command
    except Exception as e:
        st.error(f"Error generating command: {str(e)}")
        return None

def execute_command(command):
    """Execute a redbiom command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=60*5  # 5 minute timeout
        )
        return True, result.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except subprocess.CalledProcessError as e:
        return False, "", e.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    st.set_page_config(
        page_title="Redbiom Assistant", 
        page_icon="🧬", 
        layout="wide"
    )
    
    st.title("🧬 Redbiom Assistant with Streaming & Validation")
    st.markdown("*A chatbot with token-by-token generation and command verification*")
    
    initialize_session_state()
    
    # Sidebar with settings and conversation management
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Streaming toggle
        st.session_state.streaming_enabled = st.toggle(
            "🔄 Enable Streaming Generation", 
            value=st.session_state.streaming_enabled,
            help="Show command generation token by token"
        )
        
        st.markdown("---")
        
        st.header("💬 Conversation Management")
        
        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.conversation_history = []
            st.session_state.generated_command = ''
            st.session_state.command_outputs = []
            st.rerun()
        
        st.markdown(f"**Messages in history:** {len(st.session_state.conversation_history)}")
        
        if st.session_state.conversation_history:
            st.subheader("📝 Recent Conversations")
            for i, entry in enumerate(st.session_state.conversation_history[-3:], 1):
                with st.expander(f"Exchange {len(st.session_state.conversation_history) - 3 + i}"):
                    st.write("**User:**", entry['user_message'][:100] + "..." if len(entry['user_message']) > 100 else entry['user_message'])
                    st.write("**Assistant:**", entry['assistant_response'][:100] + "..." if len(entry['assistant_response']) > 100 else entry['assistant_response'])
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💭 Ask your microbiome question")
        user_query = st.text_input(
            "Question:", 
            placeholder="e.g., Find samples with Bacteroides in gut microbiome studies",
            key="user_input"
        )
        
        if st.button("🚀 Generate Command", type="primary") and user_query:
            # Generate command with or without streaming
            if st.session_state.streaming_enabled:
                st.markdown("**🔄 Generating command (streaming):**")
                with st.spinner("Starting generation..."):
                    generated_command = generate_command_streaming(user_query)
            else:
                with st.spinner("Generating command..."):
                    generated_command = generate_command_regular(user_query)
            
            if generated_command:
                st.session_state.generated_command = generated_command
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'user_message': user_query,
                    'assistant_response': generated_command
                })
                
                st.success("✅ Command generated!")
    
    with col2:
        st.subheader("ℹ️ Context Info")
        
        # Show available contexts
        with st.expander("📚 Available Contexts", expanded=False):
            contexts_info = """
            **Most Popular Contexts:**
            • `Deblur_2021.09-Illumina-16S-V4-125nt-92f954` (33,680 samples)
            • `Woltka-KEGG-Ontology-WoLr2-7dd29a` (51,036 samples) 
            • `Deblur_2021.09-Illumina-16S-V4-200nt-0b8b48` (11,159 samples)
            • `Pick_closed-reference_OTUs-Greengenes-Illumina-16S-V4-200nt-a5e305` (9,231 samples)
            """
            st.markdown(contexts_info)
        
        st.info("""
        **Quick Tips:**
        • Use streaming to see generation progress
        • Commands are validated before execution
        • Check the validation results below
        """)
    
    # Command display, validation, and execution section
    if st.session_state.generated_command:
        st.markdown("---")
        st.subheader("⚡ Generated Command")
        
        # Display the generated command
        st.code(st.session_state.generated_command, language='bash')
        
        # Command validation section
        st.markdown("### 🔍 Command Validation")
        
        is_valid, issues, suggestions = validate_redbiom_command(st.session_state.generated_command)
        
        if is_valid:
            st.success("✅ Command passed basic validation")
        else:
            st.error("❌ Command validation issues found:")
            for issue in issues:
                st.error(f"• {issue}")
            
            if suggestions:
                st.info("💡 Suggestions:")
                for suggestion in suggestions:
                    st.info(f"• {suggestion}")
        
        # Dry run check
        with st.expander("🧪 Advanced Validation (Dry Run)", expanded=False):
            if st.button("🔬 Run Validation Check"):
                with st.spinner("Running validation check..."):
                    dry_run_success, dry_run_message = dry_run_command(st.session_state.generated_command)
                    
                    if dry_run_success:
                        st.success(f"✅ {dry_run_message}")
                    else:
                        st.error(f"❌ {dry_run_message}")
        
        # Editable command
        edited_command = st.text_area(
            "✏️ Edit command if needed:",
            value=st.session_state.generated_command,
            height=100,
            help="You can modify the command before execution"
        )
        
        # Re-validate if command was edited
        if edited_command != st.session_state.generated_command:
            edited_valid, edited_issues, edited_suggestions = validate_redbiom_command(edited_command)
            if not edited_valid:
                st.warning("⚠️ Edited command has validation issues:")
                for issue in edited_issues:
                    st.warning(f"• {issue}")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Only show execute button if command passes basic validation or user acknowledges issues
            can_execute = is_valid or (edited_command != st.session_state.generated_command)
            
            execute_button_type = "primary" if is_valid else "secondary"
            execute_button_help = "Command passed validation" if is_valid else "Command has validation issues - proceed with caution"
            
            if st.button(f"▶️ Execute Command", type=execute_button_type, help=execute_button_help):
                if not is_valid:
                    st.warning("⚠️ Executing command with validation issues...")
                
                with st.spinner("Executing command..."):
                    success, stdout, stderr = execute_command(edited_command)
                    
                    execution_result = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'command': edited_command,
                        'success': success,
                        'stdout': stdout,
                        'stderr': stderr,
                        'was_validated': is_valid
                    }
                    
                    st.session_state.command_outputs.append(execution_result)
        
        with col2:
            if st.button("📋 Copy Command"):
                st.code(edited_command, language='bash')
                st.success("✨ Command ready to copy!")
        
        with col3:
            if st.button("🔄 Regenerate Command"):
                # Regenerate with the same query
                if st.session_state.conversation_history:
                    last_query = st.session_state.conversation_history[-1]['user_message']
                    
                    if st.session_state.streaming_enabled:
                        st.markdown("**🔄 Regenerating command (streaming):**")
                        with st.spinner("Starting generation..."):
                            new_command = generate_command_streaming(f"Please regenerate the command for: {last_query}")
                    else:
                        with st.spinner("Regenerating command..."):
                            new_command = generate_command_regular(f"Please regenerate the command for: {last_query}")
                    
                    if new_command:
                        st.session_state.generated_command = new_command
                        st.rerun()
        
        # Display execution results
        if st.session_state.command_outputs:
            st.markdown("---")
            st.subheader("📊 Execution Results")
            
            # Show most recent result first
            for i, result in enumerate(reversed(st.session_state.command_outputs)):
                validation_indicator = "✅" if result.get('was_validated', False) else "⚠️"
                
                with st.expander(f"{validation_indicator} Result {len(st.session_state.command_outputs) - i} - {result['timestamp']}", 
                               expanded=(i == 0)):
                    
                    if result['success']:
                        st.success(f"✅ Command executed successfully")
                        st.code(result['command'], language='bash')
                        
                        if result['stdout']:
                            format_and_display_output(result['stdout'], f"output_{len(st.session_state.command_outputs) - i}")
                        else:
                            st.info("Command executed successfully with no output")
                    else:
                        st.error(f"❌ Command failed")
                        st.code(result['command'], language='bash')
                        
                        if result['stderr']:
                            st.error("**Error Details:**")
                            st.code(result['stderr'], language='text')

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🧬 Enhanced Redbiom Assistant - Now with streaming generation and command validation
    </div>
    """, unsafe_allow_html=True)

def dry_run_command(command):
    """
    Perform a dry run check by running redbiom --help or similar safe commands
    """
    try:
        # Check if redbiom is available
        result = subprocess.run(['redbiom', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False, "redbiom command not found or not working"
        
        # For certain commands, we can do syntax validation
        if '--help' not in command:
            # Try to get help for the subcommand to validate it exists
            command_parts = command.split()
            if len(command_parts) >= 2:
                help_result = subprocess.run(
                    ['redbiom', command_parts[1], '--help'], 
                    capture_output=True, text=True, timeout=10
                )
                if help_result.returncode != 0:
                    return False, f"Subcommand '{command_parts[1]}' not found"
        
        return True, "Basic syntax validation passed"
    
    except subprocess.TimeoutExpired:
        return False, "Command validation timed out"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def initialize_session_state():
    """Initialize session state variables"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'generated_command' not in st.session_state:
        st.session_state.generated_command = ''
    
    if 'command_outputs' not in st.session_state:
        st.session_state.command_outputs = []
    
    if 'streaming_enabled' not in st.session_state:
        st.session_state.streaming_enabled = True

def build_conversation_messages():
    """Build the full conversation history including system prompt"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add all conversation history
    for entry in st.session_state.conversation_history:
        messages.append({"role": "user", "content": entry['user_message']})
        messages.append({"role": "assistant", "content": entry['assistant_response']})
    
    return messages

def generate_command_streaming(user_query):
    """Generate a redbiom command with streaming output"""
    messages = build_conversation_messages()
    messages.append({"role": "user", "content": user_query})
    
    try:
        # Create streaming placeholder
        streaming_placeholder = st.empty()
        full_response = ""
        
        # Make streaming request
        stream = client.chat.completions.create(
            model="qwen3",
            messages=messages,
            stream=True
        )
        
        # Process stream
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                
                # Update display with current response
                streaming_placeholder.code(full_response, language='bash')
                
                # Add small delay to make streaming visible
                time.sleep(0.01)
        
        cleaned_command = clean_qwen_output(full_response)
        return cleaned_command
        
    except Exception as e:
        st.error(f"Error generating command: {str(e)}")
        return None

def generate_command_regular(user_query):
    """Generate a redbiom command using regular (non-streaming) method"""
    messages = build_conversation_messages()
    messages.append({"role": "user", "content": user_query})
    
    try:
        llama_response = client.chat.completions.create(
            model="qwen3",
            messages=messages,
        )
        
        raw_command = llama_response.choices[0].message.content
        cleaned_command = clean_qwen_output(raw_command)
        
        return cleaned_command
    except Exception as e:
        st.error(f"Error generating command: {str(e)}")
        return None

def execute_command(command):
    """Execute a redbiom command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=60*5  # 5 minute timeout
        )
        return True, result.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except subprocess.CalledProcessError as e:
        return False, "", e.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    st.set_page_config(
        page_title="Redbiom Assistant", 
        page_icon="🧬", 
        layout="wide"
    )
    
    st.title("🧬 Redbiom Assistant with Streaming & Validation")
    st.markdown("*A chatbot with token-by-token generation and command verification*")
    
    initialize_session_state()
    
    # Sidebar with settings and conversation management
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Streaming toggle
        st.session_state.streaming_enabled = st.toggle(
            "🔄 Enable Streaming Generation", 
            value=st.session_state.streaming_enabled,
            help="Show command generation token by token"
        )
        
        st.markdown("---")
        
        st.header("💬 Conversation Management")
        
        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.conversation_history = []
            st.session_state.generated_command = ''
            st.session_state.command_outputs = []
            st.rerun()
        
        st.markdown(f"**Messages in history:** {len(st.session_state.conversation_history)}")
        
        if st.session_state.conversation_history:
            st.subheader("📝 Recent Conversations")
            for i, entry in enumerate(st.session_state.conversation_history[-3:], 1):
                with st.expander(f"Exchange {len(st.session_state.conversation_history) - 3 + i}"):
                    st.write("**User:**", entry['user_message'][:100] + "..." if len(entry['user_message']) > 100 else entry['user_message'])
                    st.write("**Assistant:**", entry['assistant_response'][:100] + "..." if len(entry['assistant_response']) > 100 else entry['assistant_response'])
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💭 Ask your microbiome question")
        user_query = st.text_input(
            "Question:", 
            placeholder="e.g., Find samples with Bacteroides in gut microbiome studies",
            key="user_input"
        )
        
        if st.button("🚀 Generate Command", type="primary") and user_query:
            # Generate command with or without streaming
            if st.session_state.streaming_enabled:
                st.markdown("**🔄 Generating command (streaming):**")
                with st.spinner("Starting generation..."):
                    generated_command = generate_command_streaming(user_query)
            else:
                with st.spinner("Generating command..."):
                    generated_command = generate_command_regular(user_query)
            
            if generated_command:
                st.session_state.generated_command = generated_command
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'user_message': user_query,
                    'assistant_response': generated_command
                })
                
                st.success("✅ Command generated!")
    
    with col2:
        st.subheader("ℹ️ Context Info")
        
        # Show available contexts
        with st.expander("📚 Available Contexts", expanded=False):
            contexts_info = """
            **Most Popular Contexts:**
            • `Deblur_2021.09-Illumina-16S-V4-125nt-92f954` (33,680 samples)
            • `Woltka-KEGG-Ontology-WoLr2-7dd29a` (51,036 samples) 
            • `Deblur_2021.09-Illumina-16S-V4-200nt-0b8b48` (11,159 samples)
            • `Pick_closed-reference_OTUs-Greengenes-Illumina-16S-V4-200nt-a5e305` (9,231 samples)
            """
            st.markdown(contexts_info)
        
        st.info("""
        **Quick Tips:**
        • Use streaming to see generation progress
        • Commands are validated before execution
        • Check the validation results below
        """)
    
    # Command display, validation, and execution section
    if st.session_state.generated_command:
        st.markdown("---")
        st.subheader("⚡ Generated Command")
        
        # Display the generated command
        st.code(st.session_state.generated_command, language='bash')
        
        # Command validation section
        st.markdown("### 🔍 Command Validation")
        
        is_valid, issues, suggestions = validate_redbiom_command(st.session_state.generated_command)
        
        if is_valid:
            st.success("✅ Command passed basic validation")
        else:
            st.error("❌ Command validation issues found:")
            for issue in issues:
                st.error(f"• {issue}")
            
            if suggestions:
                st.info("💡 Suggestions:")
                for suggestion in suggestions:
                    st.info(f"• {suggestion}")
        
        # Dry run check
        with st.expander("🧪 Advanced Validation (Dry Run)", expanded=False):
            if st.button("🔬 Run Validation Check"):
                with st.spinner("Running validation check..."):
                    dry_run_success, dry_run_message = dry_run_command(st.session_state.generated_command)
                    
                    if dry_run_success:
                        st.success(f"✅ {dry_run_message}")
                    else:
                        st.error(f"❌ {dry_run_message}")
        
        # Editable command
        edited_command = st.text_area(
            "✏️ Edit command if needed:",
            value=st.session_state.generated_command,
            height=100,
            help="You can modify the command before execution"
        )
        
        # Re-validate if command was edited
        if edited_command != st.session_state.generated_command:
            edited_valid, edited_issues, edited_suggestions = validate_redbiom_command(edited_command)
            if not edited_valid:
                st.warning("⚠️ Edited command has validation issues:")
                for issue in edited_issues:
                    st.warning(f"• {issue}")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Only show execute button if command passes basic validation or user acknowledges issues
            can_execute = is_valid or (edited_command != st.session_state.generated_command)
            
            execute_button_type = "primary" if is_valid else "secondary"
            execute_button_help = "Command passed validation" if is_valid else "Command has validation issues - proceed with caution"
            
            if st.button(f"▶️ Execute Command", type=execute_button_type, help=execute_button_help):
                if not is_valid:
                    st.warning("⚠️ Executing command with validation issues...")
                
                with st.spinner("Executing command..."):
                    success, stdout, stderr = execute_command(edited_command)
                    
                    execution_result = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'command': edited_command,
                        'success': success,
                        'stdout': stdout,
                        'stderr': stderr,
                        'was_validated': is_valid
                    }
                    
                    st.session_state.command_outputs.append(execution_result)
        
        with col2:
            if st.button("📋 Copy Command"):
                st.code(edited_command, language='bash')
                st.success("✨ Command ready to copy!")
        
        with col3:
            if st.button("🔄 Regenerate Command"):
                # Regenerate with the same query
                if st.session_state.conversation_history:
                    last_query = st.session_state.conversation_history[-1]['user_message']
                    
                    if st.session_state.streaming_enabled:
                        st.markdown("**🔄 Regenerating command (streaming):**")
                        with st.spinner("Starting generation..."):
                            new_command = generate_command_streaming(f"Please regenerate the command for: {last_query}")
                    else:
                        with st.spinner("Regenerating command..."):
                            new_command = generate_command_regular(f"Please regenerate the command for: {last_query}")
                    
                    if new_command:
                        st.session_state.generated_command = new_command
                        st.rerun()
        
        # Display execution results
        if st.session_state.command_outputs:
            st.markdown("---")
            st.subheader("📊 Execution Results")
            
            # Show most recent result first
            for i, result in enumerate(reversed(st.session_state.command_outputs)):
                validation_indicator = "✅" if result.get('was_validated', False) else "⚠️"
                
                with st.expander(f"{validation_indicator} Result {len(st.session_state.command_outputs) - i} - {result['timestamp']}", 
                               expanded=(i == 0)):
                    
                    if result['success']:
                        st.success(f"✅ Command executed successfully")
                        st.code(result['command'], language='bash')
                        
                        if result['stdout']:
                            format_and_display_output(result['stdout'], f"output_{len(st.session_state.command_outputs) - i}")
                        else:
                            st.info("Command executed successfully with no output")
                    else:
                        st.error(f"❌ Command failed")
                        st.code(result['command'], language='bash')
                        
                        if result['stderr']:
                            st.error("**Error Details:**")
                            st.code(result['stderr'], language='text')

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🧬 Enhanced Redbiom Assistant - Now with streaming generation and command validation
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()