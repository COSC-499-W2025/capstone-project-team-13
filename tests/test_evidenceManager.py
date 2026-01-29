"""
Unit tests for Evidence Management System
Tests both automatic extraction and manual entry of evidence
"""

import unittest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path to access src modules
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from Evidence.evidenceManager import EvidenceManager, evidence_manager
from Evidence.autoExtractor import AutoEvidenceExtractor
from Databases.database import db_manager


class TestEvidenceManager(unittest.TestCase):
    """Test EvidenceManager class"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear database
        db_manager.clear_all_data()
        
        # Create test project
        self.test_project = db_manager.create_project({
            'name': 'Test Project',
            'file_path': '/test/path',
            'project_type': 'code'
        })
        
        self.manager = EvidenceManager()
    
    def tearDown(self):
        """Clean up after tests"""
        db_manager.clear_all_data()
    
    def test_store_and_retrieve_evidence(self):
        """Test storing and retrieving evidence"""
        evidence = {
            'test_coverage': 85.5,
            'commits': 150,
            'users': 1000
        }
        
        success = self.manager.store_evidence(self.test_project.id, evidence)
        self.assertTrue(success)
        
        retrieved = self.manager.get_evidence(self.test_project.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['test_coverage'], 85.5)
        self.assertEqual(retrieved['commits'], 150)
        self.assertEqual(retrieved['users'], 1000)
    
    def test_add_manual_metric(self):
        """Test adding manual metrics"""
        success = self.manager.add_manual_metric(
            self.test_project.id,
            'users',
            1500,
            'Active monthly users'
        )
        self.assertTrue(success)
        
        evidence = self.manager.get_evidence(self.test_project.id)
        self.assertIn('manual_metrics', evidence)
        self.assertIn('users', evidence['manual_metrics'])
        self.assertEqual(evidence['manual_metrics']['users']['value'], 1500)
        self.assertEqual(evidence['manual_metrics']['users']['description'], 'Active monthly users')
    
    def test_add_feedback(self):
        """Test adding feedback"""
        success = self.manager.add_feedback(
            self.test_project.id,
            'Excellent work on this project!',
            'Professor Smith',
            5
        )
        self.assertTrue(success)
        
        evidence = self.manager.get_evidence(self.test_project.id)
        self.assertIn('feedback', evidence)
        self.assertEqual(len(evidence['feedback']), 1)
        self.assertEqual(evidence['feedback'][0]['text'], 'Excellent work on this project!')
        self.assertEqual(evidence['feedback'][0]['source'], 'Professor Smith')
        self.assertEqual(evidence['feedback'][0]['rating'], 5)
    
    def test_add_achievement(self):
        """Test adding achievements"""
        success = self.manager.add_achievement(
            self.test_project.id,
            'Won 1st place at hackathon',
            '2024-03-15'
        )
        self.assertTrue(success)
        
        evidence = self.manager.get_evidence(self.test_project.id)
        self.assertIn('achievements', evidence)
        self.assertEqual(len(evidence['achievements']), 1)
        self.assertEqual(evidence['achievements'][0]['description'], 'Won 1st place at hackathon')
        self.assertEqual(evidence['achievements'][0]['date'], '2024-03-15')
    
    def test_merge_evidence(self):
        """Test that storing evidence merges with existing data"""
        # Add manual metric
        self.manager.add_manual_metric(self.test_project.id, 'users', 1000)
        
        # Add automatic evidence
        auto_evidence = {'test_coverage': 90.0, 'commits': 200}
        self.manager.store_evidence(self.test_project.id, auto_evidence)
        
        # Both should be present
        evidence = self.manager.get_evidence(self.test_project.id)
        self.assertIn('manual_metrics', evidence)
        self.assertIn('test_coverage', evidence)
        self.assertIn('commits', evidence)
    
    def test_get_metric_value(self):
        """Test retrieving specific metric values"""
        evidence = {
            'test_coverage': 85.5,
            'git_stats': {'commits': 150}
        }
        self.manager.store_evidence(self.test_project.id, evidence)
        
        # Get top-level metric
        coverage = self.manager.get_metric_value(self.test_project.id, 'test_coverage')
        self.assertEqual(coverage, 85.5)
        
        # Get nested metric
        commits = self.manager.get_metric_value(self.test_project.id, 'commits')
        self.assertEqual(commits, 150)
    
    def test_has_evidence(self):
        """Test checking if evidence exists"""
        # Initially no evidence
        self.assertFalse(self.manager.has_evidence(self.test_project.id))
        
        # Add evidence
        self.manager.add_manual_metric(self.test_project.id, 'users', 100)
        
        # Now has evidence
        self.assertTrue(self.manager.has_evidence(self.test_project.id))
    
    def test_clear_evidence(self):
        """Test clearing evidence"""
        # Add evidence
        self.manager.add_manual_metric(self.test_project.id, 'users', 1000)
        self.assertTrue(self.manager.has_evidence(self.test_project.id))
        
        # Clear evidence
        success = self.manager.clear_evidence(self.test_project.id)
        self.assertTrue(success)
        
        # Evidence should be gone
        self.assertFalse(self.manager.has_evidence(self.test_project.id))
    
    def test_get_summary(self):
        """Test generating evidence summary"""
        # Add various types of evidence
        self.manager.store_evidence(self.test_project.id, {
            'test_coverage': 85.5,
            'readme_badges': [
                {'alt': 'Build', 'type': 'build_status'},
                {'alt': 'Coverage', 'type': 'coverage'}
            ]
        })
        self.manager.add_manual_metric(self.test_project.id, 'users', 1000)
        self.manager.add_feedback(self.test_project.id, 'Great work!', 'Client', 5)
        self.manager.add_achievement(self.test_project.id, 'Won award')
        
        summary = self.manager.get_summary(self.test_project.id)
        
        # Check evidence is in summary
        self.assertIn('Test Coverage', summary)
        self.assertIn('85.5', summary)
        self.assertIn('Badges', summary)
        self.assertIn('Build', summary)
        self.assertIn('users', summary)
        self.assertIn('Feedback', summary)
        self.assertIn('Achievements', summary)


class TestAutoEvidenceExtractor(unittest.TestCase):
    """Test AutoEvidenceExtractor class"""
    
    def setUp(self):
        """Create temporary test project directory"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
    
    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir)
    
    def test_extract_readme_badges(self):
        """Test extracting badges from README"""
        readme_content = """
# Test Project

![Build Status](https://img.shields.io/travis/user/repo)
![Coverage](https://img.shields.io/codecov/c/github/user/repo)
![License](https://img.shields.io/github/license/user/repo)
        """
        
        readme_path = self.test_path / 'README.md'
        readme_path.write_text(readme_content)
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        badges = extractor.extract_readme_badges()
        
        self.assertEqual(len(badges), 3)
        
        # Check badge types
        badge_types = [b['type'] for b in badges]
        self.assertIn('build_status', badge_types)
        self.assertIn('coverage', badge_types)
        self.assertIn('license', badge_types)
    
    def test_extract_readme_metrics(self):
        """Test extracting metrics from README"""
        readme_content = """
# Test Project

This project serves 1000+ users and achieved 40% performance improvement.
We reduced file size by 5 MB and have 150 stars on GitHub.
        """
        
        readme_path = self.test_path / 'README.md'
        readme_path.write_text(readme_content)
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        metrics = extractor.extract_readme_metrics()
        
        self.assertIn('users', metrics)
        self.assertEqual(metrics['users'], 1000)
        self.assertIn('stars', metrics)
        self.assertEqual(metrics['stars'], 150)
    
    def test_extract_coverage_from_json(self):
        """Test extracting coverage from JSON report"""
        coverage_data = {
            'total': {
                'lines': {
                    'pct': 87.5
                }
            }
        }
        
        coverage_path = self.test_path / 'coverage.json'
        with open(coverage_path, 'w') as f:
            json.dump(coverage_data, f)
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        coverage = extractor.extract_coverage_metrics()
        
        self.assertEqual(coverage, 87.5)
    
    def test_extract_coverage_from_xml(self):
        """Test extracting coverage from XML report"""
        coverage_xml = """<?xml version="1.0" ?>
<coverage line-rate="0.92">
    <packages>
        <package name="mypackage" line-rate="0.92">
        </package>
    </packages>
</coverage>
        """
        
        coverage_path = self.test_path / 'coverage.xml'
        coverage_path.write_text(coverage_xml)
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        coverage = extractor.extract_coverage_metrics()
        
        self.assertEqual(coverage, 92.0)
    
    def test_extract_ci_metrics(self):
        """Test detecting CI/CD configuration"""
        # Create GitHub Actions workflow
        workflows_dir = self.test_path / '.github' / 'workflows'
        workflows_dir.mkdir(parents=True)
        
        workflow_path = workflows_dir / 'test.yml'
        workflow_path.write_text('name: Test\non: [push]')
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        ci_metrics = extractor.extract_ci_metrics()
        
        self.assertTrue(ci_metrics['has_ci_cd'])
        self.assertEqual(ci_metrics['ci_platform'], 'GitHub Actions')
    
    def test_extract_documentation_metrics(self):
        """Test extracting documentation metrics"""
        # Create README
        readme_path = self.test_path / 'README.md'
        readme_path.write_text('\n'.join(['# Test'] + ['Line ' + str(i) for i in range(50)]))
        
        # Create docs directory
        docs_dir = self.test_path / 'docs'
        docs_dir.mkdir()
        (docs_dir / 'guide.md').write_text('Documentation')
        (docs_dir / 'api.md').write_text('API Docs')
        
        # Create CONTRIBUTING guide
        (self.test_path / 'CONTRIBUTING.md').write_text('How to contribute')
        
        # Create LICENSE
        (self.test_path / 'LICENSE').write_text('MIT License')
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        doc_metrics = extractor.extract_documentation_metrics()
        
        self.assertGreater(doc_metrics['readme_lines'], 0)
        self.assertEqual(doc_metrics['doc_files'], 2)
        self.assertTrue(doc_metrics['has_contributing_guide'])
        self.assertTrue(doc_metrics['has_license'])
    
    def test_extract_package_info(self):
        """Test extracting package information"""
        package_json = {
            'name': 'test-project',
            'version': '1.0.0',
            'dependencies': {
                'express': '^4.0.0',
                'react': '^18.0.0'
            },
            'devDependencies': {
                'jest': '^29.0.0'
            }
        }
        
        package_path = self.test_path / 'package.json'
        with open(package_path, 'w') as f:
            json.dump(package_json, f)
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        package_info = extractor.extract_package_info()
        
        self.assertEqual(package_info['package_manager'], 'npm')
        self.assertEqual(package_info['version'], '1.0.0')
        self.assertEqual(package_info['dependencies_count'], 2)
        self.assertEqual(package_info['dev_dependencies_count'], 1)
    
    def test_extract_all_evidence(self):
        """Test extracting all evidence at once"""
        # Create comprehensive test project
        readme_content = """
# Test Project
![Build](https://img.shields.io/travis/test)
1000+ users
        """
        (self.test_path / 'README.md').write_text(readme_content)
        
        coverage_data = {'total': {'lines': {'pct': 90.0}}}
        with open(self.test_path / 'coverage.json', 'w') as f:
            json.dump(coverage_data, f)
        
        (self.test_path / 'LICENSE').write_text('MIT')
        
        extractor = AutoEvidenceExtractor(str(self.test_path))
        evidence = extractor.extract_all_evidence()
        
        # Should have multiple types of evidence
        self.assertIn('readme_badges', evidence)
        self.assertIn('readme_metrics', evidence)
        self.assertIn('test_coverage', evidence)
        self.assertIn('documentation', evidence)
        
        self.assertEqual(evidence['test_coverage'], 90.0)
        self.assertTrue(evidence['documentation']['has_license'])


