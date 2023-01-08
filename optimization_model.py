import pulp

printing_profits = {
    "Offset Printing": 0.3,
    "Digital Printing": 0.5,
    "Screen Printing": 1,
    "Letterpress Printing": 1.5
}

printing_difficulty = {

}


def optimization_algorithm():
    # Define Orders
    orders = Order.query.all()

    # Define the machines
    machines = Machine.query.all()

    # Convert the orders list to the required format
    orders = [
        {
            "name": order.name,
            "type": order.order_type,
            "profit": printing_profits[order.order_type],
            "machine_times": {machine.name: (machine.equipment_capacity / 100) for machine in machines},
            "minimum_demand": order.count
        } for order in orders
    ]

    # Convert the orders list to the required format
    machines = [
        {
            "name": machine.name,
            "production_capacity": machine.equipment_capacity,
            "time": machine.available_hours
        } for machine in machines
    ]

    if not orders or not machines:
        return False, None, None

    # Create a list of order names
    order_names = [order["name"] for order in orders]

    # Create a list of machine names
    machine_names = [machine["name"] for machine in machines]

    # Create a dictionary mapping order names to their profits per unit
    profits = {order["name"]: order["profit"] for order in orders}

    # Create a dictionary mapping machine names to their maximum run times
    machine_times = {machine["name"]: machine["time"] for machine in machines}

    # Create a dictionary mapping order names to dictionaries mapping machine names to the time it takes to produce
    # one unit of the order on that machine
    order_machine_times = {order["name"]: order["machine_times"] for order in orders}

    # Create the optimization model
    model = pulp.LpProblem("Production_Optimization", pulp.LpMaximize)

    # Create a dictionary of pulp variables representing the number of units of each order to produce
    production_vars = pulp.LpVariable.dicts("Production", order_names, lowBound=0, cat="Integer")

    # Create the objective function: maximize the total profit
    model += sum(profits[order] * production_vars[order] for order in order_names)

    # Add constraints for the machine time limits
    for machine in machine_names:
        model += sum(order_machine_times[order][machine] * production_vars[order] for order in order_names) <= \
                 machine_times[machine]

    # Add constraints for the minimum demand for each product
    for i, order in enumerate(order_names):
        model += production_vars[order] >= orders[i]["minimum_demand"]

    # Solve the optimization problem
    status = model.solve()

    if pulp.LpStatus[status] == "Infeasible":
        return False, None, None

    # Create a dictionary containing the machine usage information
    machine_usage = [
        {"machine": machine['name'] + " (" + str(machine['production_capacity']) + ")", "used_hours": sum(
        order_machine_times[order][machine["name"]] * production_vars[order].value() for order in order_names), 'available_hours': machine['time']} for machine in machines
    ]

    #print(machine_usage)

    # # Check if any orders do not meet the minimum demand requirements
    total_profit = 0
    # for i, order in enumerate(order_names):
    #     if production_vars[order].value() < orders[i]["minimum_demand"]:
    #         print(f"Order {order} cannot be fully made, can create - " + str(
    #             int(production_vars[order].value())) + ", requested was - " + str(orders[i]["minimum_demand"]))
    #     else:
    #         print(f"Product {order} will be made successfully!")
    #         total_profit += profits[order] * production_vars[order].value()

    # for variable in model.variables():
    #     print(f"{variable.name}: {variable.value()}")

    # print("Profit from printing if uncompleted orders are made: " + str(model.objective.value()))

    # Print the total profit
    # print("Total profit if only products that meet minimum demand requirements are made: " + str(total_profit))

    # for order in order_names:
    #     print(order + " : " + str(production_vars[order].value()))
    # # Return the optimal production levels
    # print({order: production_vars[order].value() for order in order_names})

    production = {order: production_vars[order].value() for order in order_names}

    # Print the optimal production levels
    # print(production)

    # Extract the order names and production values from the optimization result
    order_names = list(production.keys())
    production_values = list(production.values())

    # Extract the minimum demand values from the orders list
    demand_values = [order['minimum_demand'] for order in orders]

    # Define empty lists for each of the required output values
    order_names = []
    order_types = []
    order_profits = []
    order_produced = []
    order_minimum_demand = []
    order_status = []

    # Iterate through each order and calculate the required output values
    for i, order in enumerate(orders):
        name = order["name"]
        type = order["type"]
        profit = order["profit"] * production_vars[name].value()
        produced = int(production_vars[name].value())
        minimum_demand = order["minimum_demand"]
        if produced < minimum_demand:
            status = "INCOMPLETE"
        elif produced == minimum_demand:
            status = "ENOUGH"
        else:
            status = "! EXTRA !"

        # Append the values to the respective lists
        order_names.append(name)
        order_types.append(type)
        order_profits.append(profit)
        order_produced.append(produced)
        order_minimum_demand.append(minimum_demand)
        order_status.append(status)

    # Zip the lists together to create a list of dictionaries
    order_list = [
        {"order": name, "type": type, "profit": profit, "produced": produced, "minimum_demand": minimum_demand, "status": status} for
        name, type, profit, produced, minimum_demand, status in
        zip(order_names, order_types, order_profits, order_produced, order_minimum_demand, order_status)]

    return True, order_list, machine_usage


from app import Order, Machine
