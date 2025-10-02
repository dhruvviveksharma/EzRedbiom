# import streamlit as st
# import subprocess
# import os
# from pathlib import Path
# from datetime import datetime
# import pandas as pd

# def initialize_session_state():
#     """Initialize session state for workflow tracking"""
#     if 'workflow_state' not in st.session_state:
#         st.session_state.workflow_state = {
#             'current_step': 0,
#             'completed_steps': [],
#             'study_id': '',
#             'context': 'Woltka-per-genome-WoLr2-3ab352',
#             'sample_file': '',
#             'metadata_file': '',
#             'biom_file': '',
#             'step_outputs': {},
#             'command_history': []
#         }

# def execute_command(command, description=""):
#     """Execute a shell command and return results"""
#     try:
#         st.info(f"🔄 Executing: {description}")
#         result = subprocess.run(
#             command,
#             shell=True,
#             capture_output=True,
#             text=True,
#             timeout=300,  # 5 minute timeout
#             cwd=os.getcwd()  # Execute in current directory
#         )
        
#         if result.returncode == 0:
#             return True, result.stdout, result.stderr
#         else:
#             return False, result.stdout, result.stderr
            
#     except subprocess.TimeoutExpired:
#         return False, "", "Command timed out after 5 minutes"
#     except Exception as e:
#         return False, "", str(e)

# def check_file_exists(filepath):
#     """Check if a file exists and return its info"""
#     if filepath and Path(filepath).exists():
#         file_size = Path(filepath).stat().st_size
#         return True, file_size
#     return False, 0

# def count_lines_in_file(filepath):
#     """Count non-empty lines in a file"""
#     try:
#         with open(filepath, 'r') as f:
#             return len([line for line in f if line.strip()])
#     except:
#         return 0

# def main():
#     st.set_page_config(
#         page_title="Qiita Microbiome Workflow", 
#         page_icon="🧬", 
#         layout="wide"
#     )
    
#     st.title("🧬 Qiita Microbiome Data Workflow")
#     st.markdown("*Interactive workflow for querying microbiome data - executes commands locally*")
    
#     initialize_session_state()
#     ws = st.session_state.workflow_state
    
#     # Display current working directory
#     st.info(f"💾 **Working Directory:** `{os.getcwd()}`")
    
#     # Sidebar - Workflow Overview
#     with st.sidebar:
#         st.header("📋 Workflow Steps")
        
#         steps = [
#             ("1️⃣", "Query Samples", "Get sample IDs from study"),
#             ("2️⃣", "Verify Samples", "Check retrieved samples"),
#             ("3️⃣", "Fetch Metadata", "Get sample metadata"),
#             ("4️⃣", "Get BIOM Table", "Extract feature table")
#         ]
        
#         for idx, (emoji, title, desc) in enumerate(steps):
#             if idx in ws['completed_steps']:
#                 st.success(f"{emoji} ✓ {title}")
#             elif idx == ws['current_step']:
#                 st.info(f"{emoji} → {title}")
#             else:
#                 st.text(f"{emoji} {title}")
        
#         st.markdown("---")
#         st.markdown(f"**Context:** `{ws['context']}`")
        
#         # Show command history
#         if ws['command_history']:
#             with st.expander("📜 Command History"):
#                 for i, cmd in enumerate(ws['command_history'], 1):
#                     st.caption(f"{i}. `{cmd}`")
        
#         if st.button("🔄 Reset Workflow"):
#             st.session_state.workflow_state = {
#                 'current_step': 0,
#                 'completed_steps': [],
#                 'study_id': '',
#                 'context': 'Woltka-per-genome-WoLr2-3ab352',
#                 'sample_file': '',
#                 'metadata_file': '',
#                 'biom_file': '',
#                 'step_outputs': {},
#                 'command_history': []
#             }
#             st.rerun()
    
#     # Main content area
#     current_step = ws['current_step']
    
#     # Progress bar
#     progress = len(ws['completed_steps']) / len(steps)
#     st.progress(progress)
#     st.markdown(f"**Progress:** {len(ws['completed_steps'])}/{len(steps)} steps completed")
#     st.markdown("---")
    
#     # Step 1: Query Samples
#     if current_step == 0:
#         st.header("1️⃣ Step 1: Query Samples from Qiita Study")
        
#         st.markdown("""
#         Search for samples from a specific Qiita study ID within the microbiome database.
#         """)
        
#         col1, col2 = st.columns([2, 1])
#         with col1:
#             study_id = st.text_input(
#                 "Enter Qiita Study ID",
#                 value=ws['study_id'],
#                 placeholder="e.g., 10317",
#                 help="The Qiita study ID you want to query"
#             )
#             ws['study_id'] = study_id
        
#         with col2:
#             sample_output = st.text_input(
#                 "Output filename",
#                 value="samples.txt",
#                 help="File to save sample IDs"
#             )
        
#         if study_id:
#             st.markdown("### 📝 Command Preview")
            
#             search_query = f"qiita_study_id:{study_id}"
#             command = f'redbiom search metadata "{search_query}" --context {ws["context"]} > {sample_output}'
            
#             st.code(command, language="bash")
            
#             st.markdown("### ℹ️ What this does:")
#             st.info(f"""
#             - Searches for all samples in study **{study_id}**
#             - Uses context: `{ws['context']}`
#             - Saves sample IDs to: `{sample_output}`
#             """)
            
#             col1, col2 = st.columns([3, 1])
            
#             with col2:
#                 if st.button("▶️ Run Command", type="primary", key="run_step1"):
#                     with st.spinner("Executing command..."):
#                         success, stdout, stderr = execute_command(command, "Querying samples")
                        
#                         if success or Path(sample_output).exists():
#                             ws['command_history'].append(command)
#                             file_exists, file_size = check_file_exists(sample_output)
                            
#                             if file_exists:
#                                 sample_count = count_lines_in_file(sample_output)
#                                 st.success(f"✅ Successfully retrieved {sample_count} samples!")
#                                 st.session_state.temp_success = True
#                                 ws['sample_file'] = sample_output
#                             else:
#                                 st.error("❌ Command executed but output file not found")
#                                 if stderr:
#                                     st.code(stderr, language="text")
#                         else:
#                             st.error("❌ Command failed!")
#                             if stderr:
#                                 with st.expander("Error Details"):
#                                     st.code(stderr, language="text")
#                             if stdout:
#                                 with st.expander("Output"):
#                                     st.code(stdout, language="text")
            
