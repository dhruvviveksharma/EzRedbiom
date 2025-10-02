# import streamlit as st
# import subprocess
# from datetime import datetime
# import os
# import json
# from dotenv import load_dotenv
# from openai import OpenAI
# from format_output import format_and_display_output
# from LLM_Generation.LLM_Output import clean_qwen_output
# from LLM_Generation.LLM_Output import SYSTEM_PROMPT

# load_dotenv()

# NRP_API_KEY = os.getenv("NRP_API_KEY")
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# nrp_client = OpenAI(
#     api_key=NRP_API_KEY,
#     base_url="https://llm.nrp-nautilus.io/"
# )

# def initialize_session_state():
#     """Initialize session state with enhanced tracking"""
#     if 'messages' not in st.session_state:
#         st.session_state.messages = []
    
#     if 'command_history' not in st.session_state:
#         st.session_state.command_history = []
    
#     if 'execution_results' not in st.session_state:
#         st.session_state.execution_results = {}
    
#     if 'selected_llm' not in st.session_state:
#         st.session_state.selected_llm = 'qwen3'
    
#     if 'analysis_context' not in st.session_state:
#         st.session_state.analysis_context = {
#             'current_study': None,
#             'preferred_context': None,
#             'recent_findings': [],
#             'analysis_history': []
#         }

# def extract_commands_from_response(response_text):
#     """Extract bash commands from markdown code blocks"""
#     import re
    
#     # Find all bash code blocks
#     bash_pattern = r'```bash\n(.*?)\n```'
#     commands = re.findall(bash_pattern, response_text, re.DOTALL)
    
#     # Also look for redbiom commands without bash specifier
#     redbiom_pattern = r'```\n(redbiom.*?)\n```'
#     redbiom_commands = re.findall(redbiom_pattern, response_text, re.DOTALL)
    
#     all_commands = commands + redbiom_commands
#     return [cmd.strip() for cmd in all_commands if cmd.strip().startswith('redbiom')]

# def build_enhanced_conversation_context():
#     """Build conversation context including command outputs"""
#     context_parts = []
    
#     # Add analysis context
#     if st.session_state.analysis_context['recent_findings']:
#         context_parts.append("Recent findings from previous analyses:")
#         for finding in st.session_state.analysis_context['recent_findings'][-3:]:
#             context_parts.append(f"- {finding}")
    
#     # Add recent successful commands and their outputs
#     recent_executions = [(k, v) for k, v in st.session_state.execution_results.items() 
#                         if v.get('success', False)][-5:]
    
#     if recent_executions:
#         context_parts.append("\nRecent successful command outputs:")
#         for cmd_id, result in recent_executions:
#             cmd = result.get('command', 'Unknown command')
#             output_summary = result.get('output', '')[:200] + "..." if len(result.get('output', '')) > 200 else result.get('output', '')
#             context_parts.append(f"Command: {cmd}")
#             context_parts.append(f"Output: {output_summary}")
    
#     return "\n".join(context_parts)

# def build_conversation_messages():
#     """Build messages for API call"""
#     messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
#     # Add conversation context
#     context = build_enhanced_conversation_context()
#     if context:
#         messages.append({"role": "system", "content": f"Conversation context:\n{context}"})
    
#     # Add recent message history (last 10 exchanges)
#     for message in st.session_state.messages[-20:]:  # Last 20 messages (10 exchanges)
#         messages.append({
#             "role": message["role"], 
#             "content": message["content"]
#         })
    
#     return messages

# def generate_analysis_response(user_query):
#     """Generate ChatGPT-style analysis response"""
#     messages = build_conversation_messages()
#     messages.append({"role": "user", "content": user_query})
    
#     try:
#         if st.session_state.selected_llm == 'claude':
#             # Use Claude API (you'll need to implement this based on your setup)
#             response = nrp_client.chat.completions.create(
#                 model="qwen3",  # Replace with Claude when available
#                 messages=messages,
#                 temperature=0.1
#             )
#         else:
#             response = nrp_client.chat.completions.create(
#                 model="qwen3",
#                 messages=messages,
#                 temperature=0.1
#             )
        
