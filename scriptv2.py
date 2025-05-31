import math

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def run_managed_trading():
    try:
        initial_capital = float(input("Enter your starting capital: "))
        PROFIT_PERCENTAGE = 0.92
    except ValueError:
        print("Invalid number.")
        return

    DAILY_PROFIT_TARGET_PERCENTAGE = 0.20
    target_daily_balance = initial_capital * (1 + DAILY_PROFIT_TARGET_PERCENTAGE)
    daily_profit_needed = target_daily_balance - initial_capital

    base_bet_for_initial_estimate = initial_capital / 75
    desired_profit_for_initial_estimate = PROFIT_PERCENTAGE * base_bet_for_initial_estimate
    
    estimated_successful_cycles_needed = 0
    if desired_profit_for_initial_estimate > 0:
        estimated_successful_cycles_needed = math.ceil(daily_profit_needed / desired_profit_for_initial_estimate)
    elif daily_profit_needed > 0:
        estimated_successful_cycles_needed = float('inf')
    
    cycles_completed_towards_goal = 0

    capital = initial_capital
    total_loss = 0
    round_number = 1
    current_cycle_desired_profit = 0

    print(f"\n--- Daily Goal ---")
    print(f"Starting Capital: ${initial_capital:.2f}")
    print(f"Target Daily Balance: ${target_daily_balance:.2f} (+{DAILY_PROFIT_TARGET_PERCENTAGE*100:.0f}%)")
    print(f"Profit Needed Today: ${daily_profit_needed:.2f}")
    
    if estimated_successful_cycles_needed == float('inf'):
        print(f"Estimated Successful Trades Needed: Cannot achieve with current profit settings (initial bet too small or 0).")
    else:
        print(f"Estimated Successful Trades Needed: {estimated_successful_cycles_needed}")
    print(f"------------------")

    while capital > 0 and capital < target_daily_balance: 
        if total_loss == 0:
            current_base_bet = capital / 75
            bet = current_base_bet
            current_cycle_desired_profit = PROFIT_PERCENTAGE * current_base_bet
        else:
            bet = (total_loss + current_cycle_desired_profit) / PROFIT_PERCENTAGE

        if bet > capital:
            print(f"\n[!] Not enough capital to continue. Needed: {bet:.2f} USD, Available: {capital:.2f} USD")
            break

        print(f"\n--- Trade No. {round_number} ---")
        print(f"Capital: {capital:.2f} USD")
        print(f"Total Loss: {RED if total_loss > 0 else ''}{total_loss:.2f} USD{RESET}")
        print(f"Recommended Bet: {bet:.2f} USD")
        print(f"Target Profit: {current_cycle_desired_profit:.2f} USD")

        balance_left_to_goal = max(0, target_daily_balance - capital)
        print(f"Target daily income: {balance_left_to_goal:.2f} USD")
        print(f"Profitable trades: {cycles_completed_towards_goal}")
        
        outcome = input("Enter outcome (W = win, L = loss, Q = quit): ").strip().upper()

        if outcome == 'W':
            profit = PROFIT_PERCENTAGE * bet
            capital += profit
            total_loss = 0
            cycles_completed_towards_goal += 1
            print(f"{GREEN}✅ Gained {profit:.2f} USD{RESET}")
        elif outcome == 'L':
            capital -= bet
            total_loss += bet
            print(f"❌ Lost {bet:.2f} USD")
        elif outcome == 'Q':
            print("Exiting...")
            break
        else:
            print("Invalid input. Please enter W, L, or Q.")
            continue

        round_number += 1

    print(f"\nSession ended.")
    
    final_capital_color = GREEN if capital > initial_capital else ""
    final_capital_reset = RESET if capital > initial_capital else ""

    if capital >= target_daily_balance:
        print(f"🎉 Daily goal achieved! Final capital: {final_capital_color}{capital:.2f} USD{final_capital_reset}")
    else:
        print(f"Goal not achieved. Final capital: {final_capital_color}{capital:.2f} USD{final_capital_reset}")

if __name__ == "__main__":
    run_managed_trading()