#             # Show results if file exists
#             file_exists, file_size = check_file_exists(sample_output)
#             if file_exists:
#                 col1.success(f"✓ File created: `{sample_output}` ({file_size:,} bytes)")
#                 sample_count = count_lines_in_file(sample_output)
#                 col1.metric("Samples Found", sample_count)
                
#                 if st.button("Next Step →", type="primary"):
#                     ws['sample_file'] = sample_output
#                     ws['completed_steps'].append(0)
#                     ws['current_step'] = 1
#                     st.rerun()
    
#     # Step 2: Verify Samples
#     elif current_step == 1:
#         st.header("2️⃣ Step 2: Verify Retrieved Samples")
        
#         st.markdown("""
#         Let's verify the samples were retrieved correctly.
#         """)
        
#         sample_file = ws['sample_file']
#         file_exists, file_size = check_file_exists(sample_file)
        
#         if file_exists:
#             st.success(f"✓ Sample file loaded: `{sample_file}` ({file_size:,} bytes)")
            
#             try:
#                 with open(sample_file, 'r') as f:
#                     samples = [line.strip() for line in f if line.strip()]
                
#                 st.metric("Total Samples", len(samples))
                
#                 st.markdown("### 📋 Sample Preview")
#                 with st.expander("View first 20 samples"):
#                     for i, sample in enumerate(samples[:20], 1):
#                         st.text(f"{i}. {sample}")
                
#                 st.markdown("### 📊 Sample Statistics")
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     st.metric("First Sample ID", samples[0] if samples else "N/A")
#                 with col2:
#                     st.metric("Last Sample ID", samples[-1] if samples else "N/A")
                
#                 col1, col2 = st.columns([3, 1])
#                 with col2:
#                     if st.button("Next Step →", type="primary"):
#                         ws['completed_steps'].append(1)
#                         ws['current_step'] = 2
#                         st.rerun()
#                 with col1:
#                     if st.button("← Back"):
#                         ws['current_step'] = 0
#                         st.rerun()
                
#             except Exception as e:
#                 st.error(f"Error reading sample file: {str(e)}")
#                 st.markdown("**The file might be corrupted or empty.**")
#         else:
#             st.error(f"❌ Sample file not found: `{sample_file}`")
#             st.markdown("Please complete Step 1 first.")
#             if st.button("← Back to Step 1"):
#                 ws['current_step'] = 0
#                 st.rerun()
    
#     # Step 3: Fetch Metadata
#     elif current_step == 2:
#         st.header("3️⃣ Step 3: Fetch Sample Metadata")
        
#         st.markdown("""
#         Retrieve the metadata (experimental conditions, host info, etc.) for your samples.
#         """)
        
#         metadata_output = st.text_input(
#             "Metadata output filename",
#             value="metadata.tsv",
#             help="File to save metadata"
#         )
        
#         st.markdown("### 📝 Command Preview")
        
#         command = f'redbiom fetch sample-metadata --from {ws["sample_file"]} --context {ws["context"]} --output {metadata_output} --all-columns'
        
#         st.code(command, language="bash")
        
#         st.markdown("### ℹ️ What this does:")
#         st.info(f"""
#         - Reads sample IDs from: `{ws['sample_file']}`
#         - Fetches all metadata columns for these samples
#         - Saves metadata to: `{metadata_output}`
#         - Uses context: `{ws['context']}`
#         """)
        
#         st.warning("⚠️ This command may take a few minutes depending on sample count")
        
#         col1, col2 = st.columns([3, 1])
        
#         with col2:
#             if st.button("▶️ Run Command", type="primary", key="run_step3"):
#                 with st.spinner("Fetching metadata... This may take a few minutes"):
#                     success, stdout, stderr = execute_command(command, "Fetching metadata")
                    
#                     if success or Path(metadata_output).exists():
#                         ws['command_history'].append(command)
#                         file_exists, file_size = check_file_exists(metadata_output)
                        
#                         if file_exists:
#                             st.success(f"✅ Metadata retrieved successfully!")
#                             ws['metadata_file'] = metadata_output
#                         else:
#                             st.error("❌ Command executed but output file not found")
#                             if stderr:
#                                 st.code(stderr, language="text")
#                     else:
#                         st.error("❌ Command failed!")
#                         if stderr:
#                             with st.expander("Error Details"):
#                                 st.code(stderr, language="text")
        
#         # Show results if file exists
#         file_exists, file_size = check_file_exists(metadata_output)
#         if file_exists:
#             col1.success(f"✓ File created: `{metadata_output}` ({file_size:,} bytes)")
            
#             try:
#                 df = pd.read_csv(metadata_output, sep='\t', nrows=5)
#                 col1.markdown(f"**Metadata columns:** {len(df.columns)}")
#                 with st.expander("Preview metadata (first 5 rows)"):
#                     st.dataframe(df)
#             except Exception as e:
#                 st.info(f"Preview unavailable: {str(e)}")
            
#             col1, col2 = st.columns([3, 1])
#             with col1:
#                 if st.button("← Back"):
#                     ws['current_step'] = 1
#                     st.rerun()
#             with col2:
#                 if st.button("Next Step →", type="primary"):
#                     ws['metadata_file'] = metadata_output
#                     ws['completed_steps'].append(2)
#                     ws['current_step'] = 3
#                     st.rerun()
    
#     # Step 4: Get BIOM Table
#     elif current_step == 3:
#         st.header("4️⃣ Step 4: Get BIOM Feature Table")
        
#         st.markdown("""
#         Retrieve the actual feature table (BIOM format) containing the abundance data.
#         """)
        
#         biom_output = st.text_input(
#             "BIOM output filename",
#             value="feature_table.biom",
#             help="File to save BIOM table"
#         )
        
#         st.markdown("### 📝 Command Preview")
        
#         command = f'redbiom fetch samples --from {ws["sample_file"]} --context {ws["context"]} --output {biom_output}'
        
#         st.code(command, language="bash")
        
#         st.markdown("### ℹ️ What this does:")
#         st.info(f"""
#         - Reads sample IDs from: `{ws['sample_file']}`
#         - Fetches feature abundance data for these samples
#         - Saves BIOM table to: `{biom_output}`
#         - Uses context: `{ws['context']}`
#         """)
        
#         st.warning("⚠️ This command may take several minutes for large sample sets")
        
#         col1, col2 = st.columns([3, 1])
        