#         return response.choices[0].message.content
#     except Exception as e:
#         st.error(f"Error generating response: {str(e)}")
#         return None

# def execute_command_with_tracking(command, command_id):
#     """Execute command and track results"""
#     try:
#         result = subprocess.run(
#             command,
#             shell=True,
#             capture_output=True,
#             text=True,
#             check=True,
#             timeout=300  # 5 minute timeout
#         )
        
#         # Store execution result
#         execution_result = {
#             'command': command,
#             'success': True,
#             'output': result.stdout,
#             'error': '',
#             'timestamp': datetime.now().isoformat()
#         }
        
#         st.session_state.execution_results[command_id] = execution_result
        
#         # Add to command history
#         st.session_state.command_history.append({
#             'command': command,
#             'success': True,
#             'timestamp': datetime.now().isoformat()
#         })
        
#         return True, result.stdout, ""
        
#     except subprocess.TimeoutExpired:
#         error_msg = "Command timed out after 5 minutes"
#         st.session_state.execution_results[command_id] = {
#             'command': command,
#             'success': False,
#             'output': '',
#             'error': error_msg,
#             'timestamp': datetime.now().isoformat()
#         }
#         return False, "", error_msg
        
#     except subprocess.CalledProcessError as e:
#         st.session_state.execution_results[command_id] = {
#             'command': command,
#             'success': False,
#             'output': '',
#             'error': e.stderr,
#             'timestamp': datetime.now().isoformat()
#         }
#         return False, "", e.stderr
        
#     except Exception as e:
#         error_msg = str(e)
#         st.session_state.execution_results[command_id] = {
#             'command': command,
#             'success': False,
#             'output': '',
#             'error': error_msg,
#             'timestamp': datetime.now().isoformat()
#         }
#         return False, "", error_msg

# def render_executable_command(command, command_index, message_index):
#     """Render a command in an executable cell"""
#     command_id = f"msg_{message_index}_cmd_{command_index}"
    
#     # Create expandable section for each command
#     with st.expander(f"🔧 Command {command_index + 1}: Execute", expanded=True):
#         # Display the command in a code block
#         st.code(command, language="bash")
        
#         # Execution controls
#         col1, col2, col3 = st.columns([2, 1, 1])
        
#         with col1:
#             # Option to edit the command
#             edited_command = st.text_input(
#                 "Edit command (optional):", 
#                 value=command,
#                 key=f"edit_{command_id}",
#                 label_visibility="collapsed"
#             )
        
#         with col2:
#             execute_button = st.button(
#                 "▶️ Execute", 
#                 key=f"exec_{command_id}",
#                 type="primary",
#                 help="Execute this command"
#             )
        
#         with col3:
#             # Show execution status
#             if command_id in st.session_state.execution_results:
#                 result = st.session_state.execution_results[command_id]
#                 if result['success']:
#                     st.success("✅ Done")
#                 else:
#                     st.error("❌ Failed")
        
#         # Execute command if button clicked
#         if execute_button:
#             with st.spinner(f"Executing command {command_index + 1}..."):
#                 success, stdout, stderr = execute_command_with_tracking(edited_command, command_id)
#                 st.rerun()
        
#         # Show output if command was executed
#         if command_id in st.session_state.execution_results:
#             result = st.session_state.execution_results[command_id]
            
#             if result['success']:
#                 st.markdown("**Output:**")
#                 if result['output'].strip():
#                     # Use your existing format_and_display_output function
#                     try:
#                         format_and_display_output(result['output'], f"output_{command_id}")
#                     except:
#                         st.text(result['output'])
#                 else:
#                     st.info("Command completed successfully (no output)")
                    
#                 # Update analysis context with findings
#                 if len(result['output']) > 50:  # If substantial output
#                     finding = f"Executed '{command[:50]}...' - found {len(result['output'].split(chr(10)))} lines of data"
#                     if finding not in st.session_state.analysis_context['recent_findings']:
#                         st.session_state.analysis_context['recent_findings'].append(finding)
#             else:
#                 st.markdown("**Error:**")
#                 st.error(result['error'])

