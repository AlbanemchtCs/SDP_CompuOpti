import numpy as np

def get_parameters(json_instance):
    N = len(json_instance['staff'])
    M = len(json_instance['jobs'])
    K = len(json_instance['qualifications'])
    T = int(json_instance['horizon'])
    return N,M,K,T

def generate_mapping_names(json_instance):
    """Function which maps staff members names to an integer between 0 and N-1"""
    mapping_names = {}
    for i in range(len(json_instance['staff'])):
        mapping_names[i] = json_instance['staff'][i]['name']
    return mapping_names

def generate_mapping_qualifications(json_instance):
    """Function which maps qualifications to an integer between 0 and K-1"""
    return  {v:k for (k,v) in enumerate(json_instance['qualifications'])}

def generate_qualifications_matrix(json_instance,mapping_qualif,N,K):
    """Generates a N*K matrix in which the coefficient at position (i,j) is 1
    if staff member i is qualified for competence j and 0 otherwise"""
    qualifications_mat = np.zeros((N,K))
    for i in range(N):
        for qual_k in json_instance['staff'][i]['qualifications']:
            qualifications_mat[i,mapping_qualif[qual_k]]=1
    return qualifications_mat

def generate_working_days_matrix(json_instance, N, T):
    """Generates a N*T matrix in which the coefficient at position (i,j) is 1
    if staff member i is working on day j and 0 otherwise"""
    wd_mat = np.ones((N,T))
    for i in range(N):
        for t in json_instance['staff'][i]['vacations']:
            wd_mat[i,t-1]=0
    return wd_mat

def generate_working_days_per_qualification_matrix(json_instance,mapping_qualif,M,K):
    """Generates a M*K matrix in which the coefficient at position (i,j) is M[i,j]
    if project i requires M[i,j] working days of qualification j"""
    wd_per_qual_mat = np.zeros((M,K))
    for j in range(M):
        for qual,wd in json_instance['jobs'][j]['working_days_per_qualification'].items():
            wd_per_qual_mat[j,mapping_qualif[qual]] = wd
    return wd_per_qual_mat

def generate_due_dates_matrix(json_instance, M, T):
    """Generates a M*T matrix in which the coefficient at position (i,j) is 1 
    if day j is posterior to due date of project i, and 0 otherwise"""
    due_dates_mat = np.zeros((M,T))
    for j in range(M):
        for t in range(json_instance['jobs'][j]['due_date']-1,T):
            due_dates_mat[j,t] = 1
    return due_dates_mat

def generate_gains_vect(json_instance, M):
    """Generates a M*1 vector containing the gains for each project"""
    gains_vect = np.zeros((M,))
    for j in range(M):
        gains_vect[j] = json_instance['jobs'][j]['gain']
    return gains_vect

def generate_penalties_vect(json_instance, M):
    penalties_vect = np.zeros((M,))
    for j in range(M):
        penalties_vect[j] = json_instance['jobs'][j]['daily_penalty']
    return penalties_vect