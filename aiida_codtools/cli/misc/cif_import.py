# -*- coding: utf-8 -*-
import click
from aiida.utils.cli import command
from aiida.utils.cli import options


@command()
@options.group(help='Group in which to store the raw imported CifData nodes')
@click.option(
    '-d', '--database', type=click.Choice(['cod', 'icsd', 'mpds']), default='cod', show_default=True,
    help='Select the database to import from'
)
@click.option(
    '-m', '--max-entries', type=click.INT, default=None, show_default=True, required=False,
    help='Maximum number of entries to import'
)
@click.option(
    '-x', '--number-species', type=click.INT, default=None, show_default=True,
    help='Import only cif files with this number of different species'
)
@click.option(
    '-s', '--importer-server', type=click.STRING, required=False,
    help='Optional server address thats hosts the database'
)
@click.option(
    '-h', '--importer-db-host', type=click.STRING, required=False,
    help='Optional hostname for the database'
)
@click.option(
    '-n', '--importer-db-name', type=click.STRING, required=False,
    help='Optional name for the database'
)
@click.option(
    '-p', '--importer-db-password', type=click.STRING, required=False,
    help='Optional password for the database'
)
@click.option(
    '-u', '--importer-api-url', type=click.STRING, required=False,
    help='Optional API url for the database'
)
@click.option(
    '-a', '--importer-api-key', type=click.STRING, required=False,
    help='Optional API key for the database'
)
def launch(group, database, max_entries, number_species, importer_server, importer_db_host,
    importer_db_name, importer_db_password, importer_api_url, importer_api_key):
    """
    Import cif files from various structural databases, store them as CifData nodes and add them to a Group.
    Note that to determine which cif files are already contained within the Group in order to avoid duplication,
    the attribute 'source.id' of the CifData is compared to the source id of the imported cif entry. Since there
    is no guarantee that these id's do not overlap between different structural databases and we do not check
    explicitly for the database, it is advised to use separate groups for different structural databases.
    """
    from CifFile.StarFile import StarError
    from urllib2 import HTTPError
    from aiida.tools.dbimporters import DbImporterFactory

    importer_parameters = {}
    query_parameters = {}

    if importer_server is not None:
        importer_parameters['server'] = importer_server

    if importer_db_host is not None:
        importer_parameters['host'] = importer_db_host

    if importer_db_name is not None:
        importer_parameters['db'] = importer_db_name

    if importer_db_password is not None:
        importer_parameters['passwd'] = importer_db_password

    if importer_api_url is not None:
        importer_parameters['url'] = importer_api_url

    if importer_api_key is not None:
        importer_parameters['api_key'] = importer_api_key

    if database == 'mpds':

        if number_species is None:
            raise click.BadParameter('the number of species has to be defined for the {} database'.format(database))

        query_parameters = {
            'query': {},
            'collection': 'structures'
        }

        if number_species == 1:
            query_parameters['query']['classes'] = 'unary'
        elif number_species == 2:
            query_parameters['query']['classes'] = 'binary'
        elif number_species == 3:
            query_parameters['query']['classes'] = 'ternary'
        elif number_species == 4:
            query_parameters['query']['classes'] = 'multinary'
        elif number_species == 5:
            query_parameters['query']['classes'] = 'quinary'
        else:
            raise click.BadParameter('only unaries through quinaries are supported by the {} database'
                .format(database), param_hint='number_species')

    else:
        query_parameters['number_of_elements'] = number_species

    importer_class = DbImporterFactory(database)
    importer = importer_class(**importer_parameters)

    try:
        query_results = importer.query(**query_parameters)
    except BaseException as exception:
        click.echo('database query failed: {}'.format(exception))
        return

    existing_cif_nodes = [cif.get_attr('source')['id'] for cif in group.nodes]

    counter = 0
    for entry in query_results:

        source_id = entry.source['id']

        if source_id in existing_cif_nodes:
            click.echo('Cif with source id <{}> already present in group {}'.format(source_id, group.name))
            continue

        try:
            cif = entry.get_cif_node()
        except (StarError, HTTPError) as exception:
            click.echo('Encountered an error retrieving cif data: {}'.format(exception))
        else:
            try:
                if cif.has_partial_occupancies():
                    click.echo('Cif with source id <{}> has partial occupancies, skipping'.format(source_id))
                    continue
                else:
                    cif.store()

                    group.add_nodes([cif])

                    counter += 1
                    click.echo('Newly stored CifData<{}> with source id <{}>'.format(cif.pk, source_id))
            except ValueError:
                click.echo('Cif with source id <{}> has occupancies that could not be converted to floats, skipping'
                    .format(source_id))
                continue

        if max_entries is not None and counter >= max_entries:
            click.echo('Maximum number of entries {} stored, exiting'.format(max_entries))
            break