# def render_message(message, message_index):
#     """Render a single message in ChatGPT style"""
#     if message["role"] == "user":
#         with st.chat_message("user"):
#             st.markdown(message["content"])
    
#     elif message["role"] == "assistant":
#         with st.chat_message("assistant"):
#             # Display the main response
#             st.markdown(message["content"])
            
#             # Extract and render executable commands
#             commands = extract_commands_from_response(message["content"])
            
#             if commands:
#                 st.markdown("---")
#                 st.markdown("### 🚀 Executable Commands")
                
#                 for i, command in enumerate(commands):
#                     render_executable_command(command, i, message_index)

# def save_session():
#     """Save current session to file"""
#     try:
#         session_data = {
#             'messages': st.session_state.messages,
#             'execution_results': st.session_state.execution_results,
#             'command_history': st.session_state.command_history,
#             'analysis_context': st.session_state.analysis_context,
#             'timestamp': datetime.now().isoformat()
#         }
        
#         filename = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#         with open(filename, 'w') as f:
#             json.dump(session_data, f, indent=2)
        
#         st.success(f"Session saved as {filename}")
#         return filename
#     except Exception as e:
#         st.error(f"Error saving session: {str(e)}")
#         return None

# def load_session(filename):
#     """Load session from file"""
#     try:
#         with open(filename, 'r') as f:
#             session_data = json.load(f)
        
#         st.session_state.messages = session_data.get('messages', [])
#         st.session_state.execution_results = session_data.get('execution_results', {})
#         st.session_state.command_history = session_data.get('command_history', [])
#         st.session_state.analysis_context = session_data.get('analysis_context', {
#             'current_study': None,
#             'preferred_context': None,
#             'recent_findings': [],
#             'analysis_history': []
#         })
        
#         st.success("Session loaded successfully!")
#         return True
#     except Exception as e:
#         st.error(f"Error loading session: {str(e)}")
#         return False

# def main():
#     st.set_page_config(
#         page_title="EzRedbiom Chat",
#         page_icon="🧬",
#         layout="wide"
#     )
    
#     # Header
#     st.title("🧬 EzRedbiom Interactive Analysis")
#     st.markdown("*ChatGPT-style microbiome data analysis with executable commands*")
    
#     initialize_session_state()
    
#     # Sidebar
#     with st.sidebar:
#         st.header("⚙️ Settings")
        
#         # Model selection
#         st.session_state.selected_llm = st.selectbox(
#             "AI Model:",
#             ["qwen3", "claude"],
#             index=0,
#             help="Choose your analysis assistant"
#         )
        
#         st.header("💾 Session Management")
#         col1, col2 = st.columns(2)
        
#         with col1:
#             if st.button("📁 Save Session", type="secondary"):
#                 save_session()
        
#         with col2:
#             if st.button("🗑️ Clear Chat", type="secondary"):
#                 st.session_state.messages = []
#                 st.session_state.execution_results = {}
#                 st.session_state.command_history = []
#                 st.rerun()
        
#         # Session stats
#         st.header("📊 Session Stats")
#         total_messages = len(st.session_state.messages)
#         total_commands = len(st.session_state.command_history)
#         successful_commands = sum(1 for cmd in st.session_state.command_history if cmd.get('success'))
        
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("Messages", total_messages)
#             st.metric("Commands", total_commands)
#         with col2:
#             st.metric("Successful", successful_commands)
#             if total_commands > 0:
#                 success_rate = (successful_commands / total_commands) * 100
#                 st.metric("Success Rate", f"{success_rate:.1f}%")
        
#         # Recent findings
#         if st.session_state.analysis_context['recent_findings']:
#             st.header("🔍 Recent Findings")
#             for finding in st.session_state.analysis_context['recent_findings'][-3:]:
#                 st.info(finding)
        
#         # Quick help
#         with st.expander("💡 Quick Tips", expanded=False):
#             st.markdown("""
#             **Getting Started:**
#             - Ask questions about your microbiome data
#             - The AI will break down analysis steps
#             - Execute commands directly in the chat
#             - All outputs are remembered for context
            
