import streamlit as st
import subprocess
# import ollama
import re
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

NRP_API_KEY = os.getenv("NRP_API_KEY")
client = OpenAI(
    # This is the default and can be omitted
    api_key = NRP_API_KEY,
    base_url = "https://llm.nrp-nautilus.io/"
)

# System prompt that the chatbot will never forget
SYSTEM_PROMPT = """
You are an expert assistant that converts natural language microbiome questions into 
valid Redbiom CLI commands. 

### General Redbiom CLI Syntax
Redbiom commands follow:
    redbiom [OPTIONS] <COMMAND> [SUBCOMMAND] [FLAGS] [ARGUMENTS]

Common commands:
1. search
    1. **Command: features**
        - Description: Get samples containing specified features.
        - Options:
            - `--from`: *(optional)* `"A file or stdin which provides features to search for."`
            - `--exact`: *(flag)* `"All found samples must contain all specified features."`
            - `--context`: *(required)* `"The context to search within."`
            - `--min-count`: *(optional, int ≥1, default=1)* `"Minimum number of times the feature was observed."`
            - `features...`: *(variadic argument)* `"Features to search for."`
        - Example:
            ```
            redbiom search features --context <context> --exact --min-count 5 feature1 feature2
            ```

    2. **Command: samples**
        - Description: Get features present in specified samples.
        - Options:
            - `--from`: *(optional)* `"A file or stdin which provides samples to search for."`
            - `--exact`: *(flag)* `"All found features must be present in all specified samples."`
            - `--context`: *(required)* `"The context to search within."`
            - `--min-count`: *(optional, int ≥1, default=1)* `"Minimum number of times the feature was observed."`
            - `samples...`: *(variadic argument)* `"Sample IDs to search for."`
        - Example:
            ```
            redbiom search samples --context <context> --exact --min-count 2 sample1 sample2
            ```

    3. **Command: metadata**
        - Description: Search metadata values or categories using NLP-based stem and value queries.
        - Options:
            - `--categories`: *(flag)* `"Search for metadata categories instead of values."`
            - `query`: *(required, string)* `"Search expression, can include word stems, set operators (&, |, -), or value-based queries using 'where'."`
        - Examples:
            ```
            redbiom search metadata "antibiotics & infant"
            redbiom search metadata --categories "ph - water"
            redbiom search metadata "antibiotics where age_days < 30"
            ```

    4. **Command: taxon**
        - Description: Find features associated with a given taxon.
        - Options:
            - `--context`: *(required)* `"The context to search within."`
            - `query`: *(required, string)* `"Taxon to search for (e.g., 'Bacteroides')."`
        - Example:
            ```
            redbiom search taxon --context <context> "Bacteroides"
            ```

2. fetch
    1. **Command: tags-contained**
        - Description: Get the observed tags within a context.
        - Options:
            - `--context`: *(required)* `"The context to fetch from."`
        - Example:
            ```
            redbiom fetch tags-contained --context <context>
            ```

    2. **Command: samples-contained**
        - Description: Get all sample identifiers represented in a context.
        - Options:
            - `--context`: *(optional)* `"The context to fetch from."`
            - `--unambiguous`: *(flag)* `"Return ambiguous or unambiguous identifiers."`
        - Example:
            ```
            redbiom fetch samples-contained --context <context> --unambiguous
            ```

    3. **Command: features-contained**
        - Description: Get all features represented in a context.
        - Options:
            - `--context`: *(optional)* `"The context to fetch from."`
        - Example:
            ```
            redbiom fetch features-contained --context <context>
            ```

    4. **Command: sample-metadata**
        - Description: Retrieve sample metadata.
        - Options:
            - `--from`: `"A file or stdin which provides samples to search for."`
            - `--output`: *(required)* `"A filepath to write to."`
            - `--context`: *(optional)* `"The context to search within."`
            - `--all-columns`: *(flag)* `"Include all metadata columns, filling missing with empty string."`
            - `--tagged`: *(flag)* `"Obtain tag-specific metadata (preparation info)."`
            - `--resolve-ambiguities`: *(flag)* `"Output unambiguous identifiers only. Incompatible with --tagged."`
            - `--force-category <name>`: *(repeatable)* `"Force output to include specific metadata variables."`
            - `samples...`: *(variadic argument)* `"Sample IDs to fetch metadata for."`
        - Example:
            ```
            redbiom fetch sample-metadata --context <context> --output output.tsv --all-columns sample1 sample2
            ```

    5. **Command: features**
        - Description: Fetch sample data containing given features.
        - Options:
            - `--from`: `"A file or stdin providing features to search for."`
            - `--output`: *(required)* `"A filepath to write to."`
            - `--exact`: *(flag)* `"All found samples must contain all specified features."`
            - `--context`: *(required)* `"The context to search within."`
            - `--md5`: *(bool)* `"Use MD5 for features and save original mapping to TSV."`
            - `--resolve-ambiguities`: `merge|most-reads` *(optional)* `"Resolve sample ambiguities."`
            - `--fetch-taxonomy`: *(flag)* `"Resolve taxonomy on fetch (slower; Deblur does not cache taxonomy)."`
            - `--retain-artifact-id`: *(flag)* `"When using most-reads, retain the artifact ID of the kept sample."`
            - `features...`: *(variadic argument)* `"Features to fetch."`
        - Example:
            ```
            redbiom fetch features --context <context> --output output.biom --exact --md5 feature1 feature2
            ```

    6. **Command: samples**
        - Description: Fetch sample data.
        - Options:
            - `--from`: `"A file or stdin providing samples to search for."`
            - `--output`: *(required)* `"A filepath to write to."`
            - `--context`: *(required)* `"The context to search within."`
            - `--md5`: *(bool)* `"Use MD5 for features and save original mapping to TSV."`
            - `--resolve-ambiguities`: `merge|most-reads` *(optional)* `"Resolve sample ambiguities."`
            - `--fetch-taxonomy`: *(flag)* `"Resolve taxonomy on fetch (slower; Deblur does not cache taxonomy)."`
            - `--retain-artifact-id`: *(flag)* `"When using most-reads, retain the artifact ID of the kept sample."`
            - `samples...`: *(variadic argument)* `"Sample IDs to fetch."`
        - Example:
            ```
            redbiom fetch samples --context <context> --output output.biom --md5 sample1 sample2
            ```

    7. **Command: qiita-study**
        - Description: Fetch all data from a Qiita study.
        - Options:
            - `--study-id`: *(required, int)* `"The Qiita study ID to fetch."`
            - `--context`: *(required)* `"The context to fetch from."`
            - `--resolve-ambiguities`: `merge|most-reads` *(optional)* `"Resolve sample ambiguities."`
            - `--fetch-taxonomy`: *(flag)* `"Resolve taxonomy on fetch (slower; Deblur does not cache taxonomy)."`
            - `--retain-artifact-id`: *(flag)* `"When using most-reads, retain the artifact ID of the kept sample."`
            - `--remove-blanks`: *(flag)* `"Remove samples with 'blank' in their name (case-insensitive)."`
            - `--output-basename`: *(required)* `"Base filename for outputs (TSV + BIOM)."`
            - `--md5`: *(bool)* `"Use MD5 for features and save original mapping to TSV."`
        - Example:
            ```
            redbiom fetch qiita-study --study-id 123 --context <context> --output-basename my_study --remove-blanks --md5
            ```

3. summarize
    1. **Command: contexts**
        - Description: List names of available caches.
        - Options: *(none)*
        - Example:
            ```
            redbiom summarize contexts
            ```

    2. **Command: metadata-category**
        - Description: Summarize the values within a metadata category.
        - Options:
            - `--category`: *(required)* `"The metadata category (column) to summarize."`
            - `--counter`: *(flag)* `"If true, obtain value counts."`
            - `--descending`: *(flag)* `"If true, sort in descending order."`
            - `--dump`: *(flag)* `"If true, print the sample information."`
            - `--sort-index`: *(flag)* `"If true, sort on the index instead of the values (only relevant with --counter)."`
        - Example:
            ```
            redbiom summarize metadata-category --category host_age --counter --descending
            ```

    3. **Command: metadata**
        - Description: Get the known metadata categories and associated sample counts.
        - Options:
            - `--descending`: *(flag)* `"If true, sort in descending order."`
            - `categories...`: *(variadic argument)* `"Optional categories to summarize (if empty, summarize all)."`
        - Example:
            ```
            redbiom summarize metadata --descending host_age host_sex
            ```

    4. **Command: table**
        - Description: Summarize all features in a BIOM table over a metadata category.
        - Options:
            - `--category`: *(required)* `"Metadata category to summarize over."`
            - `--context`: *(required)* `"The context to use."`
            - `--output`: *(optional)* `"Output file path to write TSV summary."`
            - `--threads`: *(optional, default=1)* `"Number of threads to use."`
            - `--verbosity`: *(optional, default=0)* `"Joblib verbosity level."`
            - `--table`: *(required)* `"Path to the BIOM table."`
        - Example:
            ```
            redbiom summarize table --category host_age --context Deblur_2021.09 --table table.biom --threads 4
            ```

    5. **Command: features**
        - Description: Summarize features over a metadata category.
        - Options:
            - `--from`: *(optional)* `"A file or stdin which provides features to summarize."`
            - `--category`: *(required)* `"Metadata category to summarize over."`
            - `--exact`: *(flag)* `"All found samples must contain all specified features."`
            - `--context`: *(required)* `"The context to use."`
            - `features...`: *(variadic argument)* `"Feature IDs to summarize."`
        - Example:
            ```
            redbiom summarize features --category host_age --context Deblur_2021.09 feature1 feature2
            ```

    6. **Command: samples**
        - Description: Summarize samples over a metadata category.
        - Options:
            - `--from`: *(optional)* `"A file or stdin which provides samples to summarize."`
            - `--category`: *(required)* `"Metadata category to summarize over."`
            - `samples...`: *(variadic argument)* `"Sample IDs to summarize."`
        - Example:
            ```
            redbiom summarize samples --category host_age sample1 sample2
            ```

    7. **Command: taxonomy**
        - Description: Summarize taxonomy at all levels for given features.
        - Options:
            - `--from`: *(optional)* `"A file or stdin which provides features to summarize."`
            - `--context`: *(required)* `"The context to search within."`
            - `--normalize-ranks`: *(optional, default='kpcofgs')* `"Coerce normalized rank info for unclassifieds."`
            - `features...`: *(variadic argument)* `"Feature IDs to summarize taxonomy for."`
        - Example:
            ```
            redbiom summarize taxonomy --context Deblur_2021.09 feature1 feature2
            ```

4. select
    1. **Command: samples-from-metadata**
        - Description: Given samples, select based on metadata.
        - Options:
            - `--from`: *(optional)* `"A file or stdin which provides samples to search for."`
            - `--context`: *(required)* `"The context to search within."`
            - `query`: *(required argument)* `"Metadata query to filter samples."`
            - `samples...`: *(variadic argument)* `"Sample IDs to check against the query."`
        - Example:
            ```
            redbiom select samples-from-metadata --context <context> "age_days < 30" sample1 sample2
            ```

    2. **Command: features-from-samples**
        - Description: Given samples, select the features associated with them.
        - Options:
            - `--from`: *(optional)* `"A file or stdin which provides samples to search for."`
            - `--context`: *(required)* `"The context to search within."`
            - `--exact`: *(flag)* `"All found features must exist in all samples."`
            - `samples...`: *(variadic argument)* `"Sample IDs to select features from."`
        - Example:
            ```
            redbiom select features-from-samples --context <context> --exact sample1 sample2
            ```

### Contexts
- Many commands (search taxon, samples, features) require a context:
    --context <context-name>
- Best practice:
    export CTX=Deblur-NA-Illumina-16S-v4-90nt-99d1d8
    redbiom search taxon g__Roseburia --context $CTX
- Get available contexts:
    redbiom summarize contexts

### Admin Commands (Do NOT generate)
The following exist but must never be suggested:
    redbiom admin load-*
    redbiom admin clear-cache
    redbiom admin rebuild-trees
    redbiom admin server *

### Rules for Command Generation
1. Output only **one complete CLI command**, starting with `redbiom`.
2. Use **only these commands**: search, fetch, summarize, select.
3. If a taxon or feature search is requested, include a context flag like:
    --context Deblur-NA-Illumina-16S-v4-90nt-99d1d8
4. Never output admin commands or destructive operations.
5. Do not explain or add extra commentary—output only the command.

Always remember our conversation history and maintain context throughout our discussion. Feel free to use terminal commands
to better serve the user, but ensure they are valid Redbiom and CLI commands.
"""

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
                    st.dataframe(df, use_container_width=True)
                    st.markdown(f"**📊 Summary:** {len(data)} rows, {len(headers)} columns")
                    
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
            timeout=60*5  # 60 second timeout
        )
        return True, result.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 60 seconds"
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
    
    st.title("🧬 Redbiom Assistant with Persistent Memory")
    st.markdown("*A chatbot that remembers our entire conversation and generates redbiom commands*")
    
    initialize_session_state()
    
    # Sidebar with conversation management
    with st.sidebar:
        st.header("💬 Conversation Management")
        
        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.conversation_history = []
            st.session_state.generated_command = ''
            st.session_state.command_outputs = []
            st.rerun()
        
        st.markdown(f"**Messages in history:** {len(st.session_state.conversation_history)}")
        
        if st.session_state.conversation_history:
            st.subheader("📝 Conversation Summary")
            for i, entry in enumerate(st.session_state.conversation_history[-3:], 1):  # Show last 3
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
            with st.spinner("Generating command..."):
                generated_command = generate_command(user_query)
                
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
        
        # Show available contexts from the uploaded data
        with st.expander("📚 Available Contexts", expanded=False):
            contexts_info = """
            **Most Popular Contexts:**
            • `Deblur_2021.09-Illumina-16S-V4-125nt-92f954` (33,680 samples)
            • `Woltka-KEGG-Ontology-WoLr2-7dd29a` (51,036 samples) 
            • `Deblur_2021.09-Illumina-16S-V4-200nt-0b8b48` (11,159 samples)
            • `Pick_closed-reference_OTUs-Greengenes-Illumina-16S-V4-200nt-a5e305` (9,231 samples)
            
            **By Data Type:**
            • **16S rRNA:** Deblur_2021.09-*, Pick_closed-reference_OTUs-Greengenes-*
            • **18S rRNA:** Deblur_2021.09-Illumina-18S-*, Pick_closed-reference_OTUs-SILVA-Illumina-18S-*
            • **ITS (Fungi):** Deblur_2021.09-Illumina-ITS-*, Pick_closed-reference_OTUs-*-ITS-*
            • **Functional:** Woltka-KEGG-*, Woltka-per-genome-*
            """
            st.markdown(contexts_info)
        
        st.info("""
        **Quick Tips:**
        • Use `redbiom summarize contexts` to see all contexts
        • Deblur contexts are generally more accurate
        • Check sample counts before analysis
        """)
        
        # Add a context search helper
        context_search = st.text_input("🔍 Search contexts:", placeholder="e.g., 16S, V4, Illumina")
        if context_search:
            # Simple context filtering based on search term
            st.markdown("**Matching contexts:**")
            st.code(f"redbiom summarize contexts | grep -i '{context_search}'", language='bash')
    
    # Command display and execution section
    if st.session_state.generated_command:
        st.markdown("---")
        st.subheader("⚡ Generated Command")
        
        # Display the generated command
        st.code(st.session_state.generated_command, language='bash')
        
        # Editable command
        edited_command = st.text_area(
            "✏️ Edit command if needed:",
            value=st.session_state.generated_command,
            height=100,
            help="You can modify the command before execution"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("▶️ Execute Command", type="primary"):
                with st.spinner("Executing command..."):
                    success, stdout, stderr = execute_command(edited_command)
                    
                    execution_result = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'command': edited_command,
                        'success': success,
                        'stdout': stdout,
                        'stderr': stderr
                    }
                    
                    st.session_state.command_outputs.append(execution_result)
        
        with col2:
            if st.button("📋 Copy Command"):
                # Create a copy-friendly display
                st.markdown("**Command to copy:**")
                st.code(edited_command, language='bash')
                st.success("✨ Command ready to copy!")
                
            if st.button("💾 Save Output", help="Save the last command output"):
                if st.session_state.command_outputs:
                    last_output = st.session_state.command_outputs[-1]
                    if last_output['success'] and last_output['stdout']:
                        # Create download button
                        st.download_button(
                            label="📥 Download Output",
                            data=last_output['stdout'],
                            file_name=f"redbiom_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("No successful output to save")
        
        # Display execution results
        if st.session_state.command_outputs:
            st.markdown("---")
            st.subheader("📊 Execution Results")
            
            # Show most recent result first
            for i, result in enumerate(reversed(st.session_state.command_outputs)):
                with st.expander(f"Result {len(st.session_state.command_outputs) - i} - {result['timestamp']}", 
                               expanded=(i == 0)):  # Expand most recent
                    
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
        🧬 Redbiom Assistant - Maintains conversation context and system instructions throughout the session
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()