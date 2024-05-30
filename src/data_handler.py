# ruff: noqa: N806
import numpy as np
import re


def generate_random_q(n=8, lb_cost=2, ub_cost=10, seed=1) -> tuple[np.ndarray, str]:
    """returns (q, instance_name)\n
    Generates random cost matrix q.\n
    Notice n=8 or less is quick while n=10 takes long,\n
    while using kbl solve_with_kbl,\n
    when lb_cost=2, ub_cost=10."""
    np.random.seed(seed=seed)
    q = np.random.randint(lb_cost, ub_cost, size=(n, n, n, n))
    instance_name = f'random_q_with_n={n}_lb_cost={lb_cost}_ub_cost={ub_cost}_seed={seed}'
    return (q, instance_name)


def generate_random_AB(n=8, lb_cost_A=2, ub_cost_A=10,  # noqa: N803, N802, PLR0917, PLR0913
                       lb_cost_B=2, ub_cost_B=10, seed=1) -> tuple[np.ndarray, np.ndarray]:  # noqa: N803
    """returns random (A, B)"""
    np.random.seed(seed=seed)
    A = np.random.randint(lb_cost_A, ub_cost_A, size=(n, n, n, n))
    B = np.random.randint(lb_cost_B, ub_cost_B, size=(n, n, n, n))
    return (A, B)


def file_to_q(file_path: str) -> tuple[np.ndarray, str]:
    """Returns (q, instance_name)\n
    Takes file path with format,\n
    \n
    n\n
    \n
    A\n
    \n
    B\n
    \n
    e.g.\n
    \n
    12\n
    \n
       0  180  120    0    0    0    0    0    0  104  112    0\n
     180    0   96 2445   78    0 1395    0  120  135    0    0\n
     120   96    0    0    0  221    0    0  315  390    0    0\n
       0 2445    0    0  108  570  750    0  234    0    0  140\n
       0   78    0  108    0    0  225  135    0  156    0    0\n
       0    0  221  570    0    0  615    0    0    0    0   45\n
       0 1395    0  750  225  615    0 2400    0  187    0    0\n
       0    0    0    0  135    0 2400    0    0    0    0    0\n
       0  120  315  234    0    0    0    0    0    0    0    0\n
     104  135  390    0  156    0  187    0    0    0   36 1200\n
     112    0    0    0    0    0    0    0    0   36    0  225\n
       0    0    0  140    0   45    0    0    0 1200  225    0\n
    \n
    0 1 2 3 1 2 3 4 2 3 4 5\n
    1 0 1 2 2 1 2 3 3 2 3 4\n
    2 1 0 1 3 2 1 2 4 3 2 3\n
    3 2 1 0 4 3 2 1 5 4 3 2\n
    1 2 3 4 0 1 2 3 1 2 3 4\n
    2 1 2 3 1 0 1 2 2 1 2 3\n
    3 2 1 2 2 1 0 1 3 2 1 2\n
    4 3 2 1 3 2 1 0 4 3 2 1\n
    2 3 4 5 1 2 3 4 0 1 2 3\n
    3 2 3 4 2 1 2 3 1 0 1 2\n
    4 3 2 3 3 2 1 2 2 1 0 1\n
    5 4 3 2 4 3 2 1 3 2 1 0\n
    \n
    Outputs matrixes A and B, which are distance and flow matrixes,\n
    and returns q which is a cost matrix.\n
    Matrix q is indexed like so q[loc_1][fac_1][loc_2][fac_2].
    """
    instance_name = re.split('[/\\\\]', file_path)[-1]
    (A, B) = file_to_AB(file_path)
    q = AB_to_q(A, B)
    return (q, instance_name)


def AB_to_q(A: np.ndarray, B: np.ndarray) -> np.ndarray:  # noqa: N802, N803
    """Takes matrixes A and B, which are distance and flow matrixes,\n
    and returns q which is a cost matrix.\n
    Matrix q is indexed like so q[loc_1][fac_1][loc_2][fac_2].
    """
    # compute n
    n = A.shape[0]
    if A.shape != (n, n) or B.shape != (n, n):
        raise Exception('check A.shape == (n, n) and B.shape == (n, n) has failed')

    # compute q
    q = np.zeros(shape=(n, n, n, n))
    for loc_1 in range(n):
        for fac_1 in range(n):
            for loc_2 in range(n):
                for fac_2 in range(n):
                    q[loc_1][fac_1][loc_2][fac_2] = \
                        A[loc_1][loc_2]*B[fac_1][fac_2]
    return q


def file_to_AB(file_path: str) -> tuple[np.ndarray, np.ndarray]:  # noqa: N802
    with open(file_path) as file:
        blocks = file.read().split('\n\n')
    if len(blocks) != 3:
        raise Exception('len(blocks) != 3 in file_to_AB')
    
    file_n = int(re.findall('[0-9]+', blocks[0])[0])
    A = str_to_matrix(blocks[1])
    B = str_to_matrix(blocks[2])

    if file_n != A.shape[0]:
        raise Exception('file_n != A.shape[0] in file_to_AB')
    return (A, B)


def str_to_matrix(string: str) -> np.ndarray:
    arr = np.fromstring(string, dtype=int, sep=' ')
    n = int(np.sqrt(len(arr)))
    matrix = arr.reshape(n, n)
    return matrix
