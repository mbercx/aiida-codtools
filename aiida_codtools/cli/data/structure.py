# -*- coding: utf-8 -*-
# yapf:disable
"""Command line interface to manipulate `StructureData` nodes."""
import click

from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo

from . import cmd_data


@cmd_data.group('structure')
def cmd_structure():
    """Commands to manipulate `StructureData` nodes."""


@cmd_structure.command('primitivize')
@options.DATA(type=types.DataParamType(sub_classes=('aiida.data:structure',)),
    help='One or multiple `StructureData` nodes.')
@click.option('-s', '--symprec', type=click.FLOAT, default=5E-3, help='Symmetry precision.')
@options.SILENT()
@options.DRY_RUN(help='Perform a dry-run without storing any of the nodes.')
@arguments.GROUP('source', required=False)
@arguments.GROUP('target', required=False, type=types.GroupParamType(create_if_not_exist=True))
@decorators.with_dbenv()
def launch_structure_primitivize(data, symprec, silent, dry_run, source, target):
    """Normalize and primitivize the specified `StructureData` nodes.

    The `StructureData` nodes can either be specified explicitly with the `--data` option or through the `SOURCE` group
    argument. If the `TARGET` argument is specified, the primitivized structure nodes will be stored in a group with
    that name. If it does not exist it will be created. Note that for nodes to be storable in a group, they have to be
    stored themselves, so the `TARGET` argument is incompatible with the `--dry-run` option.
    """
    from aiida import orm
    from aiida_codtools.calculations.functions.primitivize_structure import primitivize_structure

    if not data and not source:
        raise click.BadParameter('specify either the `SOURCE` group or specific nodes with the `--data` option.')

    if target and dry_run:
        raise click.BadParameter('the `TARGET` argument is incompatible with the `--dry-run` option.')

    if source and not all([isinstance(node, orm.StructureData) for node in source.nodes]):
        raise click.BadParameter('found a node in `SOURCE` that is not a `StructureData` node.')

    inputs = {
        'symprec': orm.Float(symprec),
        'metadata': {}
    }

    if dry_run:
        inputs['metadata']['store_provenance'] = False

    primitive_structures = []
    nodes = data or source.nodes

    with click.progressbar(label='Primitivizing structures', length=len(nodes), show_pos=True) as progress:
        for structure in source.nodes:

            progress.update(1)

            try:
                primitive, node = primitivize_structure.run_get_node(structure, **inputs)
            except Exception as exception:  # pylint: disable=broad-except
                args = (structure.pk, str(exception))
                echo.echo_error('Primitivizing of StructureData<{}> raised an exception: {}'.format(*args))
                continue

            if node.is_failed and not silent:
                args = (structure.pk, node.exit_message)
                echo.echo_error('Primitivizing of StructureData<{}> failed: {}'.format(*args))
                continue

            primitive_structures.append(primitive)

    if target:
        target.store()
        target.add_nodes(primitive_structures)

    if not silent:
        echo.echo_info('Primitivized {} structures'.format(len(primitive_structures)))


@cmd_structure.command('randomize')
@options.DATA(type=types.DataParamType(sub_classes=('aiida.data:structure',)),
    help='One or multiple `StructureData` nodes.')
@click.option('-s', '--sigma', type=click.FLOAT, default=0.1,
    help='The standard deviation in Angstrom of the normal distribution with which the random noise is generated.')
@options.SILENT()
@options.DRY_RUN(help='Perform a dry-run without storing any of the nodes.')
@arguments.GROUP('source', required=False)
@arguments.GROUP('target', required=False, type=types.GroupParamType(create_if_not_exist=True))
@decorators.with_dbenv()
def launch_structure_randomize(data, sigma, silent, dry_run, source, target):
    """Randomize the atomic positions along all crystal axes of the  specified `StructureData` nodes.

    The `StructureData` nodes can either be specified explicitly with the `--data` option or through the `SOURCE` group
    argument. If the `TARGET` argument is specified, the randomized structure nodes will be stored in a group with
    that name. If it does not exist it will be created. Note that for nodes to be storable in a group, they have to be
    stored themselves, so the `TARGET` argument is incompatible with the `--dry-run` option.
    """
    from aiida import orm
    from aiida_codtools.calculations.functions.randomize_structure import randomize_structure

    if not data and not source:
        raise click.BadParameter('specify either the `SOURCE` group or specific nodes with the `--data` option.')

    if target and dry_run:
        raise click.BadParameter('the `TARGET` argument is incompatible with the `--dry-run` option.')

    if source and not all([isinstance(node, orm.StructureData) for node in source.nodes]):
        raise click.BadParameter('found a node in `SOURCE` that is not a `StructureData` node.')

    inputs = {
        'sigma': orm.Float(sigma),
        'metadata': {}
    }

    if dry_run:
        inputs['metadata']['store_provenance'] = False

    randomized_structures = []
    nodes = data or source.nodes

    with click.progressbar(label='Randomizing structures', length=len(nodes), show_pos=True) as progress:
        for structure in source.nodes:

            progress.update(1)

            try:
                randomized, node = randomize_structure.run_get_node(structure, **inputs)
            except Exception as exception:  # pylint: disable=broad-except
                args = (structure.pk, str(exception))
                echo.echo_error('Randomizing of StructureData<{}> raised an exception: {}'.format(*args))
                continue

            if node.is_failed and not silent:
                args = (structure.pk, node.exit_message)
                echo.echo_error('Randomizing of StructureData<{}> failed: {}'.format(*args))
                continue

            randomized_structures.append(randomized)

    if target:
        target.store()
        target.add_nodes(randomized_structures)

    if not silent:
        echo.echo_info('Randomized positions of {} structures'.format(len(randomized_structures)))
