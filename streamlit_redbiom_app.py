import streamlit as st
import subprocess
import ollama
import re

st.title("🧬 Redbiom Assistant with Code Llama")

# Step 1: Get natural language question
user_query = st.text_input("Ask a microbiome question (e.g., samples with antibiotics):")

if user_query:
    ALLOWED_COMMANDS = [
    "redbiom search metadata",
    "redbiom search taxon",
    "redbiom search features",
    "redbiom fetch samples",
    "redbiom fetch sample-metadata",
    "redbiom summarize contexts",
    "redbiom summarize samples",
    "redbiom select samples-from-metadata"
    ]

    # Step 2: Generate command using Code Llama
    prompt = f"""
        You are an assistant that converts natural language questions to valid Redbiom CLI commands.
        Rules:
        1. Only output a single command starting with `redbiom`.
        2. Use ONLY these commands: 
        {ALLOWED_COMMANDS}
        3. Do NOT explain the command or add extra text.

        User input: "{user_query}"
        Output only the command:
        """

    llama_response = ollama.chat(
        model='qwen3:14b-q4_K_M',
        messages=[{"role": "user", "content": prompt}]
    )

    raw_command = llama_response['message']['content']
    pattern = r"<think>.*?</think>"
    raw_command = re.sub(pattern, "", raw_command, flags=re.DOTALL)
    # Remove common thinking tokens and extra text
    cleaned_command = raw_command.replace("Assistant:", "").replace("...", "").strip()

    st.markdown("**LLM Output:**")
    st.code(cleaned_command, language='text')

    # Try to extract the command, but fallback to cleaned output if not found
    match = re.search(r"(redbiom[^\n]*)", cleaned_command)
    if match:
        extracted_command = match.group(1)
    else:
        extracted_command = cleaned_command

    # Store command in session_state only if new query
    if "redbiom_command" not in st.session_state or st.session_state.user_query != user_query:
        st.session_state.redbiom_command = extracted_command
        st.session_state.user_query = user_query

    # Editable text area for the command
    redbiom_command = st.text_area(
        "Review or edit the Redbiom command:",
        value=st.session_state.redbiom_command,
        height=100,
        key="redbiom_command"
    )

    # Run the command
    if st.button("Run This Command"):
        try:
            result = subprocess.run(redbiom_command, shell=True, capture_output=True, text=True, check=True)
            st.success("✅ Command executed successfully!")
            st.text_area("Output", result.stdout, height=300)
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Command failed. Ran command: `{redbiom_command}`")
            st.text_area("Error Output", e.stderr, height=300)