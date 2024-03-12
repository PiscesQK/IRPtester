import random

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