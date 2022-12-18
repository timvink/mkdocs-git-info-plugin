"""
Tests running builds on different fresh mkdocs projects.
Note that pytest offers a `tmp_path` fixture that we use here.
You can reproduce locally with:
>>> import tempfile
>>> from pathlib import Path
>>> tmp_path = Path(tempfile.gettempdir()) / 'pytest-testname'
>>> os.mkdir(tmp_path)
"""

# standard lib
import logging
import os
import re
import shutil
from contextlib import contextmanager
from pathlib import Path

# MkDocs
from mkdocs.__main__ import build_command
from mkdocs.config import load_config

# other 3rd party
import git
import pytest
from click.testing import CliRunner

# package module
from mkdocs_git_revision_date_localized_plugin.util import Util
from mkdocs_git_revision_date_localized_plugin.ci import commit_count

# ##################################
# ######## Globals #################
# ##################################

# custom log level to get plugin info messages
logging.basicConfig(level=logging.INFO)


# ##################################
# ########## Helpers ###############
# ##################################

@contextmanager
def working_directory(path):
    """
    Temporarily change working directory.
    A context manager which changes the working directory to the given
    path, and then changes it back to its previous value on exit.
    Usage:
    ```python
    # Do something in original directory
    with working_directory('/my/new/path'):
        # Do something in new directory
    # Back to old directory
    ```
    """
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def get_plugin_config_from_mkdocs(mkdocs_path) -> dict:
    # instanciate plugin
    cfg_mkdocs = load_config(mkdocs_path)

    plugins = cfg_mkdocs.get("plugins")
    plugin_loaded = plugins.get("git-revision-date-localized")

    cfg = plugin_loaded.on_config(cfg_mkdocs)
    logging.info("Fixture configuration loaded: " + str(cfg))

    if plugin_loaded.config.get("enabled"):
        assert (
            plugin_loaded.config.get("locale") is not None
        ), "Locale should never be None after plugin is loaded"

        logging.info(
            "Locale '%s' determined from %s"
            % (plugin_loaded.config.get("locale"), mkdocs_path)
        )
    return plugin_loaded.config


def setup_clean_mkdocs_folder(mkdocs_yml_path, output_path):
    """
    Sets up a clean mkdocs directory
    outputpath/testproject
    ├── docs/
    └── mkdocs.yml
    Args:
        mkdocs_yml_path (Path): Path of mkdocs.yml file to use
        output_path (Path): Path of folder in which to create mkdocs project
    Returns:
        testproject_path (Path): Path to test project
    """

    testproject_path = output_path / "testproject"

    # Create empty 'testproject' folder
    if os.path.exists(str(testproject_path)):
        logging.warning(
            """This command does not work on windows.
        Refactor your test to use setup_clean_mkdocs_folder() only once"""
        )
        shutil.rmtree(str(testproject_path))

    # shutil.copytree(str(Path(mkdocs_yml_path).parent), testproject_path)

    # Copy correct mkdocs.yml file and our test 'docs/'
    if "i18n" in mkdocs_yml_path:
        shutil.copytree("tests/fixtures/i18n/docs", str(testproject_path / "docs"))
    else:
        shutil.copytree("tests/fixtures/basic_project/docs", str(testproject_path / "docs"))
    
    shutil.copyfile(mkdocs_yml_path, str(testproject_path / "mkdocs.yml"))

    if "gen-files" in mkdocs_yml_path:
        shutil.copyfile(str(Path(mkdocs_yml_path).parent / "gen_pages.py"), str(testproject_path / "gen_pages.py"))

    return testproject_path

