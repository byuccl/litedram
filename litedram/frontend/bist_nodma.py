"""
This is a bist simply using the native protocol to 
communicate with the dram controller. 
"""




from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import LiteDRAMNativePort

DATA_WIDTH_32 = 32

ONE_BIT_WIDE = 1
TWO_BITS_WIDE = 2
WIDTH_32_BITS = 32

FIXED_ADDR_MODE = 0
INCR_ADDR_MODE = 1

W_ONCE_R_ALWAYS = 0
WR_ALWAYS = 1


"""
This class, similar to bist.py, controls the native protocol 
in a much more straight-forward way without using the DMA. A 
problem we wanted to avoid in the previous bist.py was the 
necessary delay after starting the state machine in software. 
The data is meant to be a fixed value for our test.


To enable the bist, set the register "start" high. To disable
the bist, set this register low.


There are two address modes:

Fixed mode: (address_mode == 0) The Bist will use the set of addresses between 
the base address and base address + end address over and
over again. If the desired behavior is to use a certain address 
over and over again, write the address to base_address, and 0 
to the end_address.

Increment mode: (address_mode == 1) The address will increment 
by one for every write, beginning at the base address. In the
Write Mode "write/read always", it will write from base to base + end,
then read from base to base + end, then begin again from
base + end to base + end + end, and so forth. At the 
max address, this will overflow to address 0. 
Note: In "Write Once Read Always" mode, the writer and reader will 
run alternating between the two as specified above until the entire
address space has been written to. Once the entire address space has
been reached, the address will overflow to 0 and only the reader will 
run, starting at base and going to base + end, then repeating.


The data mode available in this Bist is "Fixed" mode. The 32-bit
register input_data_pattern needs to be set before running the Bist.


There are two Write modes:

Write Once Read Always: (wr_mode == 0) Write to a set of addresses
between base_address and base_address + length_address, then read 
from this range indefinietly until the Bist is disabled. 

Write/Read Always: (wr_mode == 1) Write to a set of addresses 
between base_address and base_address + length_address, then read 
from this range, then write to the next set, then read from this
next set, and so forth. This is compatible with both address modes.
"""

