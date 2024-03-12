import gurobipy as gp
from gurobipy import GRB
import numpy as np
#solver1 using gurobi solver

def solver_MILP(distance_matrix, consumption, tanksize, initial_stock, num_days, maximum_distance, truck_capacity):
    # Number of customers (excluding depot)
    num_customers = len(consumption)

    # Initialize the model
    model = gp.Model("Integrated_Clustering_TSP")

    # Decision Variables
    # Assuming x_ij variables indicate whether route from i to j is taken
    # X i1 i2 k, location 1 location 2 day (path selection)
    X = model.addVars(num_customers, num_customers, num_days, vtype=GRB.BINARY, name="x")
    
    # Y i k, location day (location selection) e is the s th stop on day k
    Y = model.addVars(num_customers, num_customers, num_days, vtype=GRB.BINARY, name="Y")

    # Variables for L planned delivery voloume to customer i on day j of product k
    D = model.addVars(num_customers, num_days, vtype=GRB.CONTINUOUS, name="D")  

    # Objective Function
    # Assuming the objective is to minimize the total distance traveled
    model.setObjective(gp.quicksum(distance_matrix[i][j] * X[i,j,k] for i in range(num_customers) for j in range(num_customers) for k in range(num_days)), GRB.MINIMIZE)
    
    # Constraints
 
 # Assuming hub is at position 0 and is the starting point of the day
    for c in range(num_days):
        model.addConstr(Y[0, 0, c] == 1)
        for e in range(num_customers):
            model.addConstr(X[e, e, c] == 0)

    # Formation of Y (every position can only be assigned at most once)
    for c in range(num_days):
        for e in range(num_customers):
            model.addConstr(Y.sum(e, '*', c) <= 1)
        for s in range(num_customers):
            model.addConstr(Y.sum('*', s, c) <= 1)

    # Assign smaller number of positions first
    for c in range(num_days):
        for s1 in range(1, num_customers):
            for s2 in range(1, num_customers):
                if s1 < s2:
                    model.addConstr(Y.sum('*', s1, c) >= Y.sum('*', s2, c))

    # Constraint: in stock
    for i in range(num_customers):
        for k in range(num_days):
            if consumption[i] != 0:
                model.addConstr(initial_stock[i] - k * consumption[i] + gp.quicksum(D[i, c] for c in range(k + 1)) >= 0.2 * tanksize[i])
                model.addConstr(initial_stock[i] - k * consumption[i] + gp.quicksum(D[i, c] for c in range(k + 1)) <= 0.95 * tanksize[i])

    # Constraint: Bridging Y and D
    for i in range(num_customers):
        for d in range(num_days):
            model.addConstr(D[i, d] <= 4000000 * Y.sum(i, '*', d))

    # Constraint: Bridging Y, X, and Form cycle on each day
    for d in range(num_days):
        for i in range(num_customers):
            model.addConstr(X.sum(i, '*', d) == Y.sum(i, '*', d))
            model.addConstr(X.sum('*', i, d) == Y.sum(i, '*', d))

    # Hamiltonian cycle
    for d in range(num_days):
        for i1 in range(num_customers):
            for i2 in range(num_customers):
                for s in range(num_customers - 1):
                    model.addConstr(Y[i1, s, d] + Y[i2, s + 1, d] - 1 <= X[i1, i2, d])

    # Constraint: Distance
    for d in range(num_days):
        model.addConstr(gp.quicksum(distance_matrix[e1][e2] * X[e1, e2, d] for e1 in range(num_customers) for e2 in range(num_customers)) <= maximum_distance)

    # Simplification constraint
    for d in range(num_days):
        model.addConstr(D[0, d] == 0)

    # Constraint: volume not exceeding truck capacity
    for k in range(num_days):
        model.addConstr(gp.quicksum(D[i, k] for i in range(num_customers)) <= truck_capacity)

    # Constraint: overall stock level shall larger than 0.4 * tanksize in the last day
    for i in range(num_customers):
        c = num_days - 1
        model.addConstr(gp.quicksum(initial_stock[i] - k * consumption[i] + gp.quicksum(D[i, c] for c in range(k + 1)) for i in range(num_customers)) >= 0.3 * np.sum(tanksize))



    # Solve the model
    model.optimize()
    
    # # Extract the solution (if optimal)
    # if model.status == GRB.OPTIMAL:
    #     solution_x = model.getAttr('X', X)
    #     # Additional logic to interpret and use the solution values
    #     print("Optimal solution found")
    #     # Example: print solution values
    #     for i in range(num_customers):
    #         for j in range(num_customers):
    #             if i != j and solution_x[i,j] > 0.5:  # Threshold due to binary nature
    #                 print(f"Route from {i} to {j} is selected.")
                    
    # else:
    #     print("No optimal solution found")

# Example call to the function (placeholders for the actual parameters)
# solver_MILP(distance_matrix, consumption, tanksize, initial_stock, num_days, maximum_distance, truck_capacity)
