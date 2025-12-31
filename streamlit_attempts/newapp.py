import streamlit as st
import subprocess
import json
import pandas as pd
from pathlib import Path
import tempfile

# has 4 tabs for each step of the workflow

def execute_redbiom_command(command):
    """Execute a redbiom command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=300  # 5 minute timeout
        )
        return True, result.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except subprocess.CalledProcessError as e:
        return False, "", e.stderr
    except Exception as e:
        return False, "", str(e)

def parse_sample_list(output):
    """Parse sample IDs from redbiom output"""
    samples = [line.strip() for line in output.strip().split('\n') if line.strip()]
    return samples

def main():
    st.set_page_config(
        page_title="Qiita Microbiome Data Query", 
        page_icon="🧬", 
        layout="wide"
    )
    
    st.title("🧬 Qiita Microbiome Data Query MVP")
    st.markdown("Query microbiome data from Qiita using redbiom")
    
    # Initialize session state
    if 'samples' not in st.session_state:
        st.session_state.samples = []
    if 'metadata' not in st.session_state:
        st.session_state.metadata = None
    if 'biom_file' not in st.session_state:
        st.session_state.biom_file = None
    
    # Sidebar with context info
    with st.sidebar:
        st.header("⚙️ Configuration")
        context = st.text_input(
            "Context", 
            value="Woltka-per-genome-WoLr2-3ab352",
            help="The redbiom context to query"
        )
        
        st.markdown("---")
        st.markdown("""
        ### 📋 Workflow Steps:
        1. **Enter Study ID** - Specify Qiita study
        2. **Get Samples** - Retrieve sample IDs
        3. **Fetch Metadata** - Get sample metadata
        4. **Get BIOM Table** - Extract feature table
        """)
        
        if st.button("🗑️ Clear All Data"):
            st.session_state.samples = []
            st.session_state.metadata = None
            st.session_state.biom_file = None
            st.rerun()
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ Query Samples", 
        "2️⃣ View Samples", 
        "3️⃣ Get Metadata", 
        "4️⃣ Get BIOM Table"
    ])
    
    # Tab 1: Query Samples
    with tab1:
        st.header("Step 1: Query Samples from Study")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            study_id = st.text_input(
                "Enter Qiita Study ID",
                placeholder="e.g., 10317",
                help="Enter the Qiita study ID you want to query"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            query_button = st.button("🔍 Query Samples", type="primary")
        
        if query_button and study_id:
            # Build the search command
            search_query = f"qiita_study_id:{study_id}"
            command = f"redbiom search metadata \"{search_query}\" --context {context}"
            
            st.markdown("**Executing Command:**")
            st.code(command, language="bash")
            
            with st.spinner("Querying samples..."):
                success, stdout, stderr = execute_redbiom_command(command)
                
                if success:
                    samples = parse_sample_list(stdout)
                    st.session_state.samples = samples
                    
                    st.success(f"✅ Found {len(samples)} samples!")
                    
                    with st.expander("View Sample IDs", expanded=False):
                        st.text(stdout)
                else:
                    st.error("❌ Query failed!")
                    st.code(stderr, language="text")
    
    # Tab 2: View Samples
    with tab2:
        st.header("Step 2: View Retrieved Samples")
        
        if st.session_state.samples:
            st.success(f"📊 Total Samples: {len(st.session_state.samples)}")
            
            # Display samples in a dataframe
            df_samples = pd.DataFrame({
                'Sample ID': st.session_state.samples
            })
            
            st.dataframe(df_samples, use_container_width=True, height=400)
            
            # Download option
            csv = df_samples.to_csv(index=False)
            st.download_button(
                label="📥 Download Sample IDs (CSV)",
                data=csv,
                file_name="sample_ids.csv",
                mime="text/csv"
            )
        else:
            st.info("ℹ️ No samples retrieved yet. Please query samples in Step 1.")
    
    # Tab 3: Get Metadata
    with tab3:
        st.header("Step 3: Fetch Sample Metadata")
        
        if not st.session_state.samples:
            st.warning("⚠️ Please query samples first (Step 1)")
        else:
            st.info(f"Ready to fetch metadata for {len(st.session_state.samples)} samples")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                output_file = st.text_input(
                    "Output filename",
                    value="metadata.txt",
                    help="Filename to save metadata"
                )
            
            with col2:
                st.write("")
                st.write("")
                fetch_metadata_button = st.button("📋 Fetch Metadata", type="primary")
            
            if fetch_metadata_button:
                # Create temp file with sample IDs
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    f.write('\n'.join(st.session_state.samples))
                    temp_sample_file = f.name
                
                command = f"redbiom fetch samples --context {context} --from {temp_sample_file} --output {output_file}"
                
                st.markdown("**Executing Command:**")
                st.code(command, language="bash")
                
                with st.spinner("Fetching metadata..."):
                    success, stdout, stderr = execute_redbiom_command(command)
                    
                    if success:
                        st.success("✅ Metadata fetched successfully!")
                        
                        # Try to read and display the metadata
                        try:
                            metadata_df = pd.read_csv(output_file, sep='\t', index_col=0)
                            st.session_state.metadata = metadata_df
                            
                            st.markdown(f"**Metadata shape:** {metadata_df.shape[0]} samples × {metadata_df.shape[1]} columns")
                            
                            st.dataframe(metadata_df, use_container_width=True, height=400)
                            
                            # Download button
                            with open(output_file, 'r') as f:
                                st.download_button(
                                    label="📥 Download Metadata",
                                    data=f.read(),
                                    file_name=output_file,
                                    mime="text/tab-separated-values"
                                )
                        except Exception as e:
                            st.error(f"Error reading metadata file: {str(e)}")
                            st.code(stdout, language="text")
                    else:
                        st.error("❌ Failed to fetch metadata!")
                        st.code(stderr, language="text")
                
                # Cleanup temp file
                Path(temp_sample_file).unlink(missing_ok=True)
    
    # Tab 4: Get BIOM Table
    with tab4:
        st.header("Step 4: Get BIOM Table")
        
        if not st.session_state.samples:
            st.warning("⚠️ Please query samples first (Step 1)")
        else:
            st.info(f"Ready to fetch BIOM table for {len(st.session_state.samples)} samples")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                biom_output = st.text_input(
                    "Output BIOM filename",
                    value="feature_table.biom",
                    help="Filename to save BIOM table"
                )
            
            with col2:
                st.write("")
                st.write("")
                fetch_biom_button = st.button("🧬 Fetch BIOM", type="primary")
            
            if fetch_biom_button:
                # Create temp file with sample IDs
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    f.write('\n'.join(st.session_state.samples))
                    temp_sample_file = f.name
                
                command = f"redbiom fetch sample-metadata --context {context} --from {temp_sample_file} --output {biom_output}"
                
                st.markdown("**Executing Command:**")
                st.code(command, language="bash")
                
                with st.spinner("Fetching BIOM table..."):
                    success, stdout, stderr = execute_redbiom_command(command)
                    
                    if success:
                        st.success("✅ BIOM table fetched successfully!")
                        st.session_state.biom_file = biom_output
                        
                        # Show file info
                        file_size = Path(biom_output).stat().st_size
                        st.markdown(f"**File created:** `{biom_output}` ({file_size:,} bytes)")
                        
                        # Download button
                        with open(biom_output, 'rb') as f:
                            st.download_button(
                                label="📥 Download BIOM Table",
                                data=f.read(),
                                file_name=biom_output,
                                mime="application/octet-stream"
                            )
                        
                        st.code(stdout, language="text")
                    else:
                        st.error("❌ Failed to fetch BIOM table!")
                        st.code(stderr, language="text")
                
                # Cleanup temp file
                Path(temp_sample_file).unlink(missing_ok=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🧬 Qiita Microbiome Data Query MVP - Powered by Redbiom
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()