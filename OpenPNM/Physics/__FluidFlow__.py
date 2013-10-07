#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: CEF PNM Team
# License: TBD
# Copyright (c) 2012

#from __future__ import print_function

"""
module __GenericPhysics__: Base class to define pore scale physics
==================================================================

.. warning:: The module must be loaded by adding an import line to Physics/__init__.py

"""

import OpenPNM
import scipy as sp

class FluidFlow(OpenPNM.Utilities.OpenPNMbase):
    r"""
    Methods in this class are used to determine the hydraulic conductivity of pores and throats from their geometric properties.
    """
    def __init__(self):
        print 'init Multiphase'

    def HagenPoiseuille(self,network):
        r"""
        ---
        """
        
        return
