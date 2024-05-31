from main_experiment_1 import do_experiment
import datetime
import sys
import os

# make possible to import from src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

from my_secrets import my_path

if __name__ == '__main__':
    variance_test_instances = ['esc32e.dat', 'esc32g.dat', 'scr12.dat', 'chr18b.dat']
    while True:
        for instance in variance_test_instances:
            try:
                do_experiment(instance)
            except Exception as e:  # noqa: BLE001
                print(f'An error occurred while running variance test on {instance},\nError: {e}')
                with open(my_path + 'results/experiment_1/errors.txt', 'a') as f:
                    f.write('\nAn error occurred while running variance test\n')
                    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
                    f.write(f'day_time: {current_datetime}\n')
                    f.write(f'instance: {instance}\n')
                    f.write(f'Error: {e}\n')
