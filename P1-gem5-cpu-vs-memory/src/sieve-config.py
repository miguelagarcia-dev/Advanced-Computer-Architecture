import argparse
import os

import m5
from m5.objects import *

# Assignment names -> current gem5 class names
MEM_TYPES = {
    "DDR3_1600_x64": DDR3_1600_8x8,
    "DDR3_2133_x64": DDR3_2133_8x8,
    "LPDDR2_S4_1066_x32": LPDDR2_S4_1066_1x32,
}

parser = argparse.ArgumentParser(description="Run the sieve in gem5")
parser.add_argument("--cpu", choices=["timing", "minor"], default="timing")
parser.add_argument("--clock", default="1GHz")
parser.add_argument("--mem", choices=list(MEM_TYPES), default="DDR3_1600_x64")
parser.add_argument("--n", default="1000000", help="sieve upper limit")
parser.add_argument(
    "--binary",
    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "sieve"),
)
args = parser.parse_args()


# ----- Caches (from the Learning gem5 cache tutorial) -----
class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20


class L1ICache(L1Cache):
    size = "16kB"


class L1DCache(L1Cache):
    size = "64kB"


class L2Cache(Cache):
    size = "256kB"
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12


# ----- System -----
system = System()
system.clk_domain = SrcClockDomain(clock=args.clock, voltage_domain=VoltageDomain())
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MB")]

# ARM CPUs because the VM (Apple Silicon) compiles ARM binaries
system.cpu = ArmTimingSimpleCPU() if args.cpu == "timing" else ArmMinorCPU()

# L1 caches
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()
system.cpu.icache_port = system.cpu.icache.cpu_side
system.cpu.dcache_port = system.cpu.dcache.cpu_side

# L2 bus and cache
system.l2bus = L2XBar()
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports
system.l2cache = L2Cache()
system.l2cache.cpu_side = system.l2bus.mem_side_ports

# Memory bus
system.membus = SystemXBar()
system.l2cache.mem_side = system.membus.cpu_side_ports
system.cpu.createInterruptController()
system.system_port = system.membus.cpu_side_ports

# Memory controller
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = MEM_TYPES[args.mem]()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# ----- Workload -----
system.workload = SEWorkload.init_compatible(args.binary)
process = Process()
process.cmd = [args.binary, args.n]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"CPU={args.cpu} clock={args.clock} mem={args.mem} n={args.n}")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")