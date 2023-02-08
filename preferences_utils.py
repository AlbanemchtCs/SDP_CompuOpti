import gurobipy as gp
from gurobipy import GRB
import numpy as np


def solve_lp_preferences(inacceptable, correct, satisfaisant):
    # Instanciation du modèle
    m = gp.Model("PL inference préférences")

    # Vecteur de variables
    w = m.addVars(3, name="w", lb=0, ub=1)
    l = m.addVar(name="lambda", lb=0.5, ub=1)

    m.update()

    m.addConstrs((gp.quicksum([w[i] for i in range(3) if inacceptable[m][i] >= correct[n][i]]) <= l-1e-6 for m in range(
        len(inacceptable)) for n in range(len(correct))), name="comparaison innacceptable et correct 1")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if correct[n][i] >= inacceptable[m][i]]) >= l for m in range(
        len(inacceptable)) for n in range(len(correct))), name="comparaison innacceptable et correct 2")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if inacceptable[m][i] >= satisfaisant[n][i]]) <= l-1e-6 for m in range(
        len(inacceptable)) for n in range(len(satisfaisant))), name="comparaison innacceptable et satisfaisant 1")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if satisfaisant[n][i] >= inacceptable[m][i]]) >= l for m in range(
        len(inacceptable)) for n in range(len(satisfaisant))), name="comparaison innacceptable et satisfaisant 2")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if correct[m][i] >= satisfaisant[n][i]]) <= l-1e-6 for m in range(
        len(correct)) for n in range(len(satisfaisant))), name="comparaison correct et satisfaisant 1")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if satisfaisant[n][i] >= correct[m][i]]) >= l for m in range(
        len(correct)) for n in range(len(satisfaisant))), name="comparaison correct et satisfaisant 2")
    m.addConstr(gp.quicksum([w[i] for i in range(3)]) == 1)

    obj = l
    m.setObjective(obj, GRB.MINIMIZE)

    # Paramétrage (mode mute)
    m.params.outputflag = 0

    # Résolution du PL
    m.optimize()

    if m.status == GRB.INFEASIBLE:
        raise Exception('no solution')

    return (l.x, [v.X for v in w.values()])


def infer_classes(inacceptable, correct, satisfaisant, remaining_actions, max_majority_threshold=1):
    action_classes = dict()
    for a in remaining_actions:
        action_classes[tuple(a)] = []
        try:
            l, _ = solve_lp_preferences(np.concatenate(
                (inacceptable, a.reshape(1, 3))), correct, satisfaisant)
            if l <= max_majority_threshold:
                action_classes[tuple(a)].append('inacceptable')
        except:
            pass
        try:
            l, _ = solve_lp_preferences(inacceptable, np.concatenate(
                (correct, a.reshape(1, 3))), satisfaisant)
            if l <= max_majority_threshold:
                action_classes[tuple(a)].append('correct')
        except:
            pass
        try:
            l, _ = solve_lp_preferences(inacceptable, correct,
                                        np.concatenate((satisfaisant, a.reshape(1, 3))))
            if l <= max_majority_threshold:
                action_classes[tuple(a)].append('satisfaisant')
        except:
            pass
    return action_classes


def get_nb_breakpoints(all_classified_actions):

    h = np.array([len(np.unique(all_classified_actions[:, i]))
                 for i in range(3)])
    c = np.floor(np.sqrt(h))
    alpha = np.floor(h/c)+1
    return alpha.astype(int)


def get_breakpoints(alpha, all_classified_actions):
    mins = np.array([np.min(all_classified_actions[:, i]) for i in range(3)])
    maxs = np.array([np.max(all_classified_actions[:, i]) for i in range(3)])
    breakpoints = []
    for i in range(3):
        l = []
        for j in range(alpha[i]):
            l.append(mins[i]+(j/(alpha[i]-1))*(maxs[i]-mins[i]))
        breakpoints.append(l)
    return breakpoints


def get_segments(a, breakpoints):
    segments_indices = []
    for i in range(len(breakpoints)):
        for j in range(len(breakpoints[i])):
            if breakpoints[i][j] <= a[i] and a[i] <= breakpoints[i][j+1]:
                indices = [j, j+1]
                break
        segments_indices.append(indices)
    return segments_indices


def interpolate_utility(a, breakpoints, i, w):
    segment_indices = get_segments(a, breakpoints)
    j = segment_indices[i][0]
    u = (gp.quicksum([w[k] for k in range(j)]) + w[j]
         * (a[i]-breakpoints[i][j])/(breakpoints[i][j+1]-breakpoints[i][j]))

    return u


def get_values_gurobi_var(x):
    return [v.X for v in x.values()]


