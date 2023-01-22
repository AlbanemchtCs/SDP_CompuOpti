def print_plannings(N,M,K,T,mapping_names,vacation_mat,qualifications,m):
    for i in range(N):
        print('planning de {} : '.format(mapping_names[i]))
        for t in range(T):
            print('jour {} : '.format(t+1),end=' ')
            if vacation_mat[i,t]==0:
                        print('jour de congé')
            for j in range(M):
                for k in range(K):
                    if m.getVarByName('x[{},{},{},{}]'.format(i,j,k,t)).X == 1 :
                        print('projet {}, compétence {}'.format(j+1,qualifications[k]))
            print('')