#             **Example Questions:**
#             - "Find samples with Bacteroides"
#             - "Analyze gut microbiome diversity"
#             - "Compare samples from different body sites"
#             """)

#     # Chat interface
#     for i, message in enumerate(st.session_state.messages):
#         render_message(message, i)

#     # Chat input
#     if prompt := st.chat_input("Ask me about your microbiome analysis..."):
#         # Add user message
#         st.session_state.messages.append({"role": "user", "content": prompt})
        
#         # Display user message immediately
#         with st.chat_message("user"):
#             st.markdown(prompt)
        
#         # Generate and display assistant response
#         with st.chat_message("assistant"):
#             with st.spinner("Analyzing your question and preparing step-by-step guidance..."):
#                 response = generate_analysis_response(prompt)
                
#                 if response:
#                     # Add to messages
#                     st.session_state.messages.append({"role": "assistant", "content": response})
                    
#                     # Display response
#                     st.markdown(response)
                    
#                     # Extract and display executable commands
#                     commands = extract_commands_from_response(response)
                    
#                     if commands:
#                         st.markdown("---")
#                         st.markdown("### 🚀 Executable Commands")
                        
#                         message_index = len(st.session_state.messages) - 1
#                         for i, command in enumerate(commands):
#                             render_executable_command(command, i, message_index)
#                 else:
#                     st.error("I apologize, but I couldn't generate a response. Please try rephrasing your question.")

#     # Footer
#     st.markdown("---")
#     st.markdown("""
#     <div style='text-align: center; color: #888; font-size: 0.8em;'>
#         🧬 EzRedbiom Interactive Analysis | Built with Streamlit | 
#         AI remembers all command outputs for context
#     </div>
#     """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()

import streamlit as st
import subprocess
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
from format_output import format_and_display_output
from LLM_Generation.LLM_Output import clean_qwen_output, SYSTEM_PROMPT

load_dotenv()

NRP_API_KEY = os.getenv("NRP_API_KEY")
client = OpenAI(
    # This is the default and can be omitted
    api_key = NRP_API_KEY,
    base_url = "https://llm.nrp-nautilus.io/"
)

# System prompt that the chatbot will never forget

def initialize_session_state():
    """Initialize session state variables"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'generated_command' not in st.session_state:
        st.session_state.generated_command = ''
    
    if 'command_outputs' not in st.session_state:
        st.session_state.command_outputs = []

def build_conversation_messages():
    """Build the full conversation history including system prompt"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add all conversation history
    for entry in st.session_state.conversation_history:
        messages.append({"role": "user", "content": entry['user_message']})
        messages.append({"role": "assistant", "content": entry['assistant_response']})
    
    return messages

def generate_command(user_query):
    """Generate a redbiom command using the LLM with full conversation context"""
    messages = build_conversation_messages()
    messages.append({"role": "user", "content": user_query})
    
    try:
        qwen_response = client.chat.completions.create(
            model="qwen3",
            messages=messages,
        )
        raw_response = qwen_response.choices[0].message.content
        cleaned_command = clean_qwen_output(raw_response)
        return cleaned_command
        # return cleaned_command
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
            timeout=60*5  # 60 second timeout
        )
        return True, result.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except subprocess.CalledProcessError as e:
        return False, "", e.stderr
    except Exception as e:
        return False, "", str(e)
    
def display_editable_command(command, message_id):
    """Display an editable command with execute button"""
    col1, col2 = st.columns([4, 1])
    
    with col1:
        edited_command = st.text_area(
            "✏️ Edit command:",
            value=command,
            height=100,
            key=f"edit_cmd_{message_id}",
            help="You can modify the command before execution"
        )
    
    with col2:
        st.write("")  # Add some spacing
        st.write("")  # Add some spacing
        if st.button("▶️ Execute", key=f"exec_btn_{message_id}", type="primary"):
            return edited_command
    
    return None

