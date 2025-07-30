# streamlit_redbiom_app.py

import streamlit as st
import redbiom.search as search
import nltk
nltk.download('punkt')
import subprocess

st.title("🔬 Redbiom Natural Language Explorer")

query = st.text_input("Ask a microbiome question (e.g., 'samples with antibiotics'):")

if query:
    # Create the command from the query
    cmd = f'redbiom search metadata "{query}"'
    
    st.code(cmd, language='bash')

    
    if st.button("Run Command"):
        try:
            # Run the command and capture output
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            st.success("Command executed successfully!")
            st.text_area("Output", result.stdout, height=300)
        except subprocess.CalledProcessError as e:
            st.error("Command failed.")
            st.text_area("Error Output", e.stderr, height=300)