class DRAMBistFSM(Module, AutoCSR):
    
    def __init__(self, dram_port : LiteDRAMNativePort):

        self.dram_port_bist = dram_port


        # Registers

        # The signal to enable (HIGH) or disable (LOW) the bist
        self.start = CSRStorage(ONE_BIT_WIDE, description="Enable(1)/Disable(0) the BIST")

        # A signal to know if the BIST is in the IDLE state
        self.bist_idle = CSRStatus(ONE_BIT_WIDE, description="Know if BIST is not running (HIGH if true)")

        # The first address our BIST should start at.
        self.base_address = CSRStorage(dram_port.address_width, description="The starting address BIST should access.")

        # A register to hold the number of bursts (in address length) that should happen in one cycle
        self.length_address = CSRStorage(dram_port.address_width, description="Burst quantity (for both reading and writing)")

        # The range of addresses our BIST should access
        self.end_address = CSRStorage(dram_port.address_width, description="The range of addresses our BIST should access.")

        # Registers to read to know the address width and data width
        self.bist_port_addr_width = CSRStatus(WIDTH_32_BITS, description="Port address width.")
        self.bist_port_data_width = CSRStatus(WIDTH_32_BITS, description="Port data width")

        # A register to contain the address mode for the bist, 0 for fixed, 1 for incr. Read above for description.
        self.address_mode = CSRStorage(TWO_BITS_WIDE, description="Address mode: 0 for fixed addr mode, 1 for increment addr mode")

        # A register to contain the write mode for the bist, 0 for write once read always, 1 for write/read always. Read above for description.
        self.wr_mode = CSRStorage(TWO_BITS_WIDE, description="Write mode: 0 for write once read always, 1 for write/read always.")

        # A register to set the mode to writer only
        self.write_only_mode = CSRStorage(ONE_BIT_WIDE, description="Write only mode: Control the part of the state machine that writes only.")

        # A register to set the mode to reader only
        self.reader_only_mode = CSRStorage(ONE_BIT_WIDE, description="Read only mode: Control the part of the state machine that reads only.")

        # Registers to acknowledge the writer is finished and acknowledged
        self.writer_finished_state = CSRStatus(ONE_BIT_WIDE, description="When high, writer is complete. Start must be set low, and this signal acknowledged.")
        self.writer_finished_acknowledge = CSRStorage(ONE_BIT_WIDE, description="When high, acknowledges that the writer is finished and can move on.")

        # Registers to acknowledge the reader is finished and acknowledged
        self.reader_finished_state = CSRStatus(ONE_BIT_WIDE, description="When high, reader is complete. Start must be set low, and this signal acknowledged.")
        self.reader_finished_acknowledge = CSRStorage(ONE_BIT_WIDE, description="When high, acknowledges that the reader is finished and can move on.")

        # A register to hold the data pattern to write or check reads from the port
        self.input_data_pattern = CSRStorage(WIDTH_32_BITS, description="Data pattern written to DRAM (Replicated/Concatenated to fill DRAM data width)")

        # Registers to output the data read from the port.
        ###########################################################################
        self.output_data_pattern1 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern2 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern3 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern4 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern5 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern6 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern7 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern8 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern9 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern10 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern11 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern12 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern13 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern14 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern15 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern16 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern17 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        self.output_data_pattern18 = CSRStatus(
            WIDTH_32_BITS, description="Data to read after performing read"
        )
        ##########################################################################

        # A register to hold the total number of ticks while writing
        self.write_ticks = CSRStatus(WIDTH_32_BITS, description="Total number of ticks during writing")

        # A register to hold the total number of ticks while reading
        self.read_ticks = CSRStatus(WIDTH_32_BITS, description="Total number of ticks during reading")

        # A register to hold the total number of writes taken place
        self.total_writes = CSRStatus(WIDTH_32_BITS, description="Total number of writes (used to calculate speed)")

        # A register to hold the total number of reads taken place
        self.total_reads = CSRStatus(WIDTH_32_BITS, description="Total number of reads (used to calculate speed)")

        # A register to signal to the user that an error has been found
        # and the state machine is waiting in a pause state.
        self.error_found_flag = CSRStatus(ONE_BIT_WIDE, description="High if the state machine is paused, as an error has been found.")

        # A register to acknowledge to the state machine that it has displayed the error and can move on.
        self.error_acknowledge_flag = CSRStorage(ONE_BIT_WIDE, description="Software should set this high if through with printing error, and state machine may move on.")

        # A register to count the number of errors
        self.error_counter = CSRStatus(WIDTH_32_BITS, description="Number of errors that occured")

        # A register to signal to the user that the max number of ticks has been reached and the bist
        # can now output data.
        self.data_pause_display_flag = CSRStatus(ONE_BIT_WIDE, description="High if the state machine has paused, as all the registers are paused and can be displayed.")

        # A register to acknowldeg to the state machine that it has displayed the data and can start over.
        self.data_acknowledge_flag = CSRStorage(ONE_BIT_WIDE, description="Acknowledge to the state machine, after its stopped, that it can now display the needed data.")

        # A register to hold the number of ticks to delay after a complete read
        self.max_delay_ticks = CSRStorage(WIDTH_32_BITS, description="Total number of ticks to delay after a read")

        # Registers to get the beginning and ending addresses
        self.beginning_address = CSRStatus(WIDTH_32_BITS, description="The address in which the BIST starts at")
        self.current_address = CSRStatus(WIDTH_32_BITS, description="Current address of reading or writing.")
        self.ending_address = CSRStatus(WIDTH_32_BITS, description="The address in which the BIST ends at.")

        # Registers to hold address with start of errors and end of errors
        self.error_beginning_address = CSRStatus(dram_port.address_width, description="Beginning address where errors start")
        self.error_ending_address = CSRStatus(dram_port.address_width, description="The last address holding a DRAM error")






        # Signals

        # A data signal to hold our data to check
        data_sig = Signal(dram_port.data_width)

        # A signal to hold the current address to write/read
        address_sig = Signal(dram_port.address_width)

        # A signal to hold the first address to write/read
        beg_address_sig = Signal(dram_port.address_width)

        # A signal to hold the last address of where the reads and writes should go
        end_address_sig = Signal(dram_port.address_width)

        # A signal to count the number of bursts in a write or read
        burst_cntr_sig = Signal(WIDTH_32_BITS)
        self.burst_cntr_sig = burst_cntr_sig

        # A signal to record if it is time to only read. Useful for "write once read always" setting.
        read_always_flag_sig = Signal(ONE_BIT_WIDE)

        # A signal to record if an error occured. Useful for "write once read always" setting
        error_flag_sig = Signal(ONE_BIT_WIDE)

        # A signal counter to count up to the max delay of ticks
        delay_tick_ctr_sig = Signal(WIDTH_32_BITS)

        # Acknowledge we have gone to the DISPLAY_DATA_PAUSE state so we can clear the counts
        display_data_pause_flag = Signal(ONE_BIT_WIDE)

        # Allow error acknowledge signal to stay high for one clock signal.
        error_ack_sig = Signal(ONE_BIT_WIDE)
        error_ack_high_prev_sig = Signal(ONE_BIT_WIDE)

        # Record error data to send to output
        self.error_data = Signal(dram_port.data_width)

        # Helper to record beginning error address
        error_beg_addr_chosen = Signal(ONE_BIT_WIDE)

        


        # A debug signal to find out which states we are in
        self.state_num_sig = CSRStatus(WIDTH_32_BITS)




        

        """
        The state machine for the bist. When started, the order of 
        the states is as follows:

        IDLE -> WRITE_REQUEST -> WRITE_REQ_REC -> WRITE_RECIEVE
        -> READ_REQUEST -> READ_REQ_REC -> READ_RECIEVE

        The three WRITE states run all the burst writes to the controller, 
        and the three READ states run all the burst reads. In the last 
        state, READ_RECIEVE, the next transition depends on the enability and 
        mode of the bist. If the START csr register is set low, the bist is 
        disabled, and the BIST will immediately go to the IDLE state. If not 
        disabled, the different modes are assessed. If in "write once read 
        always" mode, the next transition will be to the READ_REQUEST state. 
        If in "write always read always" mode, the next transition will be 
        to the WRITE_REQUEST state, where writes will begin again.

        """

        dram_port_fsm = FSM(reset_state="IDLE")
        self.submodules.dram_port_fsm = dram_port_fsm

        # Wait here until the User enables the Bist. Initialize everything beforehand
        # regardless of what sort of writing/reading mode is chosen.
        dram_port_fsm.act(
            "IDLE",
            self.state_num_sig.status.eq(0),
            self.bist_idle.status.eq(1),
            If(self.start.storage,
                NextValue(self.write_ticks.status, 0),
                NextValue(self.read_ticks.status, 0),
                NextValue(self.total_writes.status, 0),
                NextValue(self.total_reads.status, 0),
                NextValue(burst_cntr_sig, 0),
                NextValue(error_flag_sig, 0),
                NextValue(read_always_flag_sig, 0),
                NextValue(delay_tick_ctr_sig, 0),
                NextValue(self.error_counter.status, 0),
                NextValue(self.error_beginning_address.status, 0),
                NextValue(self.error_ending_address.status, 0),
                NextValue(error_beg_addr_chosen, 0),
                NextValue(address_sig, self.base_address.storage),
                NextValue(beg_address_sig, self.base_address.storage),
                NextValue(end_address_sig, self.base_address.storage + self.length_address.storage),
                If(self.write_only_mode.storage,
                    NextState("WRITER_ONLY_REQUEST"),
                ).Elif(self.reader_only_mode.storage,
                    NextState("READER_ONLY_REQUEST"),
                )
                .Else(
                    NextState("WRITE_REQUEST"),
                )
            )
        )

        dram_port_fsm.act(
            "WRITER_ONLY_REQUEST",
            self.state_num_sig.status.eq(0x11),
            dram_port.cmd.we.eq(1),
            dram_port.cmd.valid.eq(1),
            NextValue(self.write_ticks.status, self.write_ticks.status + 1),
            If(dram_port.cmd.ready,
                If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("WRITER_ONLY_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                    NextState("WRITER_ONLY_REC_REQ"),
                )
            )
        )

        dram_port_fsm.act(
            "WRITER_ONLY_REC_REQ",
            self.state_num_sig.status.eq(0x12),
            dram_port.cmd.we.eq(1),
            dram_port.wdata.valid.eq(1),
            dram_port.cmd.valid.eq(1),
            NextValue(self.write_ticks.status, self.write_ticks.status + 1),
            If(dram_port.wdata.ready,
                NextValue(self.total_writes.status, self.total_writes.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),
            ),
            If(dram_port.cmd.ready,
                If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("WRITER_ONLY_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                )
            )
        )

        dram_port_fsm.act(
            "WRITER_ONLY_RECIEVE",
            self.state_num_sig.status.eq(0x13),
            dram_port.cmd.we.eq(1),
            dram_port.wdata.valid.eq(1),
            NextValue(self.write_ticks.status, self.write_ticks.status + 1),
            If(dram_port.wdata.ready,
                NextValue(self.total_writes.status, self.total_writes.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),

                # We are done with writing a number of bursts 
                # at this "if" statement. 
                If((burst_cntr_sig + 1) >= (end_address_sig - beg_address_sig + 1),
                    NextState("WRITER_ONLY_FINISH"),
                ),
            )
        )

        dram_port_fsm.act(
            "WRITER_ONLY_FINISH",
            self.state_num_sig.status.eq(0x14),
            self.writer_finished_state.status.eq(1),
            If(self.writer_finished_acknowledge.storage,
                NextState("IDLE"),
            )
        )

        dram_port_fsm.act(
            "READER_ONLY_REQUEST",
            self.state_num_sig.status.eq(0x20),
            dram_port.cmd.valid.eq(1),
            NextValue(self.read_ticks.status, self.read_ticks.status + 1),
            If(dram_port.cmd.ready,
               If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("READER_ONLY_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                    NextState("READER_ONLY_REQ_REC"),
                )
            )
        )

        dram_port_fsm.act(
            "READER_ONLY_REQ_REC",
            self.state_num_sig.status.eq(0x21),
            dram_port.cmd.valid.eq(1),
            dram_port.rdata.ready.eq(1),
            NextValue(self.read_ticks.status, self.read_ticks.status + 1),
            If(dram_port.rdata.valid,
                NextValue(self.total_reads.status, self.total_reads.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),
                If(dram_port.rdata.data != data_sig,
                    NextValue(self.error_counter.status, self.error_counter.status + 1),
                    If(error_beg_addr_chosen == 0,
                       NextValue(self.error_beginning_address.status, self.base_address.storage + burst_cntr_sig),
                       NextValue(error_beg_addr_chosen, 1),
                    ),
                    NextValue(self.error_ending_address.status, self.base_address.storage + burst_cntr_sig),
                )
            ),
            If(dram_port.cmd.ready,
                If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("READER_ONLY_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                )
            )
        )

        dram_port_fsm.act(
            "READER_ONLY_RECIEVE",
            self.state_num_sig.status.eq(0x22),
            dram_port.rdata.ready.eq(1),
            NextValue(self.read_ticks.status, self.read_ticks.status + 1),
            If(dram_port.rdata.valid,
                NextValue(self.total_reads.status, self.total_reads.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),

                # We are done with writing a number of bursts 
                # at this "if" statement. 
                If((burst_cntr_sig + 1) >= (end_address_sig - beg_address_sig + 1),
                    NextState("READER_ONLY_FINISH"),
                    If(dram_port.rdata.data != data_sig,
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, self.base_address.storage + burst_cntr_sig),
                            NextValue(address_sig, self.base_address.storage + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ).Else(
                            NextValue(address_sig, self.error_beginning_address.status),
                        ),
                        NextValue(self.error_ending_address.status, self.base_address.storage + burst_cntr_sig),
                        NextState("READER_ONLY_ERR_REQ"), 
                    ).Elif(self.error_counter.status > 0,
                        NextValue(address_sig, self.error_beginning_address.status),
                        NextState("READER_ONLY_ERR_REQ"),
                    ),
                ).Else(
                    If(dram_port.rdata.data != data_sig,
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, self.base_address.storage + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ),
                        NextValue(self.error_ending_address.status, self.base_address.storage + burst_cntr_sig),
                    )
                )
            )
        )

        dram_port_fsm.act(
            "READER_ONLY_ERR_REQ",
            self.state_num_sig.status.eq(0x23),
            dram_port.cmd.valid.eq(1),
            If(dram_port.cmd.ready,
                NextState("READER_ONLY_ERR_REC"),
            )
        )

        dram_port_fsm.act(
            "READER_ONLY_ERR_REC",
            self.state_num_sig.status.eq(0x24),
            dram_port.rdata.ready.eq(1),
            If(dram_port.rdata.valid,
                NextValue(self.error_data, dram_port.rdata.data),
                NextState("READER_ONLY_ERR_DISPLAY"),
            )
        )

        dram_port_fsm.act(
            "READER_ONLY_ERR_DISPLAY",
            self.state_num_sig.status.eq(0x25),
            If((self.error_data == data_sig) | error_ack_sig,
                If(address_sig == self.error_ending_address.status,
                    NextState("READER_ONLY_FINISH"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                    NextState("READER_ONLY_ERR_REQ"),
                )
            ).Else(
                self.error_found_flag.status.eq(1),
            )
        )

        dram_port_fsm.act(
            "READER_ONLY_FINISH",
            self.state_num_sig.status.eq(0x26),
            self.reader_finished_state.status.eq(1),
            If(self.reader_finished_acknowledge.storage,
                NextState("IDLE"),
            )
        )



        # Set cmd.valid high, wait for cmd.ready.
        # The address_sig signal, beg_address_signal, and end_address_sig signal 
        # should be set before starting at this state.
        dram_port_fsm.act(
            "WRITE_REQUEST",
            self.state_num_sig.status.eq(0x1),
            dram_port.cmd.we.eq(1),
            dram_port.cmd.valid.eq(1),
            NextValue(self.write_ticks.status, self.write_ticks.status + 1),
            If(dram_port.cmd.ready,
                If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("WRITE_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                    NextState("WRITE_REQ_REC"),
                )
            )
        )

        # State that runs a burst write. 
        # This state should not be left until the number of
        # cycles in which cmd.valid and cmd.ready are high 
        # match the number of addresses between beg_address_sig
        # and end_address_sig.
        dram_port_fsm.act(
            "WRITE_REQ_REC",
            self.state_num_sig.status.eq(0x2),
            dram_port.cmd.we.eq(1),
            dram_port.wdata.valid.eq(1),
            dram_port.cmd.valid.eq(1),
            NextValue(self.write_ticks.status, self.write_ticks.status + 1),
            If(dram_port.wdata.ready,
                NextValue(self.total_writes.status, self.total_writes.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),
            ),
            If(dram_port.cmd.ready,
                If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("WRITE_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                )
            )
        )

        # State that finishes up the write transactions.
        # This state should not be left until the number of cycles
        # in which wdata.valid and wdata.ready are high
        # match the number of addresses between beg_address_sig
        # and end_address_sig.
        dram_port_fsm.act(
            "WRITE_RECIEVE",
            self.state_num_sig.status.eq(0x3),
            dram_port.cmd.we.eq(1),
            dram_port.wdata.valid.eq(1),
            NextValue(self.write_ticks.status, self.write_ticks.status + 1),
            If(dram_port.wdata.ready,
                NextValue(self.total_writes.status, self.total_writes.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),

                # We are done with writing a number of bursts 
                # at this "if" statement. 
                If((burst_cntr_sig + 1) >= (end_address_sig - beg_address_sig + 1),
                    NextValue(burst_cntr_sig, 0),
                    NextValue(address_sig, beg_address_sig),
                    NextState("READ_REQUEST"),
                ),
            )
        )

        # Set cmd.valid high, wait for cmd.ready.
        # The address_sig signal should be reset before starting at this state,
        # and proper values given to beg_address_sig and end_address_sig.
        dram_port_fsm.act(
            "READ_REQUEST",
            self.state_num_sig.status.eq(0x4),
            dram_port.cmd.valid.eq(1),
            NextValue(self.read_ticks.status, self.read_ticks.status + 1),
            If(dram_port.cmd.ready,
               If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("READ_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                    NextState("READ_REQ_REC"),
                )
            )
        )

        # State that runs a burst read. 
        # This state must go to the pause state if the data recieved
        # does not match expected data, and the address and data registers can
        # then be displayed for the user.
        # Procedure to the READ_RECIEVE state should not happen until the number of 
        # cycles in which cmd.valid and cmd.ready are high 
        # match the number of addresses between beg_address_sig
        # and end_address_sig.
        dram_port_fsm.act(
            "READ_REQ_REC",
            self.state_num_sig.status.eq(0x5),
            dram_port.cmd.valid.eq(1),
            dram_port.rdata.ready.eq(1),
            NextValue(self.read_ticks.status, self.read_ticks.status + 1),
            If(dram_port.rdata.valid,
                NextValue(self.total_reads.status, self.total_reads.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),
                If(dram_port.rdata.data != data_sig,
                    NextValue(self.error_counter.status, self.error_counter.status + 1),
                    If(error_beg_addr_chosen == 0,
                       NextValue(self.error_beginning_address.status, self.base_address.storage + burst_cntr_sig),
                       NextValue(error_beg_addr_chosen, 1),
                    ),
                    NextValue(self.error_ending_address.status, self.base_address.storage + burst_cntr_sig),
                )
            ),
            If(dram_port.cmd.ready,
                If(address_sig == end_address_sig,
                    NextValue(address_sig, address_sig),
                    NextState("READ_RECIEVE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                )
            )
        )

        # We have reached the final address. Keep handling the reads and comparing 
        # the data until finished.
        dram_port_fsm.act(
            "READ_RECIEVE",
            self.state_num_sig.status.eq(0x6),
            dram_port.rdata.ready.eq(1),
            NextValue(self.read_ticks.status, self.read_ticks.status + 1),
            If(dram_port.rdata.valid,
                NextValue(self.total_reads.status, self.total_reads.status + 1),
                NextValue(burst_cntr_sig, burst_cntr_sig + 1),

                # We are done with writing a number of bursts 
                # at this "if" statement. 
                If((burst_cntr_sig + 1) >= (end_address_sig - beg_address_sig + 1),
                    NextState("DISPLAY_DATA_PAUSE"),
                    If(dram_port.rdata.data != data_sig,
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, self.base_address.storage + burst_cntr_sig),
                            NextValue(address_sig, self.base_address.storage + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ).Else(
                            NextValue(address_sig, self.error_beginning_address.status),
                        ),
                        NextValue(self.error_ending_address.status, self.base_address.storage + burst_cntr_sig),
                        NextState("READ_ERR_REQ"), 
                    ).Elif(self.error_counter.status > 0,
                        NextValue(address_sig, self.error_beginning_address.status),
                        NextState("READ_ERR_REQ"),
                    ),
                ).Else(
                    If(dram_port.rdata.data != data_sig,
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, self.base_address.storage + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ),
                        NextValue(self.error_ending_address.status, self.base_address.storage + burst_cntr_sig),
                    )
                )
            )
        )

        dram_port_fsm.act(
            "READ_ERR_REQ",
            self.state_num_sig.status.eq(0x7),
            dram_port.cmd.valid.eq(1),
            If(dram_port.cmd.ready,
                NextState("READ_ERR_REC"),
            )
        )

        dram_port_fsm.act(
            "READ_ERR_REC",
            self.state_num_sig.status.eq(0x8),
            dram_port.rdata.ready.eq(1),
            If(dram_port.rdata.valid,
                NextValue(self.error_data, dram_port.rdata.data),
                NextState("READ_ERR_DISPLAY"),
            )
        )

        dram_port_fsm.act(
            "READ_ERR_DISPLAY",
            self.state_num_sig.status.eq(0x9),
            If(self.start.storage == 0,
                NextState("IDLE"),
            ).Elif((self.error_data == data_sig) | error_ack_sig,
                If(address_sig == self.error_ending_address.status,
                    NextState("DISPLAY_DATA_PAUSE"),
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                    NextState("READ_ERR_REQ"),
                )
            ).Else(
                self.error_found_flag.status.eq(1),
            )
        )


        # Once we have reached the max number of ticks, pause in this state to display the data
        dram_port_fsm.act(
            "DISPLAY_DATA_PAUSE",
            self.state_num_sig.status.eq(0xa),
            self.data_pause_display_flag.status.eq(1),
            If(self.start.storage == 0,
                NextState("IDLE"),
            ).Elif(self.data_acknowledge_flag.storage,
                NextValue(display_data_pause_flag, 1),
                NextState("END_STATE_WAIT_CHOOSER"),
            )
        )



        dram_port_fsm.act(
            "END_STATE_WAIT_CHOOSER",
            self.state_num_sig.status.eq(0xb),
            NextValue(delay_tick_ctr_sig, delay_tick_ctr_sig + 1),
            If(delay_tick_ctr_sig >= self.max_delay_ticks.storage,
                If(display_data_pause_flag,
                    NextValue(display_data_pause_flag, 0),
                    NextValue(self.write_ticks.status, 0),
                    NextValue(self.read_ticks.status, 0),
                    NextValue(self.total_writes.status, 0),
                    NextValue(self.total_reads.status, 0),
                    NextValue(burst_cntr_sig, 0),
                ),
                NextValue(delay_tick_ctr_sig, 0),
                If(~self.start.storage,
                    NextState("IDLE"),
                ).Elif(self.address_mode.storage == FIXED_ADDR_MODE,
                    NextValue(address_sig, beg_address_sig),
                    If(self.wr_mode.storage == W_ONCE_R_ALWAYS,
                        NextState("READ_REQUEST")
                    ).Elif(self.wr_mode.storage == WR_ALWAYS,
                        NextState("WRITE_REQUEST")
                    )
                ).Elif(self.address_mode.storage == INCR_ADDR_MODE,
                    If(self.wr_mode.storage == W_ONCE_R_ALWAYS,
                        # If overflow occurs when assigning the new values, 
                        # revert the new addresses back to the original ones.
                        If(error_flag_sig,
                            NextValue(beg_address_sig, beg_address_sig),
                            NextValue(address_sig, beg_address_sig),
                            NextValue(end_address_sig, end_address_sig),
                            NextState("WRITE_REQUEST"),
                        ).Elif((beg_address_sig >= (end_address_sig + self.length_address.storage + 1)) | 
                            (end_address_sig >= self.end_address.storage),
                            NextValue(beg_address_sig, self.base_address.storage),
                            NextValue(address_sig, self.base_address.storage),
                            NextValue(end_address_sig, self.base_address.storage + self.length_address.storage),
                            NextValue(read_always_flag_sig, 1),
                            NextState("READ_REQUEST"),
                        ).Else(
                            NextValue(beg_address_sig, beg_address_sig + self.length_address.storage + 1),
                            NextValue(address_sig, beg_address_sig + self.length_address.storage + 1),
                            NextValue(end_address_sig, end_address_sig + self.length_address.storage + 1),
                            If(read_always_flag_sig,
                                NextState("READ_REQUEST"),   
                            ).Else(
                                NextState("WRITE_REQUEST"),
                            )
                        ),
                    ).Elif(self.wr_mode.storage == WR_ALWAYS,
                        If(beg_address_sig >= (end_address_sig + self.length_address.storage + 1),
                            NextValue(beg_address_sig, self.base_address.storage),
                            NextValue(address_sig, self.base_address.storage),
                            NextValue(end_address_sig, self.base_address.storage + self.length_address.storage),
                        ).Else(
                            NextValue(beg_address_sig, beg_address_sig + self.length_address.storage + 1),
                            NextValue(address_sig, beg_address_sig + self.length_address.storage + 1),
                            NextValue(end_address_sig, end_address_sig + self.length_address.storage + 1),
                        ),
                        NextState("WRITE_REQUEST"),
                    )
                )   
            )
        )




        """
        This synch block allows the error acknowledge signal to stay high
        for only one clock cycle
        """
        self.sync += [
            If(self.error_acknowledge_flag.storage,
                If(error_ack_high_prev_sig,
                    error_ack_sig.eq(0),
                    error_ack_high_prev_sig.eq(1),
                ).Else(
                    error_ack_sig.eq(1),
                    error_ack_high_prev_sig.eq(1),
                )
            ).Else(
                error_ack_sig.eq(0),
                error_ack_high_prev_sig.eq(0),
            )
        ]





        """
        The data, being fixed, will be concatenated as many times as 
        needed to fill the data width. When the checker is running, the
        data will be passed across a max of 16 32-bit CSR registers.
        I figure most data widths of dram ports are 32, 64, 128, 256, or 512 
        bits wide, but if not this will raise an exception.
        If this needs to be adjusted, make sure the number of bits in
        the register "input_data_pattern" are a multiple of the dram width,
        and that the correct number of output_data signals are set to the 
        dram_por.rdata.data signal. The software, in bist_nodma.c, where 
        the register "input_data_pattern" is being
        used, may need to be adjusted so the data signal is smaller 
        as well.
        """
        if ((dram_port.data_width % DATA_WIDTH_32) != 0): 
            print("The DRAM port data width, ", dram_port.data_width, ", is not a multiple of 32.")
        else:
            self.comb += [

                # Set the cmd address to the current value of the address_sig
                dram_port.cmd.addr.eq(address_sig),

                # Get the address range
                self.beginning_address.status.eq(beg_address_sig),
                self.current_address.status.eq(address_sig),
                self.ending_address.status.eq(end_address_sig),

                # Set the port address width and data width, that we can obtain it in software
                self.bist_port_addr_width.status.eq(dram_port.address_width),
                self.bist_port_data_width.status.eq(dram_port.data_width),

                # Set the write-enable data signal to all ones in case
                # byte-enabled writes are supported
                dram_port.wdata.we.eq(~0),

                # Set the data to write with a replicated CSR register
                data_sig.eq(Replicate(self.input_data_pattern.storage, dram_port.data_width//len(self.input_data_pattern.storage))),
                dram_port.wdata.data.eq(data_sig),

            ]

            # Set the data registers to rdata.data
            for i in range(1, 19):
                if (i * DATA_WIDTH_32) <= dram_port.data_width:
                    self.comb += getattr(self, "output_data_pattern{index}".format(index = i)).status.eq(self.error_data[DATA_WIDTH_32 * (i - 1):DATA_WIDTH_32 * (i)])
                    # print("We did output_data_pattern{index} from {range1} to {range2}. YAY!!".format(index = i, range1 = DATA_WIDTH_32 * (i - 1), range2 = DATA_WIDTH_32 * (i)))
                else:
                    self.comb += getattr(self, "output_data_pattern{index}".format(index = i)).status.eq(0)
                    # print("We did not do output_data_pattern{index}. AWW!!".format(index = i))

            


