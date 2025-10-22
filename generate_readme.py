#!/usr/bin/env python3
"""
GitHub Profile README Generator
Automatically generates a beautiful README.md with GitHub statistics
"""

import os
import sys
import yaml
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict


class GitHubStatsGenerator:
    """Generates GitHub statistics and README markdown"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.token = os.environ.get('GIT_TOKEN')

        if not self.token:
            raise ValueError("GIT_TOKEN environment variable is required")

        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.username = None

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML, JSON or TOML file"""
        if not os.path.exists(config_path):
            print(f"Warning: Config file {config_path} not found. Using defaults.")
            return self.get_default_config()

        with open(config_path, 'r') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config = yaml.safe_load(f)
            elif config_path.endswith('.json'):
                config = json.load(f)
            elif config_path.endswith('.toml'):
                import toml
                config = toml.load(f)
            else:
                raise ValueError("Config file must be .yaml, .yml, .json, or .toml")

            # If config is None or empty, use defaults
            if not config:
                print(f"Warning: Config file {config_path} is empty. Using defaults.")
                return self.get_default_config()

            return config

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'profile': {
                'name': 'Developer',
                'description': 'Passionate software developer'
            },
            'repositories': {
                'include': [],
                'exclude': []
            },
            'languages': {
                'exclude': []
            }
        }

    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        response = requests.get(f'{self.base_url}/user', headers=self.headers)
        response.raise_for_status()
        user_data = response.json()
        self.username = user_data['login']
        return user_data

    def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories for the authenticated user"""
        repos = []
        page = 1

        while True:
            response = requests.get(
                f'{self.base_url}/user/repos',
                headers=self.headers,
                params={'page': page, 'per_page': 100, 'type': 'owner'}
            )
            response.raise_for_status()

            page_repos = response.json()
            if not page_repos:
                break

            repos.extend(page_repos)
            page += 1

        # Add explicitly included repositories
        included = self.config.get('repositories', {}).get('include', []) or []
        for repo_full_name in included:
            try:
                response = requests.get(
                    f'{self.base_url}/repos/{repo_full_name}',
                    headers=self.headers
                )
                if response.status_code == 200:
                    repos.append(response.json())
            except Exception as e:
                print(f"Warning: Could not fetch included repo {repo_full_name}: {e}")

        # Filter out excluded repositories
        excluded = self.config.get('repositories', {}).get('exclude', []) or []
        excluded = set(excluded)
        repos = [r for r in repos if r['full_name'] not in excluded]

        return repos

    def get_repo_languages(self, repo_full_name: str) -> Dict[str, int]:
        """Get languages used in a repository"""
        try:
            response = requests.get(
                f'{self.base_url}/repos/{repo_full_name}/languages',
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Warning: Could not fetch languages for {repo_full_name}: {e}")
            return {}

    def get_repo_stats(self, repo: Dict[str, Any], languages: Dict[str, int]) -> Dict[str, Any]:
        """Get detailed statistics for a repository"""
        try:
            response = requests.get(
                f'{self.base_url}/repos/{repo["full_name"]}/stats/code_frequency',
                headers=self.headers,
                timeout=10
            )

            total_additions = 0
            total_deletions = 0

            if response.status_code == 200:
                stats = response.json()
                # stats can be None if GitHub is still computing
                if stats and isinstance(stats, list):
                    for week_stats in stats:
                        total_additions += week_stats[1]
                        total_deletions += abs(week_stats[2])
                else:
                    print(f"Info: Stats not yet available for {repo['full_name']} (GitHub is computing)")
            elif response.status_code == 202:
                print(f"Info: Stats being computed for {repo['full_name']}, will be available later")

            # If we got no data or unreasonable data, use languages bytes as fallback
            # Approximate: 1 byte ≈ 1 character, average ~40 chars per line
            if total_additions == 0 and languages:
                total_bytes = sum(languages.values())
                total_additions = total_bytes // 40  # Rough approximation
                print(f"Info: Using language bytes approximation for {repo['full_name']}: ~{total_additions:,} lines")

            # Sanity check: if lines > 10 million, it's probably wrong
            if total_additions > 10_000_000:
                print(f"Warning: Unrealistic line count ({total_additions:,}) for {repo['full_name']}, using approximation")
                if languages:
                    total_bytes = sum(languages.values())
                    total_additions = total_bytes // 40
                else:
                    total_additions = 0

            return {
                'additions': total_additions,
                'deletions': total_deletions,
                'total_lines': total_additions
            }
        except Exception as e:
            print(f"Warning: Could not fetch stats for {repo['full_name']}: {e}")
            # Use language bytes as fallback
            if languages:
                total_bytes = sum(languages.values())
                estimated_lines = total_bytes // 40
                return {'additions': estimated_lines, 'deletions': 0, 'total_lines': estimated_lines}
            return {'additions': 0, 'deletions': 0, 'total_lines': 0}

    def calculate_statistics(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall statistics from repositories"""
        language_stats = defaultdict(int)
        total_lines = 0
        repo_stats = []

        print(f"Processing {len(repos)} repositories...")

        for i, repo in enumerate(repos):
            print(f"Processing {i+1}/{len(repos)}: {repo['name']}")

            # Get languages
            languages = self.get_repo_languages(repo['full_name'])
            excluded_langs = self.config.get('languages', {}).get('exclude', []) or []
            excluded_langs = set(excluded_langs)

            for lang, bytes_count in languages.items():
                if lang not in excluded_langs:
                    language_stats[lang] += bytes_count

            # Get code stats (pass languages for fallback calculation)
            stats = self.get_repo_stats(repo, languages)
            total_lines += stats['total_lines']

            repo_stats.append({
                'name': repo['name'],
                'full_name': repo['full_name'],
                'description': repo.get('description', ''),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'language': repo.get('language', 'Unknown'),
                'lines': stats['total_lines'],
                'url': repo['html_url']
            })

        # Sort repos by stars first, then by lines of code
        sorted_repos = sorted(repo_stats, key=lambda x: (x['stars'], x['lines']), reverse=True)

        # Handle pinned repos
        pinned = self.config.get('repositories', {}).get('pinned', {}) or {}
        top_repos = []
        used_repos = set()

        # First, place pinned repos in their designated positions
        pinned_positions = {}
        for repo_name, position in pinned.items():
            # Find the repo in sorted list
            for repo in sorted_repos:
                if repo['name'] == repo_name or repo['full_name'] == repo_name:
                    pinned_positions[position] = repo
                    used_repos.add(repo['full_name'])
                    break

        # Build top 5 with pinned repos in correct positions
        non_pinned_repos = [r for r in sorted_repos if r['full_name'] not in used_repos]
        non_pinned_idx = 0

        for pos in range(1, 6):  # Positions 1-5
            if pos in pinned_positions:
                top_repos.append(pinned_positions[pos])
            else:
                if non_pinned_idx < len(non_pinned_repos):
                    top_repos.append(non_pinned_repos[non_pinned_idx])
                    non_pinned_idx += 1

        # Sort languages by usage
        top_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'total_repos': len(repos),
            'total_lines': total_lines,
            'top_repos': top_repos,
            'top_languages': top_languages,
            'language_stats': dict(language_stats),
            'all_repos': sorted_repos
        }

    def generate_markdown(self, user_info: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """Generate the markdown content"""
        name = self.config.get('profile', {}).get('name', user_info['name'] or user_info['login'])
        description = self.config.get('profile', {}).get('description', user_info.get('bio', ''))

        md = f"""# Hi, Welcome to {user_info['login']}'s Profile! 👋

{description}

## 📊 GitHub Statistics

"""

        # Overall stats
        md += f"""### 📈 Overview

- 🗂️ **Total Repositories**: {stats['total_repos']}
- 📝 **Total Lines of Code**: {stats['total_lines']:,}
- ⭐ **Total Stars**: {sum(r['stars'] for r in stats['all_repos'])}
- 🔱 **Total Forks**: {sum(r['forks'] for r in stats['all_repos'])}

---

"""

        # Top languages (Tech Stack)
        md += "### 💻 Tech Stack / Languages\n\n"

        total_bytes = sum(bytes_count for _, bytes_count in stats['top_languages'])

        if stats['top_languages']:
            for i, (lang, bytes_count) in enumerate(stats['top_languages'], 1):
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                bar_length = int(percentage / 2)
                bar = '█' * bar_length + '░' * (50 - bar_length)
                md += f"{i}. **{lang}** - {percentage:.1f}%\n"
                md += f"   ```\n   {bar}\n   ```\n\n"
        else:
            md += "No language data available.\n\n"

        md += "---\n\n"

        # Top repositories
        md += "### 🏆 Top 5 Repositories\n\n"

        if stats['top_repos']:
            for i, repo in enumerate(stats['top_repos'], 1):
                md += f"{i}. **[{repo['name']}]({repo['url']})** - ⭐ {repo['stars']} | 🔱 {repo['forks']}\n"
                if repo['description']:
                    md += f"   - {repo['description']}\n"
                md += f"   - 💻 Language: {repo['language']} | 📝 Lines: {repo['lines']:,}\n\n"
        else:
            md += "No repositories available.\n\n"

        md += "---\n\n"

        # All repositories
        md += "### 📚 All Repositories\n\n"
        md += "| Repository | Stars | Forks | Language | Lines |\n"
        md += "|------------|-------|-------|----------|-------|\n"

        for repo in stats['all_repos']:  # Already sorted by stars + lines
            md += f"| [{repo['name']}]({repo['url']}) | ⭐ {repo['stars']} | 🔱 {repo['forks']} | {repo['language']} | {repo['lines']:,} |\n"

        md += "\n---\n\n"

        # Footer
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md += f"🤖 This profile was automatically updated on {current_date}\n"

        return md

    def generate(self, output_file: str = "README.md"):
        """Main method to generate the README"""
        print("Fetching user information...")
        user_info = self.get_user_info()
        print(f"Authenticated as: {user_info['login']}")

        print("\nFetching repositories...")
        repos = self.get_repositories()
        print(f"Found {len(repos)} repositories")

        print("\nCalculating statistics...")
        stats = self.calculate_statistics(repos)

        print("\nGenerating markdown...")
        markdown = self.generate_markdown(user_info, stats)

        print(f"\nWriting to {output_file}...")
        with open(output_file, 'w') as f:
            f.write(markdown)

        print(f"✅ Successfully generated {output_file}!")


def main():
    """Main entry point"""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "README.md"

    try:
        generator = GitHubStatsGenerator(config_file)
        generator.generate(output_file)
    except ValueError as e:
        if "GIT_TOKEN" in str(e):
            print(f"❌ Error: {e}", file=sys.stderr)
            print("\n📝 How to fix:", file=sys.stderr)
            print("1. Create a GitHub Personal Access Token:", file=sys.stderr)
            print("   https://github.com/settings/tokens", file=sys.stderr)
            print("2. Select scopes: 'repo' and 'read:user'", file=sys.stderr)
            print("3. Export the token:", file=sys.stderr)
            print("   export GIT_TOKEN='your_token_here'", file=sys.stderr)
            print("4. Run the script again\n", file=sys.stderr)
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