class TestEvidenceIntegration(unittest.TestCase):
    """Integration tests for evidence system"""
    
    def setUp(self):
        """Set up test environment"""
        db_manager.clear_all_data()
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test project in database
        self.test_project = db_manager.create_project({
            'name': 'Integration Test Project',
            'file_path': str(self.test_path),
            'project_type': 'code'
        })
        
        self.manager = evidence_manager
    
    def tearDown(self):
        """Clean up"""
        db_manager.clear_all_data()
        shutil.rmtree(self.test_dir)
    
    def test_extract_and_store_workflow(self):
        """Test complete workflow of extracting and storing evidence"""
        # Create test files
        readme = """
# Test Project
![Coverage](https://codecov.io/badge)
Serves 500+ users
        """
        (self.test_path / 'README.md').write_text(readme)
        
        coverage_data = {'total': {'lines': {'pct': 85.0}}}
        with open(self.test_path / 'coverage.json', 'w') as f:
            json.dump(coverage_data, f)
        
        # Extract and store
        evidence = self.manager.extract_and_store_evidence(
            self.test_project, 
            str(self.test_path)
        )
        
        # Verify stored in database
        retrieved = self.manager.get_evidence(self.test_project.id)
        
        self.assertIsNotNone(retrieved)
        self.assertIn('readme_badges', retrieved)
        self.assertIn('test_coverage', retrieved)
        self.assertEqual(retrieved['test_coverage'], 85.0)
    
    def test_mixed_auto_and_manual_evidence(self):
        """Test combining automatic and manual evidence"""
        # Add automatic evidence
        (self.test_path / 'README.md').write_text('# Test')
        self.manager.extract_and_store_evidence(self.test_project, str(self.test_path))
        
        # Add manual evidence
        self.manager.add_manual_metric(self.test_project.id, 'revenue', 50000, 'Monthly revenue')
        self.manager.add_feedback(self.test_project.id, 'Excellent project!', 'Client')
        self.manager.add_achievement(self.test_project.id, 'Featured in newsletter')
        
        # Retrieve and verify all evidence is present
        evidence = self.manager.get_evidence(self.test_project.id)
        
        self.assertIn('documentation', evidence)  # Auto
        self.assertIn('manual_metrics', evidence)  # Manual
        self.assertIn('feedback', evidence)  # Manual
        self.assertIn('achievements', evidence)  # Manual


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEvidenceManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoEvidenceExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestEvidenceIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)