#         with col2:
#             if st.button("▶️ Run Command", type="primary", key="run_step4"):
#                 with st.spinner("Fetching BIOM table... This may take several minutes"):
#                     success, stdout, stderr = execute_command(command, "Fetching BIOM table")
                    
#                     if success or Path(biom_output).exists():
#                         ws['command_history'].append(command)
#                         file_exists, file_size = check_file_exists(biom_output)
                        
#                         if file_exists:
#                             st.success(f"✅ BIOM table retrieved successfully!")
#                             ws['biom_file'] = biom_output
#                         else:
#                             st.error("❌ Command executed but output file not found")
#                             if stderr:
#                                 st.code(stderr, language="text")
#                     else:
#                         st.error("❌ Command failed!")
#                         if stderr:
#                             with st.expander("Error Details"):
#                                 st.code(stderr, language="text")
        
#         # Show results if file exists
#         file_exists, file_size = check_file_exists(biom_output)
#         if file_exists:
#             col1.success(f"✓ File created: `{biom_output}` ({file_size / (1024*1024):.2f} MB)")
            
#             col1, col2 = st.columns([3, 1])
#             with col1:
#                 if st.button("← Back"):
#                     ws['current_step'] = 2
#                     st.rerun()
#             with col2:
#                 if st.button("✓ Complete", type="primary"):
#                     ws['biom_file'] = biom_output
#                     ws['completed_steps'].append(3)
#                     ws['current_step'] = 4
#                     st.rerun()
    
#     # Completion screen
#     elif current_step == 4:
#         st.header("🎉 Workflow Complete!")
        
#         st.success("All steps have been completed successfully!")
        
#         st.markdown("### 📦 Generated Files")
#         st.markdown(f"**Location:** `{os.getcwd()}`")
        
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.markdown("#### 📄 Samples")
#             if ws['sample_file']:
#                 exists, size = check_file_exists(ws['sample_file'])
#                 if exists:
#                     st.success(f"✓ `{ws['sample_file']}`")
#                     st.caption(f"{size:,} bytes")
#                     sample_count = count_lines_in_file(ws['sample_file'])
#                     st.caption(f"{sample_count} samples")
        
#         with col2:
#             st.markdown("#### 📊 Metadata")
#             if ws['metadata_file']:
#                 exists, size = check_file_exists(ws['metadata_file'])
#                 if exists:
#                     st.success(f"✓ `{ws['metadata_file']}`")
#                     st.caption(f"{size:,} bytes")
        
#         with col3:
#             st.markdown("#### 🧬 BIOM Table")
#             if ws['biom_file']:
#                 exists, size = check_file_exists(ws['biom_file'])
#                 if exists:
#                     st.success(f"✓ `{ws['biom_file']}`")
#                     st.caption(f"{size / (1024*1024):.2f} MB")
        
#         st.markdown("### 🎯 Next Steps")
#         st.info("""
#         **You can now:**
#         1. Import the BIOM table into QIIME 2 for analysis
#         2. Analyze the metadata to understand your sample cohort
#         3. Convert BIOM to TSV: `biom convert -i feature_table.biom -o table.tsv --to-tsv`
#         4. Start a new workflow with a different study
#         """)
        
#         # Show all commands used
#         if ws['command_history']:
#             with st.expander("📜 View All Commands Used"):
#                 for i, cmd in enumerate(ws['command_history'], 1):
#                     st.code(f"{i}. {cmd}", language="bash")
        
#         if st.button("🔄 Start New Workflow"):
#             st.session_state.workflow_state = {
#                 'current_step': 0,
#                 'completed_steps': [],
#                 'study_id': '',
#                 'context': 'Woltka-per-genome-WoLr2-3ab352',
#                 'sample_file': '',
#                 'metadata_file': '',
#                 'biom_file': '',
#                 'step_outputs': {},
#                 'command_history': []
#             }
#             st.rerun()
    
#     # Footer
#     st.markdown("---")
#     st.markdown("""
#     <div style='text-align: center; color: #666; font-size: 0.8em;'>
#         🧬 Qiita Microbiome Workflow - Local Execution Mode
#     </div>
#     """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()

########################################################################################################################################



# import streamlit as st
# import subprocess
# import os
# from pathlib import Path
# from datetime import datetime
# import pandas as pd

# def initialize_session_state():
#     """Initialize session state for workflow tracking"""
#     if 'workflow_state' not in st.session_state:
#         st.session_state.workflow_state = {
#             'current_step': 0,
#             'completed_steps': [],
#             'study_id': '',
#             'context': 'Woltka-per-genome-WoLr2-3ab352',
#             'sample_file': '',
#             'metadata_file': '',
#             'biom_file': '',
#             'step_outputs': {},
#             'command_history': []
#         }

# def execute_command(command, description=""):
#     """Execute a shell command and return results"""
#     try:
#         st.info(f"🔄 Executing: {description}")
#         result = subprocess.run(
#             command,
#             shell=True,
#             capture_output=True,
#             text=True,
#             timeout=300,  # 5 minute timeout
#             cwd=os.getcwd()  # Execute in current directory
#         )
        
#         if result.returncode == 0:
#             return True, result.stdout, result.stderr
#         else:
#             return False, result.stdout, result.stderr
            
#     except subprocess.TimeoutExpired:
#         return False, "", "Command timed out after 5 minutes"
#     except Exception as e:
#         return False, "", str(e)

# def check_file_exists(filepath):
#     """Check if a file exists and return its info"""
#     if filepath and Path(filepath).exists():
#         file_size = Path(filepath).stat().st_size
#         return True, file_size
#     return False, 0

# def count_lines_in_file(filepath):
#     """Count non-empty lines in a file"""
#     try:
#         with open(filepath, 'r') as f:
#             return len([line for line in f if line.strip()])
#     except:
#         return 0

# def main():
#     st.set_page_config(
#         page_title="Qiita Microbiome Workflow", 
#         page_icon="🧬", 
#         layout="wide"
#     )
    
#     st.title("🧬 Qiita Microbiome Data Workflow")
#     st.markdown("*Interactive workflow for querying microbiome data - executes commands locally*")
    
#     initialize_session_state()
#     ws = st.session_state.workflow_state
    
#     # Display current working directory
#     st.info(f"💾 **Working Directory:** `{os.getcwd()}`")
    
#     # Sidebar - Workflow Overview
#     with st.sidebar:
#         st.header("📋 Workflow Steps")
        
