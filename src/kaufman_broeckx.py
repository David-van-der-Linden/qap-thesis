# this document contains the (pseudo) code for Kaufman-Broeckx Linearization

# * mathematical model
# min   sum_{i,j} w_{i,j}
# s.t.  w_{i,j} >= sum_{k} sum_{l}\
#       q_{i,j,k,l} * x_{k,l} -\
#       M_{i,j} (1 - x_{i,j})   for all i,j
#       w_{i,j} >= 0            for all i,j
#       sum_{i} x_{i,j} == 1    for all j
#       sum_{j} x_{i,j} == 1    for all i
#       x_{i,j} is binary       for all i,j
#
#       where, M_{i,j} = sum_k sum_l q_{i,j,k,l}.

# * pseudo code for gurobi
# ensure you have q in numpy array format
# compute M and make accessible as np array
# create empty model
# add binary variable x[i, j]                                   for i in range(n) for j in range(n)
# add continuos nonnegative variable w[i, j]                    for i in range(n) for j in range(n)
# add constraint sum over i is 0 till n-1 of x[i, j] == 1       for j in range(n)
# add constraint sum over j is 0 till n-1 of x[i, j] == 1       for i in range(n)
# add constraint w[i, j] >= sum over k is 0 till n-1\
#   sum over l is 0 till n-1 q[i][j][k][l] * x[k, l] -\
#   M[i][j] * (1 - x[i, j])                                     for i in range(n) for j in range(n)
# add objective min \
#   sum over i is 0 till n-1 sum over j is 0 till n-1 w[i, j]
# update model
# optimize model
# display/store results

# code
# ruff: noqa: E741
from settings import SettingsKBL
import gurobipy as gp
from gurobipy import GRB
import numpy as np
import checker as ch


class KaufmanBroeckxLinearization:
    def __init__(self, q, settings: SettingsKBL):
        self.q = q
        self.settings = settings
        self.n = ch.check_q(q=q)
        self.M = compute_M(q=q)
        
        self.model = gp.Model('Kaufman-Broeckx')

        self.x = self.model.addVars(self.n, self.n, vtype=GRB.BINARY, name='x')
        self.w = self.model.addVars(self.n, self.n, vtype=GRB.CONTINUOUS, name='w', lb=0)

        self.add_constraints()
        self.set_objective()

        if self.settings.pre_crush:
            self.model.Params.PreCrush = 1
        
        self.set_time_limit()
        self.set_threads()
        self.set_soft_mem_limit()

    def add_constraints(self):
        self.model.addConstrs((gp.quicksum(
            self.x[i, j] for i in range(self.n)) == 1 for j in range(self.n)),
            name='constr_sum_1_for_all_j')
        
        self.model.addConstrs((gp.quicksum(
            self.x[i, j] for j in range(self.n)) == 1 for i in range(self.n)),
            name='constr_sum_1_for_all_i')
        
        self.model.addConstrs((self.w[i, j] >= gp.quicksum(
            self.q[i][j][k][l] * self.x[k, l] - self.M[i][j] * (1 - self.x[i, j])
            for k in range(self.n) for l in range(self.n))
            for i in range(self.n) for j in range(self.n)),
            name='constr_on_w_for_all_ij')
    
    def set_objective(self):
        self.model.ModelSense = GRB.MINIMIZE
        self.model.setObjective(gp.quicksum(
            self.w[i, j] for i in range(self.n) for j in range(self.n)))
    
    def set_time_limit(self):
        if self.settings.time_limit == -1:
            pass
        elif self.settings.time_limit <= 0:
            raise ValueError('time_limit setting is <= 0 and not -1')
        else:
            self.model.Params.TimeLimit = self.settings.time_limit
    
    def set_threads(self):
        if self.settings.threads == -1:
            pass
        elif self.settings.threads <= 0:
            raise ValueError('threads setting is <= 0 and not -1')
        else:
            self.model.Params.Threads = self.settings.threads
    
    def set_soft_mem_limit(self):
        if self.settings.soft_mem_limit == -1:
            pass
        elif self.settings.soft_mem_limit <= 0:
            raise ValueError('soft_mem_limit setting is <= 0 and not -1')
        else:
            self.model.Params.SoftMemLimit = self.settings.soft_mem_limit


def solve_with_kbl(q: np.ndarray, settings: SettingsKBL) -> gp.Model:
    kbl = KaufmanBroeckxLinearization(q=q, settings=settings)
    kbl.model.optimize()
    return kbl.model


def compute_M(q) -> np.ndarray:  # noqa: N802
    M = np.sum(q, axis=(2, 3))  # noqa: N806
    if not isinstance(M, np.ndarray):
        raise Exception('M type is not np.ndarray')
    return M
