from get_data_list import get_data_list
import sys
import os
from time import time
import datetime

# make possible to import from src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from settings import DPS, SettingsDP, SettingsKBL, SettingsRLT  # noqa: F401, RUF100
from kaufman_broeckx import solve_with_kbl
from disjunctive_programming import solve_with_dp
import data_handler as dh
from my_secrets import my_path
import writing_tools as wt
import checker as ch


def do_experiment(data_file_name: str):  # noqa: PLR0914
    # * specify output
    output_folder_name = 'results/experiment_1/'
    output_folder_path = my_path + output_folder_name

    # * specify input
    data_path = my_path + 'data/QAPLIB/qapdata/' + data_file_name
    sol_path = get_sol_path(data_file_name)

    # * get instance
    (q, instance_name) = dh.file_to_q(data_path)

    # * specify solving methods
    do_dp = True
    do_kbl = True

    # * specify settings
    settings_dp = SettingsDP(x_is_bin=True,
                             init_with_kbl=True,
                             init_with_xy=False,
                             callback_at=DPS.ALL_MIPSOLS,
                             bd_constr_type=DPS.LAZY_CONSTR,
                             pre_crush=True,
                             minimum_w_difference=0,
                             time_limit=60*60,
                             threads=1,
                             soft_mem_limit=3.6)
    settings_kbl = SettingsKBL(pre_crush=True,
                               time_limit=60*60,
                               threads=1,
                               soft_mem_limit=3.6)

    methods = []
    if do_dp:
        methods.append(("dp", solve_with_dp, settings_dp))
    if do_kbl:
        methods.append(("kbl", solve_with_kbl, settings_kbl))

    # solve and write to txt
    for method_name, solve_with_method, settings in methods:
        print(f'\n-----Now running {method_name}, on {instance_name}-----\n')

        raw_time_start = time()
        
        model = solve_with_method(q=q, settings=settings)
        
        raw_time_stop = time()
        raw_time = raw_time_stop - raw_time_start
        
        all_checks = ch.check_all(model=model,
                                data_file=data_path,
                                sol_file=sol_path)
        
        extra_info = {'raw_time': raw_time}
        
        wt.create_txt(model=model,
                    output_folder_path=output_folder_path,
                    instance_name=instance_name,
                    settings=settings,
                    solving_technique=method_name,
                    all_checks=all_checks,
                    extra_info=extra_info)


def get_sol_path(data_file_name):
    sol_path_candidate = my_path + 'data/QAPLIB/qapsoln/' + data_file_name.split('.')[0] + '.sln'
    sol_path = sol_path_candidate if os.path.exists(sol_path_candidate) else None
    return sol_path


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python main_experiment_1.py <data_index_start> <data_index_stop>")
        sys.exit(1)
    
    data_index_start = int(sys.argv[1])
    data_index_stop = int(sys.argv[2])

    data_list = get_data_list()
    # min 0 max 135,
    # for running on all data use range(0, 136)
    # this experiment was rain in parallel with multiple smaler ranges
    for data_index in range(data_index_start, data_index_stop):
        data_file_name = data_list[data_index]
        try:
            do_experiment(data_file_name=data_file_name)
        except Exception as e:  # noqa: BLE001
            print(f'An error occurred while running on {data_file_name},\nError: {e}')
            with open(my_path + 'results/experiment_1/errors.txt', 'a') as f:
                f.write('\nAn error occurred while running\n')
                current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
                f.write(f'day_time: {current_datetime}\n')
                f.write(f'data_file_name: {data_file_name}\n')
                f.write(f'data_index: {data_index}\n')
                f.write(f'Error: {e}\n')
