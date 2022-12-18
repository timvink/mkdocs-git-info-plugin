from mkdocs.config import config_options as c
from mkdocs.config.base import Config
from mkdocs.plugins import BasePlugin

from typing import Literal

try:
    from mkdocs.plugins import event_priority
except ImportError:
    event_priority = lambda priority: lambda f: f  # No-op fallback

from mkdocs.exceptions import PluginError

from mkdocs_git_info_plugin.gitinfo import GitRepositories, FileGitInfo

class GitInfoConfig(Config):
    exclude = c.Type(list, default=[])
    enabled = c.Type(bool, default=True)

class GitInfoPlugin(BasePlugin):

    def on_startup(self, command: Literal["build", "gh-deploy", "serve"], **kwargs):
        """
        Use new mkdocs 1.4 plugin system.

        The presence of an on_startup method (even if empty) migrates the plugin 
        to the new system where the plugin object is kept across builds within 
        one mkdocs serve.
        """
        self.git_repos = GitRepositories()

    @event_priority(-50) # early priority 
    def on_files(self, files, config, **kwargs):
        for file in files:
            if not file.src_uri.endswith(".md"):
                continue
            file.git_info = FileGitInfo(file.abs_src_path, self.git_repos)

    

    @event_priority(-50) # early priority 
    def on_pre_page(self, page, config, files, **kwargs):
        """ 
        Determine git info per page.

        The pre_page event is called before any actions are taken 
        on the subject page and can be used to alter the Page instance.

        See https://www.mkdocs.org/dev-guide/plugins/#on_pre_page
        """
        pass