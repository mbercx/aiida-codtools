# -*- coding: utf-8 -*-
"""Calculation function to randomize the atomic positions of a `StructureData`."""
from aiida.engine import calcfunction


@calcfunction
def randomize_structure(structure, sigma):
    """Create a clone of the structure where a statistical noise component is added to the atomic coordinates.

    :param structure: the `StructureData` node
    :param sigma: the standard deviation in Angstrom of the normal distribution used to distort atomic positions
    :return: a `StructureData` with randomize atomic positions
    """
    from random import gauss
    from aiida.orm.nodes.data.structure import StructureData, Site

    randomized = StructureData(cell=structure.cell, pbc=structure.pbc)

    for kind in structure.kinds:
        randomized.append_kind(kind)

    sigma = sigma.value

    for site in structure.sites:
        position = [coordinate + gauss(0, sigma) for coordinate in site.position]
        randomized.append_site(Site(kind_name=site.kind_name, position=position))

    return randomized
