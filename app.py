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