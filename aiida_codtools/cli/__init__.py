# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position,wildcard-import
"""Module for the command line interface."""

from aiida.cmdline.params import options, types
import click
import click_completion

# Activate the completion of parameter types provided by the click_completion package
click_completion.init()


@click.group('aiida-codtools', context_settings={'help_option_names': ['-h', '--help']})
@options.PROFILE(type=types.ProfileParamType(load_profile=True))
def cmd_root(profile):  # pylint: disable=unused-argument
    """CLI for the `aiida-codtools` plugin."""


from .calculations import cmd_calculation
from .data import cmd_cif
from .workflows import cmd_workflow
