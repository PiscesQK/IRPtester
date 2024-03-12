'''
# def draw_customers(customers, mapsize):
#     root = tk.Tk()
#     root.title("Customer Storage Display")

#     # Set the canvas size based on the mapsize
#     canvas = tk.Canvas(root, width=mapsize, height=mapsize)
#     canvas.pack()

#     for customer in customers:
#         radius = customer.storagesize / 20  # Scaling down the size for display

#         # Use customer's location for positioning
#         x, y = customer.location
#         x, y = x * (mapsize / 100), y * (mapsize / 100)  # Scale location to fit the canvas size

#         # Draw the full circle representing the customer
#         canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline="black")

#         # Calculate stock ratio and corresponding angle for the arc
#         stock_ratio = customer.stocklv / customer.storagesize
#         stock_angle = stock_ratio * 360

#         # Draw the arc (sector) representing the stock level
#         canvas.create_arc(x - radius, y - radius, x + radius, y + radius,
#                           start=0, extent=stock_angle, fill="green")

#         # Add customer name text
#         canvas.create_text(x, y, text=customer.name)

#     root.mainloop()

# # # # Example usage
# # # customers = gencustomers(10, 1, 100, 3, 4)
# # # draw_customers(customers, 800)  # Specify the mapsize for the canvas



#     def draw_customers(self, customers, mapsize):
#         for customer in customers:
#             radius = customer.storagesize / 20
#             x, y = customer.location
#             x, y = x * (1200 / mapsize), y * (900 / mapsize)
#             self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline="black")
#             stock_ratio = customer.stocklv / customer.storagesize
#             stock_angle = stock_ratio * 360
#             self.canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=0, extent=stock_angle, fill="green")
#             self.canvas.create_text(x, y, text=customer.name)
'''

# To be fixed:
'''
the critical section of updating the customer's stock level and the date
so as to ensure that each customer will receive up to one delivery per day
need to consider the demand is cunsumed first or the delivery is arrived first
'''

# For single product
import tkinter as tk
import random
#import math
import numpy as np

from pulp import LpProblem, LpVariable, LpMinimize, lpSum, PULP_CBC_CMD, CPLEX_CMD, LpStatus,CPLEX_PY,LpMaximize


def solver_MILP(distance_matrix, consumption, tanksize, initial_stock, num_days, maximum_distance, truck_capacity):
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
        for j in range(4):
            for k in range(num_days):
                if consumption[i] != 0:
                    problem2 += initial_stock[i] - k * consumption[i] + lpSum(D[(i, c)] for c in range(k+1)) >= 0.2 * tanksize[i]
                    problem2 += initial_stock[i] - k * consumption[i] + lpSum(D[(i, c)] for c in range(k+1)) <= 0.95 * tanksize[i]

    # Constraint: Bridging Y and D
    for i in range(num_customers):
        for j in range(4):
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


class Customer:
    def __init__(self, id, location, storagesize, stocklv, demand):
        self.id = id
        self.location = location
        self.storagesize = storagesize
        self.stocklv = stocklv
        self.demand = demand
        self.delivery = [0 for _ in range(100)]  # Initialize delivery list with zeros

    def record_delivery(self, day, amount):
        """Record a delivery amount for a specific day."""
        if 0 <= day < len(self.delivery):
            self.delivery[day] += amount

    def refill(self, volume):
        self.stocklv += volume
        # Ensure stock level does not exceed storage size
        if self.stocklv > self.storagesize:
            self.stocklv = self.storagesize
    
    def consume(self, date):
        volume = self.demand[date]
        self.stocklv -= volume
        # Ensure stock level does not go below 0
        if self.stocklv < 0:
            self.stocklv = 0
    
    def assign_demand(self, demand):
        self.demand = demand

    def assign_stocklv(self, stocklv):
        self.stocklv = stocklv
    
    def assign_location(self, location):
        self.location = location

        
def gen_locs(numberofcustomers, mapsize, grid_size=35):
    # Calculate the number of cells in the grid 30 for the size +5 for the space
    y_factor = 1
    cells_per_row = mapsize // grid_size
    cells_per_row -= 1  # Leave some space around the edges
    cells_per_row_y = int(cells_per_row *y_factor)
    cells_per_row_x = int(cells_per_row *4/3)
    # Generate all possible cell positions
    all_positions = [(x, y) for x in range(1,cells_per_row_x) for y in range(1,cells_per_row_y)]
    #print(all_positions)
    # Randomly select positions for the number of customers
    selected_positions = random.sample(all_positions, numberofcustomers)
    
    # Scale positions to actual map size
    locations = [(x * grid_size + grid_size, y * grid_size /y_factor + grid_size) for x, y in selected_positions]

    print(locations)
    return locations

