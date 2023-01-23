import gurobipy as gp
from gurobipy import GRB
import numpy as np

def generate_variables_and_constraints(N,M,K,T,qualifications_mat, working_days_mat, wd_per_qual_mat):
    # Instanciation du modèle
    m = gp.Model("PL modelling CompuOpti")

    # Vecteur de variables
    x = m.addVars(N,M,K,T,name="x", vtype=GRB.BINARY)
    r = m.addVars(M,T, name="r", vtype=GRB.BINARY)
    s = m.addVars(N,M, name="s", vtype=GRB.BINARY)
    b = m.addVars(M,T, name="b", vtype=GRB.BINARY)
    y = m.addVar(name="y",vtype=GRB.INTEGER)
    z = m.addVar(name="z",vtype=GRB.INTEGER)

    m.update()

    m.addConstrs((x[i,j,k,t] <= qualifications_mat[i,k] for i in range(N) for j in range(M) for k in range(K) for t in range(T)), name = "qualification du personnel")
    m.addConstrs((gp.quicksum([x[i,j,k,t] for j in range(M) for k in range(K)]) <= 1 for i in range(N) for t in range(T)),name="unicité de l'affectation quotidienne du personnel")
    m.addConstrs((x[i,j,k,t] <= working_days_mat[i,t] for i in range(N) for j in range(M) for k in range(K) for t in range(T)), name = "congés")
    m.addConstrs(( gp.quicksum([x[i,j,k,tau] for i in range(N) for tau in range(t+1)]) >= r[j,t] * wd_per_qual_mat[j,k] for j in range(M) for k in range(K) for t in range(T)),name="couverture des qualifications")
    m.addConstrs(( gp.quicksum([x[i,j,k,tau] for i in range(N) for tau in range(t+1)]) <= wd_per_qual_mat[j,k] for j in range(M) for k in range(K) for t in range(T)),name="unicité de la réalisation d'un projet")
    m.addConstrs((K*T*s[i,j] >= gp.quicksum([x[i,j,k,t] for k in range(K) for t in range(T)]) for i in range(N) for j in range(M) ), name = "affectation à un projet si affection à une compétence de ce projet au moins un jour")
    m.addConstrs((s[i,j] <= gp.quicksum([x[i,j,k,t] for k in range(K) for t in range(T)]) for i in range(N) for j in range(M) ), name = "projet non affecté à  un membre du staff s'il n'a jamais travaillé dessus")
    m.addConstrs((N*K*b[j,t] >= gp.quicksum([x[i,j,k,t] for i in range(N) for k in range(K)]) for j in range(M) for t in range(T)), name = "le projet est commencé si un membre du staff a travaillé sur une compétence de ce projet")
    m.addConstrs((b[j,t] <= gp.quicksum([x[i,j,k,t] for i in range(N) for k in range(K)])+b[j,t-1] for j in range(M) for t in range(1,T)), name = "si le projet n'était pas commencé à t-1 et que personne n'a travaillé dessus à t, il n'est toujours pas commencé")
    m.addConstrs((b[j,0] <= gp.quicksum([x[i,j,k,0] for i in range(N) for k in range(K)]) for j in range(M)), name = "si le projet n'était pas commencé à t-1 et que personne n'a travaillé dessus à t, il n'est toujours pas commencé")
    m.addConstrs((b[j,t] >= r[j,t] for j in range(M) for t in range(T)),name="début d'un projet avant sa fin")
    m.addConstrs((y >= gp.quicksum([s[i,j] for j in range(M)]) for i in range(N)),name="linéarisation de l'objectif 2")
    m.addConstrs((z >= gp.quicksum([b[j,t] - r[j,t] for t in range(T)]) for j in range(M)), name = "linéarisation de l'objectif 3")
    m.addConstrs((r[j,t+1] >= r[j,t] for j in range(M) for t in range(T-1)),name="contrainte interne à la variable r")
    m.addConstrs((b[j,t+1] >= b[j,t] for j in range(M) for t in range(T-1)),name="contrainte interne à la variable b")
    
    return m 

