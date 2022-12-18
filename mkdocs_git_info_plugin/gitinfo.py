import os

from git import (
    Repo,
    Git,
    GitCommandError,
    GitCommandNotFound,
    InvalidGitRepositoryError,
    NoSuchPathError,
)

import logging
import functools

logger = logging.getLogger("mkdocs.plugins")


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

        self.repo_cache[abs_src_dir] = Repo(abs_src_dir, search_parent_directories=True).git

        return self.repo_cache[abs_src_dir]



class HandleGitErrors:
    """
    Decorator to handle git errors.

    This ensures we only throw a single warning instead of one for each file.
    """
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.num_calls = 0
        self.ignore_errors = False # TODO: get this from plugin config

        if self.ignore_errors:
            self.log_msg = logger.warning
        else:
            self.log_msg = logger.error

    def __call__(self, *args, **kwargs):
        self.num_calls += 1
        print(f"Call {self.num_calls} of {self.func.__name__!r}")

        def wrapper(cls, *args, **kwargs):
            """Wrapper function that decorates the function."""
            try:
                return self.func(cls, *args, **kwargs)
            except (InvalidGitRepositoryError, NoSuchPathError) as err:
                self.log(
                    "[mkdocs-git-info-plugin] Unable to find a git directory and/or git is not installed."
                    " Option 'fallback_to_build_date' set to 'true': Falling back to build date"
                )
                if self.ignore_errors:
                    return ""
                raise err
            except GitCommandError as err:
                self.log(
                    f"[git-git-info-plugin] Unable to read git logs of '{cls.abs_src_path}'. "
                    " To ignore this error, set option 'fallback_to_build_date: true'"
                )
                if self.ignore_errors:
                    return ""
                raise err
            except GitCommandNotFound as err:
                self.log(
                    "[git-info-plugin] Unable to perform command: 'git log'. Is git installed?"
                    " Option 'fallback_to_build_date' set to 'true': Falling back to build date"
                )
                if self.ignore_errors:
                    return ""
                raise err
            except Exception as err:
                raise err
        
        return wrapper



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
        self.git_info['last_commit'] = self._last_commit()
 
    @HandleGitErrors
    def _first_commit(self) -> int:
        """ 
        Return date of first commit.

        Note that:
        - diff_filter="A" will select the commit that created the file
        - format="%at" will retrieve author date in UNIX format
        
        For more see:
        - https://git-scm.com/docs/git-log#Documentation/git-log.txt-ematem
        - https://git-scm.com/docs/git-log#Documentation/git-log.txt---diff-filterACDMRTUXB82308203

        Returns:
            unix timestamp (int)
        """
        commit_timestamp = self.repo.log(
                    self.realpath, date="unix", format="%at", diff_filter="A", no_show_signature=True, follow=True
        )
        # A file can be created multiple times, through a file renamed. 
        # Commits are ordered with most recent commit first
        # Get the oldest commit only
        if commit_timestamp != "":
            commit_timestamp = commit_timestamp.split()[-1]
        return commit_timestamp

    @HandleGitErrors
    def _last_commit(self) -> int:
        """ 
        Return date of first commit.

        Note that:
        - format="%at" will retrieve author date in UNIX format

        For more see:
        - https://git-scm.com/docs/git-log#Documentation/git-log.txt-ematem

        Returns:
            unix timestamp (int)
        """
        return self.repo.log(
                self.realpath, date="unix", format="%at", n=1, no_show_signature=True
        )
    

    # TODO: something with a decorator to handle the different git command errors?
        # TODO: Add a 'status' False if there's a problem.
        # document that you can then do:
        # {% if page.meta.git.status %}
        # Git: {{ page.meta.git.short_commit }}
        # {% endif %}
    # TODO: Add a SiteGitInfo, that we initaliaze globally and the instanace we pass to FileGitInfo. 
        # Every page parsed can update the site info
    # TODO: Think about the structure that holds all the different git info
        # Because authors are nested and based on lines in a page


    # TODO: Test if `{{ git.date.strftime("%b %d, %Y %H:%M:%S") }}` works.

    # TODO: add git authors info 
    # TODO: add other git info (see issues, see mkdocs-macros)
        # https://mkdocs-macros-plugin.readthedocs.io/en/latest/git_info/#catalogue

    # TODO: Think about speed, what if user onyl needs subset of git info?

    # TODO: do CI checking
        # Include in docs the jinja test: https://mkdocs-macros-plugin.readthedocs.io/en/latest/git_info/#tip-is-this-really-a-git-repo

    # TODO: idea: {{ macros_info() }} to generate the HTML page with all the tags?

    