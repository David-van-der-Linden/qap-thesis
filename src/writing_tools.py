# ruff: noqa: SLF001
import datetime
import gurobipy as gp
import os
import pandas as pd


def create_txt(model: gp.Model, output_folder_path: str,  # noqa: PLR0913, PLR0917, C901, PLR0915
               instance_name: str, settings, solving_technique='missing',
               all_checks='missing', extra_info='not_provided') -> None:
    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    file_name = f'output_{current_datetime}'
    
    # prevent overwriting existing file
    run = 1
    while os.path.exists(output_folder_path + file_name + f'_r{run}' + '.txt'):
        run += 1
    file_name += f'_r{run}'

    with open(output_folder_path + file_name + '.txt', 'x') as f:
        f.write('Output file:\n')
        f.write(f'model.ModelName: {model.ModelName}\n')
        f.write(f'instance_name: {instance_name}\n')
        f.write(f'solving_technique: {solving_technique}\n')
        f.write(f'file created at {current_datetime}.\n\n')

        f.write(f'all_checks: {all_checks}\n\n')

        if solving_technique == 'dp':  # noqa: SIM102
            if settings.debug_benders_cuts:
                f.write('''WARNING debug_benders_cuts is set to True,
    this means the following results are NOT of the initial run!
    the run was called twice see write_constraint_storage_to_file()
    in disjunctive_programming.py for more info.\n''')
        
        f.write(f'model.Status: {model.Status}\n')
        f.write(f'model.NodeCount: {model.NodeCount}\n')
        f.write(f'model.IterCount: {model.IterCount}\n')
        f.write(f'model.Runtime: {model.Runtime}\n')
        f.write(f'model.Work: {model.Work}\n')
        f.write(f'model.SolCount: {model.SolCount}\n')
        f.write(f'model.ObjVal: {model.ObjVal}\n')
        f.write(f'model.ObjBound: {model.ObjBound}\n')
        f.write(f'model.ObjBoundC: {model.ObjBoundC}\n') # gave error in the past todo reproduce error

        f.write(f'\nextra_info: {extra_info}\n')

        # write settings
        f.write("\nSettings:\n")
        for key, value in settings.__dict__.items():
            f.write(f"{key}: {value}\n")
        if not settings.__dict__:
            f.write("settings is empty\n")

        if solving_technique == 'dp':
            f.write(f'\nmodel._callback_call_count: {model._callback_call_count}\n')
            f.write(f'model._benders_started_count: {model._benders_started_count}\n')
            f.write(f'model._total_time_in_user_cb: {model._total_time_in_user_cb}\n')
            f.write(f'model._total_num_cuts: {model._total_num_cuts}\n')

            # * callback info
            # write to txt
            f.write('model._callback_info:\n')
            f.write('(_benders_started_count, _callback_call_count, cuts_added_this_callback, time_since_init, time_spent_in_this_cb)\n')
            for tup in model._callback_info:
                f.write(f'{tup}\n')
            # pandas
            callback_info_columns =\
                ['_benders_started_count', '_callback_call_count', 'cuts_added_this_callback', 'time_since_init', 'time_spent_in_this_cb']
            df_callback_info = pd.DataFrame(model._callback_info, columns=callback_info_columns)
            df_callback_info.to_csv(output_folder_path + file_name + '_callback_info.csv', index=False, sep=';')
            
            # * cut info
            # write to txt
            f.write('\nmodel._cut_info:\n')
            f.write('(cut_number, _benders_started_count, -w_hat_val[i, j] + w_bar_val[i, j], i, j)\n')
            for tup in model._cut_info:
                f.write(f'{tup}\n')
            # pandas
            cut_info_columns =\
                ['cut_number', '_benders_started_count', 'w_difference', 'i', 'j']
            df_cut_info = pd.DataFrame(model._cut_info, columns=cut_info_columns)
            df_cut_info.to_csv(output_folder_path + file_name + '_cut_info.csv', index=False, sep=';')

        # write solution
        f.write('\nnon zero variables\n')
        f.write('var.VarName, var.X:\n')
        for var in model.getVars():
            if var.X != 0:
                f.write(f'{var.VarName},      {var.X}\n')