#         steps = [
#             ("1️⃣", "Query Samples", "Get sample IDs from study"),
#             ("2️⃣", "Verify Samples", "Check retrieved samples"),
#             ("3️⃣", "Fetch Metadata", "Get sample metadata"),
#             ("4️⃣", "Get BIOM Table", "Extract feature table")
#         ]
        
#         for idx, (emoji, title, desc) in enumerate(steps):
#             if idx in ws['completed_steps']:
#                 st.success(f"{emoji} ✓ {title}")
#             elif idx == ws['current_step']:
#                 st.info(f"{emoji} → {title}")
#             else:
#                 st.text(f"{emoji} {title}")
        
#         st.markdown("---")
#         st.markdown(f"**Context:** `{ws['context']}`")
        
#         # Show command history
#         if ws['command_history']:
#             with st.expander("📜 Command History"):
#                 for i, cmd in enumerate(ws['command_history'], 1):
#                     st.caption(f"{i}. `{cmd}`")
        
#         if st.button("🔄 Reset Workflow"):
#             st.session_state.workflow_state = {
#                 'current_step': 0,
#                 'completed_steps': [],
#                 'study_id': '',
#                 'context': 'Woltka-per-genome-WoLr2-3ab352',
#                 'sample_file': '',
#                 'metadata_file': '',
#                 'biom_file': '',
#                 'step_outputs': {},
#                 'command_history': []
#             }
#             st.rerun()
    
#     # Main content area
#     current_step = ws['current_step']
    
#     # Progress bar
#     progress = len(ws['completed_steps']) / len(steps)
#     st.progress(progress)
#     st.markdown(f"**Progress:** {len(ws['completed_steps'])}/{len(steps)} steps completed")
#     st.markdown("---")
    
#     # Step 1: Query Samples
#     if current_step == 0:
#         st.header("1️⃣ Step 1: Query Samples from Qiita Study")
        
#         st.markdown("""
#         Search for samples from a specific Qiita study ID within the microbiome database.
#         """)
        
#         col1, col2 = st.columns([2, 1])
#         with col1:
#             study_id = st.text_input(
#                 "Enter Qiita Study ID",
#                 value=ws['study_id'],
#                 placeholder="e.g., 10317",
#                 help="The Qiita study ID you want to query"
#             )
#             ws['study_id'] = study_id
        
#         with col2:
#             sample_output = st.text_input(
#                 "Output filename",
#                 value="samples.txt",
#                 help="File to save sample IDs"
#             )
        
#         if study_id:
#             st.markdown("### 📝 Command Preview")
            
#             search_query = f"qiita_study_id:{study_id}"
#             default_command = f'redbiom search metadata "{search_query}" --context {ws["context"]} > {sample_output}'
            
#             # Editable command
#             command = st.text_area(
#                 "Edit command if needed:",
#                 value=default_command,
#                 height=100,
#                 key="edit_cmd_step1",
#                 help="You can modify the command before execution"
#             )
            
#             st.markdown("### ℹ️ What this does:")
#             st.info(f"""
#             - Searches for all samples in study **{study_id}**
#             - Uses context: `{ws['context']}`
#             - Saves sample IDs to: `{sample_output}`
#             """)
            
#             col1, col2 = st.columns([3, 1])
            
#             with col2:
#                 if st.button("▶️ Run Command", type="primary", key="run_step1"):
#                     with st.spinner("Executing command..."):
#                         success, stdout, stderr = execute_command(command, "Querying samples")
                        
#                         if success or Path(sample_output).exists():
#                             ws['command_history'].append(command)
#                             file_exists, file_size = check_file_exists(sample_output)
                            
#                             if file_exists:
#                                 sample_count = count_lines_in_file(sample_output)
#                                 st.success(f"✅ Successfully retrieved {sample_count} samples!")
#                                 st.session_state.temp_success = True
#                                 ws['sample_file'] = sample_output
#                             else:
#                                 st.error("❌ Command executed but output file not found")
#                                 if stderr:
#                                     st.code(stderr, language="text")
#                         else:
#                             st.error("❌ Command failed!")
#                             if stderr:
#                                 with st.expander("Error Details"):
#                                     st.code(stderr, language="text")
#                             if stdout:
#                                 with st.expander("Output"):
#                                     st.code(stdout, language="text")
            
#             # Show results if file exists
#             file_exists, file_size = check_file_exists(sample_output)
#             if file_exists:
#                 col1.success(f"✓ File created: `{sample_output}` ({file_size:,} bytes)")
#                 sample_count = count_lines_in_file(sample_output)
#                 col1.metric("Samples Found", sample_count)
                
#                 if st.button("Next Step →", type="primary"):
#                     ws['sample_file'] = sample_output
#                     ws['completed_steps'].append(0)
#                     ws['current_step'] = 1
#                     st.rerun()
    
#     # Step 2: Verify Samples
#     elif current_step == 1:
#         st.header("2️⃣ Step 2: Verify Retrieved Samples")
        
#         st.markdown("""
#         Let's verify the samples were retrieved correctly.
#         """)
        
#         sample_file = ws['sample_file']
#         file_exists, file_size = check_file_exists(sample_file)
        
#         if file_exists:
#             st.success(f"✓ Sample file loaded: `{sample_file}` ({file_size:,} bytes)")
            
#             try:
#                 with open(sample_file, 'r') as f:
#                     samples = [line.strip() for line in f if line.strip()]
                
#                 st.metric("Total Samples", len(samples))
                
#                 st.markdown("### 📋 Sample Preview")
#                 with st.expander("View first 20 samples"):
#                     for i, sample in enumerate(samples[:20], 1):
#                         st.text(f"{i}. {sample}")
                
#                 st.markdown("### 📊 Sample Statistics")
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     st.metric("First Sample ID", samples[0] if samples else "N/A")
#                 with col2:
#                     st.metric("Last Sample ID", samples[-1] if samples else "N/A")
                
#                 col1, col2 = st.columns([3, 1])
#                 with col2:
#                     if st.button("Next Step →", type="primary"):
#                         ws['completed_steps'].append(1)
#                         ws['current_step'] = 2
#                         st.rerun()
#                 with col1:
#                     if st.button("← Back"):
#                         ws['current_step'] = 0
#                         st.rerun()
                
#             except Exception as e:
#                 st.error(f"Error reading sample file: {str(e)}")
#                 st.markdown("**The file might be corrupted or empty.**")
#         else:
#             st.error(f"❌ Sample file not found: `{sample_file}`")
#             st.markdown("Please complete Step 1 first.")
#             if st.button("← Back to Step 1"):
#                 ws['current_step'] = 0
#                 st.rerun()
    
