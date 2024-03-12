import numpy as np
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, PULP_CBC_CMD, CPLEX_CMD, LpStatus,CPLEX_PY,LpMaximize

def solver_Threshold(distance_matrix, consumption, tanksize, initial_stock, num_days, maximum_distance, truck_capacity):
    # threshold set at 30%
    threshold = 0.4
    # Placeholder for the solver_MILP function
    # Implement the logic to solve the MILP problem and return the schedule
    num_customers = len(consumption)

    problem2 = LpProblem("Integrated_Clustering_TSP", LpMinimize)

    # Variables for TSP
    # X i1 i2 k, location 1 location 2 day (path selection)
    X = {(e1, e2, k): LpVariable(name=f"X_{e1}_{e2}_{k}", lowBound=0, cat='Binary') 
        for e1 in range(num_customers) 
        for e2 in range(num_customers) 
        for k in range(num_days) }
    # Y i k, location day (location selection) e is the s th stop on day k
    Y = {(e, s, k): LpVariable(name=f"Y_{e}_{s}_{k}", lowBound=0, cat='Binary') for e in range(num_customers) for s in range (num_customers) for k in range(num_days)}
    
    # Variables for L planned delivery voloume to customer i on day j of product k
    D = {(i, k): LpVariable(name=f"D_{i}_{k}", lowBound=0, upBound = 3000, cat='Continuous') for i in range(num_customers) for k in range(num_days)}
    
    # Variables for L planned delivery voloume to customer i on day j of product k
    B = {(i, k): LpVariable(name=f"B_{i}_{k}", lowBound=0, upBound = 3000, cat='Binary') for i in range(num_customers) for k in range(num_days)}

    # Variables for C compartment i is used for product j on day k
    #C = {(i, j, k): LpVariable(name=f"C_{i}_{j}_{k}", lowBound=0, cat='Binary') for i in range(3) for j in range(4) for k in range(num_days)}

    objective = []
    for c in range(num_days):
        for e1 in range(num_customers):
            for e2 in range(num_customers):
                objective.append(distance_matrix[e1][e2] * X[(e1, e2, c)])
    # for i in range(3): # use as little compartment as possible
    #     for j in range(4):
    #         for k in range(num_days):
    #             objective.append(1 * C[(i, j, k)])
    problem2 += lpSum(objective)

    #===================================================================================================
    # Constraints
    # Constraint 1 depot in each day
    # Constraint 2 no path from i to i
    for c in range(num_days):
        #problem2 += lpSum(X[(0, a, c)] for a in range (num_customers) )== 1 #hub is in each day and is starting point of the day
        problem2 += Y[(0, 0, c)] == 1 #hub is in each day and is starting point of the day
        for e in range(num_customers):  # Start from 1 because entity 0 is the hub
            problem2 += X[(e, e, c)] == 0

    # formation of Y (every position can only be assigned atmost once)
    for c in range(num_days):
        for e in range(num_customers):  # Start from 1 because entity 0 is the hub
            problem2 += lpSum(Y[(e, s, c)] for s in range(0, num_customers)) <= 1

    for c in range(num_days):
        for s in range(num_customers):
            problem2 += lpSum(Y[(e, s, c)] for e in range(1, num_customers)) <= 1

    for c in range(num_days):#assign smaller number of positions first
        for s1 in range(1, num_customers):
            for s2 in range (1, num_customers):
                if s1 < s2:
                    problem2 += lpSum(Y[(e, s1, c)] for e in range(num_customers)) >= lpSum(Y[(e, s2, c)] for e in range(num_customers))

    # Constraint: in stock
    for i in range(num_customers):
        for d in range(num_days):
            if consumption[i] != 0:
                currentstock = initial_stock[i] - d * consumption[i] + lpSum(D[(i, c)] for c in range(d+1))
                problem2 += initial_stock[i] - d * consumption[i] + lpSum(D[(i, c)] for c in range(d+1)) >= 0.2 * tanksize[i]
                problem2 += initial_stock[i] - d * consumption[i] + lpSum(D[(i, c)] for c in range(d+1)) <= 0.95 * tanksize[i]
                problem2 += currentstock + 9999* B[(i,d)] >= threshold * tanksize[i]
                problem2 += currentstock - threshold * tanksize[i] <= 9999999 * (1 - B[(i, d)])

    # Constraint: Bridging D and B
    for i in range(num_customers):
        for d in range(num_days):
            problem2 += D[(i, d)] <= 9999999*B[(i, d)]
            problem2 += D[(i, d)] >= 0.000001*B[(i, d)]
            #problem2 += D[(i, j, d)] >= lpSum(Y[(i, e, d)] for e in range(1, num_customers))

    # Constraint: Bridging Y and D
    for i in range(num_customers):
        for d in range(num_days):
            problem2 += D[(i, d)] <= 4000000*lpSum(Y[(i, e, d)] for e in range(1, num_customers))
            #problem2 += D[(i, j, d)] >= lpSum(Y[(i, e, d)] for e in range(1, num_customers))

    # Constraint: Bridging Y and X and Form cycle on each day
    for d in range(num_days):
        for i in range(num_customers):
            problem2 += lpSum(X[(i, eo, d)] for eo in range(num_customers)) == lpSum(Y[(i, s, d)] for s in range(num_customers))
            problem2 += lpSum(X[(ei, i, d)] for ei in range(num_customers)) == lpSum(Y[(i, s, d)] for s in range(num_customers))
            # hamiltion cycle
    for d in range(num_days):
        for i1 in range(num_customers):
            for i2 in range (num_customers):
                for s in range(num_customers-1):
                    problem2 += Y[(i1, s, d)] + Y[(i2, s+1, d)] -1 <= X[i1, i2, d] 

    # Constraint: Distance
    for d in range(num_days):
        problem2 += lpSum(distance_matrix[e1][e2] * X[(e1, e2, d)] for e1 in range(num_customers) for e2 in range(num_customers) ) <= maximum_distance

    # simplication constriant
    for d in range(num_days):
            problem2 += lpSum(D[(0, d)]) == 0

    # # Constraint: no mixture of products in one compartment
    # for i in range(3):
    #     for c in range(num_days):
    #         problem2 += lpSum(C[(i, k, c)] for k in range(4)) <= 1

    # Constraint: volume not excceeding truck capacity
    for k in range(num_days):
        problem2 += lpSum(D[(i, k)] for i in range(num_customers)) <= truck_capacity


    # Constraint: overall stock level shall larger than 0.4* tanksize in the last day
    for i in range (num_customers):
        c = num_days - 1
        problem2 += lpSum(initial_stock[i] - k * consumption[i] + lpSum(D[(i, c)] for c in range(k+1)) for i in range(num_customers)) >= 0.3 * np.sum(tanksize)

    problem2.solve()

    # Output the status of the solution
    result = (problem2.status, problem2, X, D)

    return result