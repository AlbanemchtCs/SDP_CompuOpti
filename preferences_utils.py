import gurobipy as gp
from gurobipy import GRB
import numpy as np

def solve_lp_preferences(inacceptable,correct,satisfaisant):
    # Instanciation du modèle
    m = gp.Model("PL inference préférences")

    # Vecteur de variables
    w = m.addVars(3,name="w",lb=0, ub=1)
    l = m.addVar(name="lambda",lb=0.5,ub=1)

    m.update()
    
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if inacceptable[m][i]>=correct[n][i] ]) <= l-1e-6 for m in range(len(inacceptable)) for n in range(len(correct)) ), name="comparaison innacceptable et correct 1")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if correct[n][i]>=inacceptable[m][i] ]) >= l for m in range(len(inacceptable)) for n in range(len(correct)) ), name="comparaison innacceptable et correct 2")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if inacceptable[m][i]>=satisfaisant[n][i] ]) <= l-1e-6 for m in range(len(inacceptable)) for n in range(len(satisfaisant))), name="comparaison innacceptable et satisfaisant 1")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if satisfaisant[n][i]>=inacceptable[m][i] ]) >= l for m in range(len(inacceptable)) for n in range(len(satisfaisant))), name="comparaison innacceptable et satisfaisant 2")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if correct[m][i]>=satisfaisant[n][i] ]) <= l-1e-6 for m in range(len(correct)) for n in range(len(satisfaisant)) ), name="comparaison correct et satisfaisant 1")
    m.addConstrs((gp.quicksum([w[i] for i in range(3) if satisfaisant[n][i]>=correct[m][i] ]) >= l for m in range(len(correct)) for n in range(len(satisfaisant)) ), name="comparaison correct et satisfaisant 2")
    m.addConstr(gp.quicksum([w[i] for i in range(3)])==1)

    obj = l
    m.setObjective(obj, GRB.MINIMIZE)

    # Paramétrage (mode mute)
    m.params.outputflag = 0

    # Résolution du PL
    m.optimize()

    if m.status == GRB.INFEASIBLE :
        raise Exception('no solution')
    
    return (l.x, [v.X for v in w.values()])

def infer_classes(inacceptable, correct, satisfaisant,remaining_actions):
    action_classes = dict()
    for a in remaining_actions :
        action_classes[tuple(a)] = []
        try :
            print(solve_lp_preferences(np.concatenate((inacceptable,a.reshape(1,3))),correct,satisfaisant))
            action_classes[tuple(a)].append('inacceptable')
        except :
            pass
        try :
            print(solve_lp_preferences(inacceptable,np.concatenate((correct,a.reshape(1,3))),satisfaisant))
            action_classes[tuple(a)].append('correct')
        except :
            pass
        try :
            print(solve_lp_preferences(inacceptable,correct,np.concatenate((satisfaisant,a.reshape(1,3)))))
            action_classes[tuple(a)].append('satisfaisant')
        except :
            pass
    return action_classes
        