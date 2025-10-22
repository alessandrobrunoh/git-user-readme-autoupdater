#!/usr/bin/env python3
"""
Test script to verify README generation logic without GitHub API calls
"""

import os
import sys

# Mock the GIT_TOKEN for testing
os.environ['GIT_TOKEN'] = 'mock_token_for_testing'

# Import after setting the env var
from generate_readme import GitHubStatsGenerator
from datetime import datetime


def create_mock_generator():
    """Create a generator with mocked methods"""
    gen = GitHubStatsGenerator('config.yaml')

    # Store original methods
    original_get_user_info = gen.get_user_info
    original_get_repositories = gen.get_repositories
    original_get_repo_languages = gen.get_repo_languages
    original_get_repo_stats = gen.get_repo_stats

    # Mock user info
    def mock_get_user_info():
        return {
            'login': 'testuser',
            'name': 'Test User',
            'bio': 'A passionate developer',
            'html_url': 'https://github.com/testuser'
        }

    # Mock repositories
    def mock_get_repositories():
        return [
            {
                'name': 'awesome-project',
                'full_name': 'testuser/awesome-project',
                'description': 'An awesome project that does amazing things',
                'stargazers_count': 150,
                'forks_count': 30,
                'language': 'Python',
                'html_url': 'https://github.com/testuser/awesome-project'
            },
            {
                'name': 'cool-app',
                'full_name': 'testuser/cool-app',
                'description': 'A cool application',
                'stargazers_count': 75,
                'forks_count': 15,
                'language': 'JavaScript',
                'html_url': 'https://github.com/testuser/cool-app'
            },
            {
                'name': 'data-analyzer',
                'full_name': 'testuser/data-analyzer',
                'description': 'Data analysis tool',
                'stargazers_count': 50,
                'forks_count': 10,
                'language': 'Python',
                'html_url': 'https://github.com/testuser/data-analyzer'
            },
            {
                'name': 'web-scraper',
                'full_name': 'testuser/web-scraper',
                'description': 'Web scraping utility',
                'stargazers_count': 25,
                'forks_count': 5,
                'language': 'Go',
                'html_url': 'https://github.com/testuser/web-scraper'
            },
            {
                'name': 'mobile-app',
                'full_name': 'testuser/mobile-app',
                'description': 'Mobile application',
                'stargazers_count': 100,
                'forks_count': 20,
                'language': 'TypeScript',
                'html_url': 'https://github.com/testuser/mobile-app'
            }
        ]

    # Mock languages
    def mock_get_repo_languages(repo_full_name):
        languages_map = {
            'testuser/awesome-project': {'Python': 45000, 'Shell': 500},
            'testuser/cool-app': {'JavaScript': 35000, 'HTML': 5000, 'CSS': 3000},
            'testuser/data-analyzer': {'Python': 30000, 'Jupyter Notebook': 2000},
            'testuser/web-scraper': {'Go': 25000},
            'testuser/mobile-app': {'TypeScript': 40000, 'JavaScript': 5000}
        }
        return languages_map.get(repo_full_name, {})

    # Mock stats
    def mock_get_repo_stats(repo):
        lines_map = {
            'testuser/awesome-project': 5000,
            'testuser/cool-app': 3500,
            'testuser/data-analyzer': 2800,
            'testuser/web-scraper': 2000,
            'testuser/mobile-app': 4200
        }
        lines = lines_map.get(repo['full_name'], 1000)
        return {
            'additions': lines,
            'deletions': int(lines * 0.2),
            'total_lines': lines
        }

    # Replace methods
    gen.get_user_info = mock_get_user_info
    gen.get_repositories = mock_get_repositories
    gen.get_repo_languages = mock_get_repo_languages
    gen.get_repo_stats = mock_get_repo_stats

    return gen


def test_generate():
    """Test the generation process"""
    print("🧪 Testing README generation with mock data...\n")

    try:
        gen = create_mock_generator()
        gen.generate('TEST_README.md')

        print("\n✅ Test successful! Check TEST_README.md for output.")

        # Display the generated file
        print("\n" + "=" * 60)
        print("Generated README Preview:")
        print("=" * 60 + "\n")

        with open('TEST_README.md', 'r') as f:
            content = f.read()
            # Print first 50 lines
            lines = content.split('\n')
            for i, line in enumerate(lines[:50], 1):
                print(line)

            if len(lines) > 50:
                print(f"\n... and {len(lines) - 50} more lines")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_generate()
    sys.exit(0 if success else 1)
