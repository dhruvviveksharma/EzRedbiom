"""
Standalone Redbiom Functions
No LLM dependencies - just pure Python functions for Redbiom operations
"""

import subprocess
import os
from typing import Optional, List, Dict, Union
from pathlib import Path
import pandas as pd


# ============= Configuration =============

class RedbiomConfig:
    """Configuration for Redbiom connections"""
    DEFAULT_HOST = "http://redbiom.ucsd.edu:7330"
    DEFAULT_CONTEXT = "Woltka-per-genome-WoLr2-3ab352"
    
    @staticmethod
    def set_host(host: str):
        """Set the Redbiom host"""
        os.environ["REDBIOM_HOST"] = host
    
    @staticmethod
    def get_host() -> str:
        """Get current Redbiom host"""
        return os.environ.get("REDBIOM_HOST", RedbiomConfig.DEFAULT_HOST)


# ============= Core Functions =============

def run_redbiom_command(cmd: List[str], input_data: Optional[str] = None) -> Dict[str, Union[str, bool]]:
    """
    Run a Redbiom command and return results
    
    Parameters
    ----------
    cmd : List[str]
        Command to run as list of strings
    input_data : Optional[str]
        Data to pass to stdin
    
    Returns
    -------
    Dict with keys:
        - success: bool
        - stdout: str
        - stderr: str
    """
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "REDBIOM_HOST": RedbiomConfig.get_host()}
        )
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "stdout": e.stdout if e.stdout else "",
            "stderr": e.stderr if e.stderr else str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }


# ============= Search Functions =============

def search_features(features: List[str], 
                   context: str = RedbiomConfig.DEFAULT_CONTEXT,
                   exact: bool = False,
                   min_count: int = 1) -> Dict[str, Union[bool, List[str], str]]:
    """
    Search for samples containing specified features
    
    Parameters
    ----------
    features : List[str]
        Feature IDs to search for
    context : str
        Redbiom context to search within
    exact : bool
        If True, all samples must contain ALL features
    min_count : int
        Minimum number of times feature was observed
    
    Returns
    -------
    Dict with:
        - success: bool
        - samples: List[str] (if successful)
        - error: str (if failed)
    
    Example
    -------
    >>> result = search_features(['feature1', 'feature2'], exact=True, min_count=5)
    >>> if result['success']:
    ...     print(f"Found {len(result['samples'])} samples")
    """
    cmd = ["redbiom", "search", "features", "--context", context, "--min-count", str(min_count)]
    
    if exact:
        cmd.append("--exact")
    
    cmd.extend(features)
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        samples = [s.strip() for s in result["stdout"].strip().split('\n') if s.strip()]
        return {"success": True, "samples": samples}
    else:
        return {"success": False, "error": result["stderr"]}


