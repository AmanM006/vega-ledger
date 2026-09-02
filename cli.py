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
    parser_dashboard = subparsers.add_parser('dashboard', help='Launch the Next.js dark-mode dashboard (or Streamlit with --legacy)')
    parser_dashboard.add_argument('--legacy', action='store_true', help='Run legacy Streamlit UI')
    parser_mcp = subparsers.add_parser('mcp', help='Launch the FastMCP server')

    args = parser.parse_args()

    if args.command == 'run':
        subprocess.run([sys.executable, r'src\orchestration\agent.py'])
    elif args.command == 'daemon':
        subprocess.run([sys.executable, 'dry_run.py'])
    elif args.command == 'drift':
        subprocess.run([sys.executable, r'src\orchestration\drift_report.py'])
    elif args.command == 'backtest':
        subprocess.run([sys.executable, r'src\backtest\dsr_bootstrap.py'])
    elif args.command == 'mcp':
        subprocess.run([sys.executable, r'src\orchestration\mcp_server.py'])
    elif args.command == 'dashboard':
        if getattr(args, 'legacy', False):
            subprocess.run([sys.executable, '-m', 'streamlit', 'run', r'src\app\dashboard.py'])
        else:
            dashboard_dir = os.path.join(os.path.dirname(__file__), 'dashboard')
            # Run npm run start on port 3001
            subprocess.run(['npm', 'run', 'start'], cwd=dashboard_dir, shell=True)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
