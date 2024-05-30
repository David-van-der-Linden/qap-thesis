import sys
import os

# make possible to import from src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from my_secrets import my_path


def create_data_list(directory, output_file):
    # get files
    files = os.listdir(directory)
    # filter files based on extension
    data_files = [f for f in files if f.endswith('.dat')]
    
    # write to list
    with open(output_file, 'w') as f:
        for file_name in data_files:
            f.write(file_name + '\n')


if __name__ == '__main__':
    directory_path = my_path + 'data/QAPLIB/qapdata'
    output_file_path = my_path + 'experiments/experiment_1/data_list.txt'
    create_data_list(directory_path, output_file_path)