def search_samples(samples: List[str],
                  context: str = RedbiomConfig.DEFAULT_CONTEXT,
                  exact: bool = False,
                  min_count: int = 1) -> Dict[str, Union[bool, List[str], str]]:
    """
    Search for features present in specified samples
    
    Parameters
    ----------
    samples : List[str]
        Sample IDs to search for
    context : str
        Redbiom context to search within
    exact : bool
        If True, all features must be present in ALL samples
    min_count : int
        Minimum number of times feature was observed
    
    Returns
    -------
    Dict with:
        - success: bool
        - features: List[str] (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "search", "samples", "--context", context, "--min-count", str(min_count)]
    
    if exact:
        cmd.append("--exact")
    
    cmd.extend(samples)
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        features = [f.strip() for f in result["stdout"].strip().split('\n') if f.strip()]
        return {"success": True, "features": features}
    else:
        return {"success": False, "error": result["stderr"]}


def search_metadata(query: str, categories: bool = False) -> Dict[str, Union[bool, List[str], str]]:
    """
    Search metadata using NLP queries
    
    Parameters
    ----------
    query : str
        Search expression. Can include:
        - 'where' clauses: 'where age_days < 30'
        - Operators: & (and), | (or), - (not)
        - Word stems
    categories : bool
        If True, search for metadata categories instead of values
    
    Returns
    -------
    Dict with:
        - success: bool
        - results: List[str] (if successful)
        - error: str (if failed)
    
    Examples
    --------
    >>> # Search for young samples
    >>> search_metadata("where age_days < 365")
    
    >>> # Search for metadata columns
    >>> search_metadata("ph - water", categories=True)
    
    >>> # Complex query
    >>> search_metadata("where antibiotics where age_days < 30")
    """
    cmd = ["redbiom", "search", "metadata"]
    
    if categories:
        cmd.append("--categories")
    
    cmd.append(query)
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        results = [r.strip() for r in result["stdout"].strip().split('\n') if r.strip()]
        return {"success": True, "results": results}
    else:
        return {"success": False, "error": result["stderr"]}


def search_taxon(taxon: str, context: str = RedbiomConfig.DEFAULT_CONTEXT) -> Dict[str, Union[bool, List[str], str]]:
    """
    Find features associated with a taxon
    
    Parameters
    ----------
    taxon : str
        Taxon name to search for (e.g., 'Bacteroides', 'Firmicutes')
    context : str
        Redbiom context to search within
    
    Returns
    -------
    Dict with:
        - success: bool
        - features: List[str] (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "search", "taxon", "--context", context, taxon]
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        features = [f.strip() for f in result["stdout"].strip().split('\n') if f.strip()]
        return {"success": True, "features": features}
    else:
        return {"success": False, "error": result["stderr"]}


# ============= Fetch Functions =============

def fetch_samples_contained(context: str = RedbiomConfig.DEFAULT_CONTEXT,
                           unambiguous: bool = False) -> Dict[str, Union[bool, List[str], str]]:
    """
    Get all sample IDs in a context
    
    Parameters
    ----------
    context : str
        Redbiom context
    unambiguous : bool
        Return only unambiguous identifiers
    
    Returns
    -------
    Dict with:
        - success: bool
        - samples: List[str] (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "fetch", "samples-contained", "--context", context]
    
    if unambiguous:
        cmd.append("--unambiguous")
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        samples = [s.strip() for s in result["stdout"].strip().split('\n') if s.strip()]
        return {"success": True, "samples": samples}
    else:
        return {"success": False, "error": result["stderr"]}


def fetch_features_contained(context: str = RedbiomConfig.DEFAULT_CONTEXT) -> Dict[str, Union[bool, List[str], str]]:
    """
    Get all feature IDs in a context
    
    Parameters
    ----------
    context : str
        Redbiom context
    
    Returns
    -------
    Dict with:
        - success: bool
        - features: List[str] (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "fetch", "features-contained", "--context", context]
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        features = [f.strip() for f in result["stdout"].strip().split('\n') if f.strip()]
        return {"success": True, "features": features}
    else:
        return {"success": False, "error": result["stderr"]}


