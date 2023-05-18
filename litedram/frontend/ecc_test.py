from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import LiteDRAMNativePort
from litedram.frontend.axi import LiteDRAMAXIPort
from litedram.frontend.ecc import LiteDRAMNativePortECC
from litedram.frontend.dma import LiteDRAMDMAWriter, LiteDRAMDMAReader

WIDTH_32_BITS = 32

def get_ashift_awidth(dram_port):
    if isinstance(dram_port, LiteDRAMNativePort):
        ashift = log2_int(dram_port.data_width//8)
        awidth = dram_port.address_width + ashift
    elif isinstance(dram_port, LiteDRAMAXIPort):
        ashift = log2_int(dram_port.data_width//8)
        awidth = dram_port.address_width
    else:
        raise NotImplementedError
    return ashift, awidth

class DMA_Writer(Module, AutoCSR):
    def __init__(self, dram_port):

        # ashift, awidth = get_ashift_awidth(dram_port)
        
        dma = LiteDRAMDMAWriter(dram_port)
        self.submodules += dma

        # CSRS to control state machine
        self.data_sig = CSRStorage(WIDTH_32_BITS)
        self.address_sig = CSRStorage(WIDTH_32_BITS)
        self.counter = CSRStorage(WIDTH_32_BITS)
        self.start = CSRStorage()
        self.done = CSRStatus()
        self.ticks = CSRStatus(WIDTH_32_BITS)

        cmd_counter = Signal(WIDTH_32_BITS)
        data_info = Signal(dram_port.data_width)

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            If(self.start.storage,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            ),
            NextValue(self.ticks.status, 0)
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter >= self.counter.storage,
                    NextState("AWAIT_FIFO_EMPTY"),
                ),
            ),
            NextValue(self.ticks.status, self.ticks.status + 1),
        )
        fsm.act("AWAIT_FIFO_EMPTY",
            If(~dma.fifo.source.valid,
                NextState("DONE"),
            ),
        )
        fsm.act("DONE",
            self.done.status.eq(1),
            If(~self.start.storage,
                NextState("IDLE"),   
            )
        )

        # Simplify signals
        port_data_eighth = dram_port.data_width // 8
        
        self.comb += dma.sink.address.eq(self.address_sig.storage)
        self.comb += [
            data_info[:port_data_eighth].eq(self.data_sig.storage),
            data_info[port_data_eighth:(port_data_eighth * 2)].eq(self.data_sig.storage + 1),
            data_info[(port_data_eighth * 2):(port_data_eighth * 3)].eq(self.data_sig.storage + 2),
            data_info[(port_data_eighth * 3):(port_data_eighth * 4)].eq(self.data_sig.storage + 3),
            data_info[(port_data_eighth * 4):(port_data_eighth * 5)].eq(self.data_sig.storage + 4),
            data_info[(port_data_eighth * 5):(port_data_eighth * 6)].eq(self.data_sig.storage + 5),
            data_info[(port_data_eighth * 6):(port_data_eighth * 7)].eq(self.data_sig.storage + 6),
            data_info[(port_data_eighth * 7):(port_data_eighth * 8)].eq(self.data_sig.storage + 7),
            dma.sink.data.eq(data_info)
        ]

