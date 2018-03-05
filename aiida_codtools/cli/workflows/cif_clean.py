# -*- coding: utf-8 -*-
import click
from aiida.utils.cli import command
from aiida.utils.cli import options


@command()
@options.max_num_machines()
@options.max_wallclock_seconds()
@options.code(
    '--cif-filter', callback_kwargs={'entry_point': 'codtools.cif_filter'},
    help='the code that references the codtools cif_filter script'
)
@options.code(
    '--cif-select', callback_kwargs={'entry_point': 'codtools.cif_select'},
    help='the code that references the codtools cif_select script'
)
@options.group(
    '--group-cif-raw', help='the group with the raw CifData nodes'
)
@options.group(
    '--group-cif-clean', required=False, help='the group in which to store the cleaned CifData nodes'
)
@options.group(
    '--group-structure', required=False, help='the group in which to store the final StructureData nodes'
)
@click.option(
    '-m', '--max-entries', type=click.INT, default=None, show_default=True, required=False,
    help='maximum number of entries to import'
)
@click.option(
    '-f', '--skip-check', is_flag=True, default=False,
    help='skip the check whether the CifData node is an input to an already submitted workchain', 
)
def launch(cif_filter, cif_select, group_cif_raw, group_cif_clean, group_structure,
    max_num_machines, max_wallclock_seconds, max_entries, skip_check):
    """
    Run the CifCleanWorkChain on the entries in a group with raw imported CifData nodes
    """
    from aiida.orm.data.parameter import ParameterData
    from aiida.orm.group import Group
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.utils import CalculationFactory, DataFactory, WorkflowFactory
    from aiida.work.launch import run
    from aiida_quantumespresso.utils.resources import get_default_options

    CifData = DataFactory('cif')
    CifFilterCalculation = CalculationFactory('codtools.cif_filter')
    CifCleanWorkChain = WorkflowFactory('codtools.cif_clean')

    qb = QueryBuilder()
    qb.append(CifFilterCalculation, tag='calculation')
    qb.append(CifData, input_of='calculation', tag='data', project=['id'])
    qb.append(Group, filters={'id': {'==': group_cif_raw.pk}}, group_of='data')
    completed_cif_nodes = set(pk for entry in qb.all() for pk in entry)

    counter = 0
    for cif in group_cif_raw.nodes:

        if not skip_check and cif.pk in completed_cif_nodes:
            click.echo('CifData<{}> already submitted, skipping'.format(cif.pk))
            continue

        inputs = {
            'cif': cif,
            'cif_filter': cif_filter,
            'cif_select': cif_select,
            'options': ParameterData(dict=get_default_options(max_num_machines, max_wallclock_seconds))
        }

        if group_cif_clean is not None:
            inputs['group_cif'] = group_cif_clean

        if group_structure is not None:
            inputs['group_structure'] = group_structure

        click.echo('CifData<{}> submitted'.format(cif.pk))
        workchain = run(CifCleanWorkChain, **inputs)
        counter += 1

        if max_entries is not None and counter >= max_entries:
            click.echo('Maximum number of entries {} submitted, exiting'.format(max_entries))
            break