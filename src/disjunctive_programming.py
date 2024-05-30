# # * mathematical model
# note uses 1 indexing
# * main LP
# objective min
#   sum i in [n] sum j in [n]
#   (w[i,j] + q[i][j][i][j] * x[i,j])
# s.t.
# non-negative w,
# x \in x_n^=,
# and benders cuts.
# Where  x \in x_n^= means
# x >= 0,
# x <= 1,
# sum i in [n] x[i,j] == 1   for all j in [n],
# sum j in [n] x[i,j] == 1   for all i in [n].

# * subproblem
# objective min
#   sum {k \in [n] k not i} sum {l \in [n] l not j}
#   q[i][j][k][l] * x_1[k,l]
# s.t.
# x_1 >= 0
# x_1[k,l] <= x_hat[k,l]                            for all k \in [n] k not i, l \in [n] l not j,   (constr 1)
# sum {k \in [n] k not i} x_1[k,l] == x_hat[i,j]    for all l \in [n] l not j,                      (constr 2)
# sum {l \in [n] l not j} x_1[k,l] == x_hat[i,j]    for all k \in [n] k not i.                      (constr 3)

# * benders cut
# let lamb, theta, phi, be dual multipliers of constraints 1, 2, 3 respectively
# then add cut
# # w[i,j] >= sum {l in [n] l not j} theta[l] * x[i,j] +
#             sum {k in [n] k not i} phi[k] * x[i,j] +
#             sum {k in [n] k not i} sum {l in [n] l not j} lamb[k,l] * x[k,l]

# * initialization
# upon function call specification add
# kbl cuts, or xy cuts to model.

# # * gurobi code
# note uses zero indexing
# ruff: noqa: E741, SLF001
from settings import DPS
from settings import SettingsDP
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import checker as ch
import kaufman_broeckx as kbl
from time import time


