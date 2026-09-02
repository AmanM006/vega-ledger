import argparse
import subprocess
import sys
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description='Alpaca VRP Agent CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    parser_run = subparsers.add_parser('run', help='Run the agent evaluation node once')
    parser_daemon = subparsers.add_parser('daemon', help='Start the 4-hour background execution loop')
    parser_drift = subparsers.add_parser('drift', help='Generate a drift report from the verifiable log')
    parser_backtest = subparsers.add_parser('backtest', help='Run the walk-forward DSR backtest')
    parser_dashboard = subparsers.add_parser('dashboard', help='Launch the Streamlit dashboard')

    args = parser.parse_args()

    if args.command == 'run':
        subprocess.run([sys.executable, r'src\orchestration\agent.py'])
    elif args.command == 'daemon':
        subprocess.run([sys.executable, 'dry_run.py'])
    elif args.command == 'drift':
        subprocess.run([sys.executable, r'src\orchestration\drift_report.py'])
    elif args.command == 'backtest':
        subprocess.run([sys.executable, r'src\backtest\dsr_bootstrap.py'])
    elif args.command == 'dashboard':
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', r'src\app\dashboard.py'])
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
