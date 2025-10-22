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
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
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
                'exclude': [],
                'pinned': {}
            },
            'languages': {
                'exclude': []
            },
            'tech_stack': {
                'custom': []  # Custom technologies to add
            },
            'top_repos': {
                'strategy': 'language_proportional',  # or 'stars', 'lines', 'mixed'
                'count': 5
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

    def get_file_content(self, repo_full_name: str, file_path: str) -> Optional[str]:
        """Get content of a specific file from repository"""
        try:
            response = requests.get(
                f'{self.base_url}/repos/{repo_full_name}/contents/{file_path}',
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                import base64
                content = response.json().get('content', '')
                return base64.b64decode(content).decode('utf-8')
            return None
        except Exception:
            return None

    def detect_tech_stack(self, repo_full_name: str, languages: Dict[str, int]) -> Set[str]:
        """Detect technologies and frameworks used in a repository"""
        tech_stack = set()

        # Technology detection mappings
        dependency_files = {
            'Cargo.toml': self._parse_cargo_toml,
            'package.json': self._parse_package_json,
            'pom.xml': self._parse_pom_xml,
            'build.gradle': self._parse_gradle,
            'requirements.txt': self._parse_requirements_txt,
            'Pipfile': self._parse_pipfile,
            'pubspec.yaml': self._parse_pubspec,
            'go.mod': self._parse_go_mod,
            'composer.json': self._parse_composer_json,
        }

        # Check each dependency file
        for file_name, parser_func in dependency_files.items():
            content = self.get_file_content(repo_full_name, file_name)
            if content:
                tech_stack.update(parser_func(content))

        # Add base languages as technologies
        for lang in languages.keys():
            tech_stack.add(lang)

        return tech_stack

    def _parse_cargo_toml(self, content: str) -> Set[str]:
        """Parse Cargo.toml to detect Rust dependencies"""
        techs = set()
        rust_frameworks = {
            'tokio': 'Tokio',
            'actix': 'Actix',
            'actix-web': 'Actix Web',
            'axum': 'Axum',
            'rocket': 'Rocket',
            'warp': 'Warp',
            'diesel': 'Diesel',
            'sqlx': 'SQLx',
            'serde': 'Serde',
            'clap': 'Clap',
            'rayon': 'Rayon',
            'reqwest': 'Reqwest',
            'hyper': 'Hyper',
            'tonic': 'Tonic (gRPC)',
        }

        for dep, tech in rust_frameworks.items():
            if re.search(rf'\b{dep}\b', content, re.IGNORECASE):
                techs.add(tech)

        return techs

    def _parse_package_json(self, content: str) -> Set[str]:
        """Parse package.json to detect JavaScript/TypeScript dependencies"""
        techs = set()
        try:
            data = json.loads(content)
            all_deps = {}
            all_deps.update(data.get('dependencies', {}))
            all_deps.update(data.get('devDependencies', {}))

            js_frameworks = {
                'react': 'React',
                'next': 'Next.js',
                'vue': 'Vue.js',
                'nuxt': 'Nuxt.js',
                'angular': 'Angular',
                'svelte': 'Svelte',
                'express': 'Express.js',
                'fastify': 'Fastify',
                'nestjs': 'NestJS',
                'koa': 'Koa',
                'axios': 'Axios',
                'graphql': 'GraphQL',
                'apollo': 'Apollo',
                'prisma': 'Prisma',
                'sequelize': 'Sequelize',
                'typeorm': 'TypeORM',
                'mongoose': 'Mongoose',
                'redux': 'Redux',
                'mobx': 'MobX',
                'webpack': 'Webpack',
                'vite': 'Vite',
                'jest': 'Jest',
                'vitest': 'Vitest',
                'cypress': 'Cypress',
                'playwright': 'Playwright',
                'tailwindcss': 'Tailwind CSS',
                'sass': 'Sass',
                'styled-components': 'Styled Components',
            }

            for dep_name, dep_tech in js_frameworks.items():
                if any(dep_name in key.lower() for key in all_deps.keys()):
                    techs.add(dep_tech)

        except Exception:
            pass

        return techs

    def _parse_pom_xml(self, content: str) -> Set[str]:
        """Parse pom.xml to detect Java/Maven dependencies"""
        techs = set()
        techs.add('Maven')

        java_frameworks = {
            'spring-boot': 'Spring Boot',
            'spring-framework': 'Spring Framework',
            'jhipster': 'JHipster',
            'hibernate': 'Hibernate',
            'jakarta.persistence': 'JPA',
            'junit': 'JUnit',
            'mockito': 'Mockito',
            'lombok': 'Lombok',
            'jackson': 'Jackson',
            'logback': 'Logback',
            'slf4j': 'SLF4J',
        }

        for dep, tech in java_frameworks.items():
            if dep in content.lower():
                techs.add(tech)

        return techs

    def _parse_gradle(self, content: str) -> Set[str]:
        """Parse build.gradle to detect Gradle dependencies"""
        techs = set()
        techs.add('Gradle')

        if 'kotlin' in content.lower():
            techs.add('Kotlin')
        if 'spring' in content.lower():
            techs.add('Spring Boot')
        if 'android' in content.lower():
            techs.add('Android')

        return techs

    def _parse_requirements_txt(self, content: str) -> Set[str]:
        """Parse requirements.txt to detect Python dependencies"""
        techs = set()

        python_frameworks = {
            'django': 'Django',
            'flask': 'Flask',
            'fastapi': 'FastAPI',
            'tornado': 'Tornado',
            'aiohttp': 'aiohttp',
            'sqlalchemy': 'SQLAlchemy',
            'pandas': 'Pandas',
            'numpy': 'NumPy',
            'tensorflow': 'TensorFlow',
            'pytorch': 'PyTorch',
            'scikit-learn': 'Scikit-learn',
            'requests': 'Requests',
            'celery': 'Celery',
            'redis': 'Redis',
            'pytest': 'Pytest',
        }

        content_lower = content.lower()
        for dep, tech in python_frameworks.items():
            if dep in content_lower:
                techs.add(tech)

        return techs

    def _parse_pipfile(self, content: str) -> Set[str]:
        """Parse Pipfile to detect Python dependencies"""
        return self._parse_requirements_txt(content)

    def _parse_pubspec(self, content: str) -> Set[str]:
        """Parse pubspec.yaml to detect Flutter/Dart dependencies"""
        techs = {'Flutter', 'Dart'}

        flutter_packages = {
            'provider': 'Provider',
            'riverpod': 'Riverpod',
            'bloc': 'BLoC',
            'get': 'GetX',
            'dio': 'Dio',
            'firebase': 'Firebase',
        }

        content_lower = content.lower()
        for pkg, tech in flutter_packages.items():
            if pkg in content_lower:
                techs.add(tech)

        return techs

    def _parse_go_mod(self, content: str) -> Set[str]:
        """Parse go.mod to detect Go dependencies"""
        techs = {'Go'}

        go_frameworks = {
            'gin': 'Gin',
            'echo': 'Echo',
            'fiber': 'Fiber',
            'chi': 'Chi',
            'gorm': 'GORM',
            'cobra': 'Cobra',
        }

        content_lower = content.lower()
        for dep, tech in go_frameworks.items():
            if dep in content_lower:
                techs.add(tech)

        return techs

    def _parse_composer_json(self, content: str) -> Set[str]:
        """Parse composer.json to detect PHP dependencies"""
        techs = set()
        try:
            data = json.loads(content)
            require = data.get('require', {})

            if 'laravel/framework' in require:
                techs.add('Laravel')
            if 'symfony' in str(require).lower():
                techs.add('Symfony')

        except Exception:
            pass

        return techs

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
        all_tech_stack = set()

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

            # Detect tech stack
            print(f"  Detecting tech stack...")
            tech_stack = self.detect_tech_stack(repo['full_name'], languages)
            all_tech_stack.update(tech_stack)

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
                'url': repo['html_url'],
                'languages': languages
            })

        # Sort repos by stars first, then by lines of code
        sorted_repos = sorted(repo_stats, key=lambda x: (x['stars'], x['lines']), reverse=True)

        # Sort languages by usage
        top_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        # Add custom tech stack from config
        custom_tech = self.config.get('tech_stack', {}).get('custom', []) or []
        all_tech_stack.update(custom_tech)

        # Select Top N repos based on strategy
        top_repos_config = self.config.get('top_repos', {})
        strategy = top_repos_config.get('strategy', 'language_proportional')
        count = top_repos_config.get('count', 5)

        top_repos = self._select_top_repos(
            sorted_repos,
            language_stats,
            strategy,
            count
        )

        return {
            'total_repos': len(repos),
            'total_lines': total_lines,
            'top_repos': top_repos,
            'top_languages': top_languages,
            'language_stats': dict(language_stats),
            'all_repos': sorted_repos,
            'tech_stack': sorted(all_tech_stack)
        }

    def _select_top_repos(
        self,
        sorted_repos: List[Dict[str, Any]],
        language_stats: Dict[str, int],
        strategy: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """Select top N repos based on the chosen strategy"""

        # Handle pinned repos first
        pinned = self.config.get('repositories', {}).get('pinned', {}) or {}
        pinned_positions = {}
        used_repos = set()

        for repo_name, position in pinned.items():
            for repo in sorted_repos:
                if repo['name'] == repo_name or repo['full_name'] == repo_name:
                    pinned_positions[position] = repo
                    used_repos.add(repo['full_name'])
                    break

        # Get non-pinned repos
        available_repos = [r for r in sorted_repos if r['full_name'] not in used_repos]

        # Select repos based on strategy
        if strategy == 'language_proportional':
            selected = self._select_by_language_proportion(available_repos, language_stats, count)
        elif strategy == 'stars':
            selected = available_repos[:count]
        elif strategy == 'lines':
            selected = sorted(available_repos, key=lambda x: x['lines'], reverse=True)[:count]
        elif strategy == 'mixed':
            # Mixed: 60% weight on stars, 40% on lines
            selected = sorted(
                available_repos,
                key=lambda x: (x['stars'] * 0.6 + x['lines'] / 10000 * 0.4),
                reverse=True
            )[:count]
        else:
            selected = available_repos[:count]

        # Build final list with pinned repos in their positions
        top_repos = []
        selected_idx = 0

        for pos in range(1, count + 1):
            if pos in pinned_positions:
                top_repos.append(pinned_positions[pos])
            else:
                if selected_idx < len(selected):
                    top_repos.append(selected[selected_idx])
                    selected_idx += 1

        return top_repos

    def _select_by_language_proportion(
        self,
        repos: List[Dict[str, Any]],
        language_stats: Dict[str, int],
        count: int
    ) -> List[Dict[str, Any]]:
        """Select repos proportionally based on language usage"""

        if not language_stats:
            return repos[:count]

        total_bytes = sum(language_stats.values())

        # Calculate how many repos each language should get
        lang_allocations = {}
        for lang, bytes_count in language_stats.items():
            percentage = bytes_count / total_bytes
            allocation = round(percentage * count)
            if allocation > 0:
                lang_allocations[lang] = allocation

        # Adjust allocations to match count exactly
        current_total = sum(lang_allocations.values())
        if current_total < count:
            # Add remaining slots to top languages
            sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
            for lang, _ in sorted_langs:
                if current_total >= count:
                    break
                if lang in lang_allocations:
                    lang_allocations[lang] += 1
                    current_total += 1
        elif current_total > count:
            # Remove slots from bottom languages
            sorted_langs = sorted(language_stats.items(), key=lambda x: x[1])
            for lang, _ in sorted_langs:
                if current_total <= count:
                    break
                if lang in lang_allocations and lang_allocations[lang] > 0:
                    lang_allocations[lang] -= 1
                    current_total -= 1

        # Select best repos for each language
        selected = []
        lang_repos = defaultdict(list)

        # Group repos by their primary language
        for repo in repos:
            primary_lang = repo.get('language', 'Unknown')
            lang_repos[primary_lang].append(repo)

        # Sort repos within each language group by stars and lines
        for lang in lang_repos:
            lang_repos[lang].sort(key=lambda x: (x['stars'], x['lines']), reverse=True)

        # Select repos according to allocation
        for lang, allocation in sorted(lang_allocations.items(), key=lambda x: x[1], reverse=True):
            if lang in lang_repos:
                selected.extend(lang_repos[lang][:allocation])

        # If we still need more repos, fill with best remaining
        if len(selected) < count:
            used_names = {r['full_name'] for r in selected}
            remaining = [r for r in repos if r['full_name'] not in used_names]
            needed = count - len(selected)
            selected.extend(remaining[:needed])

        return selected[:count]

    def generate_markdown(self, user_info: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """Generate the markdown content"""
        name = self.config.get('profile', {}).get('name', user_info['name'] or user_info['login'])
        description = self.config.get('profile', {}).get('description', user_info.get('bio', ''))

        md = f"""# Hi, Welcome to {user_info['login']}'s Profile! 👋

{description}

"""

        # Tech Stack section (BEFORE GitHub Statistics)
        if stats.get('tech_stack'):
            md += "## 🛠️ Technologies & Tools\n\n"

            tech_stack = stats['tech_stack']

            # Categorize technologies
            categories = {
                'Languages': ['Rust', 'Java', 'JavaScript', 'TypeScript', 'Python', 'Go', 'Dart', 'Kotlin', 'PHP', 'Ruby', 'C++', 'C#'],
                'Frameworks & Libraries': ['React', 'Vue.js', 'Angular', 'Svelte', 'Next.js', 'Nuxt.js', 'Spring Boot', 'Spring Framework', 'Django', 'Flask', 'FastAPI', 'Express.js', 'NestJS', 'Fastify', 'Actix Web', 'Axum', 'Rocket', 'Tokio', 'Gin', 'Echo', 'Fiber', 'Laravel', 'Symfony', 'Flutter'],
                'Databases & ORMs': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Diesel', 'SQLx', 'Prisma', 'TypeORM', 'Sequelize', 'Mongoose', 'Hibernate', 'GORM', 'SQLAlchemy'],
                'Tools & Build Systems': ['Maven', 'Gradle', 'Webpack', 'Vite', 'Docker', 'Kubernetes'],
                'Testing': ['Jest', 'Vitest', 'Pytest', 'JUnit', 'Cypress', 'Playwright', 'Mockito'],
                'Other': []
            }

            categorized = {cat: [] for cat in categories.keys()}

            for tech in tech_stack:
                placed = False
                for cat, cat_techs in categories.items():
                    if cat != 'Other' and tech in cat_techs:
                        categorized[cat].append(tech)
                        placed = True
                        break
                if not placed:
                    categorized['Other'].append(tech)

            # Display categorized tech stack
            for category, techs in categorized.items():
                if techs:
                    md += f"**{category}:**  \n"
                    tech_badges = ' • '.join(f"`{tech}`" for tech in sorted(techs))
                    md += f"{tech_badges}\n\n"

            md += "---\n\n"

        md += "## 📊 GitHub Statistics\n\n"

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