def fetch_sample_metadata(samples: Optional[List[str]] = None,
                         output: str = None,
                         context: str = RedbiomConfig.DEFAULT_CONTEXT,
                         all_columns: bool = True,
                         resolve_ambiguities: bool = False) -> Dict[str, Union[bool, str, pd.DataFrame]]:
    """
    Fetch sample metadata
    
    Parameters
    ----------
    samples : Optional[List[str]]
        Sample IDs to fetch. If None, fetches all samples in context
    output : str
        Output TSV file path. If None, returns DataFrame
    context : str
        Redbiom context
    all_columns : bool
        Include all metadata columns
    resolve_ambiguities : bool
        Output unambiguous identifiers only
    
    Returns
    -------
    Dict with:
        - success: bool
        - file: str (if output specified)
        - dataframe: pd.DataFrame (if output is None)
        - error: str (if failed)
    
    Examples
    --------
    >>> # Fetch all metadata to file
    >>> fetch_sample_metadata(output="metadata.tsv")
    
    >>> # Fetch specific samples as DataFrame
    >>> result = fetch_sample_metadata(samples=['sample1', 'sample2'])
    >>> df = result['dataframe']
    """
    # Get samples if not provided
    if samples is None:
        sample_result = fetch_samples_contained(context)
        if not sample_result["success"]:
            return {"success": False, "error": f"Could not fetch samples: {sample_result['error']}"}
        samples = sample_result["samples"]
    
    # Prepare command
    cmd = ["redbiom", "fetch", "sample-metadata", "--context", context]
    
    if all_columns:
        cmd.append("--all-columns")
    
    if resolve_ambiguities:
        cmd.append("--resolve-ambiguities")
    
    # Use temp file if no output specified
    use_temp = output is None
    if use_temp:
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv')
        output = temp_file.name
        temp_file.close()
    
    cmd.extend(["--output", output])
    
    # Run command
    result = run_redbiom_command(cmd, input_data='\n'.join(samples))
    
    if result["success"]:
        if use_temp:
            try:
                df = pd.read_csv(output, sep='\t')
                os.unlink(output)
                return {"success": True, "dataframe": df}
            except Exception as e:
                return {"success": False, "error": f"Could not read output: {str(e)}"}
        else:
            return {"success": True, "file": output}
    else:
        if use_temp:
            os.unlink(output)
        return {"success": False, "error": result["stderr"]}


def fetch_samples(samples: Optional[List[str]] = None,
                 output: str = None,
                 context: str = RedbiomConfig.DEFAULT_CONTEXT,
                 resolve_ambiguities: Optional[str] = None,
                 md5: bool = False,
                 fetch_taxonomy: bool = False) -> Dict[str, Union[bool, str]]:
    """
    Fetch sample data as BIOM table
    
    Parameters
    ----------
    samples : Optional[List[str]]
        Sample IDs to fetch. If None, fetches all samples
    output : str
        Output BIOM file path (required)
    context : str
        Redbiom context
    resolve_ambiguities : Optional[str]
        How to resolve ambiguities: 'merge' or 'most-reads'
    md5 : bool
        Use MD5 for features
    fetch_taxonomy : bool
        Resolve taxonomy on fetch (slower)
    
    Returns
    -------
    Dict with:
        - success: bool
        - file: str (if successful)
        - error: str (if failed)
    
    Example
    -------
    >>> fetch_samples(
    ...     samples=['sample1', 'sample2'],
    ...     output='my_samples.biom',
    ...     resolve_ambiguities='merge'
    ... )
    """
    if output is None:
        return {"success": False, "error": "output parameter is required"}
    
    # Get samples if not provided
    if samples is None:
        sample_result = fetch_samples_contained(context)
        if not sample_result["success"]:
            return {"success": False, "error": f"Could not fetch samples: {sample_result['error']}"}
        samples = sample_result["samples"]
    
    # Prepare command
    cmd = ["redbiom", "fetch", "samples", "--context", context, "--output", output]
    
    if resolve_ambiguities:
        cmd.extend(["--resolve-ambiguities", resolve_ambiguities])
    
    if md5:
        cmd.append("--md5")
    
    if fetch_taxonomy:
        cmd.append("--fetch-taxonomy")
    
    # Run command
    result = run_redbiom_command(cmd, input_data='\n'.join(samples))
    
    if result["success"]:
        return {"success": True, "file": output}
    else:
        return {"success": False, "error": result["stderr"]}