#     # Step 3: Fetch Metadata
#     elif current_step == 2:
#         st.header("3️⃣ Step 3: Fetch Sample Metadata")
        
#         st.markdown("""
#         Retrieve the metadata (experimental conditions, host info, etc.) for your samples.
#         """)
        
#         metadata_output = st.text_input(
#             "Metadata output filename",
#             value="metadata.tsv",
#             help="File to save metadata"
#         )
        
#         st.markdown("### 📝 Command Preview")
        
#         default_command = f'redbiom fetch sample-metadata --from {ws["sample_file"]} --context {ws["context"]} --output {metadata_output} --all-columns'
        
#         # Editable command
#         command = st.text_area(
#             "Edit command if needed:",
#             value=default_command,
#             height=100,
#             key="edit_cmd_step3",
#             help="You can modify the command before execution"
#         )
        
#         st.markdown("### ℹ️ What this does:")
#         st.info(f"""
#         - Reads sample IDs from: `{ws['sample_file']}`
#         - Fetches all metadata columns for these samples
#         - Saves metadata to: `{metadata_output}`
#         - Uses context: `{ws['context']}`
#         """)
        
#         st.warning("⚠️ This command may take a few minutes depending on sample count")
        
#         col1, col2 = st.columns([3, 1])
        
#         with col2:
#             if st.button("▶️ Run Command", type="primary", key="run_step3"):
#                 with st.spinner("Fetching metadata... This may take a few minutes"):
#                     success, stdout, stderr = execute_command(command, "Fetching metadata")
                    
#                     if success or Path(metadata_output).exists():
#                         ws['command_history'].append(command)
#                         file_exists, file_size = check_file_exists(metadata_output)
                        
#                         if file_exists:
#                             st.success(f"✅ Metadata retrieved successfully!")
#                             ws['metadata_file'] = metadata_output
#                         else:
#                             st.error("❌ Command executed but output file not found")
#                             if stderr:
#                                 st.code(stderr, language="text")
#                     else:
#                         st.error("❌ Command failed!")
#                         if stderr:
#                             with st.expander("Error Details"):
#                                 st.code(stderr, language="text")
        
#         # Show results if file exists
#         file_exists, file_size = check_file_exists(metadata_output)
#         if file_exists:
#             col1.success(f"✓ File created: `{metadata_output}` ({file_size:,} bytes)")
            
#             try:
#                 df = pd.read_csv(metadata_output, sep='\t', nrows=5)
#                 col1.markdown(f"**Metadata columns:** {len(df.columns)}")
#                 with st.expander("Preview metadata (first 5 rows)"):
#                     st.dataframe(df)
#             except Exception as e:
#                 st.info(f"Preview unavailable: {str(e)}")
            
#             col1, col2 = st.columns([3, 1])
#             with col1:
#                 if st.button("← Back"):
#                     ws['current_step'] = 1
#                     st.rerun()
#             with col2:
#                 if st.button("Next Step →", type="primary"):
#                     ws['metadata_file'] = metadata_output
#                     ws['completed_steps'].append(2)
#                     ws['current_step'] = 3
#                     st.rerun()
    
#     # Step 4: Get BIOM Table
#     elif current_step == 3:
#         st.header("4️⃣ Step 4: Get BIOM Feature Table")
        
#         st.markdown("""
#         Retrieve the actual feature table (BIOM format) containing the abundance data.
#         """)
        
#         biom_output = st.text_input(
#             "BIOM output filename",
#             value="feature_table.biom",
#             help="File to save BIOM table"
#         )
        
#         st.markdown("### 📝 Command Preview")
        
#         default_command = f'redbiom fetch samples --from {ws["sample_file"]} --context {ws["context"]} --output {biom_output}'
        
#         # Editable command
#         command = st.text_area(
#             "Edit command if needed:",
#             value=default_command,
#             height=100,
#             key="edit_cmd_step4",
#             help="You can modify the command before execution"
#         )
        
#         st.markdown("### ℹ️ What this does:")
#         st.info(f"""
#         - Reads sample IDs from: `{ws['sample_file']}`
#         - Fetches feature abundance data for these samples
#         - Saves BIOM table to: `{biom_output}`
#         - Uses context: `{ws['context']}`
#         """)
        
#         st.warning("⚠️ This command may take several minutes for large sample sets")
        
#         col1, col2 = st.columns([3, 1])
        
#         with col2:
#             if st.button("▶️ Run Command", type="primary", key="run_step4"):
#                 with st.spinner("Fetching BIOM table... This may take several minutes"):
#                     success, stdout, stderr = execute_command(command, "Fetching BIOM table")
                    
#                     if success or Path(biom_output).exists():
#                         ws['command_history'].append(command)
#                         file_exists, file_size = check_file_exists(biom_output)
                        
#                         if file_exists:
#                             st.success(f"✅ BIOM table retrieved successfully!")
#                             ws['biom_file'] = biom_output
#                         else:
#                             st.error("❌ Command executed but output file not found")
#                             if stderr:
#                                 st.code(stderr, language="text")
#                     else:
#                         st.error("❌ Command failed!")
#                         if stderr:
#                             with st.expander("Error Details"):
#                                 st.code(stderr, language="text")
        
#         # Show results if file exists
#         file_exists, file_size = check_file_exists(biom_output)
#         if file_exists:
#             col1.success(f"✓ File created: `{biom_output}` ({file_size / (1024*1024):.2f} MB)")
            
#             col1, col2 = st.columns([3, 1])
#             with col1:
#                 if st.button("← Back"):
#                     ws['current_step'] = 2
#                     st.rerun()
#             with col2:
#                 if st.button("✓ Complete", type="primary"):
#                     ws['biom_file'] = biom_output
#                     ws['completed_steps'].append(3)
#                     ws['current_step'] = 4
#                     st.rerun()
    
#     # Completion screen
#     elif current_step == 4:
#         st.header("🎉 Workflow Complete!")
        
#         st.success("All steps have been completed successfully!")
        
#         st.markdown("### 📦 Generated Files")
#         st.markdown(f"**Location:** `{os.getcwd()}`")
        
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.markdown("#### 📄 Samples")
#             if ws['sample_file']:
#                 exists, size = check_file_exists(ws['sample_file'])
#                 if exists:
#                     st.success(f"✓ `{ws['sample_file']}`")
#                     st.caption(f"{size:,} bytes")
#                     sample_count = count_lines_in_file(ws['sample_file'])
#                     st.caption(f"{sample_count} samples")
        