class DMA_Reader(Module, AutoCSR):
    def __init__(self, dram_port):
        
        #ashift, awidth = get_ashift_awidth(dram_port)
        
        dma = LiteDRAMDMAReader(dram_port)
        self.submodules += dma

        self.start = CSRStorage()
        self.counter = CSRStorage(WIDTH_32_BITS)
        self.address_sig = CSRStorage(WIDTH_32_BITS)
        self.data_ready = CSRStatus()
        self.data_handshake1 = CSRStorage(description="Set this high first for getting valid data, handshake2 must be low")
        self.data_handshake2 = CSRStorage(description="Set this high second to continue on, handshake1 must be low")
        self.done = CSRStatus()
        self.ticks = CSRStatus(WIDTH_32_BITS)

        cmd_counter = Signal(WIDTH_32_BITS)
        data_output_sig = Signal(576)

        self.data_status_0 = CSRStatus(WIDTH_32_BITS)
        self.data_status_1 = CSRStatus(WIDTH_32_BITS)
        self.data_status_2 = CSRStatus(WIDTH_32_BITS)
        self.data_status_3 = CSRStatus(WIDTH_32_BITS)
        self.data_status_4 = CSRStatus(WIDTH_32_BITS)
        self.data_status_5 = CSRStatus(WIDTH_32_BITS)
        self.data_status_6 = CSRStatus(WIDTH_32_BITS)
        self.data_status_7 = CSRStatus(WIDTH_32_BITS)
        self.data_status_8 = CSRStatus(WIDTH_32_BITS)
        self.data_status_9 = CSRStatus(WIDTH_32_BITS)
        self.data_status_10 = CSRStatus(WIDTH_32_BITS)
        self.data_status_11 = CSRStatus(WIDTH_32_BITS)
        self.data_status_12 = CSRStatus(WIDTH_32_BITS)
        self.data_status_13 = CSRStatus(WIDTH_32_BITS)
        self.data_status_14 = CSRStatus(WIDTH_32_BITS)
        self.data_status_15 = CSRStatus(WIDTH_32_BITS)
        self.data_status_16 = CSRStatus(WIDTH_32_BITS)
        self.data_status_17 = CSRStatus(WIDTH_32_BITS)

        self.comb += [
            self.data_status_0.status.eq(data_output_sig[0:(WIDTH_32_BITS)]),
            self.data_status_1.status.eq(data_output_sig[(WIDTH_32_BITS):(2 * WIDTH_32_BITS)]),
            self.data_status_2.status.eq(data_output_sig[(2 * WIDTH_32_BITS):(3 * WIDTH_32_BITS)]),
            self.data_status_3.status.eq(data_output_sig[(3 * WIDTH_32_BITS):(4 * WIDTH_32_BITS)]),
            self.data_status_4.status.eq(data_output_sig[(4 * WIDTH_32_BITS):(5 * WIDTH_32_BITS)]),
            self.data_status_5.status.eq(data_output_sig[(5 * WIDTH_32_BITS):(6 * WIDTH_32_BITS)]),
            self.data_status_6.status.eq(data_output_sig[(6 * WIDTH_32_BITS):(7 * WIDTH_32_BITS)]),
            self.data_status_7.status.eq(data_output_sig[(7 * WIDTH_32_BITS):(8 * WIDTH_32_BITS)]),
            self.data_status_8.status.eq(data_output_sig[(8 * WIDTH_32_BITS):(9 * WIDTH_32_BITS)]),
            self.data_status_9.status.eq(data_output_sig[(9 * WIDTH_32_BITS):(10 * WIDTH_32_BITS)]),
            self.data_status_10.status.eq(data_output_sig[(10 * WIDTH_32_BITS):(11 * WIDTH_32_BITS)]),
            self.data_status_11.status.eq(data_output_sig[(11 * WIDTH_32_BITS):(12 * WIDTH_32_BITS)]),
            self.data_status_12.status.eq(data_output_sig[(12 * WIDTH_32_BITS):(13 * WIDTH_32_BITS)]),
            self.data_status_13.status.eq(data_output_sig[(13 * WIDTH_32_BITS):(14 * WIDTH_32_BITS)]),
            self.data_status_14.status.eq(data_output_sig[(14 * WIDTH_32_BITS):(15 * WIDTH_32_BITS)]),
            self.data_status_15.status.eq(data_output_sig[(15 * WIDTH_32_BITS):(16 * WIDTH_32_BITS)]),
            self.data_status_16.status.eq(data_output_sig[(16 * WIDTH_32_BITS):(17 * WIDTH_32_BITS)]),
            self.data_status_17.status.eq(data_output_sig[(17 * WIDTH_32_BITS):(18 * WIDTH_32_BITS)]),
        ]

        self.read_addr_idle_fsm = CSRStatus()
        self.read_addr_run_fsm = CSRStatus()
        self.read_addr_done_fsm = CSRStatus()

        self.read_data_idle_fsm = CSRStatus()
        self.read_data_run_fsm = CSRStatus()
        self.read_data_wait_fsm = CSRStatus()
        self.read_data_done_fsm = CSRStatus()


        # setattr(self, "dataout_{}".format(i//WIDTH_32_BITS), CSRStatus(WIDTH_32_BITS))
        # getattr(self, "dataout_{}".format(i//WIDTH_32_BITS)).status.eq(data_output_sig[i:(i + WIDTH_32_BITS)])

        cmd_fsm = FSM(reset_state="IDLE")
        self.submodules += cmd_fsm
        cmd_fsm.act("IDLE",
            self.read_addr_idle_fsm.status.eq(1),
            If(self.start.storage,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            )
        )
        cmd_fsm.act("RUN",
            self.read_addr_run_fsm.status.eq(1),
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter >= self.counter.storage,
                    NextState("DONE")
                )
            )
        )
        cmd_fsm.act("DONE",
            self.read_addr_done_fsm.status.eq(1),
            If(~self.start.storage,
                NextState("IDLE"),   
            )            
        )

        self.comb += dma.sink.address.eq(self.address_sig.storage)


        ########################################################################
        data_counter = Signal(dram_port.address_width, reset_less=True)

        data_fsm = FSM(reset_state="IDLE")
        self.submodules += data_fsm
        data_fsm.act("IDLE",
            self.read_data_idle_fsm.status.eq(1),
            If(self.start.storage,
                NextValue(data_counter, 0),
                NextState("RUN")
            ),
        )
        data_fsm.act("RUN",
            self.read_data_run_fsm.status.eq(1),
            If((dma.source.valid & self.data_handshake1.storage),
                data_output_sig.eq(dma.source.data),
                NextValue(data_counter, data_counter + 1),
                NextState("WAIT"),
            ),
        )
        data_fsm.act("WAIT",
            self.read_data_wait_fsm.status.eq(1),
            data_output_sig.eq(dma.source.data),
            self.data_ready.status.eq(1),
            If(self.data_handshake2.storage, 
                dma.source.ready.eq(1),
                If((data_counter >= self.counter.storage),
                    NextState("DONE"),
                ).Else(
                    NextState("RUN"),
                ),
            ),
        )
        data_fsm.act("DONE",
            self.read_data_done_fsm.status.eq(1),
            self.done.status.eq(1),
            If(~self.start.storage,
                NextState("IDLE"),   
            )
        )