def fetch_features(features: List[str],
                  output: str,
                  context: str = RedbiomConfig.DEFAULT_CONTEXT,
                  exact: bool = False,
                  md5: bool = False,
                  resolve_ambiguities: Optional[str] = None,
                  fetch_taxonomy: bool = False) -> Dict[str, Union[bool, str]]:
    """
    Fetch sample data containing specific features
    
    Parameters
    ----------
    features : List[str]
        Feature IDs to fetch
    output : str
        Output BIOM file path
    context : str
        Redbiom context
    exact : bool
        All samples must contain ALL features
    md5 : bool
        Use MD5 for features
    resolve_ambiguities : Optional[str]
        How to resolve ambiguities: 'merge' or 'most-reads'
    fetch_taxonomy : bool
        Resolve taxonomy on fetch
    
    Returns
    -------
    Dict with:
        - success: bool
        - file: str (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "fetch", "features", "--context", context, "--output", output]
    
    if exact:
        cmd.append("--exact")
    
    if md5:
        cmd.append("--md5")
    
    if resolve_ambiguities:
        cmd.extend(["--resolve-ambiguities", resolve_ambiguities])
    
    if fetch_taxonomy:
        cmd.append("--fetch-taxonomy")
    
    cmd.extend(features)
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        return {"success": True, "file": output}
    else:
        return {"success": False, "error": result["stderr"]}


def fetch_qiita_study(study_id: int,
                     output_basename: str,
                     context: str = RedbiomConfig.DEFAULT_CONTEXT,
                     resolve_ambiguities: Optional[str] = None,
                     remove_blanks: bool = False,
                     md5: bool = False) -> Dict[str, Union[bool, str]]:
    """
    Fetch all data from a Qiita study
    
    Parameters
    ----------
    study_id : int
        Qiita study ID
    output_basename : str
        Base filename for outputs (will create .tsv and .biom)
    context : str
        Redbiom context
    resolve_ambiguities : Optional[str]
        How to resolve ambiguities: 'merge' or 'most-reads'
    remove_blanks : bool
        Remove blank samples
    md5 : bool
        Use MD5 for features
    
    Returns
    -------
    Dict with:
        - success: bool
        - files: List[str] (if successful)
        - error: str (if failed)
    """
    cmd = [
        "redbiom", "fetch", "qiita-study",
        "--study-id", str(study_id),
        "--context", context,
        "--output-basename", output_basename
    ]
    
    if resolve_ambiguities:
        cmd.extend(["--resolve-ambiguities", resolve_ambiguities])
    
    if remove_blanks:
        cmd.append("--remove-blanks")
    
    if md5:
        cmd.extend(["--md5", "True"])
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        files = [f"{output_basename}.tsv", f"{output_basename}.biom"]
        return {"success": True, "files": files}
    else:
        return {"success": False, "error": result["stderr"]}


# ============= Summarize Functions =============

def list_contexts() -> Dict[str, Union[bool, List[str], str]]:
    """
    List all available Redbiom contexts
    
    Returns
    -------
    Dict with:
        - success: bool
        - contexts: List[str] (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "summarize", "contexts"]
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        contexts = [c.strip() for c in result["stdout"].strip().split('\n') if c.strip()]
        return {"success": True, "contexts": contexts}
    else:
        return {"success": False, "error": result["stderr"]}


def summarize_metadata_category(category: str,
                                counter: bool = False,
                                descending: bool = False) -> Dict[str, Union[bool, Dict, str]]:
    """
    Summarize values within a metadata category
    
    Parameters
    ----------
    category : str
        Metadata category to summarize
    counter : bool
        Get value counts
    descending : bool
        Sort in descending order
    
    Returns
    -------
    Dict with:
        - success: bool
        - summary: Dict or List (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "summarize", "metadata-category", "--category", category]
    
    if counter:
        cmd.append("--counter")
    
    if descending:
        cmd.append("--descending")
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        return {"success": True, "summary": result["stdout"]}
    else:
        return {"success": False, "error": result["stderr"]}


def summarize_taxonomy(features: List[str],
                      context: str = RedbiomConfig.DEFAULT_CONTEXT) -> Dict[str, Union[bool, str]]:
    """
    Summarize taxonomy for features
    
    Parameters
    ----------
    features : List[str]
        Feature IDs to summarize
    context : str
        Redbiom context
    
    Returns
    -------
    Dict with:
        - success: bool
        - taxonomy: str (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "summarize", "taxonomy", "--context", context]
    cmd.extend(features)
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        return {"success": True, "taxonomy": result["stdout"]}
    else:
        return {"success": False, "error": result["stderr"]}


