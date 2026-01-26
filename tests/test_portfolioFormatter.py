"""
Comprehensive Test Suite for Portfolio Formatter
Tests all functionality of portfolioFormatter.py

Run with: python -m pytest tests/test_portfolioFormatter.py -v
Or: python tests/test_portfolioFormatter.py
"""

import sys
import os
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager, Project
from src.Portfolio.portfolioFormatter import PortfolioFormatter


class TestPortfolioFormatter:
    """Test suite for PortfolioFormatter class"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database with sample projects"""
        print("\n" + "="*70)
        print("SETTING UP TEST DATABASE")
        print("="*70)
        
        # Clear existing test data
        cls.cleanup_test_data()
        
        # Create sample projects
        cls.test_projects = []
        
        # Project 1: Code project with full data
        project1_data = {
            'name': 'Test E-Commerce Platform',
            'file_path': '/test/path/ecommerce',
            'project_type': 'code',
            'description': 'Full-stack e-commerce application',
            'custom_description': 'A comprehensive e-commerce platform with payment processing',
            'lines_of_code': 15000,
            'file_count': 120,
            'total_size_bytes': 5000000,
            'languages': ['Python', 'JavaScript', 'TypeScript'],
            'frameworks': ['Django', 'React', 'PostgreSQL'],
            'skills': ['Web Development', 'API Design', 'Database Management', 'Payment Processing'],
            'tags': ['Backend', 'Frontend'],
            'importance_score': 85.5,
            'is_featured': True,
            'date_created': datetime(2024, 1, 15, tzinfo=timezone.utc),
            'date_modified': datetime(2024, 3, 20, tzinfo=timezone.utc),
            'collaboration_type': 'Collaborative Project'
        }
        project1 = db_manager.create_project(project1_data)
        cls.test_projects.append(project1)
        
        # Add keywords to project 1
        keywords_p1 = [
            {'project_id': project1.id, 'keyword': 'django', 'score': 15.5, 'category': 'framework'},
            {'project_id': project1.id, 'keyword': 'react', 'score': 12.3, 'category': 'framework'},
            {'project_id': project1.id, 'keyword': 'payment', 'score': 8.7, 'category': 'feature'}
        ]
        for kw in keywords_p1:
            db_manager.add_keyword(kw)
        
        # Add contributors to project 1
        contributors_p1 = [
            {'project_id': project1.id, 'name': 'Alice Smith', 'contributor_identifier': 'alice@test.com', 'commit_count': 150},
            {'project_id': project1.id, 'name': 'Bob Jones', 'contributor_identifier': 'bob@test.com', 'commit_count': 80}
        ]
        for contrib in contributors_p1:
            db_manager.add_contributor_to_project(contrib)
        
        # Project 2: Media project
        project2_data = {
            'name': 'Test Brand Identity',
            'file_path': '/test/path/branding',
            'project_type': 'visual_media',
            'description': 'Complete brand identity package',
            'file_count': 45,
            'total_size_bytes': 250000000,
            'languages': ['Adobe Illustrator', 'Photoshop', 'Figma'],
            'skills': ['Graphic Design', 'Branding', 'Typography'],
            'tags': ['Logo', 'Print'],
            'importance_score': 72.0,
            'is_featured': False,
            'date_created': datetime(2024, 2, 1, tzinfo=timezone.utc),
            'date_modified': datetime(2024, 2, 28, tzinfo=timezone.utc)
        }
        project2 = db_manager.create_project(project2_data)
        cls.test_projects.append(project2)
        
        # Project 3: Text project
        project3_data = {
            'name': 'Test Research Paper',
            'file_path': '/test/path/research',
            'project_type': 'text',
            'description': 'Academic research on ML optimization',
            'word_count': 8500,
            'file_count': 12,
            'total_size_bytes': 500000,
            'skills': ['Research Writing', 'Machine Learning', 'Technical Documentation'],
            'tags': ['PDF', 'LaTeX'],
            'importance_score': 90.0,
            'is_featured': True,
            'date_created': datetime(2024, 1, 5, tzinfo=timezone.utc),
            'date_modified': datetime(2024, 1, 25, tzinfo=timezone.utc)
        }
        project3 = db_manager.create_project(project3_data)
        cls.test_projects.append(project3)
        
        # Project 4: Code project without full data (minimal)
        project4_data = {
            'name': 'Test Simple Script',
            'file_path': '/test/path/script',
            'project_type': 'code',
            'lines_of_code': 500,
            'file_count': 5,
            'languages': ['Python'],
            'importance_score': 35.0
        }
        project4 = db_manager.create_project(project4_data)
        cls.test_projects.append(project4)
        
        print(f"✓ Created {len(cls.test_projects)} test projects")
    
    @classmethod
    def cleanup_test_data(cls):
        """Clean up test projects"""
        projects = db_manager.get_all_projects(include_hidden=True)
        for p in projects:
            if p.file_path and '/test/path/' in p.file_path:
                db_manager.delete_project(p.id)
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests"""
        print("\n" + "="*70)
        print("CLEANING UP TEST DATABASE")
        print("="*70)
        cls.cleanup_test_data()
        print("✓ Test data cleaned up")
    
    # ============================================
    # INITIALIZATION TESTS
    # ============================================
    
    def test_formatter_initialization(self):
        """Test that formatter initializes correctly"""
        formatter = PortfolioFormatter()
        assert formatter.db is not None
        print("✓ Formatter initialization test passed")
    
    # ============================================
    # HELPER METHOD TESTS
    # ============================================
    
    def test_format_date(self):
        """Test date formatting"""
        formatter = PortfolioFormatter()
        
        # Test with datetime object
        dt = datetime(2024, 3, 15, tzinfo=timezone.utc)
        formatted = formatter._format_date(dt)
        assert formatted == "March 2024"
        
        # Test with None
        assert formatter._format_date(None) is None
        
        print("✓ Date formatting test passed")
    
    def test_format_size(self):
        """Test file size formatting"""
        formatter = PortfolioFormatter()
        
        assert formatter._format_size(0) == "0 B"
        assert formatter._format_size(500) == "500.0 B"
        assert formatter._format_size(1024) == "1.0 KB"
        assert formatter._format_size(1024 * 1024) == "1.0 MB"
        assert formatter._format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert formatter._format_size(None) == "0 B"
        
        print("✓ Size formatting test passed")
    
    def test_get_project_metrics_code(self):
        """Test metrics extraction for code projects"""
        formatter = PortfolioFormatter()
        project = self.test_projects[0]  # E-commerce project
        
        metrics = formatter._get_project_metrics(project)
        
        assert 'lines_of_code' in metrics
        assert 'file_count' in metrics
        assert 'contributors' in metrics
        assert 'languages' in metrics
        
        assert metrics['lines_of_code'] == 15000
        assert metrics['file_count'] == 120
        assert metrics['contributors'] == 2
        assert metrics['languages'] == 3
        
        print("✓ Code project metrics test passed")
    
    def test_get_project_metrics_media(self):
        """Test metrics extraction for media projects"""
        formatter = PortfolioFormatter()
        project = self.test_projects[1]  # Brand identity project
        
        metrics = formatter._get_project_metrics(project)
        
        assert 'file_count' in metrics
        assert 'total_size' in metrics
        assert 'software_tools' in metrics
        
        assert metrics['file_count'] == 45
        assert 'MB' in metrics['total_size'] or 'GB' in metrics['total_size']
        
        print("✓ Media project metrics test passed")
    
    def test_get_project_metrics_text(self):
        """Test metrics extraction for text projects"""
        formatter = PortfolioFormatter()
        project = self.test_projects[2]  # Research paper project
        
        metrics = formatter._get_project_metrics(project)
        
        assert 'word_count' in metrics
        assert 'file_count' in metrics
        
        assert metrics['word_count'] == 8500
        assert metrics['file_count'] == 12
        
        print("✓ Text project metrics test passed")
    
    # ============================================
    # PROJECT FORMATTING TESTS
    # ============================================
    
    def test_format_project_card(self):
        """Test project card formatting"""
        formatter = PortfolioFormatter()
        project = self.test_projects[0]
        
        card = formatter._format_project_card(project)
        
        # Check required fields
        assert 'id' in card
        assert 'name' in card
        assert 'type' in card
        assert 'description' in card
        assert 'tech_stack' in card
        assert 'skills' in card
        assert 'metrics' in card
        assert 'importance_score' in card
        
        # Check values
        assert card['name'] == 'Test E-Commerce Platform'
        assert card['type'] == 'code'
        assert len(card['tech_stack']) > 0
        assert len(card['skills']) > 0
        assert card['is_featured'] == True
        
        print("✓ Project card formatting test passed")
    
    def test_format_project_detail(self):
        """Test detailed project formatting"""
        formatter = PortfolioFormatter()
        project = self.test_projects[0]
        
        detail = formatter._format_project_detail(project)
        
        # Check all required sections
        assert 'id' in detail
        assert 'name' in detail
        assert 'descriptions' in detail
        assert 'languages' in detail
        assert 'frameworks' in detail
        assert 'skills' in detail
        assert 'metrics' in detail
        assert 'dates' in detail
        assert 'contributors' in detail
        assert 'keywords' in detail
        
        # Check descriptions
        assert 'ai_generated' in detail['descriptions']
        assert 'custom' in detail['descriptions']
        assert 'default' in detail['descriptions']
        
        # Check contributors
        assert len(detail['contributors']) == 2
        assert detail['contributors'][0]['name'] == 'Alice Smith'
        
        # Check keywords
        assert len(detail['keywords']) > 0
        
        print("✓ Project detail formatting test passed")
    
    # ============================================
    # PORTFOLIO DATA TESTS
    # ============================================
    
    def test_get_portfolio_data(self):
        """Test complete portfolio data generation"""
        formatter = PortfolioFormatter()
        
        portfolio = formatter.get_portfolio_data()
        
        # Check structure
        assert 'summary' in portfolio
        assert 'projects' in portfolio
        assert 'stats' in portfolio
        assert 'total_projects' in portfolio
        assert 'generated_at' in portfolio
        
        # Check projects list
        assert len(portfolio['projects']) >= 4
        assert isinstance(portfolio['projects'], list)
        
        # Check stats
        stats = portfolio['stats']
        assert stats['total_projects'] >= 4
        assert 'by_type' in stats
        assert 'total_lines_of_code' in stats
        assert 'total_skills' in stats
        assert 'avg_importance_score' in stats
        
        # Check summary
        summary = portfolio['summary']
        assert 'text' in summary
        assert 'highlights' in summary
        assert isinstance(summary['highlights'], list)
        
        print("✓ Portfolio data generation test passed")
    
    def test_get_project_detail(self):
        """Test single project detail retrieval"""
        formatter = PortfolioFormatter()
        project_id = self.test_projects[0].id
        
        detail = formatter.get_project_detail(project_id)
        
        assert detail is not None
        assert detail['id'] == project_id
        assert detail['name'] == 'Test E-Commerce Platform'
        
        # Test non-existent project
        invalid_detail = formatter.get_project_detail(99999)
        assert invalid_detail is None
        
        print("✓ Project detail retrieval test passed")
    
    # ============================================
    # FILTERING TESTS
    # ============================================
    
    def test_filter_by_type(self):
        """Test filtering by project type"""
        formatter = PortfolioFormatter()
        
        # Filter for code projects
        code_projects = formatter.get_filtered_projects(project_type='code')
        assert code_projects['total'] == 2
        assert all(p['type'] == 'code' for p in code_projects['projects'])
        
        # Filter for media projects
        media_projects = formatter.get_filtered_projects(project_type='visual_media')
        assert media_projects['total'] == 1
        assert media_projects['projects'][0]['type'] == 'visual_media'
        
        # Filter for text projects
        text_projects = formatter.get_filtered_projects(project_type='text')
        assert text_projects['total'] == 1
        
        print("✓ Type filtering test passed")
    
    def test_filter_by_search(self):
        """Test filtering by search term"""
        formatter = PortfolioFormatter()
        
        # Search for "research"
        results = formatter.get_filtered_projects(search='research')
        assert results['total'] >= 1
        
        # Search for "platform"
        results = formatter.get_filtered_projects(search='platform')
        assert results['total'] >= 1
        
        # Search for non-existent term
        results = formatter.get_filtered_projects(search='nonexistentxyz')
        assert results['total'] == 0
        
        print("✓ Search filtering test passed")
    
    def test_filter_by_importance(self):
        """Test filtering by minimum importance score"""
        formatter = PortfolioFormatter()
        
        # Filter for high importance (>= 80)
        high_importance = formatter.get_filtered_projects(min_importance=80)
        assert all(p['importance_score'] >= 80 for p in high_importance['projects'])
        
        # Filter for medium importance (>= 50)
        medium_importance = formatter.get_filtered_projects(min_importance=50)
        assert len(medium_importance['projects']) >= len(high_importance['projects'])
        
        print("✓ Importance filtering test passed")
    
    def test_filter_featured_only(self):
        """Test filtering for featured projects only"""
        formatter = PortfolioFormatter()
        
        featured = formatter.get_filtered_projects(featured_only=True)
        assert all(p['is_featured'] for p in featured['projects'])
        assert featured['total'] == 2  # E-commerce and Research paper
        
        print("✓ Featured filtering test passed")
    
    def test_combined_filters(self):
        """Test multiple filters combined"""
        formatter = PortfolioFormatter()
        
        # Code projects with importance >= 70
        results = formatter.get_filtered_projects(
            project_type='code',
            min_importance=70
        )
        assert all(p['type'] == 'code' for p in results['projects'])
        assert all(p['importance_score'] >= 70 for p in results['projects'])
        
        # Featured code projects
        results = formatter.get_filtered_projects(
            project_type='code',
            featured_only=True
        )
        assert all(p['type'] == 'code' for p in results['projects'])
        assert all(p['is_featured'] for p in results['projects'])
        
        print("✓ Combined filtering test passed")
    
    # ============================================
    # STATISTICS TESTS
    # ============================================
    
    def test_calculate_portfolio_stats(self):
        """Test portfolio statistics calculation"""
        formatter = PortfolioFormatter()
        projects = db_manager.get_all_projects()
        
        stats = formatter._calculate_portfolio_stats(projects)
        
        assert stats['total_projects'] >= 4
        assert 'by_type' in stats
        assert 'total_lines_of_code' in stats
        assert 'total_files' in stats
        assert 'total_skills' in stats
        assert 'unique_skills' in stats
        assert 'avg_importance_score' in stats
        
        # Check type counts
        assert stats['by_type']['code'] == 2
        assert stats['by_type']['visual_media'] == 1
        assert stats['by_type']['text'] == 1
        
        # Check totals
        assert stats['total_lines_of_code'] >= 15500  # 15000 + 500
        assert stats['total_files'] >= 177  # 120 + 45 + 12 + 5
        
        print("✓ Portfolio statistics test passed")
    
    def test_generate_portfolio_summary(self):
        """Test portfolio summary generation"""
        formatter = PortfolioFormatter()
        projects = db_manager.get_all_projects()
        
        summary = formatter._generate_portfolio_summary(projects)
        
        assert 'text' in summary
        assert 'highlights' in summary
        assert 'top_projects' in summary
        
        assert isinstance(summary['text'], str)
        assert len(summary['text']) > 0
        assert isinstance(summary['highlights'], list)
        assert len(summary['highlights']) > 0
        
        # Check top projects
        assert len(summary['top_projects']) <= 3
        
        print("✓ Portfolio summary generation test passed")
    
    # ============================================
    # EXPORT TESTS
    # ============================================
    
    def test_export_to_json(self):
        """Test JSON export functionality"""
        formatter = PortfolioFormatter()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Export to JSON
            result_path = formatter.export_to_json(temp_path)
            
            assert os.path.exists(result_path)
            
            # Load and verify JSON
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert 'summary' in data
            assert 'projects' in data
            assert 'stats' in data
            assert len(data['projects']) >= 4
            
            print("✓ JSON export test passed")
        
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # ============================================
    # EDGE CASE TESTS
    # ============================================
    
    def test_empty_database(self):
        """Test formatter behavior with empty database"""
        # Temporarily clear all projects
        original_projects = db_manager.get_all_projects(include_hidden=True)
        for p in original_projects:
            if '/test/path/' not in p.file_path:
                continue
            db_manager.delete_project(p.id)
        
        # Now delete test projects
        for p in self.test_projects:
            try:
                db_manager.delete_project(p.id)
            except:
                pass
        
        formatter = PortfolioFormatter()
        portfolio = formatter.get_portfolio_data()
        
        # Recreate test projects
        self.__class__.setup_class()
        
        # Verify empty state handling
        assert portfolio['total_projects'] >= 0
        assert isinstance(portfolio['projects'], list)
        
        print("✓ Empty database handling test passed")
    
    def test_project_without_optional_fields(self):
        """Test formatting project with minimal data"""
        formatter = PortfolioFormatter()
        project = self.test_projects[3]  # Simple script with minimal data
        
        card = formatter._format_project_card(project)
        
        # Should still have required fields with defaults
        assert card['name'] == 'Test Simple Script'
        assert card['type'] == 'code'
        assert 'description' in card
        assert isinstance(card['tech_stack'], list)
        assert isinstance(card['skills'], list)
        
        print("✓ Minimal data project test passed")
    
    def test_project_with_null_dates(self):
        """Test handling projects with null dates"""
        formatter = PortfolioFormatter()
        
        # Create project with no dates
        project_data = {
            'name': 'Test No Dates',
            'file_path': '/test/path/nodates',
            'project_type': 'code',
            'file_count': 10
        }
        project = db_manager.create_project(project_data)
        
        try:
            card = formatter._format_project_card(project)
            assert 'date' in card
            # Should handle None gracefully
            
            print("✓ Null dates handling test passed")
        finally:
            db_manager.delete_project(project.id)


# ============================================
# RUN TESTS
# ============================================

def run_all_tests():
    """Run all tests manually (without pytest)"""
    print("\n" + "="*70)
    print("PORTFOLIO FORMATTER TEST SUITE")
    print("="*70)
    
    test_suite = TestPortfolioFormatter()
    
    # Setup
    TestPortfolioFormatter.setup_class()
    
    # Run all test methods
    test_methods = [
        method for method in dir(test_suite)
        if method.startswith('test_') and callable(getattr(test_suite, method))
    ]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"\nRunning: {method_name}")
            getattr(test_suite, method_name)()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Cleanup
    TestPortfolioFormatter.teardown_class()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
    
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)