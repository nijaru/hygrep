import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="MyApp Management CLI")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations")
    parser.add_argument("--seed", action="store_true", help="Seed database with dummy data")
    args = parser.parse_args()

    if args.migrate:
        print("Running migrations...")
    elif args.seed:
        print("Seeding data...")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()\n