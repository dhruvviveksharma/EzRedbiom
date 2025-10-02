import streamlit as st
import pandas as pd

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
                    df = pd.DataFrame(data, columns=headers)
                    
                    # Check for study IDs in CSV data
                    study_column = None
                    study_ids = []
                    for col in df.columns:
                        column_study_ids = []
                        for val in df[col]:
                            if str(val).strip():
                                parts = str(val).split('.')
                                if parts and parts[0].isdigit():
                                    column_study_ids.append(parts[0])
                        if column_study_ids:
                            study_column = col
                            study_ids.extend(column_study_ids)
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
                    
                    # Only show study links if we found study IDs
                    if study_ids:
                        st.markdown("---")
                        st.markdown("**🔗 Qiita Studies Found:**")
                        unique_study_ids = list(set(study_ids))  # Remove duplicates
                        cols = st.columns(min(4, len(unique_study_ids)))
                        for idx, study_id in enumerate(unique_study_ids):
                            col_idx = idx % len(cols)
                            with cols[col_idx]:
                                qiita_url = f"https://qiita.ucsd.edu/study/description/{study_id}"
                                st.markdown(f"[📊 {study_id}]({qiita_url})")
                    
                    with st.expander("🔍 View Raw Output"):
                        st.code(output, language='text')
                    return
                    
        except Exception as e:
            # If parsing fails, fall back to raw display
            st.warning(f"Failed to parse tabular data: {str(e)}")
    
    # Check if it's a simple list (one item per line)
    elif len(lines) > 3 and all(len(line.strip()) > 0 for line in lines[:10]):
        # st.markdown("**📋 Output List:**")
        
        # # Show first few items with numbering
        # display_limit = min(20, len(lines))
        # for i, line in enumerate(lines[:display_limit], 1):
        #     if line.strip():
        #         st.markdown(f"{i}. `{line.strip()}`")
        
        # if len(lines) > display_limit:
        #     st.markdown(f"*... and {len(lines) - display_limit} more items*")
            
        # st.markdown(f"**📊 Summary:** {len([l for l in lines if l.strip()])} items total")
        
        # # Show raw output in expandable section
        # with st.expander("🔍 View Raw Output"):
        #     st.code(output, language='text')
        # return
        headers = lines[0].split(',')
        data = []
        for line in lines[1:]:
            if line.strip():
                data.append(line.split(','))
        
        if data and len(data[0]) == len(headers):
            st.markdown("**📋 Formatted Output:**")
            df = pd.DataFrame(data, columns=headers)
            
            # Check for study IDs in CSV data
            study_column = None
            study_ids = []
            for col in df.columns:
                column_study_ids = []
                for val in df[col]:
                    if str(val).strip():
                        parts = str(val).split('.')
                        if parts and parts[0].isdigit():
                            column_study_ids.append(parts[0])
                if column_study_ids:
                    study_column = col
                    study_ids.extend(column_study_ids)
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
            
            # Only show study links if we found study IDs
            if study_ids:
                st.markdown("---")
                st.markdown("**🔗 Qiita Studies Found:**")
                unique_study_ids = list(set(study_ids))  # Remove duplicates
                cols = st.columns(min(4, len(unique_study_ids)))
                for idx, study_id in enumerate(unique_study_ids):
                    col_idx = idx % len(cols)
                    with cols[col_idx]:
                        qiita_url = f"https://qiita.ucsd.edu/study/description/{study_id}"
                        st.markdown(f"[📊 {study_id}]({qiita_url})")
            
            with st.expander("🔍 View Raw Output"):
                st.code(output, language='text')
            return
    
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