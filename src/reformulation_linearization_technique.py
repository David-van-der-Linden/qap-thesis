# * objective
# min sum{i,j,k,l \in [n]} q[i][j][k][l] * y[i,j,k,l]
# todo assert that # min sum{i,j,k,l \in [n]} q[i][j][k][l] * y[i,j,k,l] + b[i][j] * x[i,j] is not better
# meaning look into handeling of y[i,j,i,j]
# * vars
# x is bin
# y is bin

# * row and column constraints
# sum_{i} x_{i,j} == 1    for all j
# sum_{j} x_{i,j} == 1    for all i

# * McCormick inequalities, for all i,j,k,l \in [n]
# y[i,j,k,l] <= x[i,j]
# y[i,j,k,l] <= x[k,l]
# y[i,j,k,l] >= x[i,j] + x[k,l] - 1
# y[i,j,k,l] >= 0

# * derivation RLT cuts
# sum i x[i,j] = 1 for all j \in [n],
# =>
# sum i x[i,j] * x[k,l] = x[k,l] for all j, k, l \in [n],
# since x and y are binary and we have the McCormick inequalities we may
# substitute x[i,j] * x[k,l] by y[i,j,k,l]
# similarly one can sum over j, k and l (k and l may be redundant due to symmetry of y)

# * RLT cuts
# sum i y[i,j,k,l] = x[k,l] for all j, k, l \in [n],
# sum j y[i,j,k,l] = x[k,l] for all i, k, l \in [n],
# ruff: noqa: E741
from settings import SettingsRLT
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import checker as ch


class ReformulationLinearizationTechnique:
    def __init__(self, q, settings: SettingsRLT):
        self.q = q
        self.settings = settings
        self.n = ch.check_q(q=q)

        self.model = gp.Model('Reformulation-Linearization-Technique')

        self.add_vars()
        self.add_y_symmetry_constraints()
        self.add_constraints()
        self.set_objective()

        self.set_time_limit()
        self.set_threads()
        self.set_soft_mem_limit()
        
        if self.settings.pre_crush:
            self.model.Params.PreCrush = 1

    def add_vars(self):
        self.x = self.model.addVars(self.n, self.n, vtype=GRB.BINARY, name='x')

        self.y = gp.tupledict()
        for i in range(self.n):
            for j in range(self.n):
                for k in range(self.n):
                    for l in range(self.n):
                        self.y[i, j, k, l] = self.model.addVar(vtype=GRB.BINARY, name=f'y[{i},{j},{k},{l}]')

    def add_y_symmetry_constraints(self):
        for i in range(self.n):
            for j in range(self.n):
                for k in range(self.n):
                    for l in range(self.n):
                        self.model.addConstr(self.y[i, j, k, l] == self.y[k, l, i, j])
                        # note redundant constraints will be removed in preprocessing

    def add_constraints(self):
        self.add_row_and_col_constr()
        self.add_mccormick_ineqs()
        self.add_all_rlt_cuts()

    def add_row_and_col_constr(self):
        # sum_{i} x_{i,j} == 1    for all j
        for j in range(self.n):
            self.model.addConstr(
                gp.quicksum(self.x[i, j]
                            for i in range(self.n))
                == 1)
        
        # sum_{j} x_{i,j} == 1    for all i
        for i in range(self.n):
            self.model.addConstr(
                gp.quicksum(self.x[i, j]
                            for j in range(self.n))
                == 1)
    
    def add_mccormick_ineqs(self):
        for i in range(self.n):
            for j in range(self.n):
                for k in range(self.n):
                    for l in range(self.n):
                        self.add_mccormick_ineq(i, j, k, l)

    def add_mccormick_ineq(self, i, j, k, l):
        # y[i,j,k,l] <= x[i,j]
        self.model.addConstr(self.y[i, j, k, l] <= self.x[i, j])
        # y[i,j,k,l] <= x[k,l]
        self.model.addConstr(self.y[i, j, k, l] <= self.x[k, l])
        # y[i,j,k,l] >= x[i,j] + x[k,l] - 1
        self.model.addConstr(self.y[i, j, k, l] >= self.x[i, j] + self.x[k, l] - 1)
        # y[i,j,k,l] >= 0
        # is implied by y being binary

    def add_all_rlt_cuts(self):
        # sum i x[i,j] * x[k,l] = x[k,l] for all j, k, l \in [n],
        # sum j x[i,j] * x[k,l] = x[k,l] for all i, k, l \in [n],
        # todo consider not adding cuts where k=i or l=j
        for j in range(self.n):
            for k in range(self.n):
                for l in range(self.n):
                    self.add_col_rlt_cut(j, k, l)
        
        for i in range(self.n):
            for k in range(self.n):
                for l in range(self.n):
                    self.add_row_rlt_cut(i, k, l)
    
    def add_col_rlt_cut(self, j, k, l):
        self.model.addConstr(
            gp.quicksum(self.y[i, j, k, l] for i in range(self.n))
            == self.x[k, l]
        )

    def add_row_rlt_cut(self, i, k, l):
        self.model.addConstr(
            gp.quicksum(self.y[i, j, k, l] for j in range(self.n))
            == self.x[k, l]
        )
    
    def set_objective(self):
        # min sum{i,j,k,l \in [n]} q[i][j][k][l] * y[i,j,k,l]
        self.model.ModelSense = GRB.MINIMIZE
        self.model.setObjective(gp.quicksum(
            self.q[i][j][k][l] * self.y[i, j, k, l]
            for i in range(self.n) for j in range(self.n)
            for k in range(self.n) for l in range(self.n)))
        
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


def solve_with_rlt(q: np.ndarray, settings: SettingsRLT) -> gp.Model:
    rlt = ReformulationLinearizationTechnique(q=q, settings=settings)
    
    if settings.write_to_lp:
        rlt.model.write('test_out/temp_rlt_debug_without_rlt_1.lp')
    
    rlt.model.optimize()
    return rlt.model
