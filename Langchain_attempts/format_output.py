"""
Redbiom LangChain Tools for LLM-powered microbiome analysis
Uses latest LangChain patterns for tool calling
"""

import subprocess
import os
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


# ============= Tool Schemas =============

class SearchFeaturesInput(BaseModel):
    """Input schema for searching features in Redbiom"""
    features: List[str] = Field(description="List of feature IDs to search for")
    context: str = Field(description="The Redbiom context to search within", default="Woltka-per-genome-WoLr2-3ab352")
    exact: bool = Field(description="If True, all found samples must contain ALL specified features", default=False)
    min_count: int = Field(description="Minimum number of times the feature was observed", default=1)

class SearchSamplesInput(BaseModel):
    """Input schema for searching samples in Redbiom"""
    samples: List[str] = Field(description="List of sample IDs to search for")
    context: str = Field(description="The Redbiom context to search within", default="Woltka-per-genome-WoLr2-3ab352")
    exact: bool = Field(description="If True, all found features must exist in ALL specified samples", default=False)
    min_count: int = Field(description="Minimum number of times features were observed", default=1)

class SearchMetadataInput(BaseModel):
    """Input schema for searching metadata"""
    query: str = Field(description="Search expression, can include 'where' clauses like 'where age_days < 30'")
    categories: bool = Field(description="If True, search for metadata categories instead of values", default=False)

class FetchSamplesInput(BaseModel):
    """Input schema for fetching sample data"""
    samples: Optional[List[str]] = Field(description="List of sample IDs to fetch. If None, fetches all samples in context", default=None)
    output: str = Field(description="Output file path for the BIOM table")
    context: str = Field(description="The Redbiom context to fetch from", default="Woltka-per-genome-WoLr2-3ab352")
    resolve_ambiguities: Optional[str] = Field(description="How to resolve ambiguities: 'merge' or 'most-reads'", default=None)
    md5: bool = Field(description="Use MD5 for features", default=False)

class FetchMetadataInput(BaseModel):
    """Input schema for fetching sample metadata"""
    samples: Optional[List[str]] = Field(description="List of sample IDs. If None, fetches all samples in context", default=None)
    output: str = Field(description="Output TSV file path for metadata")
    context: str = Field(description="The Redbiom context to fetch from", default="Woltka-per-genome-WoLr2-3ab352")
    all_columns: bool = Field(description="Include all metadata columns", default=True)

class DownloadQiitaStudyInput(BaseModel):
    """Input schema for downloading data from Qiita"""
    study_id: int = Field(description="The Qiita study ID to download")
    data_type: str = Field(description="Type of data: 'raw', 'biom', 'sample_information', or 'prep_information'")
    output_dir: str = Field(description="Directory to save downloaded files")
    specific_data_type: Optional[str] = Field(description="Specific data type filter like '16S' or 'Metagenomic'", default=None)


# ============= Tool Implementations =============

@tool
def search_redbiom_features(features: List[str], context: str = "Woltka-per-genome-WoLr2-3ab352", 
                           exact: bool = False, min_count: int = 1) -> str:
    """
    Search for samples containing specified features in Redbiom.
    
    Returns sample IDs that contain the specified features.
    Use this when you need to find which samples have certain microbes/genes.
    """
    cmd = ["redbiom", "search", "features", "--context", context, "--min-count", str(min_count)]
    
    if exact:
        cmd.append("--exact")
    
    cmd.extend(features)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, 
                              env={**os.environ, "REDBIOM_HOST": "http://redbiom.ucsd.edu:7330"})
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


@tool
def search_redbiom_metadata(query: str, categories: bool = False) -> str:
    """
    Search metadata using NLP-based queries.
    
    Use 'where' clauses for filtering: 'where age_days < 30'
    Use operators: & (and), | (or), - (not)
    Set categories=True to search for metadata column names instead of values.
    """
    cmd = ["redbiom", "search", "metadata"]
    
    if categories:
        cmd.append("--categories")
    
    cmd.append(query)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                              env={**os.environ, "REDBIOM_HOST": "http://redbiom.ucsd.edu:7330"})
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


@tool
def fetch_redbiom_samples(output: str, context: str = "Woltka-per-genome-WoLr2-3ab352",
                         samples: Optional[List[str]] = None, resolve_ambiguities: Optional[str] = None,
                         md5: bool = False) -> str:
    """
    Fetch sample data from Redbiom and save as BIOM table.
    
    If samples is None or empty, fetches ALL samples from the context.
    Use resolve_ambiguities='merge' or 'most-reads' to handle duplicate samples.
    """
    # First, get samples if not provided
    if not samples:
        fetch_cmd = ["redbiom", "fetch", "samples-contained", "--context", context]
        try:
            fetch_result = subprocess.run(fetch_cmd, capture_output=True, text=True, check=True,
                                        env={**os.environ, "REDBIOM_HOST": "http://redbiom.ucsd.edu:7330"})
            samples = fetch_result.stdout.strip().split('\n')
        except subprocess.CalledProcessError as e:
            return f"Error fetching sample list: {e.stderr}"
    
    # Now fetch the actual data
    cmd = ["redbiom", "fetch", "samples", "--context", context, "--output", output]
    
    if resolve_ambiguities:
        cmd.extend(["--resolve-ambiguities", resolve_ambiguities])
    
    if md5:
        cmd.append("--md5")
    
    # Use stdin to pass samples
    try:
        result = subprocess.run(cmd, input='\n'.join(samples), capture_output=True, 
                              text=True, check=True,
                              env={**os.environ, "REDBIOM_HOST": "http://redbiom.ucsd.edu:7330"})
        return f"Successfully saved BIOM table to {output}\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


