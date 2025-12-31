import unittest
from unittest.mock import patch, MagicMock
import subprocess
from typing import List
from tools import search_features, search_samples, search_metadata, search_taxon, fetch_sample_metadata, fetch_features, fetch_samples, \
fetch_qiita_study, fetch_samples_contained, fetch_features_contained, summarize_contexts, summarize_metadata_category,\
summarize_metadata, summarize_features, summarize_samples ,summarize_taxonomy, select_samples_from_metadata, \
select_features_from_samples

# Import the functions (assuming they're in a module called redbiom_functions)
# from redbiom_functions import *

# For testing purposes, I'll include the function signatures here
# In practice, import them from your module


class TestSearchFunctions(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_search_features_basic(self, mock_run):
        """Test basic search_features call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = search_features("context1", ["feature1", "feature2"])
        
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom search features --context context1", cmd)
        self.assertIn("--min-count 1", cmd)
        self.assertIn("feature1 feature2", cmd)
        self.assertNotIn("--exact", cmd)
    
    @patch('subprocess.run')
    def test_search_features_with_exact(self, mock_run):
        """Test search_features with exact flag"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = search_features("context1", ["feature1"], exact=True, min_count=5)
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--exact", cmd)
        self.assertIn("--min-count 5", cmd)
    
    @patch('subprocess.run')
    def test_search_samples_basic(self, mock_run):
        """Test basic search_samples call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = search_samples("context1", ["sample1", "sample2"])
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom search samples --context context1", cmd)
        self.assertIn("sample1 sample2", cmd)
    
    @patch('subprocess.run')
    def test_search_metadata_basic(self, mock_run):
        """Test basic search_metadata call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = search_metadata("body_site:gut")
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom search metadata", cmd)
        self.assertIn('"body_site:gut"', cmd)
        self.assertNotIn("--categories", cmd)
    
    @patch('subprocess.run')
    def test_search_metadata_with_categories(self, mock_run):
        """Test search_metadata with categories flag"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = search_metadata("body_site", categories=True)
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--categories", cmd)
    
    @patch('subprocess.run')
    def test_search_taxon(self, mock_run):
        """Test search_taxon call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = search_taxon("context1", "g__Bacteroides")
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom search taxon --context context1", cmd)
        self.assertIn('"g__Bacteroides"', cmd)


class TestFetchFunctions(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_fetch_sample_metadata_basic(self, mock_run):
        """Test basic fetch_sample_metadata call"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = fetch_sample_metadata("output.tsv")
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom fetch sample-metadata --output output.tsv", cmd)
        self.assertNotIn("--context", cmd)
        self.assertNotIn("--all-columns", cmd)
    
    @patch('subprocess.run')
    def test_fetch_sample_metadata_with_options(self, mock_run):
        """Test fetch_sample_metadata with various options"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = fetch_sample_metadata(
            "output.tsv",
            context="context1",
            samples=["sample1", "sample2"],
            all_columns=True,
            resolve_ambiguities=True,
            tagged=True,
            force_categories=["category1", "category2"]
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--context context1", cmd)
        self.assertIn("--all-columns", cmd)
        self.assertIn("--resolve-ambiguities", cmd)
        self.assertIn("--tagged", cmd)
        self.assertIn("--force-category category1", cmd)
        self.assertIn("--force-category category2", cmd)
    
    @patch('subprocess.run')
    def test_fetch_features_basic(self, mock_run):
        """Test basic fetch_features call"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = fetch_features("output.biom", "context1", ["feature1"])
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom fetch features --context context1 --output output.biom", cmd)
        self.assertIn("feature1", cmd)
        self.assertNotIn("--exact", cmd)
        self.assertNotIn("--md5", cmd)
    
    @patch('subprocess.run')
    def test_fetch_features_with_options(self, mock_run):
        """Test fetch_features with all options"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = fetch_features(
            "output.biom",
            "context1",
            ["feature1", "feature2"],
            exact=True,
            md5=True,
            resolve_ambiguities="most-reads",
            fetch_taxonomy=True
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--exact", cmd)
        self.assertIn("--md5", cmd)
        self.assertIn("--resolve-ambiguities most-reads", cmd)
        self.assertIn("--fetch-taxonomy", cmd)
    
    @patch('subprocess.run')
    def test_fetch_samples_basic(self, mock_run):
        """Test basic fetch_samples call"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = fetch_samples("output.biom", "context1", ["sample1", "sample2"])
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom fetch samples --context context1 --output output.biom", cmd)
        self.assertIn("sample1 sample2", cmd)
    
    @patch('subprocess.run')
    def test_fetch_qiita_study(self, mock_run):
        """Test fetch_qiita_study call"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = fetch_qiita_study(10317, "context1", "study_output")
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom fetch qiita-study --study-id 10317", cmd)
        self.assertIn("--context context1", cmd)
        self.assertIn("--output-basename study_output", cmd)
        self.assertIn("--md5 True", cmd)
    
    @patch('subprocess.run')
    def test_fetch_qiita_study_with_options(self, mock_run):
        """Test fetch_qiita_study with options"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = fetch_qiita_study(
            10317,
            "context1",
            "study_output",
            resolve_ambiguities="most-reads",
            fetch_taxonomy=True,
            remove_blanks=True,
            md5=False
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--resolve-ambiguities most-reads", cmd)
        self.assertIn("--fetch-taxonomy", cmd)
        self.assertIn("--remove-blanks", cmd)
        self.assertNotIn("--md5 True", cmd)
    
    @patch('subprocess.run')
    def test_fetch_samples_contained_basic(self, mock_run):
        """Test basic fetch_samples_contained call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = fetch_samples_contained()
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom fetch samples-contained", cmd)
        self.assertNotIn("--context", cmd)
    
    @patch('subprocess.run')
    def test_fetch_samples_contained_with_context(self, mock_run):
        """Test fetch_samples_contained with context"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = fetch_samples_contained(context="context1", unambiguous=True)
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--context context1", cmd)
        self.assertIn("--unambiguous", cmd)
    
    @patch('subprocess.run')
    def test_fetch_features_contained(self, mock_run):
        """Test fetch_features_contained call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = fetch_features_contained(context="context1")
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom fetch features-contained", cmd)
        self.assertIn("--context context1", cmd)


class TestSummarizeFunctions(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_summarize_contexts(self, mock_run):
        """Test summarize_contexts call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_contexts()
        
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, "redbiom summarize contexts")
    
    @patch('subprocess.run')
    def test_summarize_metadata_category_basic(self, mock_run):
        """Test basic summarize_metadata_category call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_metadata_category("body_site")
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom summarize metadata-category --category body_site", cmd)
        self.assertNotIn("--counter", cmd)
    
    @patch('subprocess.run')
    def test_summarize_metadata_category_with_options(self, mock_run):
        """Test summarize_metadata_category with options"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_metadata_category(
            "body_site",
            counter=True,
            descending=True,
            dump=True
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--counter", cmd)
        self.assertIn("--descending", cmd)
        self.assertIn("--dump", cmd)
    
    @patch('subprocess.run')
    def test_summarize_metadata_basic(self, mock_run):
        """Test basic summarize_metadata call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_metadata()
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom summarize metadata", cmd)
    
    @patch('subprocess.run')
    def test_summarize_metadata_with_categories(self, mock_run):
        """Test summarize_metadata with categories"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_metadata(
            categories=["body_site", "age_years"],
            descending=True
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--descending", cmd)
        self.assertIn("body_site age_years", cmd)
    
    @patch('subprocess.run')
    def test_summarize_features(self, mock_run):
        """Test summarize_features call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_features(
            "body_site",
            "context1",
            ["feature1", "feature2"],
            exact=True
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom summarize features --category body_site --context context1", cmd)
        self.assertIn("--exact", cmd)
        self.assertIn("feature1 feature2", cmd)
    
    @patch('subprocess.run')
    def test_summarize_samples(self, mock_run):
        """Test summarize_samples call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_samples("body_site", ["sample1", "sample2"])
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom summarize samples --category body_site", cmd)
        self.assertIn("sample1 sample2", cmd)
    
    @patch('subprocess.run')
    def test_summarize_taxonomy(self, mock_run):
        """Test summarize_taxonomy call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = summarize_taxonomy(
            "context1",
            ["feature1", "feature2"],
            normalize_ranks="kpcofgs"
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom summarize taxonomy --context context1", cmd)
        self.assertIn("--normalize-ranks kpcofgs", cmd)
        self.assertIn("feature1 feature2", cmd)


class TestSelectFunctions(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_select_samples_from_metadata(self, mock_run):
        """Test select_samples_from_metadata call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = select_samples_from_metadata(
            "context1",
            "where body_site=='gut'",
            ["sample1", "sample2"]
        )
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom select samples-from-metadata --context context1", cmd)
        self.assertIn('"where body_site==\'gut\'"', cmd)
        self.assertIn("sample1 sample2", cmd)
    
    @patch('subprocess.run')
    def test_select_features_from_samples_basic(self, mock_run):
        """Test basic select_features_from_samples call"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = select_features_from_samples("context1", ["sample1", "sample2"])
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("redbiom select features-from-samples --context context1", cmd)
        self.assertIn("sample1 sample2", cmd)
        self.assertNotIn("--exact", cmd)
    
    @patch('subprocess.run')
    def test_select_features_from_samples_with_exact(self, mock_run):
        """Test select_features_from_samples with exact flag"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        result = select_features_from_samples("context1", ["sample1"], exact=True)
        
        cmd = mock_run.call_args[0][0]
        self.assertIn("--exact", cmd)


class TestErrorHandling(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_timeout_error(self, mock_run):
        """Test timeout error handling"""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)
        
        result = search_features("context1", ["feature1"])
        
        self.assertIn("Error:", result)
    
    @patch('subprocess.run')
    def test_general_exception(self, mock_run):
        """Test general exception handling"""
        mock_run.side_effect = Exception("Test exception")
        
        result = search_features("context1", ["feature1"])
        
        self.assertIn("Error: Test exception", result)
    
    @patch('subprocess.run')
    def test_stderr_output(self, mock_run):
        """Test stderr output when stdout is empty"""
        mock_run.return_value = MagicMock(stdout="", stderr="Error message", returncode=1)
        
        result = search_features("context1", ["feature1"])
        
        self.assertEqual(result, "Error message")
    
    @patch('subprocess.run')
    def test_fetch_success_message(self, mock_run):
        """Test fetch function success message"""
        mock_run.return_value = MagicMock(stdout="Fetched data", stderr="", returncode=0)
        
        result = fetch_features("output.biom", "context1", ["feature1"])
        
        self.assertIn("Success!", result)
        self.assertIn("output.biom", result)


class TestCommandConstruction(unittest.TestCase):
    """Test that commands are constructed with proper shell=True handling"""
    
    @patch('subprocess.run')
    def test_shell_true_parameter(self, mock_run):
        """Verify shell=True is passed to subprocess.run"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        search_features("context1", ["feature1"])
        
        call_kwargs = mock_run.call_args[1]
        self.assertTrue(call_kwargs.get('shell'))
        self.assertTrue(call_kwargs.get('capture_output'))
        self.assertTrue(call_kwargs.get('text'))
    
    @patch('subprocess.run')
    def test_timeout_parameter(self, mock_run):
        """Verify timeout is set appropriately"""
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        
        search_features("context1", ["feature1"])
        
        call_kwargs = mock_run.call_args[1]
        self.assertIn('timeout', call_kwargs)
        self.assertEqual(call_kwargs['timeout'], 300)


if __name__ == '__main__':
    unittest.main(verbosity=2)