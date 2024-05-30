from dataclasses import dataclass
from enum import Enum


class DPS(Enum):
    ALL_MIPSOLS = 'all_mipsols'
    ALL_MIPNODES = 'all_mipnodes'
    USER_CUT = 'user_cut'
    LAZY_CONSTR = 'lazy_constr'


@dataclass
class SettingsDP:
    """### Pre Crush
    If pre_crush is set to True then model.Params.PreCrush == 1, preventing some user cuts from getting ignored.\n
    ### Time Limit
    The time_limit setting is in seconds, setting time limit to -1 disables the time limit.\n
    ### Threads
    Setting threads to -1 lets gurobi pick the amount of threads, (this will be practically as many as possible),\n
    in order to allow for fair comparison between methods it might be best to set threads to 1.\n
    ### Soft Memory Limit
    The soft_mem_limit setting changes the memory limit (in GB meaning 10^9 bytes) of gurobi,\n
    for more on soft mem limit see gurobi documentation.\n
    ### Debug
    Keep all debug settings at there default unless you know what you are doing."""
    x_is_bin: bool = True
    init_with_kbl: bool = True
    init_with_xy: bool = False
    callback_at: str = DPS.ALL_MIPSOLS
    bd_constr_type: str = DPS.LAZY_CONSTR
    pre_crush: bool = True
    minimum_w_difference: float = 0.
    time_limit: float = -1
    threads: int = -1
    soft_mem_limit: int = -1
    debug_benders_cuts: bool = False
    debug_add_benders_cuts: bool = True
    debug_print_cut_info: bool = False


@dataclass
class SettingsKBL:
    """### Pre Crush
    If pre_crush is set to True then model.Params.PreCrush == 1, preventing some user cuts from getting ignored.\n
    ### Time Limit
    The time_limit setting is in seconds, setting time limit to -1 disables the time limit.\n
    ### Threads
    Setting threads to -1 lets gurobi pick the amount of threads, (this will be practically as many as possible),\n
    in order to allow for fair comparison between methods it might be best to set threads to 1.\n
    ### Soft Memory Limit
    The soft_mem_limit setting changes the memory limit (in GB meaning 10^9 bytes) of gurobi,\n
    for more on soft mem limit see gurobi documentation."""
    pre_crush: bool = True
    time_limit: float = -1
    threads: int = -1
    soft_mem_limit: int = -1


@dataclass
class SettingsRLT:
    """### Pre Crush
    If pre_crush is set to True then model.Params.PreCrush == 1, preventing some user cuts from getting ignored.\n
    ### Time Limit
    The time_limit setting is in seconds, setting time limit to -1 disables the time limit.\n
    ### Threads
    Setting threads to -1 lets gurobi pick the amount of threads, (this will be practically as many as possible),\n
    in order to allow for fair comparison between methods it might be best to set threads to 1.\n
    ### Soft Memory Limit
    The soft_mem_limit setting changes the memory limit (in GB meaning 10^9 bytes) of gurobi,\n
    for more on soft mem limit see gurobi documentation."""
    pre_crush: bool = True
    write_to_lp: bool = False
    time_limit: float = -1
    threads: int = -1
    soft_mem_limit: int = -1