def set_objective_and_solve(m,obj_num,gains_vect,penalties_vect,due_dates_mat,M,T):
    obj1 = -gp.quicksum([m.getVarByName('r[{},{}]'.format(j,T-1))*(gains_vect[j]-gp.quicksum([penalties_vect[j]*(1-m.getVarByName('r[{},{}]'.format(j,t)))*due_dates_mat[j,t] for t in range(T)])) for j in range(M)])
    obj2 = m.getVarByName('y')
    obj3 = m.getVarByName('z')
    if obj_num == 1:
        obj = obj1
    elif obj_num == 2:
        obj=obj2
    elif obj_num == 3:
        obj=obj3
    else :
        raise Exception("""please chose a valid objective number : 
        1 : gain maximisation
        2 : minimisation of maximum number of project affected to one staff member
        3 : minimisation of total duration of projects""")
    m.setObjective(obj, GRB.MINIMIZE)

    m.params.outputflag = 0

    # Résolution du PL
    m.optimize()

    return int(-obj1.getValue()),int(obj2.x),int(obj3.x)
    

def add_epsilon_constraint(m,epsilon):
    m.addConstr(m.getVarByName('y') <= epsilon[1] , name = 'espilon constraint obj 2')
    m.addConstr(m.getVarByName('z') <= epsilon[2] , name = 'espilon constraint obj 3')
    return m

def solve_epsilon_constraint(m,epsilon,gains_vect,penalties_vect,due_dates_mat,M,T):
    m.setParam('TimeLimit',120)
    m = add_epsilon_constraint(m,epsilon)
    obj1 = -gp.quicksum([m.getVarByName('r[{},{}]'.format(j,T-1))*(gains_vect[j]-gp.quicksum([penalties_vect[j]*(1-m.getVarByName('r[{},{}]'.format(j,t)))*due_dates_mat[j,t] for t in range(T)])) for j in range(M)])
    obj2 = m.getVarByName('y')
    obj3 = m.getVarByName('z')
    m.setObjective(obj1 + 1e-6*obj3, GRB.MINIMIZE)

    m.params.outputflag = 0

    # Résolution du PL
    m.optimize()

    if m.status == GRB.INFEASIBLE:
        raise Exception('no solution')

    return [int(obj1.getValue()),int(obj2.x),int(obj3.x)]

def run_epsilon_constraint(m,optimal_sol,nadir_sol,gains_vect,penalties_vect,due_dates_mat,M,T):   
    pareto_surface = []
    epsilon_constraints = []
    epsilon = np.array(nadir_sol)
    sol_2 = np.inf
    feasible=True
    while sol_2 > optimal_sol[1] and feasible :
        sol_3 = np.inf
        while sol_3 > optimal_sol[2] and feasible:
            print('step with eps2 = {} and eps3 = {}'.format(epsilon[1],epsilon[2]))
            try:
                base_model = m.copy()
                solution = solve_epsilon_constraint(base_model,epsilon,gains_vect,penalties_vect,due_dates_mat,M,T)
            except:
                feasible = False
                break
            pareto_surface.append(solution)
            epsilon_constraints.append(epsilon.copy())
            print('solution found : ', solution)
            sol_2,sol_3 = solution[1],solution[2]
            epsilon[2] = sol_3 - 1
        epsilon[1] -= 1
        epsilon[2] = nadir_sol[2]
        if not(feasible):
            try :
                base_model = m.copy()
                solve_epsilon_constraint(base_model,epsilon,gains_vect,penalties_vect,due_dates_mat,M,T)
                feasible = True
            except :
                break
    return np.array(pareto_surface),np.array(epsilon_constraints)

def is_pareto_efficient(pareto_front):
    is_efficient = np.ones(pareto_front.shape[0], dtype = bool)
    for i, c in enumerate(pareto_front):
        if is_efficient[i]:
            is_efficient[is_efficient] = np.any(pareto_front[is_efficient]<c, axis=1)  
            is_efficient[i] = True  
    return is_efficient

def filter_pareto_front(pareto_front,mask):
    return np.abs(pareto_front[mask])



