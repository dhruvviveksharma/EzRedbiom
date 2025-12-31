import os
import json
from typing import Optional, List, Literal
from openai import OpenAI


# ============================================================================
# LOAD TOOLS CONFIGURATION
# ============================================================================

with open("tools.json") as f:
    tools = json.load(f)["tools"]

# ============================================================================
# FUNCTION IMPLEMENTATIONS - All return command strings
# ============================================================================

def search_features(context: str, features: List[str], exact: bool = False, min_count: int = 1) -> str:
    """Get samples containing specified features from redbiom database."""
    cmd = f"redbiom search features --context {context}"
    if exact:
        cmd += " --exact"
    cmd += f" --min-count {min_count}"
    cmd += " " + " ".join(features)
    return cmd


def search_samples(context: str, samples: List[str], exact: bool = False, min_count: int = 1) -> str:
    """Get features present in specified samples from redbiom database."""
    cmd = f"redbiom search samples --context {context}"
    if exact:
        cmd += " --exact"
    cmd += f" --min-count {min_count}"
    cmd += " " + " ".join(samples)
    return cmd


def search_metadata(query: str, categories: bool = False) -> str:
    """Search metadata values or categories using NLP-based queries."""
    cmd = "redbiom search metadata"
    if categories:
        cmd += " --categories"
    cmd += f' "{query}"'
    return cmd


def search_taxon(context: str, taxon: str) -> str:
    """Find features associated with a given taxon."""
    cmd = f'redbiom search taxon --context {context} "{taxon}"'
    return cmd


def fetch_sample_metadata(
    output: str,
    context: Optional[str] = None,
    samples: Optional[List[str]] = None,
    all_columns: bool = False,
    resolve_ambiguities: bool = False,
    tagged: bool = False,
    force_categories: Optional[List[str]] = None
) -> str:
    """Retrieve sample metadata and save to a file."""
    cmd = f"redbiom fetch sample-metadata --output {output}"
    
    if context:
        cmd += f" --context {context}"
    if all_columns:
        cmd += " --all-columns"
    if resolve_ambiguities:
        cmd += " --resolve-ambiguities"
    if tagged:
        cmd += " --tagged"
    if force_categories:
        for cat in force_categories:
            cmd += f" --force-category {cat}"
    if samples:
        cmd += " " + " ".join(samples)
    return cmd


def fetch_features(
    output: str,
    context: str,
    features: List[str],
    exact: bool = False,
    md5: bool = False,
    resolve_ambiguities: str = "none",
    fetch_taxonomy: bool = False
) -> str:
    """Fetch sample data containing given features and save to BIOM file."""
    cmd = f"redbiom fetch features --context {context} --output {output}"
    
    if exact:
        cmd += " --exact"
    if md5:
        cmd += " --md5"
    if resolve_ambiguities != "none":
        cmd += f" --resolve-ambiguities {resolve_ambiguities}"
    if fetch_taxonomy:
        cmd += " --fetch-taxonomy"
    cmd += " " + " ".join(features)
    return cmd


def fetch_samples(
    output: str,
    context: str,
    samples: List[str],
    md5: bool = False,
    resolve_ambiguities: str = "none",
    fetch_taxonomy: bool = False
) -> str:
    """Fetch sample data and save to BIOM file format."""
    cmd = f"redbiom fetch samples --context {context} --output {output}"
    
    if md5:
        cmd += " --md5"
    if resolve_ambiguities != "none":
        cmd += f" --resolve-ambiguities {resolve_ambiguities}"
    if fetch_taxonomy:
        cmd += " --fetch-taxonomy"
    cmd += " " + " ".join(samples)
    return cmd


def fetch_qiita_study(
    study_id: int,
    context: str,
    output_basename: str,
    resolve_ambiguities: str = "none",
    fetch_taxonomy: bool = False,
    remove_blanks: bool = False,
    md5: bool = True
) -> str:
    """Fetch all data from a Qiita study."""
    cmd = f"redbiom fetch qiita-study --study-id {study_id} --context {context} --output-basename {output_basename}"
    
    if resolve_ambiguities != "none":
        cmd += f" --resolve-ambiguities {resolve_ambiguities}"
    if fetch_taxonomy:
        cmd += " --fetch-taxonomy"
    if remove_blanks:
        cmd += " --remove-blanks"
    if md5:
        cmd += " --md5"
    return cmd


def fetch_samples_contained(context: Optional[str] = None, unambiguous: bool = False) -> str:
    """Get all sample IDs contained in the database."""
    cmd = "redbiom fetch samples-contained"
    
    if context:
        cmd += f" --context {context}"
    if unambiguous:
        cmd += " --unambiguous"
    return cmd


def fetch_features_contained(context: Optional[str] = None) -> str:
    """Get all feature IDs contained in the database."""
    cmd = "redbiom fetch features-contained"
    
    if context:
        cmd += f" --context {context}"
    return cmd


def summarize_contexts() -> str:
    """Get summary information about available contexts."""
    cmd = "redbiom summarize contexts"
    return cmd


def summarize_metadata_category(category: str, counter: bool = False, descending: bool = False, dump: bool = False) -> str:
    """Summarize values for a specific metadata category."""
    cmd = f"redbiom summarize metadata-category --category {category}"
    
    if counter:
        cmd += " --counter"
    if descending:
        cmd += " --descending"
    if dump:
        cmd += " --dump"
    return cmd


def summarize_metadata(categories: Optional[List[str]] = None, descending: bool = False) -> str:
    """Summarize metadata across all or specific categories."""
    cmd = "redbiom summarize metadata"
    
    if descending:
        cmd += " --descending"
    if categories:
        cmd += " " + " ".join(categories)
    return cmd


