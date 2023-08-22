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
WIDTH_64_BITS = 64

FIXED_ADDR_MODE = 0
INCR_ADDR_MODE = 1

READ_ALWAYS = 0
W_ONCE_R_ALWAYS = 1
WR_ALWAYS = 2


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
    
    def __init__(self, dram_port : LiteDRAMNativePort, sys_clk_freq : int):

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

        # The difference between the length and base addresses.
        self.base_length_diff = CSRStorage(WIDTH_32_BITS, description="The difference between the length and base addresses.")

        # Registers to read to know the address width and data width
        self.bist_port_addr_width = CSRStatus(WIDTH_32_BITS, description="Port address width.")
        self.bist_port_data_width = CSRStatus(WIDTH_32_BITS, description="Port data width")

        # A register to contain the address mode for the bist, 0 for fixed, 1 for incr. Read above for description.
        self.address_mode = CSRStorage(TWO_BITS_WIDE, description="Address mode: 0 for fixed addr mode, 1 for increment addr mode")

        # A register to contain the write mode for the bist, 0 for write once read always, 1 for write/read always. Read above for description.
        self.wr_mode = CSRStorage(TWO_BITS_WIDE, description="Write mode: 0 for read always, 1 for write once read always, 2 for write/read always.")

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
        self.seconds_delay = CSRStorage(WIDTH_32_BITS, description="Total number of seconds to delay after a read")

        # Registers to get the beginning and ending addresses
        self.beginning_address = CSRStatus(WIDTH_32_BITS, description="The address in which the BIST starts at")
        self.current_address = CSRStatus(WIDTH_32_BITS, description="Current address of reading or writing.")
        self.ending_address = CSRStatus(WIDTH_32_BITS, description="The address in which the BIST ends at.")

        # Registers to hold address with start of errors and end of errors
        self.error_beginning_address = CSRStatus(dram_port.address_width, description="Beginning address where errors start")
        self.error_ending_address = CSRStatus(dram_port.address_width, description="The last address holding a DRAM error")
        
        self.error_max_count = CSRStorage(WIDTH_32_BITS, description="Max number of errors to display")

        # A register to disable the error_flag_sig for read-only mode
        self.error_flag_enable = CSRStorage(ONE_BIT_WIDE, reset=ONE_BIT_WIDE, description="Disable the error flag in order to simply read continuously without scrubbing.")






        # Signals

        # A data signal to hold our data to check
        data_sig = Signal(dram_port.data_width)
        self.data_sig = data_sig

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
        self.read_always_flag_sig = read_always_flag_sig

        # A signal, for the condition of write once read always mode, that we are scrubbing
        # and need to reach all the addresses.
        scrubbing_flag_sig = Signal(ONE_BIT_WIDE)
        self.scrubbing_flag_sig = scrubbing_flag_sig

        # A signal to record if an error occured. Useful for "write once read always" setting
        error_flag_sig = Signal(ONE_BIT_WIDE)
        self.error_flag_sig = error_flag_sig

        # A signal counter to count up to the max delay of ticks
        delay_tick_ctr_sig = Signal(WIDTH_64_BITS)

        # A signal that is set to the number of seconds times the number of clock cycles per second
        delay_max_ticks_sig = Signal(WIDTH_64_BITS)

        # Allow error acknowledge signal to stay high for one clock signal.
        error_ack_sig = Signal(ONE_BIT_WIDE)
        error_ack_high_prev_sig = Signal(ONE_BIT_WIDE)

        # Record error data to send to output
        self.error_data = Signal(dram_port.data_width)

        # Helper to record beginning error address
        error_beg_addr_chosen = Signal(ONE_BIT_WIDE)

        # A signal holding the maximum address possible
        max_address_sig = Signal(dram_port.address_width)

        # A debug signal to find out which states we are in
        self.state_num_sig = CSRStatus(WIDTH_32_BITS)

        # Counter signal to control how many errors displayed
        error_display_counter_sig = Signal(WIDTH_32_BITS)
        error_max_display_counter_sig = Signal(WIDTH_32_BITS)
        self.error_display_counter_sig = error_display_counter_sig




        ##############################
        # Debugging signal
        ##############################
        self.chooser_cntr_sig = chooser_cntr_sig = Signal(WIDTH_32_BITS)
        ##############################




        

        """
        The state machine for the bist. This is a three-way state machine
        with the "IDLE" state in the center of it all.

        The general paths the bist may run are as follows:

        Writer only:

        IDLE -> WRITER_ONLY_REQUEST -> WRITER_ONLY_REC_REQ -> WRITER_ONLY_RECIEVE -> 
        WRITER_ONLY_FINISH -> IDLE

        Reader only:

        IDLE -> READER_ONLY_REQUEST -> READER_ONLY_REQ_REC -> READER_ONLY_RECIEVE -> 
        READER_ONLY_ERR_REQ -> READER_ONLY_RECIEVE -> READER_ONLY_ERR_DISPLAY -> 
        READER_ONLY_FINISH -> IDLE

        Continuous:

        IDLE -> WRITE_REQUEST -> WRITE_REQ_REC -> WRITE_RECIEVE -> READ_REQUEST -> 
        READ_REQ_REC -> READ_RECIEVE -> READ_ERR_REQ -> READ_ERR_REC -> READ_ERR_DISPLAY -> 
        END_STATE_WAIT_CHOOSER -> WRITE_REQUEST -> ...

        For the "Reader only" and the "Writer only" functions, three states each will 
        run the bursts in the native protocol for reading and writing. Afterwards, these
        will wait in the "WRITER_ONLY_FINISH" and "READER_ONLY_FINISH" states until the 
        software has used the data saved in the necessary CSR registers. In the "Reader
        Only" section, instead of immediately going to "READER_ONLY_FINISH", three more
        "ERR" states will conduct a series of single reads if errors were found 
        throughout the burst read, and wait in the "READER_ONLY_ERR_DISPLAY" state until
        software has printed out the address and erroneous data. If no errors are found, 
        these three states are skipped.

        For the "Continuous" function, three states conduct the burst write, and three 
        states conduct the burst read, with three error states to reread the errors and 
        pause to allow for software to display the erroneous data. The last state,
        "END_STATE_WAIT_CHOOSER", will choose which addresses to use and whether to 
        write or read next, depending on the settings given to the bist.

        """

        dram_port_fsm = FSM(reset_state="IDLE")
        self.submodules.dram_port_fsm = dram_port_fsm

        # This is the state in which the BIST resides after it is disabled.
        # Before a transition to start reading or writing, all counters and
        # flags are reset to 0, and the address variables are chosen based 
        # on user settings.
        dram_port_fsm.act(
            "IDLE",
            self.state_num_sig.status.eq(0),
            self.bist_idle.status.eq(1),

            # A transition will only occur if the "start" register is set 
            # high. One, and only one, of either the registers 
            # write_only_mode or read_only_mode must be set high for 
            # either transition to the read_only or write_only settings.
            # If both are low, the transition to the continuous mode 
            # will be taken.
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
                NextValue(scrubbing_flag_sig, 0),
                NextValue(chooser_cntr_sig, 0),
                NextValue(error_display_counter_sig, 0),
                If(self.error_max_count.storage == 0,
                    NextValue(error_max_display_counter_sig, max_address_sig),
                ).Else(
                    NextValue(error_max_display_counter_sig, self.error_max_count.storage),
                ),
                NextValue(address_sig, self.base_address.storage),
                NextValue(beg_address_sig, self.base_address.storage),
                NextValue(end_address_sig, self.base_address.storage + self.length_address.storage),
                If(self.write_only_mode.storage,
                    NextState("WRITER_ONLY_REQUEST"),
                ).Elif(self.reader_only_mode.storage,
                    NextState("READER_ONLY_REQUEST"),
                )
                .Else(
                    If(self.wr_mode.storage == READ_ALWAYS,
                        NextState("READ_REQUEST"),
                        NextValue(read_always_flag_sig, 1),
                    ).Else(
                        NextState("WRITE_REQUEST"),
                    ),
                )
            )
        )

        # The beginning state of the "write_only" mode. The signals
        # cmd.we and cmd.valid are set high. A transition will only 
        # occur if the signal cmd.ready is high.
        # If only a single address is input (i.e. the register 
        # length_address is set to zero), a transition will go to
        # the writer_only_recieve state, else a transition will go
        # to the writer_only recieve and request state.
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

        # The middle state of the "write_only" mode. Both wdata.valid
        # and cmd.valid are set high while holding the cmd.we signal high.
        # The current address is compared to the last desired address to write to,
        # and for every transition the address doesn't match, the current address is 
        # incremented. When it matches, a transition will occur to the 
        # writer_only recieve state - this signifies we have sent commands 
        # to write to all the addresses in our range we have specified. 
        # The number of writes is recorded and incremented every time 
        # wdata.ready goes high.
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

        # The end state of the "write only" mode. All the addresses to write 
        # have been set; now we wait for all the writes to finish while 
        # wdata.valid is held high, all while keeping track of the number of
        # writes occuring when wdata.ready goes high. A transition to 
        # "writer_only_finish" is taken once the number of writes match the 
        # number of addresses we've written to.
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
                # at this "if" statement: the number of writes 
                # match the number of addresses we've written to.
                If((burst_cntr_sig + 1) >= (self.base_length_diff.storage + 1),
                    NextState("WRITER_ONLY_FINISH"),
                ),
            )
        )

        # The last state of the "write_only" mode. Basically, wait here
        # until the program has finished printing all the saved data in
        # the CSR registers and acknowledges it is done.
        dram_port_fsm.act(
            "WRITER_ONLY_FINISH",
            self.state_num_sig.status.eq(0x14),
            self.writer_finished_state.status.eq(1),
            If(self.writer_finished_acknowledge.storage,
                NextState("IDLE"),
            )
        )

        # The beginning state of the "read_only" mode. The signal
        # cmd.valid are set high. A transition will only 
        # occur if the signal cmd.ready is high.
        # If only a single address is input (i.e. the register 
        # length_address is set to zero), a transition will go to
        # the reader_only_recieve statewhere a burst read 
        # may occur, else a transition will go
        # to the reader_only recieve and request state.
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

        # The middle state of the "read only" mode. The signals 
        # cmd.valid and rdata.ready are held high. The data is 
        # not held here; an error counter simply increments if 
        # the data does not match what is expected. If errors 
        # are found, the address where the errors start and 
        # the address where the errors end are both saved to reduce
        # time when running the single reads with the three 
        # error-reading states. Once the address reaches the last 
        # in the range that the user has set, we have sent commands 
        # to read from all the addresses in our range we have 
        # specified, and a transition to the "reader_only_recieve" 
        # state will occur. The number of reads is recorded and 
        # incremented every time rdata.ready goes high. 
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
                       NextValue(self.error_beginning_address.status, beg_address_sig + burst_cntr_sig),
                       NextValue(error_beg_addr_chosen, 1),
                    ),
                    NextValue(self.error_ending_address.status, beg_address_sig + burst_cntr_sig),
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

        # The third state of the "read only" mode. The signal rdata.ready
        # is continuously set high. A transition will only occur to the 
        # "READER_ONLY_FINISH" state if no data errors are found. The 
        # number of reads is continuously measured, incremented every
        # time rdata.ready is set high. The number of errors is also 
        # kept track of as well.
        # Once the reads are finished (i.e. the number of reads matches
        # the number of addresses sent to the controller), a transition
        # is taken base on these statements:
        # - If erros were counted, go to the "READER_ONLY_ERR_REQ" state
        # - If errors were not counted, but the last read is an error, 
        # go to the "READER_ONLY_ERR_REQ" state.
        # - Else go to the "READER_ONLY_FINISH" state.
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
                If((burst_cntr_sig + 1) >= (self.base_length_diff.storage + 1),
                    NextState("READER_ONLY_FINISH"),
                    If(dram_port.rdata.data != data_sig,
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, beg_address_sig + burst_cntr_sig),
                            NextValue(address_sig, self.base_address.storage + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ).Else(
                            NextValue(address_sig, self.error_beginning_address.status),
                        ),
                        NextValue(self.error_ending_address.status, beg_address_sig + burst_cntr_sig),
                        NextState("READER_ONLY_ERR_REQ"), 
                    ).Elif(self.error_counter.status > 0,
                        NextValue(address_sig, self.error_beginning_address.status),
                        NextState("READER_ONLY_ERR_REQ"),
                    ),
                ).Else(
                    If(dram_port.rdata.data != data_sig,
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, beg_address_sig + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ),
                        NextValue(self.error_ending_address.status, beg_address_sig + burst_cntr_sig),
                    )
                )
            )
        )

        # The first error-reading state of the "read only" mode.
        # The reading has been finished, and there are errors.
        # Beginning at the first address where errors occured, 
        # do a single read. Set cmd.valid high, and wait for 
        # cmd.ready to go high. The address is set in a comb
        # block at the end of this page.
        dram_port_fsm.act(
            "READER_ONLY_ERR_REQ",
            self.state_num_sig.status.eq(0x23),
            dram_port.cmd.valid.eq(1),
            If(dram_port.cmd.ready,
                NextState("READER_ONLY_ERR_REC"),
            )
        )

        # The second error-reading state of the "read only" mode.
        # The reading has been finished, and there are errors.
        # Now that cmd.ready was set high with the appropriate 
        # address, set rdata.ready high and wait for rdata.valid 
        # to go high.
        dram_port_fsm.act(
            "READER_ONLY_ERR_REC",
            self.state_num_sig.status.eq(0x24),
            dram_port.rdata.ready.eq(1),
            If(dram_port.rdata.valid,
                NextValue(self.error_data, dram_port.rdata.data),
                NextState("READER_ONLY_ERR_DISPLAY"),
            )
        )

        # The third error-reading state of the "read only" mode.
        # The reading has been finished, and there are errors.
        # Beginning at the first address where errors occured, 
        # do a single read. Set cmd.valid high, and wait for 
        # cmd.ready to go high. The address is set in a comb
        # block at the end of this page.
        dram_port_fsm.act(
            "READER_ONLY_ERR_DISPLAY",
            self.state_num_sig.status.eq(0x25),
            If(((self.error_data == data_sig) | error_ack_sig | (error_display_counter_sig >= error_max_display_counter_sig)),
                If((address_sig == self.error_ending_address.status) | 
                   (error_display_counter_sig >= error_max_display_counter_sig),
                    NextState("READER_ONLY_FINISH"),
                    NextValue(error_display_counter_sig, 0),
                ).Else(
                    # Note: My train of thought here is that the error_found_flag will not go high 
                    # unless there is an error, and error_ack_sig will not go high until software
                    # sees the error_found_flag go high and sets error_ack_sig high. Therefore, 
                    # error_ack_sig will not go high unless an error is found.
                    If(error_ack_sig,
                        NextValue(error_display_counter_sig, error_display_counter_sig + 1),
                    ),
                    NextValue(address_sig, address_sig + 1),
                    NextState("READER_ONLY_ERR_REQ"),
                )
            ).Else(
                self.error_found_flag.status.eq(1),
            )
        )

        # The final state of the "read-only" mode. All reading
        # has been finished, including errors, and the User must
        # print out a summary taken from the CSR registers. Pause
        # here and wait until program has finished printing out 
        # everything from the registers.
        dram_port_fsm.act(
            "READER_ONLY_FINISH",
            self.state_num_sig.status.eq(0x26),
            self.reader_finished_state.status.eq(1),
            If(self.reader_finished_acknowledge.storage,
                NextState("IDLE"),
            )
        )


        # The beginning state of the continuous mode. The signals
        # cmd.we and cmd.valid are set high. A transition will only 
        # occur if the signal cmd.ready is high.
        # If only a single address is input (i.e. the register 
        # length_address is set to zero), a transition will go to
        # the writer_only_recieve state, else a transition will go
        # to the writer_only recieve and request state.
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

        # The second state of the continuous mode. Both wdata.valid
        # and cmd.valid are set high while holding the cmd.we signal high.
        # The current address is compared to the last desired address to write to,
        # and for every transition the address doesn't match, the current address is 
        # incremented. When it matches, a transition will occur to the 
        # writer_only recieve state - this signifies we have sent commands 
        # to write to all the addresses in our range we have specified. 
        # The number of writes is recorded and incremented every time 
        # wdata.ready goes high.
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
                If((address_sig == end_address_sig) | 
                   ((address_sig == (self.base_address.storage - 1)) &  # max_address_sig
                    ((self.wr_mode.storage == W_ONCE_R_ALWAYS) | (self.wr_mode.storage == READ_ALWAYS)) & 
                    (self.address_mode.storage == INCR_ADDR_MODE) & 
                    (scrubbing_flag_sig == 0)),
                    NextValue(address_sig, address_sig),
                    NextState("WRITE_RECIEVE"),
                    If((address_sig == (self.base_address.storage - 1)) & ((self.wr_mode.storage == W_ONCE_R_ALWAYS) | (self.wr_mode.storage == READ_ALWAYS)) & (self.address_mode.storage == INCR_ADDR_MODE), # max_address_sig
                       NextValue(read_always_flag_sig, 1),
                    )
                ).Else(
                    NextValue(address_sig, address_sig + 1),
                )
            )
        )

        # The third state of the continuous mode. All the addresses to write 
        # have been set; now we wait for all the writes to finish while 
        # wdata.valid is held high, all while keeping track of the number of
        # writes occuring when wdata.ready goes high. A transition to 
        # "READ_REQUEST" is taken once the number of writes match the 
        # number of addresses we've written to.
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
                If(((burst_cntr_sig + 1) >= (self.base_length_diff.storage + 1)) | 
                   ((((burst_cntr_sig + beg_address_sig) & max_address_sig) == (address_sig)) & read_always_flag_sig & (scrubbing_flag_sig == 0)),
                   # (((burst_cntr_sig + address_sig) == (self.base_address.storage - 1)) & read_always_flag_sig & (scrubbing_flag_sig == 0)),
                    If(~self.start.storage,
                        NextState("IDLE"),
                    ).Else(
                        NextValue(burst_cntr_sig, 0),
                        NextValue(address_sig, beg_address_sig),
                        NextValue(scrubbing_flag_sig, 0),
                        NextState("READ_REQUEST"),
                    )
                ),
            )
        )

        # The fourth state of the continuous mode. The signal
        # cmd.valid are set high. A transition will only 
        # occur if the signal cmd.ready is high.
        # If only a single address is input (i.e. the register 
        # length_address is set to zero), a transition will go to
        # the reader_only_recieve state where a burst read 
        # may occur, else a transition will go
        # to the reader_only recieve and request state.
        dram_port_fsm.act(
            "READ_REQUEST",
            NextValue(delay_tick_ctr_sig, delay_tick_ctr_sig + 1),
            If(delay_tick_ctr_sig >= delay_max_ticks_sig,
                NextValue(delay_tick_ctr_sig, delay_tick_ctr_sig),
                self.state_num_sig.status.eq(0x4),
                dram_port.cmd.valid.eq(1),
                NextValue(self.read_ticks.status, self.read_ticks.status + 1),
                If(dram_port.cmd.ready,
                If(address_sig == end_address_sig,
                        NextValue(address_sig, address_sig),
                        NextValue(delay_tick_ctr_sig, 0),
                        NextState("READ_RECIEVE"),
                    ).Else(
                        NextValue(address_sig, address_sig + 1),
                        NextValue(delay_tick_ctr_sig, 0),
                        NextState("READ_REQ_REC"),
                    )
                )
            )
        )

        # The fifth state of the continuous mode. The signals 
        # cmd.valid and rdata.ready are held high. The data is 
        # not held here; an error counter simply increments if 
        # the data does not match what is expected. If errors 
        # are found, the address where the errors start and 
        # the address where the errors end are both saved to reduce
        # time when running the single reads with the three 
        # error-reading states. Once the address reaches the last 
        # in the range that the user has set, we have sent commands 
        # to read from all the addresses in our range we have 
        # specified, and a transition to the "reader_only_recieve" 
        # state will occur. The number of reads is recorded and 
        # incremented every time rdata.ready goes high. 
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
                    NextValue(error_flag_sig, 1),
                    NextValue(self.error_counter.status, self.error_counter.status + 1),
                    If(error_beg_addr_chosen == 0,
                       NextValue(self.error_beginning_address.status, beg_address_sig + burst_cntr_sig),
                       NextValue(error_beg_addr_chosen, 1),
                    ),
                    NextValue(self.error_ending_address.status, beg_address_sig + burst_cntr_sig),
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

        # The third state of the continuous mode. The signal rdata.ready
        # is continuously set high. A transition will only occur to the 
        # "DISPLAY_DATA_PAUSE" state if no data errors are found. The 
        # number of reads is continuously measured, incremented every
        # time rdata.ready is set high. The number of errors is also 
        # kept track of as well.
        # Once the reads are finished (i.e. the number of reads matches
        # the number of addresses sent to the controller), a transition
        # is taken base on these statements:
        # - If erros were counted, go to the "READ_ERR_REQ" state
        # - If errors were not counted, but the last read is an error, 
        # go to the "READ_ERR_REQ" state.
        # - Else go to the "DISPLAY_DATA_PAUSE" state.
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
                If((burst_cntr_sig + 1) >= (self.base_length_diff.storage + 1),
                    NextState("DISPLAY_DATA_PAUSE"),
                    If(dram_port.rdata.data != data_sig,
                        NextValue(error_flag_sig, 1),
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, beg_address_sig + burst_cntr_sig),
                            NextValue(address_sig, self.base_address.storage + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ).Else(
                            NextValue(address_sig, self.error_beginning_address.status),
                        ),
                        NextValue(self.error_ending_address.status, beg_address_sig + burst_cntr_sig),
                        NextState("READ_ERR_REQ"), 
                    ).Elif((error_flag_sig == 1),# self.error_counter.status > 0,
                        NextValue(address_sig, self.error_beginning_address.status),
                        NextState("READ_ERR_REQ"),
                    ),
                ).Else(
                    If(dram_port.rdata.data != data_sig,
                        NextValue(error_flag_sig, 1),
                        NextValue(self.error_counter.status, self.error_counter.status + 1),
                        If(error_beg_addr_chosen == 0,
                            NextValue(self.error_beginning_address.status, beg_address_sig + burst_cntr_sig),
                            NextValue(error_beg_addr_chosen, 1),
                        ),
                        NextValue(self.error_ending_address.status, beg_address_sig + burst_cntr_sig),
                    )
                )
            )
        )

        # The first error-reading state of the continuous mode.
        # The reading has been finished, and there are errors.
        # Beginning at the first address where errors occured, 
        # do a single read. Set cmd.valid high, and wait for 
        # cmd.ready to go high. The address is set in a comb
        # block at the end of this page.
        dram_port_fsm.act(
            "READ_ERR_REQ",
            self.state_num_sig.status.eq(0x7),
            dram_port.cmd.valid.eq(1),
            If(dram_port.cmd.ready,
                NextState("READ_ERR_REC"),
            )
        )

        # The second error-reading state of the continuous mode.
        # The reading has been finished, and there are errors.
        # Now that cmd.ready was set high with the appropriate 
        # address, set rdata.ready high and wait for rdata.valid 
        # to go high.
        dram_port_fsm.act(
            "READ_ERR_REC",
            self.state_num_sig.status.eq(0x8),
            dram_port.rdata.ready.eq(1),
            If(dram_port.rdata.valid,
                NextValue(self.error_data, dram_port.rdata.data),
                NextState("READ_ERR_DISPLAY"),
            )
        )

        # The third error-reading state of the "read only" mode.
        # The reading has been finished, and there are errors.
        # Beginning at the first address where errors occured, 
        # do a single read. Set cmd.valid high, and wait for 
        # cmd.ready to go high. The address is set in a comb
        # block at the end of this page.
        dram_port_fsm.act(
            "READ_ERR_DISPLAY",
            self.state_num_sig.status.eq(0x9),
            If(self.start.storage == 0,
                NextState("IDLE"),
            ).Elif((self.error_data == data_sig) | error_ack_sig | (error_display_counter_sig >= error_max_display_counter_sig),
                If((address_sig == self.error_ending_address.status) | 
                  (error_display_counter_sig >= error_max_display_counter_sig),
                    NextState("DISPLAY_DATA_PAUSE"),
                    NextValue(error_display_counter_sig, 0),
                ).Else(
                    # Note: My train of thought here is that the error_found_flag will not go high 
                    # unless there is an error, and error_ack_sig will not go high until software
                    # sees the error_found_flag go high and sets error_ack_sig high. Therefore, 
                    # error_ack_sig will not go high unless an error is found.
                    If(error_ack_sig,
                        NextValue(error_display_counter_sig, error_display_counter_sig + 1),
                    ),
                    NextValue(address_sig, address_sig + 1),
                    NextState("READ_ERR_REQ"),
                )
            ).Else(
                self.error_found_flag.status.eq(1),
            )
        )


        # The final state of the continuous mode. All reading
        # has been finished, including errors, and the User must
        # print out a summary taken from the CSR registers. Pause
        # here and wait until program has finished printing out 
        # everything from the registers.
        dram_port_fsm.act(
            "DISPLAY_DATA_PAUSE",
            self.state_num_sig.status.eq(0xa),
            self.data_pause_display_flag.status.eq(1),
            If(self.start.storage == 0,
                NextState("IDLE"),
            ).Elif(self.data_acknowledge_flag.storage,
                NextState("END_STATE_WAIT_CHOOSER"),
            )
        )


        # Now that all reading has been finished, wait for a set
        # amount of clock cycles (specified by software program
        # controlling the CSR register) and choose what to do next:
        # * If the state machine is disabled (i.e. the start CSR 
        # register is set low), return to the "IDLE" state.
        # * Else if the state machine is in fixed address mode,
        # the 'beg_address' and 'end_address' signals are already
        # set. Depending on if the state machine is in write-once 
        # or write-always mode, go to the "READ_REQUEST" state or 
        # the "WRITE_REQUEST" state, respectively.
        # * Else if the mode is in increment address mode,
        # the 'beg_address' and the 'end_address' signals need
        # to be set to cover the next set of addresses above the 
        # original. Scrubbing will only happen if there were 
        # errors found during the previous read. If there were, the flag
        # error_flag_sig will go high, and the state machine will
        # head to the "WRITE_REQUEST" state to write the pattern 
        # to all the current addresses again without incrementing them.
        dram_port_fsm.act(
            "END_STATE_WAIT_CHOOSER",
            self.state_num_sig.status.eq(0xb),
            # NextValue(delay_tick_ctr_sig, delay_tick_ctr_sig + 1),
            # If(delay_tick_ctr_sig >= delay_max_ticks_sig,
            If(self.start.storage,
                NextValue(self.write_ticks.status, 0),
                NextValue(self.read_ticks.status, 0),
                NextValue(self.total_writes.status, 0),
                NextValue(self.total_reads.status, 0),
                NextValue(burst_cntr_sig, 0),
                NextValue(delay_tick_ctr_sig, 0),
                NextValue(error_beg_addr_chosen, 0),
                NextValue(self.error_counter.status, 0),
                NextValue(chooser_cntr_sig, chooser_cntr_sig + 1),
                If(~self.start.storage,
                    NextState("IDLE"),
                ).Elif(self.address_mode.storage == FIXED_ADDR_MODE,
                    NextValue(address_sig, beg_address_sig),
                    If((self.wr_mode.storage == W_ONCE_R_ALWAYS) | (self.wr_mode.storage == READ_ALWAYS),
                        If(error_flag_sig & self.error_flag_enable.storage,
                            NextValue(error_flag_sig, 0),
                            NextValue(scrubbing_flag_sig, 1),
                            NextState("WRITE_REQUEST"),
                        ).Else(
                            NextState("READ_REQUEST"),
                        ),
                    ).Elif(self.wr_mode.storage == WR_ALWAYS,
                        NextState("WRITE_REQUEST")
                    )
                ).Elif(self.address_mode.storage == INCR_ADDR_MODE,
                    If((self.wr_mode.storage == W_ONCE_R_ALWAYS) | (self.wr_mode.storage == READ_ALWAYS),
                        # If overflow occurs when assigning the new values, 
                        # revert the new addresses back to the original ones.
                        If(error_flag_sig & self.error_flag_enable.storage,
                            NextValue(beg_address_sig, beg_address_sig),
                            NextValue(address_sig, beg_address_sig),
                            NextValue(end_address_sig, end_address_sig),
                            NextValue(error_flag_sig, 0),
                            NextValue(scrubbing_flag_sig, 1),
                            NextState("WRITE_REQUEST"),
                        ).Else(
                            NextValue(beg_address_sig, beg_address_sig + self.length_address.storage + 1),
                            NextValue(address_sig, beg_address_sig + self.length_address.storage + 1),
                            NextValue(end_address_sig, end_address_sig + self.length_address.storage + 1),
                            # If(beg_address_sig >= (end_address_sig + self.length_address.storage + 1),
                            #     NextValue(beg_address_sig, self.base_address.storage),
                            #     NextValue(address_sig, self.base_address.storage),
                            #     NextValue(end_address_sig, self.base_address.storage + self.length_address.storage),
                            # ).Else(
                            #     NextValue(beg_address_sig, beg_address_sig + self.length_address.storage + 1),
                            #     NextValue(address_sig, beg_address_sig + self.length_address.storage + 1),
                            #     NextValue(end_address_sig, end_address_sig + self.length_address.storage + 1),
                            # ),
                            If(read_always_flag_sig,
                                NextState("READ_REQUEST"),   
                            ).Else(
                                NextState("WRITE_REQUEST"),
                            )
                        ),
                    ).Elif(self.wr_mode.storage == WR_ALWAYS,
                        NextValue(beg_address_sig, beg_address_sig + self.length_address.storage + 1),
                        NextValue(address_sig, beg_address_sig + self.length_address.storage + 1),
                        NextValue(end_address_sig, end_address_sig + self.length_address.storage + 1),
                        # If(beg_address_sig >= (end_address_sig + self.length_address.storage + 1),
                        #     NextValue(beg_address_sig, self.base_address.storage),
                        #     NextValue(address_sig, self.base_address.storage),
                        #     NextValue(end_address_sig, self.base_address.storage + self.length_address.storage),
                        # ).Else(
                        #     NextValue(beg_address_sig, beg_address_sig + self.length_address.storage + 1),
                        #     NextValue(address_sig, beg_address_sig + self.length_address.storage + 1),
                        #     NextValue(end_address_sig, end_address_sig + self.length_address.storage + 1),
                        # ),
                        NextState("WRITE_REQUEST"),
                    )
                )   
            ).Elif(~self.start.storage,
                NextState("IDLE"),
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

                # # # For debugging
                # # #######################################################
                # If((burst_cntr_sig <= 0x2) & (dram_port.cmd.we) & (dram_port.wdata.valid) & (scrubbing_flag_sig == 0),
                #     data_sig.eq(0),
                # ).Elif((burst_cntr_sig >= 0x1fffffd) & (dram_port.cmd.we) & (dram_port.wdata.valid) & (scrubbing_flag_sig == 0),
                #     data_sig.eq(0),
		
                # # # If(((self.state_num_sig == 0x04) | (self.state_num_sig == 0x05) | (self.state_num_sig == 0x06)) & (chooser_cntr_sig == 0x03) & (burst_cntr_sig == 0x04),
                # # #     data_sig.eq(0),
                # # # ).Elif(((self.state_num_sig == 0x07) | (self.state_num_sig == 0x08) | (self.state_num_sig == 0x09)) & (chooser_cntr_sig == 0x03) & (address_sig == 0x04),
                # # #     data_sig.eq(0),
                # ).Else(
                #     data_sig.eq(Replicate(self.input_data_pattern.storage, dram_port.data_width//len(self.input_data_pattern.storage))),
                # ),
                # # ########################################################

                # Set the data to write with a replicated CSR register
                data_sig.eq(Replicate(self.input_data_pattern.storage, dram_port.data_width//len(self.input_data_pattern.storage))),
                dram_port.wdata.data.eq(data_sig),

                # NextValue(chooser_cntr_sig, 0),

                # Set the number of cycles to delay based on the number of seconds specified
                delay_max_ticks_sig.eq(self.seconds_delay.storage * sys_clk_freq),

                # Set this signal to the maximum address
                max_address_sig.eq(~0),

            ]

            # Set the data registers to rdata.data
            for i in range(1, 19):
                if (i * DATA_WIDTH_32) <= dram_port.data_width:
                    self.comb += getattr(self, "output_data_pattern{index}".format(index = i)).status.eq(self.error_data[DATA_WIDTH_32 * (i - 1):DATA_WIDTH_32 * (i)])
                    # print("We did output_data_pattern{index} from {range1} to {range2}. YAY!!".format(index = i, range1 = DATA_WIDTH_32 * (i - 1), range2 = DATA_WIDTH_32 * (i)))
                else:
                    self.comb += getattr(self, "output_data_pattern{index}".format(index = i)).status.eq(0)
                    # print("We did not do output_data_pattern{index}. AWW!!".format(index = i))

            