def gen_storages(numberofcustomers, numofL, numofM):
    # Generate storage sizes for each customer
    storages = []
    for _ in range(numofL):
        storages.append(random.randint(1000, 3000))
    for _ in range(numofM):
        storages.append(random.randint(800, 1500))
    for _ in range(numberofcustomers - numofL - numofM):
        storages.append(random.randint(500, 800))
    return storages

def gen_demands(storages, sigmafactor):
    demands = []
    if type(storages) == list:
        for storage in storages:
            mean_demand = random.gauss(0.06, 0.15) * storage
            # Generate a list of 100 demand values, each following the distribution
            customer_demands = [max(0, int(random.gauss(mean_demand, mean_demand * sigmafactor))) for _ in range(100)]
            demands.append(customer_demands)
        return demands
    else:
        mean_demand = random.gauss(0.05, 0.1) * storages
        # Generate a list of 100 demand values, each following the distribution
        customer_demands = [max(0, int(random.gauss(mean_demand, mean_demand * sigmafactor))) for _ in range(100)]
        demands.append(customer_demands)
        return customer_demands

def gencustomers(numberofcustomers, clustertype, mapsize, numofL, numofM):
    locations = gen_locs(numberofcustomers, mapsize)
    storages = gen_storages(numberofcustomers, numofL, numofM)
    sigmafactor = clustertype#!!!!tmp
    demands = gen_demands(storages,sigmafactor)
    customers = []
    for i in range(numberofcustomers):
        # Assuming 'i' as the unique customer ID
        customer = Customer(i, locations[i], storages[i], random.randint(int(storages[i]*0.15), storages[i]), demands[i])
        customers.append(customer)
    return customers

def get_storage_level_color(stock_ratio):
    if stock_ratio >= 0.6:
        return "#05EE00" #light green"
    elif stock_ratio >= 0.3:
        return "#FFEE00" #yellow"
    elif stock_ratio >= 0.15:
        return "#FF9911" #orange
    else:
        return "#FF2A2A" #red

