# -*- coding: utf-8 -*-
from aiida.orm import CalculationFactory
from aiida_codtools.parsers.baseclass import BaseCodtoolsParser


class CiffilterParser(BaseCodtoolsParser):
    """
    Parser for the output of filter scripts from cod-tools package.
    """

    def __init__(self, calc):
        """
        Initialize the instance of CiffilterParser
        """
        self._supported_calculation_class = CalculationFactory('codtools.ciffilter')
        super(CiffilterParser, self).__init__(calc)
