import sys
import os

# make possible to import from src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from my_secrets import my_path


def get_data_list():
    input_file = my_path + 'experiments/experiment_1/data_list.txt'
    with open(input_file) as f:
        data_files = [line.strip() for line in f]
    return data_files