@tool
def fetch_redbiom_metadata(output: str, context: str = "Woltka-per-genome-WoLr2-3ab352",
                          samples: Optional[List[str]] = None, all_columns: bool = True) -> str:
    """
    Fetch sample metadata from Redbiom and save as TSV.
    
    If samples is None or empty, fetches metadata for ALL samples in the context.
    """
    # Get samples if not provided
    if not samples:
        fetch_cmd = ["redbiom", "fetch", "samples-contained", "--context", context]
        try:
            fetch_result = subprocess.run(fetch_cmd, capture_output=True, text=True, check=True,
                                        env={**os.environ, "REDBIOM_HOST": "http://redbiom.ucsd.edu:7330"})
            samples = fetch_result.stdout.strip().split('\n')
        except subprocess.CalledProcessError as e:
            return f"Error fetching sample list: {e.stderr}"
    
    cmd = ["redbiom", "fetch", "sample-metadata", "--context", context, "--output", output]
    
    if all_columns:
        cmd.append("--all-columns")
    
    try:
        result = subprocess.run(cmd, input='\n'.join(samples), capture_output=True,
                              text=True, check=True,
                              env={**os.environ, "REDBIOM_HOST": "http://redbiom.ucsd.edu:7330"})
        return f"Successfully saved metadata to {output}\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


@tool
def download_qiita_study(study_id: int, data_type: str, output_dir: str,
                        specific_data_type: Optional[str] = None) -> str:
    """
    Download data from a Qiita study.
    
    data_type options: 'raw', 'biom', 'sample_information', 'prep_information'
    specific_data_type options: '16S', 'Metagenomic', etc. (only for raw/biom)
    
    Returns the download URL and saves instructions.
    """
    base_url = "https://qiita.ucsd.edu/public_download/"
    
    params = [f"data={data_type}", f"study_id={study_id}"]
    
    if specific_data_type and data_type in ['raw', 'biom']:
        params.append(f"data_type={specific_data_type}")
    
    url = base_url + "?" + "&".join(params)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Use wget or curl to download
    download_cmd = ["wget", "-P", output_dir, url]
    
    try:
        subprocess.run(download_cmd, check=True)
        return f"Successfully downloaded from {url} to {output_dir}"
    except subprocess.CalledProcessError as e:
        return f"Download URL: {url}\nManual download may be required.\nError: {str(e)}"


@tool
def list_redbiom_contexts() -> str:
    """
    List all available Redbiom contexts (databases).
    
    Use this to see what contexts are available before running other commands.
    """
    cmd = ["redbiom", "summarize", "contexts"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                              env={**os.environ, "REDBIOM_HOST": "http://redbiom.ucsd.edu:7330"})
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


@tool  
def extract_sample_ids_from_file(input_file: str, output_file: str, 
                                 column: int = 1, delimiter: str = '\t',
                                 transform: Optional[str] = None) -> str:
    """
    Extract sample IDs from a file (like metadata TSV).
    
    column: which column to extract (1-indexed)
    delimiter: field separator (default tab)
    transform: optional transformation like 'shorten' to extract first two dot-separated fields
    
    Example: transform='shorten' converts '10317.000000001.1' to '10317.000000001'
    """
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        # Skip header
        sample_ids = []
        for line in lines[1:]:
            fields = line.strip().split(delimiter)
            if len(fields) >= column:
                sample_id = fields[column - 1]
                
                if transform == 'shorten':
                    # Extract first two dot-separated fields
                    parts = sample_id.split('.')
                    if len(parts) >= 2:
                        sample_id = f"{parts[0]}.{parts[1]}"
                
                sample_ids.append(sample_id)
        
        # Write to output
        with open(output_file, 'w') as f:
            f.write('\n'.join(sample_ids))
        
        return f"Extracted {len(sample_ids)} sample IDs to {output_file}"
    except Exception as e:
        return f"Error: {str(e)}"


# ============= LLM Agent Setup =============

def create_redbiom_agent(api_key: Optional[str] = None):
    """
    Create a LangChain agent with Redbiom tools.
    
    Usage:
        agent = create_redbiom_agent()
        result = agent.invoke("Get all WGS samples from the WoLr2 context")
    """
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate
    
    # Initialize Claude
    llm = ChatAnthropic(
        model="qwen3",
        anthropic_api_key=api_key
    )
    
    # Collect all tools
    tools = [
        search_redbiom_features,
        search_redbiom_metadata,
        fetch_redbiom_samples,
        fetch_redbiom_metadata,
        download_qiita_study,
        list_redbiom_contexts,
        extract_sample_ids_from_file
    ]
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert microbiome data analyst specializing in Redbiom and Qiita.

