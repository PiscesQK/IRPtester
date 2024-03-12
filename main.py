# main.py
import tkinter as tk
from customer import Customer, gencustomers, gen_locs, gen_storages, gen_demands, get_storage_level_color
from solver_puLP import solver_MILP
#from solver import solver_MILP
from solver2 import solver_Threshold
import numpy as np

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Customer Storage Display")
        self.geometry("1800x1000")

        #default values
        self.numberofcustomers = 10
        self.mapsize = 800
        self.clustertype = 0#uniform /stationary demand
        self.numofL = 3
        self.numofM = 10
        self.sigma = 1
        self.customers = []  # Initialize an empty list for customers
        self.date = 15  # Initialize the date
        self.current_page = 1  # Track the current page for display in dashboard
        self.setup_ui()


    def setup_ui(self):
        self.setup_controlpanel()
        self.setup_dashboard()
        self.setup_canvas()

    def setup_controlpanel(self):
        # Control Panel setup
        self.control_panel = tk.Frame(self, height=100, width=1800)
        self.control_panel.pack(side=tk.TOP, fill=tk.X)
        self.entries = {}
        parameters = ['numberofcustomers', 'clustertype', 'mapsize', 'numofL', 'numofM', 'sigma']
        for i, parameter in enumerate(parameters):
            tk.Label(self.control_panel, text=parameter).grid(row=0, column=i*2)
            entry = tk.Entry(self.control_panel)
            entry.grid(row=0, column=i*2+1)
            self.entries[parameter] = entry

        #button in the control panel to trigger customer generation all at default values
        generate_scene_btn = tk.Button(self.control_panel, text="Generate Scene", command=self.gen_scene)
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

    def gen_scene(self):
        # Define default values
        defaults = {
            'numberofcustomers': 10,
            'clustertype': 0,
            'mapsize': 800,
            'numofL': 3,
            'numofM': 10,
            'sigma': 1,
        }# Retrieve values from entries, use defaults if empty or invalid
        try:
            numberofcustomers = int(self.entries['numberofcustomers'].get()) if self.entries['numberofcustomers'].get().strip() else defaults['numberofcustomers']
            clustertype = int(self.entries['clustertype'].get()) if self.entries['clustertype'].get().strip() else defaults['clustertype']
            mapsize = int(self.entries['mapsize'].get()) if self.entries['mapsize'].get().strip() else defaults['mapsize']
            numofL = int(self.entries['numofL'].get()) if self.entries['numofL'].get().strip() else defaults['numofL']
            numofM = int(self.entries['numofM'].get()) if self.entries['numofM'].get().strip() else defaults['numofM']
            sigma = int(self.entries['sigma'].get()) if self.entries['sigma'].get().strip() else defaults['sigma']
        except ValueError:
            # If there's still an error after using defaults, this indicates a non-integer input
            print("Please ensure all inputs are valid integers. Using all default values.")
            numberofcustomers, clustertype, mapsize, numofL, numofM, sigma = defaults.values()
        # Generate customers based on the inputs
        self.mapsize = mapsize
        self.numberofcustomers = numberofcustomers
        self.clustertype = clustertype
        self.numofL = numofL
        self.numofM = numofM
        self.sigma = sigma
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
            newdemands = gen_demands(self.customers[i].storagesize, self.sigma)
            self.customers[i].assign_demand(newdemands) 
        self.draw_customers()
        self.update_display_content(self.current_page)
        self.update_and_display_consumption()

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



    def setup_dashboard(self): 
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
        maximum_distance = 2000
        truck_capacity = 2000
        num_days = 14
        result = solver_MILP(self.distance_matrix, self.Consumption, self.Tanksize, self.current_stock_lv, num_days, maximum_distance, truck_capacity)
        result2 = solver_Threshold(self.distance_matrix, self.Consumption, self.Tanksize, self.current_stock_lv, num_days, maximum_distance, truck_capacity)
        print("cycle" + str(result[1].objective.value()))
        print("threshold" + str(result2[1].objective.value()))
        nextdayschedule = result[3]
        #print(nextdayschedule)
        #for i in range(0,self.numberofcustomers):
            #print(f"Customer {i} next day delivery: {nextdayschedule[(i, 0)].value()}")

#####################################################################################################################################################










    def setup_canvas(self):
        # Canvas for drawing customers, initially empty
        self.canvas = tk.Canvas(self, width=1200, height=900, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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



# Example usage
if __name__ == "__main__":
    app = Application()
    app.mainloop()
