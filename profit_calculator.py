import pandas as pd
import random

# Variables
initial_amount = 300.0  # initial amount to start with
transaction_percentage = 5.0 / 100  # percentage of amount used per transaction
profit_percentage = 5.0 / 100  # average profit percentage per transaction
fee_percentage = 0.0750 / 100  # fee per transaction
transactions_per_day = 20  # number of transactions per day
goal_amount = 10000.0  # goal amount to reach
days_in_year = 365  # number of days in a year
success_rate = 50.0 / 100  # success rate per transaction
loss_percentage = 3 / 100  # loss percentage for unsuccessful transactions
average_days_in_month = 30.44  # average number of days in a month


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
pd.options.display.float_format = (
    "${:,.2f}".format
)  # Set the decimal format for 'Amount'
print(df)

# Calculate the number of transactions to reach the goal
count = 0
current_amount = initial_amount  # reset the current amount
while current_amount < goal_amount:
    current_amount = calculate_transaction(current_amount)
    count += 1

days_to_reach_goal = count / transactions_per_day
months_to_reach_goal = days_to_reach_goal / average_days_in_month

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

results_df = pd.DataFrame(
    {
        "Description": [
            "Transactions to reach goal",
            "Days to reach goal",
            "Months to reach goal",
            "Estimated amount after 6 months",
            "Estimated amount after 12 months",
        ],
        "Value": [
            count,
            "{:.2f}".format(days_to_reach_goal),
            "{:.2f}".format(months_to_reach_goal),
            "${:,.2f}".format(estimated_amount_6_months),
            "${:,.2f}".format(estimated_amount_12_months),
        ],
    }
)
print("\n", results_df)
