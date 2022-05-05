# -*- coding: utf-8 -*-
"""Work function to check the composition of a `StructureData` against the chemical formula of a CifData node."""

import re

from CifFile import StarError
from aiida.engine import workfunction
from aiida.plugins import DataFactory, WorkflowFactory
import numpy as np

CifData = DataFactory('cif')


def get_formula_from_cif(cif: CifData) -> str:
    """
    Simplification of ``aiida.orm.cif.get_formulae``.
    Works for MPDS cif files as well.
    """
    formula_tags = ('_chemical_formula_sum', '_pauling_file_chemical_formula')
    datablock = cif.values.first_block()
    formula = next(iter(datablock.get(tag) for tag in formula_tags))

    if formula is None:
        pauling_phase = datablock.get('_pauling_file_phase')
        formula = pauling_phase if pauling_phase is None else pauling_phase.split('/')[0]

    return formula


# this function will be added to aiida.orm.nodes.data.cif
def parse_formula(formula):
    """
    Parses the Hill formulae. Does not need spaces as separators.
    Works also for partial occupancies and for chemical groups enclosed in round/square/curly brackets.
    Elements are counted and a dictionary is returned.
    e.g.  'C[NH2]3NO3'  -->  {'C': 1, 'N': 4, 'H': 6, 'O': 3}
    """

    def chemcount_str_to_number(string):
        if not string:
            quantity = 1
        else:
            quantity = float(string)
            if quantity.is_integer():
                quantity = int(quantity)
        return quantity

    contents = {}

    # split blocks with parentheses
    for block in re.split(r'(\([^\)]*\)[^A-Z\(\[\{]*|\[[^\]]*\][^A-Z\(\[\{]*|\{[^\}]*\}[^A-Z\(\[\{]*)', formula):
        if not block:  # block is void
            continue

        # get molecular formula (within parentheses) & count
        group = re.search(r'[\{\[\(](.+)[\}\]\)]([\.\d]*)', block)
        if group is None:  # block does not contain parentheses
            molformula = block
            molcount = 1
        else:
            molformula = group.group(1)
            molcount = chemcount_str_to_number(group.group(2))

        for part in re.findall(r'[A-Z][^A-Z\s]*', molformula.replace(' ', '')):  # split at uppercase letters
            match = re.match(r'(\D+)([\.\d]+)?', part)  # separates element and count

            if match is None:
                continue

            species = match.group(1)
            quantity = chemcount_str_to_number(match.group(2)) * molcount
            contents[species] = contents.get(species, 0) + quantity
    return contents


def parse_formula_from_structure(structure):
    """
    Returns a dictionary with the elements of a StructureData and their quantities.
    """
    return structure.get_pymatgen().composition.get_el_amt_dict()


class MissingElementsError(Exception):
    """
    An exception that will be raised if the parsed structure misses some elements or has additional elements with
    respect to the chemical formula reported in the CIF file. This is probably due to non-defined or non-listed sites.
    """


class DifferentCompositionsError(Exception):
    """
    An exception that will be raised if the parsed structure has a different composition with respect to the chemical
    formula reported in the CIF file.
    """


def _check_formula(cif, structure):
    """
    Compare CIF formula against StructureData formula and report any inconsistency.
    """
    # pylint: disable=too-many-locals
    report = ''
    formula_s = structure.get_formula('hill', ' ')
    formula_c = None
    try:
        assert len(cif.values.keys()) == 1, 'More than one CIF key.'
        formula_c = get_formula_from_cif(cif)
    except StarError:  # ignore unparsable CIF files (this should not happen)
        report += ' | Unparsable CIF'
        formula_c = cif.get_attribute('formulae')

    if not formula_c:
        # we cannot do any check without a formula... hope for the best
        report += ' | No formula in CIF'
        return report

    report += f'cif [{formula_c}]  structure [{formula_s}]'

    has_partial_occupancies = structure.get_extra('partial_occupancies')
    if has_partial_occupancies:
        report += ' | Partial occupancies'

    # get formula dictionaries {element: count}
    formuladic_s = parse_formula_from_structure(structure)
    formuladic_c = parse_formula(formula_c)
    # remove elements with zero occupancy
    for key in [key for key, value in formuladic_c.items() if value == 0.]:
        formuladic_c.pop(key)

    # FIRST CHECK: find missing elements, ignore vacancies ('X')
    # (symmetric difference of the sets -- contains elements not present in both sets)
    missing_elements = (set(formuladic_s.keys()) ^ set(formuladic_c.keys())) - {'X'}
    if missing_elements:
        report += f' | Missing elements: {list(missing_elements)}'
        raise MissingElementsError(report)
        #return False, report

    # SECOND CHECK: find inconsistent formulas
    # ratios of all the elements should be the same
    elements = formuladic_c.keys()
    elcount_c = np.array([formuladic_c[key] for key in elements])
    elcount_s = np.array([formuladic_s[key] for key in elements])

    # ratios should be (all) > 1
    # for integer occ., for each element the absolute tolerance on the ratio is 0.5 / (the smallest count)
    # if the ratio difference is larger than this value, the structure can have more than one atom difference
    if any(elcount_c > elcount_s):
        ratios = elcount_c / elcount_s
        atol = 0.499999 / np.ceil(elcount_s)
    else:
        ratios = elcount_s / elcount_c
        atol = 0.499999 / np.ceil(elcount_c)

    if has_partial_occupancies:
        # for partial occ., compare ratios against the first one
        # use an absolute tolerance of 0.05 + a 2 % relative tolerance
        compare_with_ratio = ratios[0]
        atol = 0.05
        rtol = 0.02
    else:
        # for integer occ., compare ratios against the first one rounded to the nearest integer
        # use only the absolute tolerance estimated above
        compare_with_ratio = np.round(ratios[0])
        rtol = 0.

    bad_ratios = not np.allclose(ratios, compare_with_ratio, atol=atol, rtol=rtol)
    if bad_ratios:
        report += f' | Different compositions (ratios: {list(zip(elements, [round(r, 3) for r in ratios]))})'
        raise DifferentCompositionsError(report)
    report += ' | OK'

    return report


@workfunction
def check_formula(cif, structure):
    """
    Compare CIF formula against StructureData formula and report any inconsistency.
    """
    CifCleanWorkChain = WorkflowFactory('codtools.cif_clean')  # pylint: disable=invalid-name

    report_msg = None

    # check structure chemical formula against cif one
    try:
        report_msg = _check_formula(cif, structure)
    except MissingElementsError as err:
        report_msg, = err.args
        return CifCleanWorkChain.exit_codes.ERROR_FORMULA_MISSING_ELEMENTS
    except DifferentCompositionsError as err:
        report_msg, = err.args
        return CifCleanWorkChain.exit_codes.ERROR_FORMULA_DIFFERENT_COMPOSITION
    finally:
        if report_msg:
            structure.set_extra('check_formula_log', report_msg)

    return structure
