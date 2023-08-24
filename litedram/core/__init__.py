#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import AutoCSR, CSRStorage, CSRStatus

from litedram.dfii import DFIInjector
from litedram.core.controller import ControllerSettings, LiteDRAMController
from litedram.core.crossbar import LiteDRAMCrossbar

# Core ---------------------------------------------------------------------------------------------

class LiteDRAMCore(Module, AutoCSR):
    def __init__(self, phy, geom_settings, timing_settings, clk_freq, **kwargs):
        self.submodules.dfii = DFIInjector(
            addressbits = max(geom_settings.addressbits, getattr(phy, "addressbits", 0)),
            bankbits    = max(geom_settings.bankbits, getattr(phy, "bankbits", 0)),
            nranks      = phy.settings.nranks,
            databits    = phy.settings.dfi_databits,
            nphases     = phy.settings.nphases)
        self.comb += self.dfii.master.connect(phy.dfi)

        self.trefi_csr = CSRStorage(32)
        self.refresh_ctr = CSRStatus(32)
        self.refresh_enable = CSRStorage(1, reset=1)
        self.submodules.controller = controller = LiteDRAMController(
            phy_settings    = phy.settings,
            geom_settings   = geom_settings,
            timing_settings = timing_settings,
            clk_freq        = clk_freq,
            trefi_csr = self.trefi_csr,
            refresh_ctr = self.refresh_ctr,
            refresh_enable = self.refresh_enable,
            **kwargs)
        self.comb += controller.dfi.connect(self.dfii.slave)

        self.submodules.crossbar = LiteDRAMCrossbar(controller.interface)

        print("\n\n\ntrefi: {}\n\n\n".format(timing_settings.tREFI))
