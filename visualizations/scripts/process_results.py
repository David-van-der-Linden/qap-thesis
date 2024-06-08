import os
import pandas as pd
import re
import sys

# make possible to import from src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from my_secrets import my_path


def extract_data_from_file(filepath):
    with open(filepath) as file:
        content = file.read()
    
    # for all data that is expected to be in each file
    data = {
        'ModelName': re.search(r'\nmodel.ModelName:\s*(\S+)', content).group(1),
        'instance_name': re.search(r'\ninstance_name:\s*(\S+)', content).group(1),
        'solving_technique': re.search(r'\nsolving_technique:\s*(\S+)', content).group(1),
        'file_created_at': re.search(r'\nfile created at\s*(\S+)', content).group(1),
        'model.Status': int(re.search(r'\nmodel.Status:\s*(\S+)', content).group(1)),
        'NodeCount': float(re.search(r'\nmodel.NodeCount:\s*(\S+)', content).group(1)),
        'IterCount': float(re.search(r'\nmodel.IterCount:\s*(\S+)', content).group(1)),
        'Runtime': float(re.search(r'\nmodel.Runtime:\s*(\S+)', content).group(1)),
        'Work': float(re.search(r'\nmodel.Work:\s*(\S+)', content).group(1)),
        'SolCount': int(re.search(r'\nmodel.SolCount:\s*(\S+)', content).group(1)),
        'ObjVal': float(re.search(r'\nmodel.ObjVal:\s*(\S+)', content).group(1))
    }

    # * grace full pattern extraction,
    # for data that is expected to be missing in some files
    def extract_float(pattern, default=None):
        match = re.search(pattern=pattern,
                          string=content)
        return float(match.group(1)) if match else default
    
    def extract_int(pattern, default=None):
        match = re.search(pattern=pattern,
                          string=content)
        return int(match.group(1)) if match else default
    
    data['ObjBound'] = extract_float(r'\nmodel.ObjBound:\s*(\S+)')
    data['ObjBoundC'] = extract_float(r'\nmodel.ObjBoundC:\s*(\S+)')
    data['raw_time'] = extract_float(r"\nextra_info:.*'raw_time':\s*([^,\}\n\r]+)[\},]")
    data['callback_call_count'] = extract_int(r'\nmodel._callback_call_count:\s*(\S+)')
    data['benders_started_count'] = extract_int(r'\nmodel._benders_started_count:\s*(\S+)')
    data['total_time_in_user_cb'] = extract_float(r'\nmodel._total_time_in_user_cb:\s*(\S+)')
    data['total_num_cuts'] = extract_int(r'\nmodel._total_num_cuts:\s*(\S+)')

    # all checks
    all_checks_match = re.search(r'\nall_checks:\s*\(\((\S+),\s(\S+),\s(\S+)\)', content)
    data['check_1'] = all_checks_match.group(1)
    data['check_2'] = all_checks_match.group(2)
    data['check_3'] = all_checks_match.group(3)

    data['real_obj_val'] = extract_float(r'real_obj_val:\s*([\d\.])')

    return data


def get_df_from_results_dir(directory):
    data_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt') and file.startswith('output'):
                file_path = os.path.join(root, file)
                data = extract_data_from_file(file_path)
                data['output_file_name'] = file
                data_list.append(data)
    
    df = pd.DataFrame(data_list)
    return df


def process_results(directory_path, pkl_name):
    """pkl_name must end in .pkl"""
    df = get_df_from_results_dir(directory_path)
    df.to_pickle(my_path + 'visualizations/data_frames/' + pkl_name)


if __name__ == '__main__':
    # * specify input directory and output file
    do_test_out = False
    do_experiment_1 = True
    do_preliminary_tests = True
    if do_test_out:
        dir_results_test_out = my_path + 'results/test_out'
        process_results(dir_results_test_out, 'processed_test_out.pkl')
    if do_experiment_1:
        dir_results_exp_1 = my_path + 'results/experiment'
        process_results(dir_results_exp_1, 'processed_exp_1.pkl')
    if do_preliminary_tests:
        dir_results_exp_1 = my_path + 'results/preliminary_tests'
        process_results(dir_results_exp_1, 'processed_prelims.pkl')