class EccTester(Module):
    def __init__(self, sdram):

        # Get all four ports
        nonecc_w = sdram.crossbar.get_port()
        nonecc_r = sdram.crossbar.get_port()
        ecc_helper_w = sdram.crossbar.get_port()
        ecc_helper_r = sdram.crossbar.get_port()

        # Get the number of ecc bits needed
        ecc_bits_extra = ecc_helper_w.data_width // 8
        index = 0
        while (2 ** index) < ecc_bits_extra:
            index += 1
        index += 1
        ecc_bits_extra = index

        # Declare ports to be sent through ecc module
        ecc_w = LiteDRAMNativePort(
            mode=ecc_helper_w.mode,
            address_width=ecc_helper_w.address_width,
            data_width=ecc_helper_w.data_width - (ecc_bits_extra * 8),
        )
        ecc_r = LiteDRAMNativePort(
            mode=ecc_helper_r.mode,
            address_width=ecc_helper_r.address_width,
            data_width=ecc_helper_r.data_width - (ecc_bits_extra * 8),
        )

        # Add ECC Modules
        self.submodules += LiteDRAMNativePortECC(
            ecc_r, ecc_helper_r,
            with_error_injection=True
        )
        self.submodules += LiteDRAMNativePortECC(
            ecc_w, ecc_helper_w,
            with_error_injection=True
        )

        # Finally, add all modules to control ports
        self.submodules.non_ecc_writer = DMA_Writer(nonecc_w)
        self.submodules.non_ecc_reader = DMA_Reader(nonecc_r)
        self.submodules.ecc_writer = DMA_Writer(ecc_w)
        self.submodules.ecc_reader = DMA_Reader(ecc_r)
        # setattr(self.submodules, f"nonecc_writer", non_ecc_writer)
        # setattr(self.submodules, f"nonecc_reader", non_ecc_reader)
        # setattr(self.submodules, f"ecc_writer", ecc_writer)
        # setattr(self.submodules, f"ecc_reader", ecc_reader)
        # self.add_csr("non_ecc_writer")
        # self.add_csr("non_ecc_reader")
        # self.add_csr("ecc_writer")
        # self.add_csr("ecc_reader")






        
        