#         with col2:
#             st.markdown("#### 📊 Metadata")
#             if ws['metadata_file']:
#                 exists, size = check_file_exists(ws['metadata_file'])
#                 if exists:
#                     st.success(f"✓ `{ws['metadata_file']}`")
#                     st.caption(f"{size:,} bytes")
        
#         with col3:
#             st.markdown("#### 🧬 BIOM Table")
#             if ws['biom_file']:
#                 exists, size = check_file_exists(ws['biom_file'])
#                 if exists:
#                     st.success(f"✓ `{ws['biom_file']}`")
#                     st.caption(f"{size / (1024*1024):.2f} MB")
        
#         st.markdown("### 🎯 Next Steps")
#         st.info("""
#         **You can now:**
#         1. Import the BIOM table into QIIME 2 for analysis
#         2. Analyze the metadata to understand your sample cohort
#         3. Convert BIOM to TSV: `biom convert -i feature_table.biom -o table.tsv --to-tsv`
#         4. Start a new workflow with a different study
#         """)
        
#         # Show all commands used
#         if ws['command_history']:
#             with st.expander("📜 View All Commands Used"):
#                 for i, cmd in enumerate(ws['command_history'], 1):
#                     st.code(f"{i}. {cmd}", language="bash")
        
#         if st.button("🔄 Start New Workflow"):
#             st.session_state.workflow_state = {
#                 'current_step': 0,
#                 'completed_steps': [],
#                 'study_id': '',
#                 'context': 'Woltka-per-genome-WoLr2-3ab352',
#                 'sample_file': '',
#                 'metadata_file': '',
#                 'biom_file': '',
#                 'step_outputs': {},
#                 'command_history': []
#             }
#             st.rerun()
    
#     # Footer
#     st.markdown("---")
#     st.markdown("""
#     <div style='text-align: center; color: #666; font-size: 0.8em;'>
#         🧬 Qiita Microbiome Workflow - Local Execution Mode
#     </div>
#     """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()


#######################################################################################################################################

import streamlit as st
import subprocess
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

def initialize_session_state():
    """Initialize session state for workflow tracking"""
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = {
            'current_step': 0,
            'completed_steps': [],
            'study_id': '',
            'context': 'Woltka-per-genome-WoLr2-3ab352',
            'sample_file': '',
            'metadata_file': '',
            'biom_file': '',
            'step_outputs': {},
            'command_history': []
        }

def execute_command(command, description=""):
    """Execute a shell command and return results"""
    try:
        st.info(f"🔄 Executing: {description}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=os.getcwd()  # Execute in current directory
        )
        
        if result.returncode == 0:
            return True, result.stdout, result.stderr
        else:
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except Exception as e:
        return False, "", str(e)

def check_file_exists(filepath):
    """Check if a file exists and return its info"""
    if filepath and Path(filepath).exists():
        file_size = Path(filepath).stat().st_size
        return True, file_size
    return False, 0