def summarize_features(category: str, context: str, features: List[str], exact: bool = False) -> str:
    """Summarize features by a metadata category."""
    cmd = f"redbiom summarize features --category {category} --context {context}"
    
    if exact:
        cmd += " --exact"
    cmd += " " + " ".join(features)
    return cmd


def summarize_samples(category: str, samples: List[str]) -> str:
    """Summarize samples by a metadata category."""
    cmd = f"redbiom summarize samples --category {category}"
    cmd += " " + " ".join(samples)
    return cmd


def summarize_taxonomy(context: str, features: List[str], normalize_ranks: str = "kpcofgs") -> str:
    """Summarize taxonomy for given features."""
    cmd = f"redbiom summarize taxonomy --context {context} --normalize-ranks {normalize_ranks}"
    cmd += " " + " ".join(features)
    return cmd


def select_samples_from_metadata(context: str, query: str, samples: List[str]) -> str:
    """Select samples from a set that match metadata criteria."""
    cmd = f'redbiom select samples-from-metadata --context {context} "{query}"'
    cmd += " " + " ".join(samples)
    return cmd


def select_features_from_samples(context: str, samples: List[str], exact: bool = False) -> str:
    """Select features present in given samples."""
    cmd = f"redbiom select features-from-samples --context {context}"
    
    if exact:
        cmd += " --exact"
    cmd += " " + " ".join(samples)
    return cmd


# ============================================================================
# FUNCTION REGISTRY
# ============================================================================

available_functions = {
    "search_features": search_features,
    "search_samples": search_samples,
    "search_metadata": search_metadata,
    "search_taxon": search_taxon,
    "fetch_sample_metadata": fetch_sample_metadata,
    "fetch_features": fetch_features,
    "fetch_samples": fetch_samples,
    "fetch_qiita_study": fetch_qiita_study,
    "fetch_samples_contained": fetch_samples_contained,
    "fetch_features_contained": fetch_features_contained,
    "summarize_contexts": summarize_contexts,
    "summarize_metadata_category": summarize_metadata_category,
    "summarize_metadata": summarize_metadata,
    "summarize_features": summarize_features,
    "summarize_samples": summarize_samples,
    "summarize_taxonomy": summarize_taxonomy,
    "select_samples_from_metadata": select_samples_from_metadata,
    "select_features_from_samples": select_features_from_samples
}


# ============================================================================
# AGENT IMPLEMENTATION
# ============================================================================

def run_agent(client: OpenAI, user_query: str, max_iterations: int = 5) -> dict:
    """
    Run the agent to process a user query and generate redbiom commands.
    
    Args:
        client: OpenAI client instance
        user_query: Natural language query from user
        max_iterations: Maximum number of tool calling iterations
    
    Returns:
        Dictionary containing conversation history, commands, and results
    """
    messages = [{"role": "user", "content": user_query}]
    commands_generated = []
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call the LLM with tools
        response = client.chat.completions.create(
            model="qwen3",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        # Check if the model wants to call functions
        tool_calls = response_message.tool_calls
        
        if not tool_calls:
            # No more function calls, we're done
            break
        
        # Process each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"\n[Tool Call] {function_name}")
            print(f"[Arguments] {json.dumps(function_args, indent=2)}")
            
            # Get the function from our registry
            function_to_call = available_functions.get(function_name)
            
            if function_to_call:
                # Call the function to get the command
                command = function_to_call(**function_args)
                print(f"[Command Generated] {command}")
                
                commands_generated.append({
                    "function": function_name,
                    "arguments": function_args,
                    "command": command
                })
                
                # Add the function response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": command
                })
            else:
                # Function not found
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": f"Error: Function {function_name} not found"
                })
    
    return {
        "messages": messages,
        "commands": commands_generated,
        "final_response": response_message.content if response_message.content else None
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize the OpenAI client with NRP API
    client = OpenAI(
        api_key="ifjO4oMMtU6MAXw2wc9cdaCjGU3FfdZs",
        base_url="https://ellm.nrp-nautilus.io/v1"
    )
    
    # Example queries
    example_queries = [
        "Find samples containing Bacteroides in the Woltka-per-genome-WoLr2-3ab352 context",
        "Search for samples where age is less than 30 days and antibiotics were used",
        "Get all available contexts in the database",
        "Download study 10317 from Qiita using context Woltka-per-genome-WoLr2-3ab352 and save it as study_10317",
        "Find features associated with Escherichia coli in Woltka-per-genome-WoLr2-3ab352"
    ]
    
    print("=" * 80)
    print("REDBIOM AGENT - EXAMPLE QUERIES")
    print("=" * 80)
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print('='*80)
        
        result = run_agent(client, query)
        
        if result["commands"]:
            print(f"\n✓ Generated {len(result['commands'])} command(s):")
            for j, cmd_info in enumerate(result["commands"], 1):
                print(f"\n  Command {j}:")
                print(f"    Function: {cmd_info['function']}")
                print(f"    Command:  {cmd_info['command']}")
        
        if result["final_response"]:
            print(f"\n💬 AI Response: {result['final_response']}")
        
        print()
    
    print("=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("Enter your queries (type 'exit' to quit):\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        print("\nProcessing...")
        result = run_agent(client, user_input)
        
        if result["commands"]:
            print(f"\n✓ Generated {len(result['commands'])} command(s):")
            for cmd_info in result["commands"]:
                print(f"  → {cmd_info['command']}")
        
        if result["final_response"]:
            print(f"\nAI: {result['final_response']}")
        
        print()