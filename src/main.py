from settings import DPS, SettingsDP, SettingsKBL, SettingsRLT  # noqa: F401, RUF100
from reformulation_linearization_technique import solve_with_rlt
from kaufman_broeckx import solve_with_kbl
from disjunctive_programming import solve_with_dp
import data_handler as dh
from my_secrets import my_path
import writing_tools as wt
import checker as ch
from time import time

if __name__ == "__main__":
    # * specify output
    output_folder_name = 'results/test_out/'
    output_folder_path = my_path + output_folder_name

    # * specify input
    sol_path = None
    # data_path = my_path + 'data/QAPLIB/qapdata/tai10a.dat'
    # data_path = my_path + 'data/QAPLIB/qapdata/chr18b.dat'
    # sol_path = my_path + 'data/QAPLIB/qapsoln/chr18b.sln'
    data_path = my_path + 'data/test_inputs/3x3_test.dat'

    # * get instance
    # (q, instance_name) = dh.generate_random_q()
    (q, instance_name) = dh.file_to_q(data_path)

    # * specify solving methods
    do_rlt = False
    do_dp = True
    do_kbl = True

    # * specify settings
    settings_rlt = SettingsRLT(threads=1)
    settings_dp = SettingsDP(threads=1)
    settings_kbl = SettingsKBL(threads=1)

    methods = []
    if do_rlt:
        methods.append(("rlt", solve_with_rlt, settings_rlt))
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