When users ask questions about microbiome analysis:
1. Explain your understanding of their question
2. Break down the analysis into clear steps
3. Use the available tools to execute commands
4. Explain what each step accomplishes
5. Connect the results to answer their original question

Available context: Woltka-per-genome-WoLr2-3ab352

Be concise but thorough. Always explain WHY you're running each command."""),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor


# ============= Testing Functions =============

def test_workflow_example():
    """
    Test the example workflow from the requirements:
    1. Query all WGS samples
    2. Extract sample IDs
    3. Query matching 16S samples
    """
    print("=" * 80)
    print("Testing Example Workflow")
    print("=" * 80)
    
    # Step 1: Fetch WGS samples and metadata
    print("\n[1] Fetching WGS samples metadata...")
    result1 = fetch_redbiom_metadata(
        output="WoLr2_md.tsv",
        context="Woltka-per-genome-WoLr2-3ab352"
    )
    print(result1)
    
    # Step 2: Fetch WGS samples BIOM
    print("\n[2] Fetching WGS samples BIOM table...")
    result2 = fetch_redbiom_samples(
        output="WoLr2_ft.biom",
        context="Woltka-per-genome-WoLr2-3ab352",
        resolve_ambiguities="merge"
    )
    print(result2)
    
    # Step 3: Extract shortened sample IDs
    print("\n[3] Extracting sample IDs...")
    result3 = extract_sample_ids_from_file(
        input_file="WoLr2_md.tsv",
        output_file="sample_ids.txt",
        transform="shorten"
    )
    print(result3)
    
    print("\n" + "=" * 80)
    print("Workflow test completed!")
    print("=" * 80)


def test_agent_queries():
    """
    Test the LLM agent with various queries
    """
    agent = create_redbiom_agent()
    
    test_queries = [
        "Get all WGS samples and their metadata from the WoLr2 context",
        "Find samples containing features related to Bacteroides",
        "Search for samples where age_days is less than 30",
    ]
    
    print("=" * 80)
    print("Testing Agent Queries")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n\n{'=' * 80}")
        print(f"Query: {query}")
        print("=" * 80)
        
        try:
            result = agent.invoke({"input": query})
            print("\nResult:")
            print(result["output"])
        except Exception as e:
            print(f"Error: {str(e)}")


def test_individual_tools():
    """
    Test each tool individually
    """
    print("=" * 80)
    print("Testing Individual Tools")
    print("=" * 80)
    
    # Test 1: List contexts
    print("\n[Test 1] Listing available contexts...")
    result = list_redbiom_contexts()
    print(result)
    
    # Test 2: Search metadata
    print("\n[Test 2] Searching for infant samples...")
    result = search_redbiom_metadata("where age_days < 365")
    print(result[:500] if len(result) > 500 else result)  # Truncate if too long
    
    # Test 3: Search features (using a common taxon)
    print("\n[Test 3] Searching for Bacteroides features...")
    # Note: This would need actual feature IDs, this is just a demonstration
    print("Skipping - requires specific feature IDs")
    
    print("\n" + "=" * 80)
    print("Individual tool tests completed!")
    print("=" * 80)


# ============= Main Execution =============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Redbiom LangChain Tools")
    parser.add_argument("--test", choices=["workflow", "agent", "tools", "all"], 
                       help="Run tests", default=None)
    parser.add_argument("--query", type=str, help="Run a single query with the agent")
    parser.add_argument("--api-key", type=str, help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    
    args = parser.parse_args()
    
    import os 
    import dotenv
    dotenv.load_dotenv()  # Load from .env if available
    # Set API key if provided
    if args.api_key:
        os.environ["NRP_API_KEY"] = args.api_key
    else:
        os.environ["NRP_API_KEY"] = os.getenv("NRP_API_KEY")
    
    # Set Redbiom host
    os.environ["REDBIOM_HOST"] = "http://redbiom.ucsd.edu:7330"
    
    if args.test:
        if args.test == "workflow" or args.test == "all":
            test_workflow_example()
        
        if args.test == "tools" or args.test == "all":
            test_individual_tools()
        
        if args.test == "agent" or args.test == "all":
            test_agent_queries()
    
    elif args.query:
        agent = create_redbiom_agent(args.api_key)
        result = agent.invoke({"input": args.query})
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(result["output"])
    
    else:
        print("Redbiom LangChain Tools")
        print("=" * 80)
        print("\nUsage:")
        print("  python redbiom_tools.py --test all              # Run all tests")
        print("  python redbiom_tools.py --test workflow         # Test workflow")
        print("  python redbiom_tools.py --test agent            # Test agent")
        print("  python redbiom_tools.py --test tools            # Test individual tools")
        print("  python redbiom_tools.py --query 'your query'    # Run a single query")
        print("\nExamples:")
        print("  python redbiom_tools.py --query 'Get all WGS samples metadata'")
        print("  python redbiom_tools.py --query 'Find samples with age less than 30 days'")
        print("=" * 80)