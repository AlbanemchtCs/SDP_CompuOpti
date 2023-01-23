from gurobipy import *
from utils import (get_parameters, generate_mapping_names, generate_mapping_qualifications,
                   generate_qualifications_matrix, generate_working_days_matrix,
                   generate_working_days_per_qualification_matrix, generate_due_dates_matrix,
                   generate_gains_vect, generate_penalties_vect)
from display_utils import print_plannings
from lp_utils import (generate_variables_and_constraints, set_objective_and_solve,
                      add_epsilon_constraint, solve_epsilon_constraint, run_epsilon_constraint,
                     is_pareto_efficient,filter_pareto_front)

import json
import sys

def save_efficient_solutions(instance_type):
    
    with open('instances/instances_given/{}_instance.json'.format(instance_type)) as f:
        json_instance = json.load(f)
        f.close()
    
    N,M,K,T = get_parameters(json_instance)
    mapping_qualif = generate_mapping_qualifications(json_instance)
    qualifications_mat = generate_qualifications_matrix(json_instance,mapping_qualif,N,K)
    working_days_mat = generate_working_days_matrix(json_instance,N,T)
    wd_per_qual_mat = generate_working_days_per_qualification_matrix(json_instance, mapping_qualif, M, K)
    due_dates_mat = generate_due_dates_matrix(json_instance, M, T)
    gains_vect = generate_gains_vect(json_instance, M)
    penalties_vect = generate_penalties_vect(json_instance, M)
    m = generate_variables_and_constraints(N,M,K,T,qualifications_mat, working_days_mat, wd_per_qual_mat)

    obj1,obj2,obj3 = set_objective_and_solve(m,1,gains_vect,penalties_vect,due_dates_mat,M,T)
    obj1_opti = obj1

    optimal_sol = obj1_opti, 0, 0
    nadir_sol = 0,M,T

    pareto_surface_non_filtered, epsilon_constraints = run_epsilon_constraint(m,optimal_sol,nadir_sol,gains_vect,penalties_vect,due_dates_mat,M,T)
    mask = is_pareto_efficient(pareto_surface_non_filtered)
    pareto_surface = filter_pareto_front(pareto_surface_non_filtered,mask)
    epsilon_cstr = epsilon_constraints[mask]

    with open('pareto_surfaces/{}_instance.json'.format(instance_type),"w") as sol_file:
        json.dump({'pareto_surface':pareto_surface.tolist(), 'constraints':epsilon_cstr.tolist()},sol_file)
        sol_file.close()

if __name__ == "__main__":
    save_efficient_solutions(sys.argv[1])

