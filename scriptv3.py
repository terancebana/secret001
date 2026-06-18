import math
import csv
from datetime import datetime

RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def get_float_input(prompt, min_val=None, max_val=None):
    while True:
        try:
            value = float(input(prompt))
            if min_val is not None and value < min_val:
                print(f"  Value must be at least {min_val}. Try again.")
                continue
            if max_val is not None and value > max_val:
                print(f"  Value must be at most {max_val}. Try again.")
                continue
            return value
        except ValueError:
            print("  Invalid number. Please enter a numeric value.")


def get_optional_float(prompt, default=None, min_val=None, max_val=None):
    raw = input(prompt).strip()
    if raw == "":
        return default
    try:
        value = float(raw)
        if min_val is not None and value < min_val:
            print(f"  Value must be at least {min_val}. Using default.")
            return default
        if max_val is not None and value > max_val:
            print(f"  Value must be at most {max_val}. Using default.")
            return default
        return value
    except ValueError:
        print("  Invalid number. Using default.")
        return default


def losses_until_bust(capital, total_loss, desired_profit, profit_pct, max_sim=30):
    sim_cap   = capital
    sim_loss  = total_loss
    sim_want  = desired_profit
    for i in range(max_sim):
        if sim_loss == 0:
            sim_bet  = sim_cap / 75
            sim_want = profit_pct * sim_bet
        else:
            sim_bet  = (sim_loss + sim_want) / profit_pct
        if sim_bet > sim_cap:
            return i
        sim_cap  -= sim_bet
        sim_loss += sim_bet
    return max_sim


def print_separator(char="─", width=44):
    print(char * width)


