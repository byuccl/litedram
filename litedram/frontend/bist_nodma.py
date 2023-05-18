
from migen import *

from litex.soc.interconnect.csr import *

from litedram.core.crossbar import LiteDRAMNativePort

class Port_Reader(Module, AutoCSR):
    
    def __init__(self, dram_port : LiteDRAMNativePort):


