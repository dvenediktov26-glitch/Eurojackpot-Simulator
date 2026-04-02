"""Legacy command-line entry point kept for historical reference."""

from app.simulation import run_simulation


def main() -> None:
    prize_amounts = {
        "Class 1": 10_000_000.0,
        "Class 2": 500_000.0,
        "Class 3": 50_000.0,
        "Class 4": 5_000.0,
        "Class 5": 500.0,
        "Class 6": 200.0,
        "Class 7": 100.0,
        "Class 8": 50.0,
        "Class 9": 25.0,
        "Class 10": 20.0,
        "Class 11": 15.0,
        "Class 12": 10.0,
    }

    stats = run_simulation(
        n_draws=100_000,
        seed=None,
        prize_amounts=prize_amounts,
    )

    print("EUROJACKPOT SIMULATION RESULTS")
    print(f"Draws simulated: {stats.draws_simulated}")
    print(f"Tickets played: {stats.tickets_played}")
    print(f"Winning tickets: {stats.winning_tickets}")
    print(f"Winning ticket ratio: {stats.winning_ticket_ratio:.6f}")
    print(f"Total spent: {stats.total_spent:.2f} EUR")
    print(f"Total won: {stats.total_won:.2f} EUR")
    print(f"Net result: {stats.net_result:.2f} EUR")
    print(f"RTP: {stats.rtp:.6f}")
    print("\nPrize class distribution:")

    for prize_class, count in sorted(stats.prize_class_counts.items()):
        print(f"  {prize_class}: {count}")


if __name__ == "__main__":
    main()