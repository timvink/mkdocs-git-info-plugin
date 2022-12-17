import os

from git import (
    Repo,
    Git,
    GitCommandError,
    GitCommandNotFound,
    InvalidGitRepositoryError,
    NoSuchPathError,
)

from dataclasses import dataclass

class GitRepositories:
    """
    Utility class that holds references to git repo locations.
    """

    def __init__(self):
        """Initialize utility class."""
        self.repo_cache = {}

    def get_repo(self, abs_src_path: str) -> Git:
        """
        Get the repository for a given file path.
        """
        if not os.path.isdir(abs_src_path):
            abs_src_dir = os.path.dirname(abs_src_path)
        else:
            abs_src_dir = abs_src_path

        if abs_src_dir in self.repo_cache.keys():
            return self.repo_cache[abs_src_dir]

        try:
            self.repo_cache[abs_src_dir] = Repo(abs_src_dir, search_parent_directories=True).git
        except:
            breakpoint()

        return self.repo_cache[abs_src_dir]


@dataclass
class FileGitInfo:
    """
    Holds the git-related information for a mkdocs file.
    """
    def __init__(self, abs_src_path: str, git_repos: GitRepositories):
        """Initialize utility class."""
        self.abs_src_path = abs_src_path
        self.git_repos = git_repos

        # Get the canoncial path (follow symlinks)
        self.realpath = os.path.realpath(abs_src_path)

        self.repo = git_repos.get_repo(self.realpath)
        self.git_info = {}

        self.git_info['first_commit'] = self._first_commit()
 
    def _first_commit(self) -> int:

        commit_timestamp = self.repo.log(
                    self.realpath, date="unix", format="%at", diff_filter="A", no_show_signature=True, follow=True
        )
        # A file can be created multiple times, through a file renamed. 
        # Commits are ordered with most recent commit first
        # Get the oldest commit only
        if commit_timestamp != "":
            commit_timestamp = commit_timestamp.split()[-1]
        return commit_timestamp

    def _last_commit(self) -> int:
        return self.repo.log(
                self.realpath, date="unix", format="%at", n=1, no_show_signature=True
        )

    # TODO: something with a decorator to handle the different git command errors?
        # TODO: Add a 'status' False if there's a problem.
        # document that you can then do:
        # {% if git.status %}
        # Git: {{ git.short_commit }}
        # {% endif %}
    # TODO: Add a SiteGitInfo, that we initaliaze globally and the instanace we pass to FileGitInfo. 
        # Every page parsed can update the site info
    # TODO: Think about the structure that holds all the different git info

    # TODO: Test if `{{ git.date.strftime("%b %d, %Y %H:%M:%S") }}` works.

    # TODO: add git authors info 
    # TODO: add other git info (see issues, see mkdocs-macros)
        # https://mkdocs-macros-plugin.readthedocs.io/en/latest/git_info/#catalogue

    # TODO: do CI checking
        # Include in docs the jinja test: https://mkdocs-macros-plugin.readthedocs.io/en/latest/git_info/#tip-is-this-really-a-git-repo

    # TODO: idea: {{ macros_info() }} to generate the HTML page with all the tags?

    