def count_lines_in_file(filepath):
    """Count non-empty lines in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return len([line for line in f if line.strip()])
    except:
        return 0

def clean_file_encoding(filepath):
    """Clean files with invalid bytes and encoding issues"""
    try:
        # Read with error handling for bad bytes
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Decode with error handling - ignore/replace bad bytes
        cleaned_content = content.decode('utf-8', errors='ignore')
        
        # Remove null bytes and other control characters (except newlines and tabs)
        cleaned_content = ''.join(char for char in cleaned_content 
                                 if char.isprintable() or char in '\n\t\r')
        
        # Write back cleaned content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        return True, "File cleaned successfully"
    except Exception as e:
        return False, f"Error cleaning file: {str(e)}"

def safe_read_file(filepath, nrows=None):
    """Safely read files with potential encoding issues"""
    try:
        # Try UTF-8 first
        df = pd.read_csv(filepath, sep='\t', nrows=nrows, encoding='utf-8')
        return df, None
    except UnicodeDecodeError:
        try:
            # Try latin-1 as fallback
            df = pd.read_csv(filepath, sep='\t', nrows=nrows, encoding='latin-1')
            return df, "Warning: File read with latin-1 encoding"
        except:
            try:
                # Try with error handling
                df = pd.read_csv(filepath, sep='\t', nrows=nrows, encoding='utf-8', errors='ignore')
                return df, "Warning: Some characters were ignored due to encoding issues"
            except Exception as e:
                return None, f"Error reading file: {str(e)}"
    except Exception as e:
        return None, f"Error reading file: {str(e)}"

def main():
    st.set_page_config(
        page_title="Qiita Microbiome Workflow", 
        page_icon="🧬", 
        layout="wide"
    )
    
    st.title("🧬 Qiita Microbiome Data Workflow")
    st.markdown("*Interactive workflow for querying microbiome data - executes commands locally*")
    
    initialize_session_state()
    ws = st.session_state.workflow_state
    
    # Display current working directory
    st.info(f"💾 **Working Directory:** `{os.getcwd()}`")
    
    # Sidebar - Workflow Overview
    with st.sidebar:
        st.header("📋 Workflow Steps")
        
        steps = [
            ("1️⃣", "Query Samples", "Get sample IDs from study"),
            ("2️⃣", "Verify Samples", "Check retrieved samples"),
            ("3️⃣", "Fetch Metadata", "Get sample metadata"),
            ("4️⃣", "Get BIOM Table", "Extract feature table")
        ]
        
        for idx, (emoji, title, desc) in enumerate(steps):
            if idx in ws['completed_steps']:
                st.success(f"{emoji} ✓ {title}")
            elif idx == ws['current_step']:
                st.info(f"{emoji} → {title}")
            else:
                st.text(f"{emoji} {title}")
        
        st.markdown("---")
        st.markdown(f"**Context:** `{ws['context']}`")
        
        # Show command history
        if ws['command_history']:
            with st.expander("📜 Command History"):
                for i, cmd in enumerate(ws['command_history'], 1):
                    st.caption(f"{i}. `{cmd}`")
        
        if st.button("🔄 Reset Workflow"):
            st.session_state.workflow_state = {
                'current_step': 0,
                'completed_steps': [],
                'study_id': '',
                'context': 'Woltka-per-genome-WoLr2-3ab352',
                'sample_file': '',
                'metadata_file': '',
                'biom_file': '',
                'step_outputs': {},
                'command_history': []
            }
            st.rerun()
    
    # Main content area
    current_step = ws['current_step']
    
    # Progress bar
    progress = len(ws['completed_steps']) / len(steps)
    st.progress(progress)
    st.markdown(f"**Progress:** {len(ws['completed_steps'])}/{len(steps)} steps completed")
    st.markdown("---")
    
    # Step 1: Query Samples
    if current_step == 0:
        st.header("1️⃣ Step 1: Query Samples from Qiita Study")
        
        st.markdown("""
        Search for samples from a specific Qiita study ID within the microbiome database.
        """)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            study_id = st.text_input(
                "Enter Qiita Study ID",
                value=ws['study_id'],
                placeholder="e.g., 10317",
                help="The Qiita study ID you want to query"
            )
            ws['study_id'] = study_id
        
        with col2:
            sample_output = st.text_input(
                "Output filename",
                value="samples.txt",
                help="File to save sample IDs"
            )
        
        if study_id:
            st.markdown("### 📝 Command Preview")
            
            search_query = f"qiita_study_id:{study_id}"
            default_command = f'redbiom search metadata "{search_query}" --context {ws["context"]} > {sample_output}'
            
            # Editable command
            command = st.text_area(
                "Edit command if needed:",
                value=default_command,
                height=100,
                key="edit_cmd_step1",
                help="You can modify the command before execution"
            )
            
            st.markdown("### ℹ️ What this does:")
            st.info(f"""
            - Searches for all samples in study **{study_id}**
            - Uses context: `{ws['context']}`
            - Saves sample IDs to: `{sample_output}`
            """)
            
            col1, col2 = st.columns([3, 1])
            
            with col2:
                if st.button("▶️ Run Command", type="primary", key="run_step1"):
                    with st.spinner("Executing command..."):
                        success, stdout, stderr = execute_command(command, "Querying samples")
                        
                        if success or Path(sample_output).exists():
                            ws['command_history'].append(command)
                            file_exists, file_size = check_file_exists(sample_output)
                            
                            if file_exists:
                                sample_count = count_lines_in_file(sample_output)
                                st.success(f"✅ Successfully retrieved {sample_count} samples!")
                                st.session_state.temp_success = True
                                ws['sample_file'] = sample_output
                            else:
                                st.error("❌ Command executed but output file not found")
                                if stderr:
                                    st.code(stderr, language="text")
                        else:
                            st.error("❌ Command failed!")
                            if stderr:
                                with st.expander("Error Details"):
                                    st.code(stderr, language="text")
                            if stdout:
                                with st.expander("Output"):
                                    st.code(stdout, language="text")
            
            # Show results if file exists
            file_exists, file_size = check_file_exists(sample_output)
            if file_exists:
                col1.success(f"✓ File created: `{sample_output}` ({file_size:,} bytes)")
                sample_count = count_lines_in_file(sample_output)
                col1.metric("Samples Found", sample_count)
                
                if st.button("Next Step →", type="primary"):
                    ws['sample_file'] = sample_output
                    ws['completed_steps'].append(0)
                    ws['current_step'] = 1
                    st.rerun()
    
    # Step 2: Verify Samples
    elif current_step == 1:
        st.header("2️⃣ Step 2: Verify Retrieved Samples")
        
        st.markdown("""
        Let's verify the samples were retrieved correctly.
        """)
        
        sample_file = ws['sample_file']
        file_exists, file_size = check_file_exists(sample_file)
        
        if file_exists:
            st.success(f"✓ Sample file loaded: `{sample_file}` ({file_size:,} bytes)")
            
            # Add cleaning option
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🧹 Clean File", help="Remove invalid bytes and encoding issues"):
                    with st.spinner("Cleaning file..."):
                        success, message = clean_file_encoding(sample_file)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            try:
                with open(sample_file, 'r', encoding='utf-8', errors='ignore') as f:
                    samples = [line.strip() for line in f if line.strip() and not line.startswith('PK')]
                
                # Filter out lines that look like binary data
                samples = [s for s in samples if len(s) > 5 and s.replace('.', '').replace('_', '').replace('-', '').isalnum()]
                
                st.metric("Total Samples", len(samples))
                
                st.markdown("### 📋 Sample Preview")
                with st.expander("View first 20 samples"):
                    for i, sample in enumerate(samples[:20], 1):
                        st.text(f"{i}. {sample}")
                
                st.markdown("### 📊 Sample Statistics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("First Sample ID", samples[0] if samples else "N/A")
                with col2:
                    st.metric("Last Sample ID", samples[-1] if samples else "N/A")
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("Next Step →", type="primary"):
                        ws['completed_steps'].append(1)
                        ws['current_step'] = 2
                        st.rerun()
                with col1:
                    if st.button("← Back"):
                        ws['current_step'] = 0
                        st.rerun()
                
            except Exception as e:
                st.error(f"Error reading sample file: {str(e)}")
                st.markdown("**The file might be corrupted or empty.**")
        else:
            st.error(f"❌ Sample file not found: `{sample_file}`")
            st.markdown("Please complete Step 1 first.")
            if st.button("← Back to Step 1"):
                ws['current_step'] = 0
                st.rerun()
    
    # Step 3: Fetch Metadata
    elif current_step == 2:
        st.header("3️⃣ Step 3: Fetch Sample Metadata")
        
        st.markdown("""
        Retrieve the metadata (experimental conditions, host info, etc.) for your samples.
        """)
        
        metadata_output = st.text_input(
            "Metadata output filename",
            value="metadata.tsv",
            help="File to save metadata"
        )
        
        st.markdown("### 📝 Command Preview")
        
        default_command = f'redbiom fetch sample-metadata --from {ws["sample_file"]} --context {ws["context"]} --output {metadata_output} --all-columns'
        
        # Editable command
        command = st.text_area(
            "Edit command if needed:",
            value=default_command,
            height=100,
            key="edit_cmd_step3",
            help="You can modify the command before execution"
        )
        
        st.markdown("### ℹ️ What this does:")
        st.info(f"""
        - Reads sample IDs from: `{ws['sample_file']}`
        - Fetches all metadata columns for these samples
        - Saves metadata to: `{metadata_output}`
        - Uses context: `{ws['context']}`
        """)
        
        st.warning("⚠️ This command may take a few minutes depending on sample count")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("▶️ Run Command", type="primary", key="run_step3"):
                with st.spinner("Fetching metadata... This may take a few minutes"):
                    success, stdout, stderr = execute_command(command, "Fetching metadata")
                    
                    if success or Path(metadata_output).exists():
                        ws['command_history'].append(command)
                        file_exists, file_size = check_file_exists(metadata_output)
                        
                        if file_exists:
                            st.success(f"✅ Metadata retrieved successfully!")
                            ws['metadata_file'] = metadata_output
                        else:
                            st.error("❌ Command executed but output file not found")
                            if stderr:
                                st.code(stderr, language="text")
                    else:
                        st.error("❌ Command failed!")
                        if stderr:
                            with st.expander("Error Details"):
                                st.code(stderr, language="text")
        
        # Show results if file exists
        file_exists, file_size = check_file_exists(metadata_output)
        if file_exists:
            col1.success(f"✓ File created: `{metadata_output}` ({file_size:,} bytes)")
            
            # Add cleaning option
            col_clean1, col_clean2 = st.columns([3, 1])
            with col_clean2:
                if st.button("🧹 Clean File", key="clean_metadata", help="Remove invalid bytes and encoding issues"):
                    with st.spinner("Cleaning file..."):
                        success, message = clean_file_encoding(metadata_output)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            try:
                df, warning = safe_read_file(metadata_output, nrows=5)
                if df is not None:
                    if warning:
                        st.warning(warning)
                    col1.markdown(f"**Metadata columns:** {len(df.columns)}")
                    with st.expander("Preview metadata (first 5 rows)"):
                        st.dataframe(df)
                else:
                    st.error(warning)
            except Exception as e:
                st.info(f"Preview unavailable: {str(e)}")
                st.info("💡 Try clicking the 'Clean File' button to fix encoding issues")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("← Back"):
                    ws['current_step'] = 1
                    st.rerun()
            with col2:
                if st.button("Next Step →", type="primary"):
                    ws['metadata_file'] = metadata_output
                    ws['completed_steps'].append(2)
                    ws['current_step'] = 3
                    st.rerun()
    
    # Step 4: Get BIOM Table
    elif current_step == 3:
        st.header("4️⃣ Step 4: Get BIOM Feature Table")
        
        st.markdown("""
        Retrieve the actual feature table (BIOM format) containing the abundance data.
        """)
        
        biom_output = st.text_input(
            "BIOM output filename",
            value="feature_table.biom",
            help="File to save BIOM table"
        )
        
        st.markdown("### 📝 Command Preview")
        
        default_command = f'redbiom fetch samples --from {ws["sample_file"]} --context {ws["context"]} --output {biom_output}'
        
        # Editable command
        command = st.text_area(
            "Edit command if needed:",
            value=default_command,
            height=100,
            key="edit_cmd_step4",
            help="You can modify the command before execution"
        )
        
        st.markdown("### ℹ️ What this does:")
        st.info(f"""
        - Reads sample IDs from: `{ws['sample_file']}`
        - Fetches feature abundance data for these samples
        - Saves BIOM table to: `{biom_output}`
        - Uses context: `{ws['context']}`
        """)
        
        st.warning("⚠️ This command may take several minutes for large sample sets")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("▶️ Run Command", type="primary", key="run_step4"):
                with st.spinner("Fetching BIOM table... This may take several minutes"):
                    success, stdout, stderr = execute_command(command, "Fetching BIOM table")
                    
                    if success or Path(biom_output).exists():
                        ws['command_history'].append(command)
                        file_exists, file_size = check_file_exists(biom_output)
                        
                        if file_exists:
                            st.success(f"✅ BIOM table retrieved successfully!")
                            ws['biom_file'] = biom_output
                        else:
                            st.error("❌ Command executed but output file not found")
                            if stderr:
                                st.code(stderr, language="text")
                    else:
                        st.error("❌ Command failed!")
                        if stderr:
                            with st.expander("Error Details"):
                                st.code(stderr, language="text")
        
        # Show results if file exists
        file_exists, file_size = check_file_exists(biom_output)
        if file_exists:
            col1.success(f"✓ File created: `{biom_output}` ({file_size / (1024*1024):.2f} MB)")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("← Back"):
                    ws['current_step'] = 2
                    st.rerun()
            with col2:
                if st.button("✓ Complete", type="primary"):
                    ws['biom_file'] = biom_output
                    ws['completed_steps'].append(3)
                    ws['current_step'] = 4
                    st.rerun()
    
    # Completion screen
    elif current_step == 4:
        st.header("🎉 Workflow Complete!")
        
        st.success("All steps have been completed successfully!")
        
        st.markdown("### 📦 Generated Files")
        st.markdown(f"**Location:** `{os.getcwd()}`")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📄 Samples")
            if ws['sample_file']:
                exists, size = check_file_exists(ws['sample_file'])
                if exists:
                    st.success(f"✓ `{ws['sample_file']}`")
                    st.caption(f"{size:,} bytes")
                    sample_count = count_lines_in_file(ws['sample_file'])
                    st.caption(f"{sample_count} samples")
        
        with col2:
            st.markdown("#### 📊 Metadata")
            if ws['metadata_file']:
                exists, size = check_file_exists(ws['metadata_file'])
                if exists:
                    st.success(f"✓ `{ws['metadata_file']}`")
                    st.caption(f"{size:,} bytes")
        
        with col3:
            st.markdown("#### 🧬 BIOM Table")
            if ws['biom_file']:
                exists, size = check_file_exists(ws['biom_file'])
                if exists:
                    st.success(f"✓ `{ws['biom_file']}`")
                    st.caption(f"{size / (1024*1024):.2f} MB")
        
        st.markdown("### 🎯 Next Steps")
        st.info("""
        **You can now:**
        1. Import the BIOM table into QIIME 2 for analysis
        2. Analyze the metadata to understand your sample cohort
        3. Convert BIOM to TSV: `biom convert -i feature_table.biom -o table.tsv --to-tsv`
        4. Start a new workflow with a different study
        """)
        
        # Show all commands used
        if ws['command_history']:
            with st.expander("📜 View All Commands Used"):
                for i, cmd in enumerate(ws['command_history'], 1):
                    st.code(f"{i}. {cmd}", language="bash")
        
        if st.button("🔄 Start New Workflow"):
            st.session_state.workflow_state = {
                'current_step': 0,
                'completed_steps': [],
                'study_id': '',
                'context': 'Woltka-per-genome-WoLr2-3ab352',
                'sample_file': '',
                'metadata_file': '',
                'biom_file': '',
                'step_outputs': {},
                'command_history': []
            }
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🧬 Qiita Microbiome Workflow - Local Execution Mode
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()