# Window configuration 
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Customer Storage Display")
        self.geometry("1800x1000")
        self.numberofcustomers = 10
        self.mapsize = 800
        self.clustertype = 0#uniform /stationary demand
        self.numofL = 3
        self.numofM = 10
        self.capsize = 1
        self.customers = []  # Initialize an empty list for customers
        self.date = 15  # Initialize the date
        self.current_page = 1  # Track the current page for display in dashboard
        self.setup_ui()


    def setup_ui(self):
        # Control Panel setup
        self.control_panel = tk.Frame(self, height=100, width=1800)
        self.control_panel.pack(side=tk.TOP, fill=tk.X)
        self.entries = {}
        parameters = ['numberofcustomers', 'clustertype', 'mapsize', 'numofL', 'numofM', 'capsize']
        for i, parameter in enumerate(parameters):
            tk.Label(self.control_panel, text=parameter).grid(row=0, column=i*2)
            entry = tk.Entry(self.control_panel)
            entry.grid(row=0, column=i*2+1)
            self.entries[parameter] = entry

        #button in the control panel to trigger customer generation all at default values
        generate_scene_btn = tk.Button(self.control_panel, text="Generate Scene", command=self.init_display)
        generate_scene_btn.grid(row=1, column=8, padx=5)

        # Button to generate new location
        update_loc_btn = tk.Button(self.control_panel, text="New Map", command=self.update_location)
        update_loc_btn.grid(row=1, column=9, padx=5)
        # Button to generate new demand
        update_demand_btn = tk.Button(self.control_panel, text="New Demand", command=self.update_demand)
        update_demand_btn.grid(row=1, column=10, padx=5)

        # Button to update the info
        next_day_btn = tk.Button(self.control_panel, text="Next day", command=self.next_day)
        next_day_btn.grid(row=1, column=11, padx=5)

        # dashboard area (remains unchanged)
        self.dashboard_area = tk.Frame(self, height=900, width=600, bg='#DDDDDD')
        self.dashboard_area.pack_propagate(False)
        self.dashboard_area.pack(side=tk.RIGHT, fill=tk.Y)
        # Setup for message display in dashboard_area (for the delivery input)
        self.message_display = tk.Label(self.dashboard_area, text="", font=("Arial", 12), justify=tk.LEFT)
        self.message_display.pack(pady=10)

        # dashboard area adjustment to include input for deliveries
        self.delivery_input = tk.Entry(self.dashboard_area, width=50)
        self.delivery_input.pack(pady=10)
        tk.Button(self.dashboard_area, text="Delivery Sent", command=self.process_deliveries).pack()

        # Buttons for different pages
        self.page_buttons_frame = tk.Frame(self.dashboard_area)
        self.page_buttons_frame.pack(pady=10)

        self.page1_btn = tk.Button(self.page_buttons_frame, text="Page 1", command=lambda: self.update_display_content(1))
        self.page1_btn.pack(side=tk.LEFT)

        self.page2_btn = tk.Button(self.page_buttons_frame, text="Page 2", command=lambda: self.update_display_content(2))
        self.page2_btn.pack(side=tk.LEFT)

        self.page3_btn = tk.Button(self.page_buttons_frame, text="Page 3", command=lambda: self.update_display_content(3))
        self.page3_btn.pack(side=tk.LEFT)

        # # Initialize the scrollable area below the "Delivery Sent" button for the customer stats
        # self.info_text = tk.Text(self.dashboard_area, height=200, width=600,bg='blue')
        # self.info_text.pack_propagate(False)
        # self.info_scroll = tk.Scrollbar(self.dashboard_area, command=self.info_text.yview)
        # self.info_scroll.pack_propagate(False)
        # self.info_text.configure(yscrollcommand=self.info_scroll.set)
        # self.info_scroll.pack(side=tk.RIGHT)#, fill=tk.Y, expand=False)
        # self.info_text.pack(side=tk.TOP)#, fill=tk.BOTH, expand=False)

        # # Operatetable area setup
        # self.operatetable_area = tk.Frame(self.dashboard_area, height=300, width=600, bg='Red')
        # self.operatetable_area.pack_propagate(False)  # Prevents the widget from changing its size to fit its contents
        # self.operatetable_area.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # # A Label or Text widget inside the operatetable area for displaying text
        # self.operatetable_text = tk.Label(self.operatetable_area, height=15, width=72,bg='grey')  # Adjust the height and width accordingly
        # self.operatetable_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Initialize a new frame for the scrollable text area within the dashboard area
        self.scrollable_text_frame = tk.Frame(self.dashboard_area, height=300, width=600)
        self.scrollable_text_frame.pack_propagate(False)  # This will keep the size of the frame as specified
        self.scrollable_text_frame.pack(side=tk.TOP, fill=tk.X)  # Pack the frame at the top of the dashboard area

        # Initialize the Text widget within the new frame and configure it with a Scrollbar
        self.info_text = tk.Text(self.scrollable_text_frame, bg='#EEEEEE')
        self.info_scroll = tk.Scrollbar(self.scrollable_text_frame, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=self.info_scroll.set)

        # Pack the Text widget and Scrollbar within the new frame
        self.info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Operatetable area setup, now it will be directly below the scrollable text frame
        self.operatetable_area = tk.Frame(self.dashboard_area, height=400, width=600)#, bg='red')
        self.operatetable_area.pack_propagate(False)  # Keep the size of the operatetable area as specified
        self.operatetable_area.pack(side=tk.TOP, fill=tk.X)  # Pack the operatetable area below the scrollable text frame

        # Inside the operatetable area, create a label or another widget as needed
        self.operatetable_text = tk.Label(self.operatetable_area, bg='#AADDDD')
        self.operatetable_text.pack(fill=tk.BOTH, expand=True)

        # Create buttons within the operatetable area
        self.generate_route_btn = tk.Button(self.operatetable_area, text="Generate Route", command=self.generate_route)
        self.generate_route_btn.pack(side=tk.LEFT, padx=10, pady=10)

        self.ask_schedule_btn = tk.Button(self.operatetable_area, text="Ask for Schedule", command=self.ask_for_schedule)
        self.ask_schedule_btn.pack(side=tk.LEFT, padx=10, pady=10)

                



        # Canvas for drawing customers, initially empty
        self.canvas = tk.Canvas(self, width=1200, height=900, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        


    def init_display(self):
        # Define default values
        defaults = {
            'numberofcustomers': 10,
            'clustertype': 0,
            'mapsize': 800,
            'numofL': 3,
            'numofM': 10,
            'capsize': 1,
        }# Retrieve values from entries, use defaults if empty or invalid
        try:
            numberofcustomers = int(self.entries['numberofcustomers'].get()) if self.entries['numberofcustomers'].get().strip() else defaults['numberofcustomers']
            clustertype = int(self.entries['clustertype'].get()) if self.entries['clustertype'].get().strip() else defaults['clustertype']
            mapsize = int(self.entries['mapsize'].get()) if self.entries['mapsize'].get().strip() else defaults['mapsize']
            numofL = int(self.entries['numofL'].get()) if self.entries['numofL'].get().strip() else defaults['numofL']
            numofM = int(self.entries['numofM'].get()) if self.entries['numofM'].get().strip() else defaults['numofM']
            capsize = int(self.entries['capsize'].get()) if self.entries['capsize'].get().strip() else defaults['capsize']
        except ValueError:
            # If there's still an error after using defaults, this indicates a non-integer input
            print("Please ensure all inputs are valid integers. Using all default values.")
            numberofcustomers, clustertype, mapsize, numofL, numofM, capsize = defaults.values()
        # Generate customers based on the inputs
        self.mapsize = mapsize
        self.numberofcustomers = numberofcustomers
        self.clustertype = clustertype
        self.numofL = numofL
        self.numofM = numofM
        self.capsize = capsize
        self.customers = gencustomers(numberofcustomers, clustertype, mapsize, numofL, numofM)
        self.date = 15  # Reset the date
        self.date_text = tk.Label(self.control_panel, text=f"Day {self.date}", font=("Arial", 24), fg="#AA77AA")
        self.date_text.place(x=6, y=40, anchor="w")
        # Clear the existing canvas and redraw
        # self.canvas.delete("all")
        self.draw_customers()
        self.display_customer_info()
        self.update_display_content(self.current_page)
        self.update_and_display_consumption()

    def update_location(self):
        #noc = len(self.customers)
        newlocations = gen_locs(self.numberofcustomers, self.mapsize)
        for i in range(self.numberofcustomers):
            self.customers[i].assign_location(newlocations[i]) 
        self.draw_customers()
        self.display_customer_info()
        self.update_display_content(self.current_page)
    
    def update_demand(self):
        # Update the demand for each customer
        for i in range(self.numberofcustomers):
            newdemands = gen_demands(self.customers[i].storagesize, self.capsize)
            self.customers[i].assign_demand(newdemands) 
        self.draw_customers()
        self.update_display_content(self.current_page)
        self.update_and_display_consumption()
        

    def draw_customers(self):
        self.canvas.delete("all")
        fixed_radius = 15  # Fixed size for all squares
        for customer in self.customers:
            x, y = customer.location
            stock_ratio = customer.stocklv / customer.storagesize
            color = get_storage_level_color(stock_ratio)
            # Draw the circle with fixed size and color based on stock level
            self.canvas.create_rectangle(x - fixed_radius, y - fixed_radius, x + fixed_radius, y + fixed_radius, fill=color, outline="black")
            # Label with customer id
            self.canvas.create_text(x-20, y, text=str(customer.id), font=('','10','bold'),fill='black')
            # Label with storage level (in ratio % )
            self.canvas.create_text(x, y - fixed_radius +7, text=f"{int(stock_ratio*100)}%",font=('','12','bold'))
            # Label with storage size in 2 decimal places
            self.canvas.create_text(x, y + fixed_radius -7 , text=f"{round(customer.storagesize / 1000,1)}k", font=('','12','bold'))   
            #self.canvas.create_text(x, y + fixed_radius + 10, text=f"V: {customer.storagesize / 1000}k")
    
    def display_customer_info(self):
        self.info_text.delete('1.0', tk.END)  # Clear existing info
        for customer in self.customers:
            info = f"ID: {customer.id}, Storage: {customer.storagesize}, Stock Level: {customer.stocklv}\n"
            self.info_text.insert(tk.END, info)


    def update_display_content(self, page):
        self.info_text.delete('1.0', tk.END)  # Clear existing content
        
        if page == 1:
            self.current_page = 1
            # Display current content (as already implemented)
            self.display_customer_info()
        elif page == 2:
            self.current_page = 2
            # Display next 5 days' demand
            for customer in self.customers:
                info = f"ID: {customer.id}, Next 5 days demand: {customer.demand[self.date:self.date+5]}\n"
                self.info_text.insert(tk.END, info)
        elif page == 3:
            self.current_page = 3
            # Display deliveries received in the past 7 days
            for customer in self.customers:
                lst = customer.delivery[max(0, self.date-7):self.date]
                lst = lst[::-1]
                info = f"ID: {customer.id}, Past 7 days deliveries: {lst}\n"
                self.info_text.insert(tk.END, info)

    
    def next_day(self):
        # Redraw customers to reflect any changes made by deliveries
        #self.customers
        for customer in self.customers:
            customer.consume(self.date)
        self.date +=1
        self.draw_customers()
        self.update_display_content(self.current_page)
        print(f"Day {self.date} - Customers updated")
        for customer in self.customers:
            print(f"Customer {customer.id} demand: {customer.demand}")
        self.date_text = tk.Label(self.control_panel, text=f"Day {self.date}", font=("Arial", 24), fg="#AA77AA")
        self.date_text.place(x=6, y=40, anchor="w")
        self.update_and_display_consumption()


    def process_deliveries(self):
        # Parse the input from the delivery_input Entry widget
        delivery_str = self.delivery_input.get()
        print(delivery_str + "!!!")
        try:
            # Manually parsing the input string to create a dictionary
            deliveries_str = delivery_str.split(',')  # Splitting by comma for multiple entries
            deliveries = {int(k.strip()): int(v.strip()) for k, v in (item.split(':') for item in deliveries_str)}
            print(deliveries)

            for customer_id, volume in deliveries.items():
                # Find the customer by id and refill
                for customer in self.customers:
                    if customer.id == customer_id:
                        customer.refill(volume)
                        customer.record_delivery(self.date, volume)
            #self.draw_customers()
        except ValueError as e:  # Catching conversion errors
            print(f"Error processing deliveries: {e}")
        



        # Display the "Request Sent" message with the input message
        self.message_display.config(text=f"Request Sent\n{delivery_str}")


    def update_and_display_consumption(self):
        # Calculate the new average consumption over the first 15 days
        self.Consumption = np.array([np.mean(customer.demand[:15]) for customer in self.customers])

        # Convert the new average consumption to a string and display it
        consumption_str = np.array2string(self.Consumption, precision=2, separator=', ')
        display_text = f"Average Consumption:\n{consumption_str}"
        self.operatetable_text.config(text=display_text)



    def generate_route(self):
        # Assuming Customer locations are stored as (x, y) tuples
        locations = np.array([customer.location for customer in self.customers])

        # Calculate pairwise Euclidean distance matrix
        distance_matrix = np.sqrt(np.sum((locations[:, np.newaxis, :] - locations[np.newaxis, :, :]) ** 2, axis=2))

        # Add the depot's distances to the first row and column
        depot_location = np.array([self.mapsize / 2, self.mapsize / 2])
        depot_distances = np.sqrt(np.sum((locations - depot_location) ** 2, axis=1))
        distance_matrix = np.vstack((depot_distances, distance_matrix))
        depot_column = np.append(0, depot_distances)  # Include zero distance for depot to depot
        distance_matrix = np.column_stack((depot_column, distance_matrix))

        # Save the final distance matrix
        self.distance_matrix = distance_matrix
        print(self.distance_matrix)

        distance_matrix_str = np.array2string(self.distance_matrix, precision=2, separator=', ')
        consumption_str = np.array2string(self.Consumption, precision=2, separator=', ')
        display_text = f"Distance Matrix:\n{distance_matrix_str}\n\nAverage Consumption:\n{consumption_str}"
        self.operatetable_text.config(text=display_text)
        print("11")
        print(distance_matrix_str)
        print("11")

        # Calculate the mean consumption over the first 15 days
        Consumption = np.array([np.mean(customer.demand[self.date:self.date + 15]) for customer in self.customers])

        # Save the mean consumption
        self.Consumption = Consumption

        # Create a NumPy array for Tanksize
        Tanksize = np.array([customer.storagesize for customer in self.customers])

        # Save the tank sizes
        self.Tanksize = Tanksize

        current_stock_lv = np.array([customer.stocklv for customer in self.customers])
        self.current_stock_lv = current_stock_lv

        # Output to the operational table area for now (can be replaced with proper output logic)
        self.operatetable_text.config(text='Route generated and data prepared for optimization.')

    def ask_for_schedule(self):
        print('111')
        print(type(self.distance_matrix))
        #show size
        print(self.distance_matrix.shape)
        print(type(self.Consumption))
        print(self.Consumption.shape)
        print(type(self.Tanksize))
        print(self.Tanksize.shape)
        print(type(self.current_stock_lv))
        print(self.current_stock_lv.shape)

        # Call the MILP solver function with the distance matrix, consumption, and tank sizes
        maximum_distance = 10000
        truck_capacity = 2000
        num_days = 5
        result = solver_MILP(self.distance_matrix, self.Consumption, self.Tanksize, self.current_stock_lv, num_days, maximum_distance, truck_capacity)
        print(result[1].objective.value())
        nextdayschedule = result[3]
        print(nextdayschedule)
        for i in range(0,self.numberofcustomers):
            print(f"Customer {i} next day delivery: {nextdayschedule[(i, 0)].value()}")



# Example usage
app = Application()
app.mainloop()