# ============= Select Functions =============

def select_samples_from_metadata(query: str,
                                 samples: Optional[List[str]] = None,
                                 context: str = RedbiomConfig.DEFAULT_CONTEXT) -> Dict[str, Union[bool, List[str], str]]:
    """
    Filter samples based on metadata query
    
    Parameters
    ----------
    query : str
        Metadata query (e.g., "age_days < 30")
    samples : Optional[List[str]]
        Sample IDs to filter. If None, uses all samples in context
    context : str
        Redbiom context
    
    Returns
    -------
    Dict with:
        - success: bool
        - samples: List[str] (if successful)
        - error: str (if failed)
    
    Example
    -------
    >>> select_samples_from_metadata("age_days < 30", samples=['sample1', 'sample2'])
    """
    cmd = ["redbiom", "select", "samples-from-metadata", "--context", context, query]
    
    if samples:
        input_data = '\n'.join(samples)
    else:
        input_data = None
    
    result = run_redbiom_command(cmd, input_data=input_data)
    
    if result["success"]:
        filtered_samples = [s.strip() for s in result["stdout"].strip().split('\n') if s.strip()]
        return {"success": True, "samples": filtered_samples}
    else:
        return {"success": False, "error": result["stderr"]}


def select_features_from_samples(samples: List[str],
                                 context: str = RedbiomConfig.DEFAULT_CONTEXT,
                                 exact: bool = False) -> Dict[str, Union[bool, List[str], str]]:
    """
    Get features associated with samples
    
    Parameters
    ----------
    samples : List[str]
        Sample IDs
    context : str
        Redbiom context
    exact : bool
        All features must exist in ALL samples
    
    Returns
    -------
    Dict with:
        - success: bool
        - features: List[str] (if successful)
        - error: str (if failed)
    """
    cmd = ["redbiom", "select", "features-from-samples", "--context", context]
    
    if exact:
        cmd.append("--exact")
    
    cmd.extend(samples)
    
    result = run_redbiom_command(cmd)
    
    if result["success"]:
        features = [f.strip() for f in result["stdout"].strip().split('\n') if f.strip()]
        return {"success": True, "features": features}
    else:
        return {"success": False, "error": result["stderr"]}


# ============= Utility Functions =============

