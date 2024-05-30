import data_handler as dh
import re
import gurobipy as gp
from gurobipy import GRB
from itertools import product
import numpy as np


def check_all(model: gp.Model, data_file: str, sol_file: str): # tuple[tuple[bool, bool, bool], tuple[str, str, str]]: # todo improve sol file not provided handeling
    """Given __ will check,\n
    if sol is consistent with data,\n
    if model attains objective it claims, and \n
    if sol file optimum is equal to model optimum.\n
    Returns ((sol_consist_w_data, model_consist_w_data, obj_val_match), ('', model_warnings, '')"""
    
    if sol_file:
        (_, sol_obj_val, _) = sol_file_to_info(sol_file) # todo (low priority) optimize sol_file_to_info() is also called inside check_sol_file()
        sol_consist_w_data = check_sol_file(data_file, sol_file)
    else:
        sol_consist_w_data = 'sol_file_not_provided'
    model_consist_w_data, model_warnings = check_model(model, data_file)
    
    obj_val_match = sol_obj_val == model.ObjVal if sol_file else 'sol_file_not_provided'
    
    return ((sol_consist_w_data, model_consist_w_data, obj_val_match), ('', model_warnings, ''))


def check_sol_file(data_file, sol_file) -> bool:
    """Given data file and solution file,\n
    it will check if the permutation yields the claimed objective.\n
    Also asserts dimensions of data and solution file match"""

    (A, B) = dh.file_to_AB(data_file)  # noqa: N806
    data_n = A.shape[0]
    (sol_n, claimed_obj_val, permutation) = sol_file_to_info(sol_file)
    if data_n != sol_n:
        raise Exception('Dimensions of solution and data file do not match')

    obj_val = 0
    for i, pi in enumerate(permutation):
        for j, pj in enumerate(permutation):
            obj_val += A[i][j] *B[pi-1][pj-1]

    return claimed_obj_val == obj_val


def sol_file_to_info(sol_file) -> tuple[int, int, list[int]]:
    """Returns (n, obj_val, permutation)"""
    with open(sol_file) as file:
        all_ints = [int(num) for num in re.findall('[0-9]+', file.read())]
    n = all_ints[0]
    obj_val = all_ints[1]
    permutation = all_ints[2:]
    if len(permutation) != n:
        raise Exception('len(permutation) != n')
    return (n, obj_val, permutation)


def check_model(model: gp.Model, data_file: str) -> tuple[bool, str]:
    """Given a solved model,\n
    this function will check if model attains objective it claims"""
    (A, B) = dh.file_to_AB(data_file)  # noqa: N806
    n = A.shape[0]
    warnings_to_return = ''
    
    # * define x and check its type
    # we want: x = model.getVarByName('x'), but that doesn't work
    # This does work: something = model.getVarByName('x[0,0]')
    x = gp.tupledict()
    for i in range(n):
        for j in range(n):
            x[i, j] = model.getVarByName(f'x[{i},{j}]')
            if x[i, j].getAttr(GRB.Attr.VType) != 'B':
                # raise Exception(f'Variable x[{i},{j}] is not Binary type')
                # print(f'waring Variable x[{i},{j}] is not Binary type not binary')
                warnings_to_return += f'waring Variable x[{i},{j}] is not Binary type not binary\n'

    # * compute real_obj_val
    real_obj_val = comp_obj_val_naive(x, A, B)

    if model.ObjVal == real_obj_val:
        return (True, warnings_to_return)
    else:
        return (False, f'model.ObjVal: {model.ObjVal}, real_obj_val: {real_obj_val}\n' + warnings_to_return)


def comp_obj_val_naive(x, A, B):  # noqa: N803
    """Computes the real objective value given x A and B using the naive method\n
    naive method has\n
    pros: understandable, quick runtime\n
    cons: it has many layers of indentation, slow to read\n
    """
    n = A.shape[0]
    real_obj_val = 0
    for loc_1 in range(n):  # noqa: PLR1702
        for fac_1 in range(n):
            if x[loc_1, fac_1].X == 1:
                for loc_2 in range(n):
                    for fac_2 in range(n):
                        if x[loc_2, fac_2].X == 1:
                            real_obj_val += A[loc_1][loc_2] * B[fac_1][fac_2]
    return real_obj_val


def comp_obj_val_adjorn(x, A, B):  # noqa: N803
    """Computes the real objective value given x A and B using Adjorn's method\n
    Adjorn's method has\n
    pro: less indentation more readable\n
    con: sower due to unnecessary iterations over loc_2 fac_2 when x[loc_1, fac_1].X != 1"""
    n = A.shape[0]
    r = range(n)
    adjorns_iter = product(r, r, r, r)
    real_obj_val = 0
    for loc_1, fac_1, loc_2, fac_2 in adjorns_iter:
        if x[loc_1, fac_1].X == 1 and x[loc_2, fac_2].X == 1:
            real_obj_val += A[loc_1][loc_2] * B[fac_1][fac_2]
    return real_obj_val


def comp_obj_val_mei(x, A, B):  # noqa: N803
    """Computes the real objective value given x A and B using Mei's method\n
    Mei's method has\n
    pro: less indentation than naive method, quick runtime\n
    con: more complex
    """
    # contains bug # todo fix
    n = A.shape[0]
    r = range(n)
    meis_iter_1 = product(r, r)
    meis_iter_2 = product(r, r)
    real_obj_val = 0
    for loc_1, fac_1 in meis_iter_1:
        if x[loc_1, fac_1].X == 1:
            for loc_2, fac_2 in meis_iter_2:
                if x[loc_2, fac_2].X == 1:
                    real_obj_val += A[loc_1][loc_2] * B[fac_1][fac_2]
    
    return real_obj_val


def check_q(q) -> int:
    """checks if q is np.ndarray,\n
    checks if q.shape == (n, n, n, n)\n
    returns n"""
    if not isinstance(q, np.ndarray):
        raise Exception('q is not type np.ndarray')
    n = q.shape[0]
    if q.shape != (n, n, n, n):
        raise Exception('q.shape != (n, n, n, n)')

    if not np.all(q >= 0):
        raise Exception('q has a negative entry')
    return n
