# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
"""Module for the command line interface."""
from aiida.cmdline.params import options, types
import click


@click.group('aiida-codtools', context_settings={'help_option_names': ['-h', '--help']})
@options.PROFILE(type=types.ProfileParamType(load_profile=True), expose_value=False)
def cmd_root():
    """CLI for the `aiida-codtools` plugin."""


from .calculations import cmd_calculation
from .data import cmd_cif
from .workflows import cmd_workflow