def run_managed_trading():
    print(f"\n{BOLD}{CYAN}{'='*44}")
    print(f"        TradeTrack v3 — Managed Trading")
    print(f"{'='*44}{RESET}")

    print(f"\n{YELLOW}{BOLD}⚠  DISCLAIMER:{RESET}")
    print(f"{YELLOW}  Martingale strategies do NOT eliminate the")
    print(f"  house edge. A losing streak causes exponential")
    print(f"  bet growth that can wipe your account rapidly.")
    print(f"  Trade responsibly and never risk money you")
    print(f"  cannot afford to lose.{RESET}\n")

    print_separator()
    print(f"{BOLD}Session Setup{RESET}")
    print_separator()

    initial_capital      = get_float_input("Starting capital ($): ", min_val=0.01)
    profit_pct_raw       = get_optional_float(
        "Payout rate % (default 92): ", default=92.0, min_val=1.0, max_val=999.0
    )
    PROFIT_PERCENTAGE    = profit_pct_raw / 100.0

    daily_target_raw     = get_optional_float(
        "Daily profit target % (default 20): ", default=20.0, min_val=0.1, max_val=10000.0
    )
    DAILY_TARGET_PCT     = daily_target_raw / 100.0

    stop_loss_raw        = get_optional_float(
        "Stop-loss: max % of capital to lose before auto-stop (Enter to skip): ",
        default=None, min_val=0.1, max_val=99.9
    )
    stop_loss_floor      = (initial_capital * (1 - stop_loss_raw / 100.0)) if stop_loss_raw else None

    target_daily_balance = initial_capital * (1 + DAILY_TARGET_PCT)
    daily_profit_needed  = target_daily_balance - initial_capital

    base_bet_estimate    = initial_capital / 75
    profit_estimate      = PROFIT_PERCENTAGE * base_bet_estimate
    est_trades_needed    = (
        math.ceil(daily_profit_needed / profit_estimate)
        if profit_estimate > 0 else float("inf")
    )

    # State
    capital                       = initial_capital
    total_loss                    = 0.0
    round_number                  = 1
    cycles_completed              = 0
    current_cycle_desired_profit  = 0.0
    trade_history                 = []
    peak_capital                  = initial_capital
    max_drawdown_pct              = 0.0
    consecutive_losses            = 0
    max_consecutive_losses        = 0
    consecutive_wins              = 0
    max_consecutive_wins          = 0

    print(f"\n")
    print_separator("═")
    print(f"{BOLD}  Daily Goal{RESET}")
    print_separator("═")
    print(f"  Starting Capital   : ${initial_capital:>10.2f}")
    print(f"  Target Balance     : ${target_daily_balance:>10.2f}  (+{DAILY_TARGET_PCT*100:.0f}%)")
    print(f"  Profit Needed      : ${daily_profit_needed:>10.2f}")
    print(f"  Payout Rate        : {PROFIT_PERCENTAGE*100:.1f}%")
    if stop_loss_floor is not None:
        print(f"  Stop-Loss Floor    : ${stop_loss_floor:>10.2f}  (-{stop_loss_raw:.0f}%)")
    if est_trades_needed == float("inf"):
        print(f"  Est. Trades Needed : N/A (check payout rate)")
    else:
        print(f"  Est. Trades Needed : {est_trades_needed}")
    print_separator("═")

    # ── Main loop ────────────────────────────────────────────────────────────
    while capital > 0 and capital < target_daily_balance:

        # Stop-loss gate
        if stop_loss_floor is not None and capital <= stop_loss_floor:
            print(f"\n{RED}{BOLD}[STOP-LOSS TRIGGERED]{RESET}")
            print(f"{RED}Capital ${capital:.2f} reached your floor of ${stop_loss_floor:.2f}.{RESET}")
            break

        # Bet sizing
        if total_loss == 0:
            base_bet                     = capital / 75
            bet                          = base_bet
            current_cycle_desired_profit = PROFIT_PERCENTAGE * base_bet
        else:
            bet = (total_loss + current_cycle_desired_profit) / PROFIT_PERCENTAGE

        if bet > capital:
            print(f"\n{RED}[!] Insufficient capital.")
            print(f"    Needed : ${bet:.2f}")
            print(f"    Have   : ${capital:.2f}{RESET}")
            break

        # Bust-risk warning
        bust_in = losses_until_bust(
            capital, total_loss, current_cycle_desired_profit, PROFIT_PERCENTAGE
        )
        current_drawdown_pct = ((peak_capital - capital) / peak_capital * 100) if peak_capital > 0 else 0
        win_rate             = (cycles_completed / (round_number - 1) * 100) if round_number > 1 else 0.0
        streak_str           = (
            f"{RED}-{consecutive_losses} streak{RESET}" if consecutive_losses > 0
            else f"{GREEN}+{consecutive_wins} streak{RESET}" if consecutive_wins > 0
            else "—"
        )

        print(f"\n")
        print_separator()
        print(f"  {BOLD}Trade #{round_number}{RESET}")
        print_separator()
        print(f"  Capital          : ${capital:.2f}")
        print(f"  Total Loss       : {RED if total_loss > 0 else ''}"
              f"${total_loss:.2f}{RESET}")
        print(f"  Recommended Bet  : ${bet:.2f}")
        print(f"  Target Profit    : ${current_cycle_desired_profit:.2f}")
        print(f"  Left to Goal     : ${max(0.0, target_daily_balance - capital):.2f}")
        print(f"  Win Rate         : {win_rate:.1f}%  |  Wins: {cycles_completed}  |  {streak_str}")
        print(f"  Drawdown         : {current_drawdown_pct:.1f}%  |  Max: {max_drawdown_pct:.1f}%")

        if bust_in == 0:
            print(f"  {RED}{BOLD}⚠  CRITICAL: Next loss will BUST your account!{RESET}")
        elif bust_in <= 3:
            print(f"  {RED}⚠  WARNING: {bust_in} more loss(es) will bust your account!{RESET}")
        elif bust_in <= 6:
            print(f"  {YELLOW}⚠  CAUTION: {bust_in} consecutive losses until bust.{RESET}")

        outcome = input("  Outcome (W / L / Q): ").strip().upper()

        if outcome == "W":
            profit   = PROFIT_PERCENTAGE * bet
            capital += profit
            if capital > peak_capital:
                peak_capital = capital
            total_loss           = 0.0
            consecutive_losses   = 0
            consecutive_wins    += 1
            if consecutive_wins > max_consecutive_wins:
                max_consecutive_wins = consecutive_wins
            cycles_completed    += 1
            trade_history.append({
                "trade": round_number, "outcome": "W",
                "bet": round(bet, 2), "result": round(profit, 2),
                "capital": round(capital, 2)
            })
            print(f"  {GREEN}✅  Gained  +${profit:.2f}   →  Capital: ${capital:.2f}{RESET}")

        elif outcome == "L":
            capital   -= bet
            total_loss += bet
            consecutive_wins     = 0
            consecutive_losses  += 1
            if consecutive_losses > max_consecutive_losses:
                max_consecutive_losses = consecutive_losses
            dd = ((peak_capital - capital) / peak_capital * 100) if peak_capital > 0 else 0
            if dd > max_drawdown_pct:
                max_drawdown_pct = dd
            trade_history.append({
                "trade": round_number, "outcome": "L",
                "bet": round(bet, 2), "result": round(-bet, 2),
                "capital": round(capital, 2)
            })
            print(f"  {RED}❌  Lost    -${bet:.2f}   →  Capital: ${capital:.2f}   "
                  f"(Streak: -{consecutive_losses}){RESET}")

        elif outcome == "Q":
            print("  Quitting session...")
            break

        else:
            print(f"  {YELLOW}Invalid input. Enter W, L, or Q.{RESET}")
            continue

        round_number += 1

    # ── Session summary ───────────────────────────────────────────────────────
    total_trades  = round_number - 1
    total_losses  = total_trades - cycles_completed
    final_pl      = capital - initial_capital
    final_wr      = (cycles_completed / total_trades * 100) if total_trades > 0 else 0.0
    pl_color      = GREEN if final_pl >= 0 else RED
    pl_sign       = "+" if final_pl >= 0 else ""

    print(f"\n\n")
    print_separator("═")
    print(f"{BOLD}  SESSION SUMMARY{RESET}")
    print_separator("═")
    print(f"  Starting Capital     : ${initial_capital:.2f}")
    print(f"  Final Capital        : {pl_color}${capital:.2f}{RESET}")
    print(f"  Net P&L              : {pl_color}{pl_sign}${final_pl:.2f}{RESET}")
    print_separator()
    print(f"  Total Trades         : {total_trades}")
    print(f"  Wins                 : {GREEN}{cycles_completed}{RESET}")
    print(f"  Losses               : {RED}{total_losses}{RESET}")
    print(f"  Win Rate             : {final_wr:.1f}%")
    print_separator()
    print(f"  Max Consecutive Wins : {GREEN}{max_consecutive_wins}{RESET}")
    print(f"  Max Consecutive Loss : {RED}{max_consecutive_losses}{RESET}")
    print(f"  Max Drawdown         : {RED}{max_drawdown_pct:.1f}%{RESET}")
    print_separator("═")

    if capital >= target_daily_balance:
        print(f"\n  {GREEN}{BOLD}🎉  Daily goal achieved!{RESET}")
    elif stop_loss_floor and capital <= stop_loss_floor:
        print(f"\n  {RED}Stop-loss triggered. Session ended.{RESET}")
    else:
        print(f"\n  Goal not achieved.")

    # ── Trade history ─────────────────────────────────────────────────────────
    if trade_history:
        show_log = input("\nPrint trade log to screen? (Y/N): ").strip().upper()
        if show_log == "Y":
            print(f"\n  {'#':<6} {'Out':<5} {'Bet':>10} {'Result':>10} {'Capital':>12}")
            print_separator()
            for t in trade_history:
                color  = GREEN if t["outcome"] == "W" else RED
                sign   = "+" if t["result"] >= 0 else ""
                print(f"  {t['trade']:<6} {color}{t['outcome']:<5}{RESET} "
                      f"${t['bet']:>9.2f} "
                      f"{color}{sign}${abs(t['result']):>8.2f}{RESET} "
                      f"${t['capital']:>11.2f}")

        save_csv = input("Save session log to CSV? (Y/N): ").strip().upper()
        if save_csv == "Y":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename  = f"trade_log_{timestamp}.csv"
            with open(filename, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["trade", "outcome", "bet", "result", "capital"])
                writer.writeheader()
                writer.writerows(trade_history)
            print(f"  {GREEN}Saved → {filename}{RESET}")


if __name__ == "__main__":
    run_managed_trading()
