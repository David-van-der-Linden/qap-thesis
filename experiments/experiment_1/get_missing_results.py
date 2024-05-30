from get_data_list import get_data_list
import os
import sys

# make possible to import from src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from my_secrets import my_path


def get_instances_ran():
    """outputs instances_ran_w_dp, instances_ran_w_kbl"""
    instances_ran_w_dp = []
    instances_ran_w_kbl = []
    for file_name in os.listdir(my_path + 'results/experiment_1'):
        if not file_name.endswith('.txt'):
            continue
        
        if file_name == 'errors.txt':
            continue
        
        if file_name[0:6] != 'output':
            raise Exception(f'unexpected file in results/experiment_1, file_name: {file_name}')

        with open(my_path + 'results/experiment_1/' + file_name) as f:
            lines = f.read().split('\n')
        
        split_2 = lines[2].split()
        assert split_2[0] == 'instance_name:'
        instance_name = split_2[1]

        split_3 = lines[3].split()
        assert split_3[0] == 'solving_technique:'
        solving_technique = split_3[1]

        if solving_technique == 'dp':
            instances_ran_w_dp.append(instance_name)
        elif solving_technique == 'kbl':
            instances_ran_w_kbl.append(instance_name)
        else:
            raise Exception('unexpected solving_technique')
    return instances_ran_w_dp, instances_ran_w_kbl


def get_missing(data_list, instances_ran_w_dp, instances_ran_w_kbl):
    """returns missing_dp, missing_kbl"""
    missing_dp = []
    missing_kbl = []
    for instance in data_list:
        if instance not in instances_ran_w_dp:
            missing_dp.append(instance)
        if instance not in instances_ran_w_kbl:
            missing_kbl.append(instance)
    return missing_dp, missing_kbl


def create_missing_txt(output_file, missing):
    with open(output_file, 'w') as f:
        for file_name in missing:
            f.write(file_name + '\n')


if __name__ == '__main__':
    data_list = get_data_list()
    instances_ran_w_dp, instances_ran_w_kbl = get_instances_ran()
    missing_dp, missing_kbl = get_missing(data_list=data_list,
                                          instances_ran_w_dp=instances_ran_w_dp,
                                          instances_ran_w_kbl=instances_ran_w_kbl)
    
    output_file_dp = my_path + 'experiments/experiment_1/missing_dp.txt'
    output_file_kbl = my_path + 'experiments/experiment_1/missing_kbl.txt'
    create_missing_txt(output_file_dp, missing_dp)
    create_missing_txt(output_file_kbl, missing_kbl)