class DisjunctiveProgrammingMethod:
    def __init__(self, q, settings: SettingsDP):
        self.q = q
        self.settings = settings
        self.check_settings()
        self.n = ch.check_q(q=q)

        self.model = gp.Model('Disjunctive-Programming')
        self.add_variables()
        self.add_constraints()
        self.set_objective()
        self.init_with()

        self.set_time_limit()
        self.set_threads()
        self.set_soft_mem_limit()

        self.prepare_callback()
        if self.settings.pre_crush:
            self.model.Params.PreCrush = 1
        
        self.init_time = time()

    def add_variables(self):
        if self.settings.x_is_bin:
            self.x = self.model.addVars(self.n, self.n, vtype=GRB.BINARY, name='x')
        else:
            self.x = self.model.addVars(self.n, self.n, vtype=GRB.CONTINUOUS, name='x', lb=0, ub=1)
        
        self.w = self.model.addVars(self.n, self.n, vtype=GRB.CONTINUOUS, name='w', lb=0)

    def add_constraints(self):
        # * x in X_n^=
        self.model.addConstrs((gp.quicksum(
            self.x[i, j] for i in range(self.n)) == 1 for j in range(self.n)),
            name='constr_sum_1_for_all_j')
        self.model.addConstrs((gp.quicksum(
            self.x[i, j] for j in range(self.n)) == 1 for i in range(self.n)),
            name='constr_sum_1_for_all_i')

    def init_with(self):
        """Initializes with KBL constraints and XY constraints depending on self.settings"""
        if self.settings.init_with_kbl and self.settings.init_with_xy:
            print('!\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('warning initializing with both kbl and xy is discouraged')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n!')

        if self.settings.init_with_kbl:
            M = kbl.compute_M(q=self.q)  # noqa: N806
            # todo make M tighter given w of dp is without q[i][j][i][j] * x[i][j]

            self.model.addConstrs((self.w[i, j] >= gp.quicksum(
                self.q[i][j][k][l] * self.x[k, l] - M[i][j] * (1 - self.x[i, j])
                for k in range(self.n) if k != i for l in range(self.n) if l != j)
                for i in range(self.n) for j in range(self.n)),
                name='constr_on_w_for_all_ij')
            # note in sum k!=i and l!=j since w of dp is without q[i][j][i][j] * x[i][j]
        
        if self.settings.init_with_xy:
            # todo implement
            raise Exception('init_with_xy not implemented yet')

    def set_objective(self):
        self.model.ModelSense = GRB.MINIMIZE
        self.model.setObjective(gp.quicksum(
            (self.w[i, j] + self.q[i][j][i][j] * self.x[i, j])
            for i in range(self.n) for j in range(self.n)))
        
    def benders_callback(self, do_not_use_model, where):  # noqa: ARG002, C901
        """Instead of specifying the model via the function input use self.model"""
        # only run code at specified callback
        self.model._callback_call_count += 1
        
        if where != self.callback_at:
            return
        
        # when self.callback_at is set to GRB.Callback.MIPNODE we check for
        # optimality of node and only continue if optimal
        if self.callback_at == GRB.Callback.MIPNODE:
            status = self.model.cbGet(GRB.Callback.MIPNODE_STATUS)
            if status != GRB.OPTIMAL:
                return
        
        self.model._benders_started_count += 1
        start_timer = time()
        # since benders call is made main problem variables
        # self.x and self.w are the subproblem x_hat and w_hat
        # x_hat = self.x
        # w_hat = self.w
        x_hat_val = gp.tupledict()
        for i in range(self.n):
            for j in range(self.n):
                x_hat_val[i, j] = self.cb_get_solution(self.x[i, j])
        
        w_hat_val = gp.tupledict()
        for i in range(self.n):
            for j in range(self.n):
                w_hat_val[i, j] = self.cb_get_solution(self.w[i, j])

        w_bar_val = gp.tupledict()
        # todo make loop smarter
        cuts_added_this_callback = 0
        for i in range(self.n):
            for j in range(self.n):
                spdp = self.solve_subproblem(x_hat_val=x_hat_val, i=i, j=j)

                w_bar_val[i, j] = spdp.model.ObjVal
                
                if self.settings.debug_print_cut_info and -w_hat_val[i, j] + w_bar_val[i, j] > 0:
                    print(f'------debug_print_cut_info for (i,j): ({i},{j})------')
                    print(f'-w_hat_val[i, j] + w_bar_val[i, j] = {-w_hat_val[i, j] + w_bar_val[i, j]}')
                    print(f'w_hat_val[i, j]: {w_hat_val[i, j]}')
                    print(f'w_bar_val[i, j]: {w_bar_val[i, j]}')
                    print('spdp.x_1:\n', spdp.x_1)
                    print('spdp.x_hat_val:\n', spdp.x_hat_val)
                    print()
                
                if w_hat_val[i, j] < w_bar_val[i, j] - self.settings.minimum_w_difference:
                    # (x_hat, w_hat[i,j]) is not in P_{i,j}
                    # Add Benders cut to the main problem
                    self.add_benders_cut(spdp)
                    cuts_added_this_callback += 1
                    self.model._total_num_cuts += 1
                    self.model._cut_info.append((self.model._total_num_cuts,
                                                 self.model._benders_started_count,
                                                  -w_hat_val[i, j] + w_bar_val[i, j],
                                                  i,
                                                  j))
                else:
                    # (x_hat, w_hat[i,j]) is in P_{i,j}
                    # no cut to be added
                    pass
        
        stop_timer = time()
        time_spent_in_this_cb = stop_timer - start_timer
        self.model._total_time_in_user_cb += time_spent_in_this_cb

        self.model._callback_info.append((
            self.model._benders_started_count,
            self.model._callback_call_count,
            cuts_added_this_callback,
            time() - self.init_time,
            time_spent_in_this_cb))

    def solve_subproblem(self, x_hat_val, i, j):
        spdp = SubProblemDP(x_hat_val=x_hat_val, i=i, j=j, q=self.q, gp_sp_output=False)
        spdp.model.optimize()
        # if spdp.model.Status != 2: # todo add propper error handeling and writing to logfile when subproblem is not solved till optimality
        #     raise Exception('subproblem was not solved till optimality')
        return spdp

    def add_benders_cut(self, spdp):  # noqa: C901
        # let lamb, theta, phi, be dual multipliers of constraints 1, 2, 3 respectively
        theta = {}
        for l in range(self.n):
            if l != spdp.j:
                theta[l] = spdp.model.getConstrByName(f'spdp_constr_2-l={l}').Pi

        phi = {}
        for k in range(self.n):
            if k != spdp.i:
                phi[k] = spdp.model.getConstrByName(f'spdp_constr_3-k={k}').Pi
        
        lamb = gp.tupledict()
        for k in range(self.n):
            if k != spdp.i:
                for l in range(self.n):
                    if l != spdp.j:
                        lamb[k, l] = spdp.model.getConstrByName(f'spdp_constr_1-k={k}_l={l}').Pi

        # adding the cut
        # w[i,j] >= sum {l in [n] l not j} theta[l] * x[i,j] +
        #           sum {k in [n] k not i} phi[k] * x[i,j] +
        #           sum {k in [n] k not i} sum {l in [n] l not j} lamb[k,l] * x[k,l]

        # create short hand for left hand side and right hand side of cut
        lhs = gp.LinExpr(self.w[spdp.i, spdp.j])
        rhs = gp.LinExpr(
            gp.quicksum(theta[l] for l in range(self.n) if l != spdp.j) * self.x[spdp.i, spdp.j] +
            gp.quicksum(phi[k] for k in range(self.n) if k != spdp.i) * self.x[spdp.i, spdp.j] +
            gp.quicksum(lamb[k, l] * self.x[k, l] for k in range(self.n) if k != spdp.i
                        for l in range(self.n) if l != spdp.j))
        
        # add constraint
        if self.settings.debug_add_benders_cuts:
            self.cb_add_bd_constr(lhs >= rhs)
        
        # store constraint for debugging
        if self.settings.debug_benders_cuts:
            self.constraint_storage.append((lhs, rhs))

    def init_constraint_storage(self):
        self.constraint_storage = []

    def write_constraint_storage_to_file(self, debug_lp_path):
        """The file extension determines the file type .lp as suffix is recommend\n
        Note when this function is called model is optimized again,\n
        this will effect results taken from self.model if taken after function call."""
        for constr_tup in self.constraint_storage:
            lhs = constr_tup[0]
            rhs = constr_tup[1]
            self.model.addConstr(lhs >= rhs)
        self.model.optimize()
        self.model.write(debug_lp_path)

    def prepare_callback(self):
        self.set_callback_at()
        self.set_cb_get_solution()
        self.set_cb_add_bd_constr()
        self.set_callback_params()
        self.model._callback_call_count = 0
        self.model._benders_started_count = 0
        self.model._total_time_in_user_cb = 0
        self.model._callback_info = []
        self.model._total_num_cuts = 0
        self.model._cut_info = []

    def set_callback_at(self):
        if self.settings.callback_at == DPS.ALL_MIPSOLS:
            self.callback_at = GRB.Callback.MIPSOL
        elif self.settings.callback_at == DPS.ALL_MIPNODES:
            self.callback_at = GRB.Callback.MIPNODE
        else:
            raise ValueError('Invalid callback_at value')
    
    def set_cb_get_solution(self):
        """"Function is set to either use gurobipy's cbGetSolution or cbGetNodeRel"""
        if self.callback_at == GRB.Callback.MIPSOL:
            self.cb_get_solution = self.model.cbGetSolution
        elif self.callback_at == GRB.Callback.MIPNODE:
            self.cb_get_solution = self.model.cbGetNodeRel
        else:
            raise ValueError('self.callback_at is not set as expected')
    
    def set_cb_add_bd_constr(self):
        if self.settings.bd_constr_type == DPS.LAZY_CONSTR:
            self.cb_add_bd_constr = self.model.cbLazy
        elif self.settings.bd_constr_type == DPS.USER_CUT:
            self.cb_add_bd_constr = self.model.cbCut
        else:
            raise ValueError('bd_constr_type setting is not DPS.LAZY_CONSTR or DPS.USER_CUT')
    
    def set_callback_params(self):
        if self.settings.bd_constr_type == DPS.LAZY_CONSTR:
            self.model.params.LazyConstraints = 1
        elif self.settings.bd_constr_type == DPS.USER_CUT:
            pass
        else:
            raise ValueError('bd_constr_type is not DPS.LAZY_CONSTR or DPS.USER_CUT')
    
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
    
    def check_settings(self):
        """most settings are already checked when called, this function checks remaining settings,
        at this moment the only setting being checked by this function is if the """
        if self.settings.minimum_w_difference < 0:
            raise ValueError(f'Minimum bender decomposition cut violation should not be negative. Hoever, it is set to {self.settings.minimum_w_difference}')