def extract_sample_ids(input_file: str,
                      output_file: Optional[str] = None,
                      column: int = 1,
                      delimiter: str = '\t',
                      transform: Optional[str] = None,
                      skip_header: bool = True) -> Dict[str, Union[bool, List[str], str]]:
    """
    Extract sample IDs from a file
    
    Parameters
    ----------
    input_file : str
        Input file path
    output_file : Optional[str]
        Output file path. If None, returns list
    column : int
        Column to extract (1-indexed)
    delimiter : str
        Field separator
    transform : Optional[str]
        Transformation to apply:
        - 'shorten': Extract first two dot-separated fields
        - 'prefix': Extract everything before first dot
    skip_header : bool
        Skip first line
    
    Returns
    -------
    Dict with:
        - success: bool
        - sample_ids: List[str] (if output_file is None)
        - file: str (if output_file specified)
        - error: str (if failed)
    
    Example
    -------
    >>> # Extract and shorten IDs
    >>> result = extract_sample_ids('metadata.tsv', 'ids.txt', transform='shorten')
    >>> # Returns list instead
    >>> result = extract_sample_ids('metadata.tsv')
    >>> ids = result['sample_ids']
    """
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        # Skip header if requested
        start_idx = 1 if skip_header else 0
        
        sample_ids = []
        for line in lines[start_idx:]:
            fields = line.strip().split(delimiter)
            if len(fields) >= column:
                sample_id = fields[column - 1]
                
                # Apply transform
                if transform == 'shorten':
                    parts = sample_id.split('.')
                    if len(parts) >= 2:
                        sample_id = f"{parts[0]}.{parts[1]}"
                elif transform == 'prefix':
                    sample_id = sample_id.split('.')[0]
                
                sample_ids.append(sample_id)
        
        # Write or return
        if output_file:
            with open(output_file, 'w') as f:
                f.write('\n'.join(sample_ids))
            return {"success": True, "file": output_file, "count": len(sample_ids)}
        else:
            return {"success": True, "sample_ids": sample_ids, "count": len(sample_ids)}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_qiita_url(study_id: int,
                      data_type: str,
                      output_dir: str,
                      specific_data_type: Optional[str] = None,
                      prep_id: Optional[int] = None) -> Dict[str, Union[bool, str]]:
    """
    Generate and optionally download from Qiita public download URL
    
    Parameters
    ----------
    study_id : int
        Qiita study ID
    data_type : str
        Type: 'raw', 'biom', 'sample_information', 'prep_information'
    output_dir : str
        Output directory
    specific_data_type : Optional[str]
        Filter: '16S', 'Metagenomic', etc.
    prep_id : Optional[int]
        Preparation ID (for prep_information only)
    
    Returns
    -------
    Dict with:
        - success: bool
        - url: str
        - file: str (if downloaded)
        - error: str (if failed)
    
    Example
    -------
    >>> download_qiita_url(10317, 'biom', './output', specific_data_type='16S')
    """
    base_url = "https://qiita.ucsd.edu/public_download/"
    
    params = [f"data={data_type}", f"study_id={study_id}"]
    
    if specific_data_type and data_type in ['raw', 'biom']:
        params.append(f"data_type={specific_data_type}")
    
    if prep_id and data_type == 'prep_information':
        params.append(f"prep_id={prep_id}")
    
    url = base_url + "?" + "&".join(params)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Try to download with wget
    try:
        result = subprocess.run(
            ["wget", "-P", output_dir, url],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "success": True,
            "url": url,
            "output_dir": output_dir
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        # wget failed or not found, return URL for manual download
        return {
            "success": True,
            "url": url,
            "message": "Download URL generated. Use wget or curl to download manually."
        }


# ============= Main/Testing =============

if __name__ == "__main__":
    """Example usage"""
    
    print("Redbiom Functions - Example Usage\n")
    print("=" * 80)
    
    # Set host
    RedbiomConfig.set_host("http://redbiom.ucsd.edu:7330")
    
    # Example 1: List contexts
    print("\n1. Listing available contexts...")
    result = list_contexts()
    if result["success"]:
        print(f"Found {len(result['contexts'])} contexts:")
        for ctx in result['contexts'][:5]:
            print(f"  - {ctx}")
    else:
        print(f"Error: {result['error']}")
    
    # Example 2: Search metadata
    print("\n2. Searching for infant samples...")
    result = search_metadata("where age_days < 365")
    if result["success"]:
        print(f"Found {len(result['results'])} samples")
        print(f"First 5: {result['results'][:5]}")
    else:
        print(f"Error: {result['error']}")
    
    # Example 3: Fetch metadata as DataFrame
    print("\n3. Fetching sample metadata...")
    result = fetch_sample_metadata(
        samples=['10317.000000001', '10317.000000002'],
        context="Woltka-per-genome-WoLr2-3ab352"
    )
    if result["success"]:
        df = result['dataframe']
        print(f"Fetched metadata with shape: {df.shape}")
        print(df.head())
    else:
        print(f"Error: {result['error']}")
    
    print("\n" + "=" * 80)
    print("Examples complete!")