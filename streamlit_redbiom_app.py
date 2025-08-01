import streamlit as st
import subprocess
import ollama
import re

st.title("🧬 Redbiom Assistant with Code Llama")
if 'generated_command' not in st.session_state:
    st.session_state.generated_command = ''
# Step 1: Get natural language question
user_query = st.text_input("Ask a microbiome question (e.g., samples with antibiotics):")

if user_query and user_query != st.session_state.get('last_query', ''):
    # Step 2: Generate command using Code Llama
    prompt = f"""
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

        ---

        User question: "{user_query}"

        Output the single Redbiom CLI command that answers the question.

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

    # Store the generated command and query in session state
    st.session_state.generated_command = cleaned_command
    st.session_state.last_query = user_query

# Display the command editor
if st.session_state.generated_command:
    st.markdown("**LLM Generated Command:**")
    st.code(st.session_state.generated_command, language='text')
    
    # Editable text area for the command
    redbiom_command = st.text_area(
        "Review or edit the Redbiom command:",
        value=st.session_state.generated_command,
        height=100,
        key="command_editor"
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