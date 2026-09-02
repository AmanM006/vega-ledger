from mcp.server.fastmcp import FastMCP
import os
import json

mcp = FastMCP("VRP-Agent-MCP")

@mcp.tool()
def get_verifiable_log() -> str:
    """Retrieve the cryptographically verifiable trading log."""
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "verifiable_log.json")
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            return json.dumps(json.load(f)[-5:], indent=2)
    return "Log not found."

@mcp.tool()
def run_evaluation() -> str:
    """Force the agent to run an evaluation cycle."""
    import subprocess
    import sys
    agent_path = os.path.join(os.path.dirname(__file__), "agent.py")
    res = subprocess.run([sys.executable, agent_path], capture_output=True, text=True)
    return res.stdout

if __name__ == "__main__":
    mcp.run()
