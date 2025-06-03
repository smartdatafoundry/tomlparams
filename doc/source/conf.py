# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

from tomlparams import __version__

project = "TOMLParams"
copyright = "2025, Bigspark Limited"
author = "Bigspark Limited"
release = __version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
]

myst_enable_extensions = [
    "colon_fence",
    "dollarmath",
    "substitution",
]

templates_path = ["_templates"]
exclude_patterns = [
    "colon_fence",
    "dollarmath",
    "substitution",
]


html_theme = "alabaster"
html_static_path = ["_static"]
html_logo = "img/tomlparams-logo-left.png"

latex_logo = "img/tomlparams-logo.png"
