"""
Automatic Evidence Extractor
Automatically extracts success metrics from project files including:
- README badges (CI/CD, coverage, quality)
- Test coverage reports
- Git statistics
- Documentation metrics
- Performance benchmarks
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess


class AutoEvidenceExtractor:
    """Extracts evidence from project files automatically"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.evidence = {}
    
    def extract_all_evidence(self) -> Dict[str, Any]:
        """
        Extract all available evidence from project
        
        Returns:
            Dictionary containing all extracted evidence
        """
        self.evidence = {}
        
        # Extract from README
        self.extract_readme_badges()
        self.extract_readme_metrics()
        
        # Extract from test coverage
        self.extract_coverage_metrics()
        
        # Skip git statistics - already handled by existing Git insights feature
        # self.extract_git_statistics()
        
        # Extract from CI/CD configs
        self.extract_ci_metrics()
        
        # Extract from documentation
        self.extract_documentation_metrics()
        
        # Extract from package files
        self.extract_package_info()
        
        return self.evidence
    
    def extract_readme_badges(self) -> List[Dict[str, str]]:
        """
        Extract badges from README files
        Badges often indicate: build status, coverage, quality scores, downloads
        
        Returns:
            List of badge dictionaries
        """
        readme_files = [
            'README.md', 'README.MD', 'readme.md',
            'README.txt', 'README.rst', 'README'
        ]
        
        for readme_name in readme_files:
            readme_path = self.project_path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8', errors='ignore')
                    badges = self._parse_badges(content)
                    if badges:
                        self.evidence['readme_badges'] = badges
                        return badges
                except Exception as e:
                    print(f"Error reading README: {e}")
        
        return []
    
    def _parse_badges(self, content: str) -> List[Dict[str, str]]:
        """Parse markdown/HTML badges from content"""
        badges = []
        
        # Markdown badge pattern: ![alt](url)
        md_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        for match in re.finditer(md_pattern, content):
            alt_text = match.group(1)
            url = match.group(2)
            
            badge_info = {
                'alt': alt_text,
                'url': url,
                'type': self._classify_badge(alt_text, url)
            }
            badges.append(badge_info)
        
        # HTML badge pattern: <img alt="..." src="...">
        html_pattern = r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*>'
        for match in re.finditer(html_pattern, content):
            alt_text = match.group(1)
            url = match.group(2)
            
            badge_info = {
                'alt': alt_text,
                'url': url,
                'type': self._classify_badge(alt_text, url)
            }
            badges.append(badge_info)
        
        return badges
    
    def _classify_badge(self, alt_text: str, url: str) -> str:
        """Classify badge type based on text and URL"""
        combined = (alt_text + ' ' + url).lower()
        
        if any(word in combined for word in ['coverage', 'codecov', 'coveralls']):
            return 'coverage'
        elif any(word in combined for word in ['build', 'ci', 'travis', 'github actions', 'circleci']):
            return 'build_status'
        elif any(word in combined for word in ['quality', 'codacy', 'codeclimate', 'lgtm']):
            return 'code_quality'
        elif any(word in combined for word in ['downloads', 'pypi', 'npm']):
            return 'downloads'
        elif any(word in combined for word in ['version', 'release']):
            return 'version'
        elif any(word in combined for word in ['license']):
            return 'license'
        elif any(word in combined for word in ['stars', 'forks']):
            return 'popularity'
        else:
            return 'other'
    
    def extract_readme_metrics(self) -> Dict[str, Any]:
        """
        Extract quantifiable metrics mentioned in README
        Examples: "1000+ users", "95% uptime", "40% faster"
        
        Returns:
            Dictionary of extracted metrics
        """
        readme_files = ['README.md', 'README.MD', 'readme.md', 'README.txt']
        
        for readme_name in readme_files:
            readme_path = self.project_path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8', errors='ignore')
                    metrics = self._extract_metrics_from_text(content)
                    if metrics:
                        self.evidence['readme_metrics'] = metrics
                        return metrics
                except Exception:
                    pass
        
        return {}
    
    def _extract_metrics_from_text(self, text: str) -> Dict[str, Any]:
        """Extract metrics from text using patterns"""
        metrics = {}
        
        # Pattern: "X% improvement/faster/better"
        improvement_pattern = r'(\d+(?:\.\d+)?)\s*%\s*(improvement|faster|better|increase|reduction)'
        for match in re.finditer(improvement_pattern, text, re.IGNORECASE):
            value = float(match.group(1))
            metric_type = match.group(2).lower()
            metrics[f'performance_{metric_type}'] = f"{value}%"
        
        # Pattern: "1000+ users/downloads/customers"
        user_pattern = r'(\d+(?:,\d+)*)\+?\s*(users|downloads|customers|installations|deployments)'
        for match in re.finditer(user_pattern, text, re.IGNORECASE):
            value = match.group(1).replace(',', '')
            metric_type = match.group(2).lower()
            metrics[metric_type] = int(value)
        
        # Pattern: "X MB/GB saved"
        size_pattern = r'(\d+(?:\.\d+)?)\s*(MB|GB|TB)\s*(saved|reduced|optimized)'
        for match in re.finditer(size_pattern, text, re.IGNORECASE):
            value = float(match.group(1))
            unit = match.group(2)
            metrics['size_optimization'] = f"{value} {unit}"
        
        # Pattern: "X stars/forks"
        social_pattern = r'(\d+(?:,\d+)*)\+?\s*(stars|forks|contributors)'
        for match in re.finditer(social_pattern, text, re.IGNORECASE):
            value = match.group(1).replace(',', '')
            metric_type = match.group(2).lower()
            metrics[metric_type] = int(value)
        
        return metrics
    
    def extract_coverage_metrics(self) -> Optional[float]:
        """
        Extract test coverage percentage from coverage reports
        Looks for: coverage.xml, .coverage, htmlcov/index.html, coverage.json
        
        Returns:
            Coverage percentage or None
        """
        coverage_files = [
            'coverage.xml',
            '.coverage',
            'htmlcov/index.html',
            'coverage.json',
            'coverage/coverage.json',
            '.nyc_output/coverage.json',  # Node.js
            'target/site/jacoco/index.html'  # Java
        ]
        
        for coverage_file in coverage_files:
            file_path = self.project_path / coverage_file
            if file_path.exists():
                try:
                    coverage = self._parse_coverage_file(file_path)
                    if coverage is not None:
                        self.evidence['test_coverage'] = round(coverage, 2)
                        return coverage
                except Exception as e:
                    print(f"Error parsing coverage file {coverage_file}: {e}")
        
        return None
    
    def _parse_coverage_file(self, file_path: Path) -> Optional[float]:
        """Parse coverage from various file formats"""
        try:
            if file_path.suffix == '.xml':
                # Parse XML coverage report
                content = file_path.read_text(encoding='utf-8')
                # Look for coverage percentage in XML
                match = re.search(r'line-rate="([0-9.]+)"', content)
                if match:
                    return float(match.group(1)) * 100
            
            elif file_path.suffix == '.json':
                # Parse JSON coverage report
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Try different JSON structures
                if 'total' in data and 'lines' in data['total']:
                    return data['total']['lines'].get('pct', 0)
                elif 'coverage' in data:
                    return data['coverage']
            
            elif file_path.suffix == '.html':
                # Parse HTML coverage report
                content = file_path.read_text(encoding='utf-8')
                # Look for coverage percentage in HTML
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*%\s*coverage',
                    r'total.*?(\d+(?:\.\d+)?)\s*%',
                    r'<span[^>]*>(\d+(?:\.\d+)?)\s*%</span>'
                ]
                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        return float(match.group(1))
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return None
    
    def extract_git_statistics(self) -> Dict[str, Any]:
        """
        DEPRECATED: Git statistics are now handled by the existing Git insights feature.
        This method is kept for backward compatibility but does nothing.
        
        Returns:
            Empty dictionary
        """
        # Git statistics (commits, contributors, lines added/deleted) are already
        # captured by the project's existing Git analysis features.
        # No need to duplicate this information in evidence.
        return {}
    
    def extract_ci_metrics(self) -> Dict[str, Any]:
        """
        Extract metrics from CI/CD configuration files
        
        Returns:
            Dictionary with CI metrics
        """
        ci_configs = [
            '.github/workflows',
            '.gitlab-ci.yml',
            '.travis.yml',
            'circle.yml',
            '.circleci/config.yml',
            'Jenkinsfile'
        ]
        
        ci_info = {}
        
        for config in ci_configs:
            config_path = self.project_path / config
            if config_path.exists():
                if '.github/workflows' in config:
                    ci_info['ci_platform'] = 'GitHub Actions'
                elif '.gitlab' in config:
                    ci_info['ci_platform'] = 'GitLab CI'
                elif 'travis' in config:
                    ci_info['ci_platform'] = 'Travis CI'
                elif 'circle' in config:
                    ci_info['ci_platform'] = 'CircleCI'
                elif 'Jenkins' in config:
                    ci_info['ci_platform'] = 'Jenkins'
                
                ci_info['has_ci_cd'] = True
                break
        
        if ci_info:
            self.evidence['ci_metrics'] = ci_info
        
        return ci_info
    
    def extract_documentation_metrics(self) -> Dict[str, int]:
        """
        Extract documentation metrics
        
        Returns:
            Dictionary with documentation stats
        """
        doc_stats = {
            'readme_lines': 0,
            'doc_files': 0,
            'has_contributing_guide': False,
            'has_license': False
        }
        
        # Count README lines
        for readme in ['README.md', 'README.MD', 'readme.md']:
            readme_path = self.project_path / readme
            if readme_path.exists():
                try:
                    lines = len(readme_path.read_text(encoding='utf-8').split('\n'))
                    doc_stats['readme_lines'] = lines
                except Exception:
                    pass
                break
        
        # Count documentation files
        doc_dirs = ['docs', 'documentation', 'doc']
        for doc_dir in doc_dirs:
            doc_path = self.project_path / doc_dir
            if doc_path.exists() and doc_path.is_dir():
                doc_files = list(doc_path.rglob('*.md')) + list(doc_path.rglob('*.rst'))
                doc_stats['doc_files'] = len(doc_files)
                break
        
        # Check for standard files
        if (self.project_path / 'CONTRIBUTING.md').exists():
            doc_stats['has_contributing_guide'] = True
        
        if any((self.project_path / f).exists() for f in ['LICENSE', 'LICENSE.md', 'LICENSE.txt']):
            doc_stats['has_license'] = True
        
        if any(v for v in doc_stats.values()):
            self.evidence['documentation'] = doc_stats
        
        return doc_stats
    
    def extract_package_info(self) -> Dict[str, Any]:
        """
        Extract information from package files (package.json, pyproject.toml, etc.)
        
        Returns:
            Dictionary with package information
        """
        package_info = {}
        
        # Python packages
        for file_name in ['pyproject.toml', 'setup.py', 'requirements.txt']:
            if (self.project_path / file_name).exists():
                package_info['package_manager'] = 'pip/poetry'
                break
        
        # Node.js packages
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                package_info['package_manager'] = 'npm'
                
                if 'version' in data:
                    package_info['version'] = data['version']
                
                if 'dependencies' in data:
                    package_info['dependencies_count'] = len(data['dependencies'])
                
                if 'devDependencies' in data:
                    package_info['dev_dependencies_count'] = len(data['devDependencies'])
            
            except Exception:
                pass
        
        if package_info:
            self.evidence['package_info'] = package_info
        
        return package_info


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        extractor = AutoEvidenceExtractor(project_path)
        evidence = extractor.extract_all_evidence()
        
        print("=== EXTRACTED EVIDENCE ===")
        print(json.dumps(evidence, indent=2))
    else:
        print("Usage: python autoExtractor.py <project_path>")