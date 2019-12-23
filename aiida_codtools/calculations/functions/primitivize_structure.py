# -*- coding: utf-8 -*-
"""Calculation function to generate a primitive structure from a `StructureData` using Seekpath."""
from aiida.engine import calcfunction


@calcfunction
def primitivize_structure(structure, symprec):
    """Normalize and primitivize the cell of the given structure.

    The structure is passed through SeeKpath to try and get the primitive cell. If that is successful, important
    structural parameters as determined by SeeKpath will be set as extras on the structure node which is then returned
    as output.

    :param structure: the `StructureData` node
    :param symprec: a `Float` node with symmetry precision for determining primitive cell in SeeKpath
    :return: the primitive `StructureData` as determined by SeeKpath
    """
    from seekpath.hpkot import SymmetryDetectionError
    from aiida.plugins import WorkflowFactory
    from aiida.tools import get_kpoints_path

    CifCleanWorkChain = WorkflowFactory('codtools.cif_clean')  # pylint: disable=invalid-name

    try:
        seekpath_results = get_kpoints_path(structure, symprec=symprec)
    except ValueError:
        return CifCleanWorkChain.exit_codes.ERROR_SEEKPATH_INCONSISTENT_SYMMETRY
    except SymmetryDetectionError:
        return CifCleanWorkChain.exit_codes.ERROR_SEEKPATH_SYMMETRY_DETECTION_FAILED

    # Store important information that should be easily queryable as attributes in the StructureData
    parameters = seekpath_results['parameters'].get_dict()
    structure = seekpath_results['primitive_structure']

    # Store the formula as a string, in both hill as well as hill-compact notation, so it can be easily queried for
    extras = {
        'formula_hill': structure.get_formula(mode='hill'),
        'formula_hill_compact': structure.get_formula(mode='hill_compact'),
        'chemical_system': '-{}-'.format('-'.join(sorted(structure.get_symbols_set()))),
    }

    for key in ['spacegroup_international', 'spacegroup_number', 'bravais_lattice', 'bravais_lattice_extended']:
        try:
            extras[key] = parameters[key]
        except KeyError:
            pass

    structure.set_extra_many(extras)

    return structure
