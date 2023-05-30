import pandas as pd
import random

# Variables
initial_amount = 100.0  # initial amount to start with
transaction_percentage = 5.0 / 100  # percentage of amount used per transaction
profit_percentage = 3.0 / 100  # average profit percentage per transaction
fee_percentage = 0.0750 / 100  # fee per transaction
transactions_per_day = 20  # number of transactions per day
goal_amount = 10000.0  # goal amount to reach
days_in_year = 365  # number of days in a year
success_rate = 82.0 / 100  # success rate per transaction
loss_percentage = 1.5 / 100  # loss percentage for unsuccessful transactions


# Function to calculate the transaction
def calculate_transaction(amount):
    amount_used = amount * transaction_percentage
    fee = amount_used * fee_percentage

    # Randomly determine if the transaction is successful based on the success rate
    if random.random() < success_rate:
        profit = (amount_used * profit_percentage) - fee
    else:
        profit = -amount_used * loss_percentage

    final_amount = amount + profit
    return final_amount


# Prepare data for the dataframe
data = {"Transaction #": [], "Amount": []}

# Simulate the growth over 100 transactions
current_amount = initial_amount
for i in range(1, 101):
    current_amount = calculate_transaction(current_amount)
    data["Transaction #"].append(i)
    data["Amount"].append(current_amount)

# Create the dataframe and print it
df = pd.DataFrame(data)
print(df)

# Calculate the number of transactions to reach the goal
count = 0
current_amount = initial_amount  # reset the current amount
while current_amount < goal_amount:
    current_amount = calculate_transaction(current_amount)
    count += 1

days_to_reach_goal = count / transactions_per_day

# Calculate the estimated amount after 6 months
transactions_in_half_year = transactions_per_day * (days_in_year // 2)
current_amount = initial_amount  # reset the current amount
for _ in range(transactions_in_half_year):
    current_amount = calculate_transaction(current_amount)
estimated_amount_6_months = current_amount

# Calculate the estimated amount after 12 months
transactions_in_year = transactions_per_day * days_in_year
current_amount = initial_amount  # reset the current amount
for _ in range(transactions_in_year):
    current_amount = calculate_transaction(current_amount)
estimated_amount_12_months = current_amount

print(f"\nIt will take {count} transactions to reach ${goal_amount}.")
print(f"Estimated number of days to reach the goal: {days_to_reach_goal}")
print(f"Estimated amount after 6 months: ${estimated_amount_6_months}")
print(f"Estimated amount after 12 months: ${estimated_amount_12_months}")