def main():
    st.set_page_config(
        page_title="EzRedbiom", 
        page_icon="🧬", 
        layout="wide"
    )
    
    st.title("🧬 EzRedbiom")
    st.markdown("*A chatbot for everything Redbiom*")
    
    initialize_session_state()
    
    # Sidebar with conversation management
    with st.sidebar:
        st.header("💬 Conversation Management")
        
        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.conversation_history = []
            st.session_state.pending_executions = {}
            st.rerun()
        
        st.markdown(f"**Messages in history:** {len(st.session_state.conversation_history)}")
        
        if st.session_state.conversation_history:
            st.subheader("📝 Recent Messages")
            for i, entry in enumerate(st.session_state.conversation_history[-3:]):  # Show last 3
                with st.expander(f"Exchange {len(st.session_state.conversation_history) - 3 + i + 1}"):
                    st.write("**User:**", entry['user_message'][:100] + "..." if len(entry['user_message']) > 100 else entry['user_message'])
                    st.write("**Assistant:**", entry['assistant_response'][:100] + "..." if len(entry['assistant_response']) > 100 else entry['assistant_response'])
                    if 'command' in entry:
                        st.code(entry['command'], language="bash")
        
        # Context helper
        with st.expander("📚 Context Helper", expanded=False):
            st.markdown("""
            **Popular Contexts:**
            • `Deblur_2021.09-Illumina-16S-V4-125nt-92f954` (33,680 samples)
            • `Woltka-KEGG-Ontology-WoLr2-7dd29a` (51,036 samples)
            • `Deblur_2021.09-Illumina-16S-V4-200nt-0b8b48` (11,159 samples)
            
            **Quick Tips:**
            • Use `redbiom summarize contexts` to see all contexts
            • Deblur contexts are generally more accurate
            • Check sample counts before analysis
            """)

    # Display chat history
    for i, entry in enumerate(st.session_state.conversation_history):
        # User message
        with st.chat_message("user"):
            st.markdown(entry["user_message"])
        
        # Assistant message with command
        with st.chat_message("assistant"):
            st.markdown(entry["assistant_response"])
            
            if "command" in entry:
                st.markdown("**Generated Command:**")
                
                # Check if this command has pending execution
                message_id = entry.get('id', i)
                executed_command = display_editable_command(entry["command"], message_id)
                
                # If execute button was clicked
                if executed_command:
                    with st.spinner("Executing command..."):
                        success, stdout, stderr = execute_command(executed_command)
                        
                        # Store the execution results
                        if success:
                            entry['output'] = stdout
                            entry['executed_command'] = executed_command
                            st.success("✅ Command executed successfully!")
                        else:
                            entry['error'] = stderr
                            entry['executed_command'] = executed_command
                            st.error("❌ Command execution failed!")
                        
                        st.rerun()
                
                # Show previous execution results if they exist
                if 'output' in entry:
                    st.success("✅ Previous execution successful:")
                    if entry.get('executed_command') != entry['command']:
                        st.info(f"**Executed command:** `{entry.get('executed_command', entry['command'])}`")
                    format_and_display_output(entry['output'], f"output_{i}")
                elif 'error' in entry:
                    st.error("❌ Previous execution failed:")
                    if entry.get('executed_command') != entry['command']:
                        st.info(f"**Executed command:** `{entry.get('executed_command', entry['command'])}`")
                    st.code(entry['error'], language="text")

    # Chat input
    if user_query := st.chat_input("Ask your microbiome question..."):
        # Show user message
        with st.chat_message("user"):
            st.markdown(user_query)

        # Generate assistant response
        with st.chat_message("assistant"):
            
            with st.spinner("Generating command..."):
                generated_command = generate_command(user_query)

                # Create new message entry
                message_entry = {
                    "id": str(datetime.now().timestamp()).replace('.', ''),
                    "user_message": user_query,
                    "assistant_response": "Here's your generated command:",
                    "command": generated_command
                }
                
                # Add to conversation history
                st.session_state.conversation_history.append(message_entry)
                
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🧬 EzRedbiom - Enhanced Chat Interface with Command Editing and Output Storage
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()