def solve_lp_utility_preferences(inacceptable, correct, satisfaisant, alpha, breakpoints):

    # Instanciation du modèle
    m = gp.Model("PL inference préférences avec fonctions d'utilité")

    sigma_plus_satisfaisant = m.addVars(
        len(satisfaisant), name='sigma+_satisfaisant', vtype=GRB.BINARY)
    sigma_plus_correct = m.addVars(
        len(correct), name='sigma+_correct', vtype=GRB.BINARY)
    sigma_moins_correct = m.addVars(
        len(correct), name='sigma-_correct', vtype=GRB.BINARY)
    sigma_moins_inacceptable = m.addVars(
        len(inacceptable), name='sigma-_inacceptable', vtype=GRB.BINARY)
    s = m.addVar(name='utility_threshold', lb=1e-4, ub=1)
    u = m.addVars(2, name='u', lb=0, ub=1)
    w1 = m.addVars(int(alpha[0]-1), name='w1', lb=1e-4, ub=1)
    w2 = m.addVars(int(alpha[1]-1), name='w2', lb=1e-4, ub=1)
    w3 = m.addVars(int(alpha[2]-1), name='w3', lb=1e-4, ub=1)

    ws = [w1, w2, w3]

    m.update()

    m.addConstrs((gp.quicksum([interpolate_utility(satisfaisant[n], breakpoints, i, ws[i])
                               for i in range(3)]) - u[0] + sigma_plus_satisfaisant[n] >= 1e-4 for n in range(len(satisfaisant))),
                 name="contrainte sur les erreurs de surestimation des alternatives satisfaisantes")
    m.addConstrs((gp.quicksum([interpolate_utility(correct[n], breakpoints, i, ws[i])
                               for i in range(3)]) - u[1] + sigma_plus_correct[n] >= 1e-4 for n in range(len(correct))),
                 name="contrainte sur les erreurs de surestimation des alternatives correctes")
    m.addConstrs((gp.quicksum([interpolate_utility(correct[n], breakpoints, i, ws[i])
                               for i in range(3)]) - u[0] - sigma_moins_correct[n] <= -1e-4 for n in range(len(correct))),
                 name="contrainte sur les erreurs de sous estimation des alternatives correctes")
    m.addConstrs((gp.quicksum([interpolate_utility(inacceptable[n], breakpoints, i, ws[i])
                               for i in range(3)]) - u[1] - sigma_moins_inacceptable[n] <= -1e-4 for n in range(len(inacceptable))),
                 name="contrainte sur les erreurs de sous estimation des alternatives inacceptables")
    m.addConstr(gp.quicksum([ws[i][j] for i in range(3)
                for j in range(alpha[i]-1)]) == 1, name='contrainte de normalisation des poids')
    m.addConstr(u[0]-u[1] >= s,
                name="seuil de discrimination des profils d'utilité")

    obj = gp.quicksum([sigma_plus_satisfaisant[i] for i in range(len(satisfaisant))]) \
        + gp.quicksum([sigma_plus_correct[i] for i in range(len(correct))]) \
        + gp.quicksum([sigma_moins_correct[i] for i in range(len(correct))]) \
        + gp.quicksum([sigma_moins_inacceptable[i]
                      for i in range(len(inacceptable))])
    m.setObjective(obj, GRB.MINIMIZE)

    # Paramétrage (mode mute)
    m.params.outputflag = 0

    # Résolution du PL
    m.optimize()

    if m.status == GRB.INFEASIBLE:
        raise Exception('no solution')

    return {
        "u": get_values_gurobi_var(u),
        "sigma+_satisfaisant": get_values_gurobi_var(sigma_plus_satisfaisant),
        "sigma+_correct": get_values_gurobi_var(sigma_plus_correct),
        "sigma-_correct": get_values_gurobi_var(sigma_moins_correct),
        "sigma-_inacceptable": get_values_gurobi_var(sigma_moins_inacceptable),
        "w1": get_values_gurobi_var(w1),
        "w2": get_values_gurobi_var(w2),
        "w3": get_values_gurobi_var(w3),
        "s": s.x
    }


def utadis_method(inacceptable, correct, satisfaisant, reamining_sols):
    all_classified_actions = np.concatenate(
        (inacceptable, correct, satisfaisant, reamining_sols))
    alpha = get_nb_breakpoints(all_classified_actions)
    breakpoints = get_breakpoints(alpha, all_classified_actions)
    vars = solve_lp_utility_preferences(
        inacceptable, correct, satisfaisant, alpha, breakpoints)
    return vars


def infer_preferences_utadis_method(remaining_sols, breakpoints, ws, u):

    infered_classes = {}
    for a in remaining_sols:
        total_util = np.sum([interpolate_utility(
            a, breakpoints, i, ws[i]).getValue() for i in range(3)])
        if total_util > u[0]:
            infered_classes[tuple(a)] = 'satisfaisant'
        elif total_util > u[1]:
            infered_classes[tuple(a)] = 'correct'
        else:
            infered_classes[tuple(a)] = 'inacceptable'

    return infered_classes