class SubProblemDP:
    # objective min
    #   sum {k \in [n] k not i} sum {l \in [n] l not j}
    #   q[i][j][k][l] * x_1[k,l]
    # s.t.
    # x_1 >= 0
    # x_1[k,l] <= x_hat[k,l]                            for all k \in [n] k not i, l \in [n] l not j,   (constr 1)
    # sum {k \in [n] k not i} x_1[k,l] == x_hat[i,j]    for all l \in [n] l not j,                      (constr 2)
    # sum {l \in [n] l not j} x_1[k,l] == x_hat[i,j]    for all k \in [n] k not i.                      (constr 3)
    def __init__(self, x_hat_val, i: int, j: int, q: np.ndarray, gp_sp_output: bool):  # noqa: PLR0913
        self.x_hat_val = x_hat_val
        self.i = i
        self.j = j
        self.q = q
        self.n = q.shape[0]

        if gp_sp_output:
            self.model = gp.Model('Sub-Problem-DP')
        else:
            sp_env = gp.Env(empty=True)
            sp_env.setParam("OutputFlag", 0)
            sp_env.start()
            self.model = gp.Model('Sub-Problem-DP', env=sp_env)
        
        self.add_variables() # note also adds ub as constraint
        self.add_constraints()
        self.set_objective()

    def add_variables(self):
        self.x_1 = gp.tupledict()
        for k in range(self.n):
            for l in range(self.n):
                if k != self.i and l != self.j:     # avoids creating unnecessary x_1 variables
                    # without ub when creating variable
                    self.x_1[k, l] = self.model.addVar(vtype=GRB.CONTINUOUS,
                        name=f'x_1[{k},{l}]', lb=0) # , ub=self.x_hat_val[k, l])
                    # add upper bond as constraint
                    self.model.addConstr(self.x_1[k, l] <= self.x_hat_val[k, l], name=f'spdp_constr_1-k={k}_l={l}')

    def add_constraints(self):
        # (const 1) is covered by variable bound
        # sum {k \in [n] k not i} x_1[k,l] == x_hat[i,j]    for all l \in [n] l not j,  (constr 2)
        for l in range(self.n):
            if l != self.j:
                self.model.addConstr(gp.quicksum(
            self.x_1[k, l] for k in range(self.n) if k != self.i) == self.x_hat_val[self.i, self.j],
            name=f'spdp_constr_2-l={l}')
                
        # sum {l \in [n] l not j} x_1[k,l] == x_hat[i,j]    for all k \in [n] k not i.  (constr 3)
        for k in range(self.n):
            if k != self.i:
                self.model.addConstr(gp.quicksum(
            self.x_1[k, l] for l in range(self.n) if l != self.j) == self.x_hat_val[self.i, self.j],
            name=f'spdp_constr_3-k={k}')

    def set_objective(self):
        # objective min
        #   sum {k \in [n] k not i} sum {l \in [n] l not j}
        #   q[i][j][k][l] * x_1[k,l]
        self.model.ModelSense = GRB.MINIMIZE
        self.model.setObjective(gp.quicksum(
            self.q[self.i][self.j][k][l] * self.x_1[k, l]
            for k in range(self.n) if k != self.i
            for l in range(self.n) if l != self.j))


def solve_with_dp(q: np.ndarray, settings: SettingsDP) -> gp.Model:
    dpm = DisjunctiveProgrammingMethod(q=q, settings=settings)
    
    if settings.debug_benders_cuts:
        dpm.init_constraint_storage()

    dpm.model.optimize(lambda model, where:
                       dpm.benders_callback(
                           do_not_use_model=model, where=where))
    # note model is passed as do_not_used_model but is not used in the function body

    if settings.debug_benders_cuts:
        dpm.write_constraint_storage_to_file(
            debug_lp_path='results/test_out/temp_debug_file_1.lp')
    
    return dpm.model
