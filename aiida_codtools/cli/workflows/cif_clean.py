# -*- coding: utf-8 -*-
import click

from aiida.cmdline.params import types
from aiida.cmdline.utils import decorators


@click.command()
@click.option(
    '-F', '--cif-filter', required=True, type=types.CodeParamType(entry_point='codtools.cif_filter'),
    help='Code that references the codtools cif_filter script.')
@click.option(
    '-S', '--cif-select', required=True, type=types.CodeParamType(entry_point='codtools.cif_select'),
    help='Code that references the codtools cif_select script.')
@click.option(
    '-r', '--group-cif-raw', required=False, type=types.GroupParamType(),
    help='Group with the raw CifData nodes to be cleaned.')
@click.option(
    '-c', '--group-cif-clean', required=False, type=types.GroupParamType(),
    help='Group to which to add the cleaned CifData nodes.')
@click.option(
    '-s', '--group-structure', required=False, type=types.GroupParamType(),
    help='Group to which to add the final StructureData nodes.')
@click.option(
    '-w', '--group-workchain', required=False, type=types.GroupParamType(),
    help='Group to which to add the WorkChain nodes.')
@click.option(
    '-n', '--node', type=click.INT, default=None, required=False,
    help='Specify the explicit pk of a CifData node for which to run the clean workchain.')
@click.option(
    '-N', '--starting-node', type=click.INT, default=None, required=False,
    help='Specify the starting pk of the CifData from which to start cleaning consecutively.')
@click.option(
    '-M', '--max-entries', type=click.INT, default=None, show_default=True, required=False,
    help='Maximum number of CifData entries to clean.')
@click.option(
    '-f', '--skip-check', is_flag=True, default=False,
    help='Skip the check whether the CifData node is an input to an already submitted workchain.')
@click.option(
    '-p', '--parse-engine', type=click.Choice(['ase', 'pymatgen']), default='pymatgen', show_default=True,
    help='Select the parse engine for parsing the structure from the cleaned cif if requested.')
@click.option(
    '-d', '--daemon', is_flag=True, default=False, show_default=True,
    help='Submit the process to the daemon instead of running it locally.')
@decorators.with_dbenv()
def launch(cif_filter, cif_select, group_cif_raw, group_cif_clean, group_structure, group_workchain, node,
    starting_node, max_entries, skip_check, parse_engine, daemon):
    """
    Run the CifCleanWorkChain on the entries in a group with raw imported CifData nodes. It will use
    the cif_filter and cif_select scripts of cod-tools to clean the input cif file. Additionally, if the
    'group-structure' option is passed, the workchain will also attempt to use the given parse engine
    to parse the cleaned CifData to obtain the structure and then use SeeKpath to find the
    primitive structure, which, if successful, will be added to the group-structure group
    """
    import inspect
    from datetime import datetime
    from aiida.common.exceptions import NotExistent
    from aiida.orm import load_node
    from aiida.orm.data.str import Str
    from aiida.orm.data.parameter import ParameterData
    from aiida.orm.groups import Group
    from aiida.orm.node.process import WorkChainNode
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.utils import CalculationFactory, DataFactory, WorkflowFactory
    from aiida.work.launch import run_get_node, submit
    from aiida_codtools.common.resources import get_default_options

    CifData = DataFactory('cif')
    CifFilterCalculation = CalculationFactory('codtools.cif_filter')
    CifCleanWorkChain = WorkflowFactory('codtools.cif_clean')

    # Collect the dictionary of not None parameters passed to the launch script and print to screen
    local_vars = locals()
    launch_paramaters = {}
    for arg in inspect.getargspec(launch.callback).args:
        if arg in local_vars and local_vars[arg]:
            launch_paramaters[arg] = local_vars[arg]

    click.echo('=' * 80)
    click.echo('Starting on {}'.format(datetime.utcnow().isoformat()))
    click.echo('Launch parameters: {}'.format(launch_paramaters))
    click.echo('-' * 80)

    if node is not None:

        try:
            cif_data = load_node(node)
        except NotExistent:
            raise click.BadParameter('node<{}> could not be loaded'.format(node))

        if not isinstance(cif_data, CifData):
            raise click.BadParameter('node<{}> is not a CifData node'.format(node))

        nodes = [cif_data]

    elif group_cif_raw is not None:

        # Get CifData nodes that should actually be submitted according to the input filters
        builder = QueryBuilder()
        builder.append(Group, filters={'id': {'==': group_cif_raw.pk}}, tag='group')

        if skip_check:
            builder.append(CifData, with_group='group', project=['*'])
        else:
            # Get CifData nodes that already have an associated workchain node in the `group_workchain` group.
            submitted = QueryBuilder()
            submitted.append(WorkChainNode, tag='workchain')
            submitted.append(Group, filters={'id': {'==': group_workchain.pk}}, with_node='workchain')
            submitted.append(CifData, with_outgoing='workchain', tag='data', project=['id'])
            submitted_nodes = set(pk for entry in submitted.all() for pk in entry)

            if submitted_nodes:
                filters = {'id': {'!in': submitted_nodes}}
            else:
                filters = {}

            # Get all CifData nodes that are not included in the submitted node list
            builder.append(CifData, with_group='group', filters=filters, project=['*'])

        if max_entries is not None:
            builder.limit(int(max_entries))

        nodes = [entry[0] for entry in builder.all()]

    else:
        raise click.BadParameter('you have to specify either --group-cif-raw or --node')

    counter = 0

    for cif in nodes:

        if starting_node is not None and cif.pk < starting_node:
            continue

        inputs = {
            'cif': cif,
            'cif_filter': cif_filter,
            'cif_select': cif_select,
            'parse_engine': Str(parse_engine),
            'options': ParameterData(dict=get_default_options())
        }

        if group_cif_clean is not None:
            inputs['group_cif'] = group_cif_clean

        if group_structure is not None:
            inputs['group_structure'] = group_structure

        if daemon:
            workchain = submit(CifCleanWorkChain, **inputs)
            click.echo('{} | CifData<{}> submitting: {}<{}>'.format(
                datetime.utcnow().isoformat(), cif.pk, CifCleanWorkChain.__name__, workchain.pk))
        else:
            click.echo('{} | CifData<{}> running: {}'.format(
                datetime.utcnow().isoformat(), cif.pk, CifCleanWorkChain.__name__))
            result, workchain = run_get_node(CifCleanWorkChain, **inputs)

        if group_workchain is not None:
            group_workchain.add_nodes([workchain])

        counter += 1

        if max_entries is not None and counter >= max_entries:
            break

    click.echo('-' * 80)
    click.echo('Submitted {} new workchains'.format(counter))
    click.echo('Stopping on {}'.format(datetime.utcnow().isoformat()))
    click.echo('=' * 80)
