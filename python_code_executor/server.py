"""
MCP Server for Python Code Execution.

This module provides an MCP server that exposes tools for executing
Python code in an isolated sandbox environment.

Supports both stdio and SSE transport modes.
"""

import argparse
import logging
import sys
from mcp.server.fastmcp import FastMCP

from .executor import SandboxExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the MCP server and sandbox executor
mcp = FastMCP(
    name="Python Code Executor",
    instructions="Execute Python code safely in an isolated sandbox environment"
)
executor = SandboxExecutor()


@mcp.tool()
def execute_python(code: str, timeout: int = 60) -> str:
    """
    Execute Python code in an isolated sandbox environment.
    
    The code runs in a dedicated virtual environment with its own
    installed packages. Use install_package to add dependencies.
    
    Args:
        code: The complete Python code to execute.
        timeout: Maximum execution time in seconds (default: 60, max: 300).
    
    Returns:
        The output of the code execution, including stdout and stderr.
    
    Examples:
        - Simple math: execute_python("print(2 + 2)")
        - Using imports: execute_python("import math; print(math.pi)")
    """
    # Clamp timeout to reasonable bounds
    timeout = max(1, min(timeout, 300))
    
    logger.info(f"Executing Python code (timeout: {timeout}s)")
    result = executor.execute_code(code, timeout=timeout)
    return result.to_string()


@mcp.tool()
def install_package(package_names: str) -> str:
    """
    Install Python packages into the sandbox environment.
    
    Packages are installed using pip and persist across executions
    until the environment is reset.
    
    Args:
        package_names: Space-separated list of packages to install.
                      Can include version specifiers (e.g., "pandas>=2.0").
    
    Returns:
        Installation status and output.
    
    Examples:
        - Single package: install_package("numpy")
        - Multiple packages: install_package("pandas matplotlib seaborn")
        - With version: install_package("requests>=2.28.0")
    """
    packages = package_names.split()
    if not packages:
        return "Error: No package names provided"
    
    logger.info(f"Installing packages: {packages}")
    result = executor.install_packages(packages)
    
    if result.success:
        return f"Successfully installed: {package_names}\n\n{result.stdout}"
    else:
        error_msg = result.error_message or result.stderr
        return f"Installation failed:\n{error_msg}"


@mcp.tool()
def list_installed_packages() -> str:
    """
    List all packages installed in the sandbox environment.
    
    Returns:
        A formatted list of installed packages and their versions.
    """
    logger.info("Listing installed packages")
    result = executor.list_packages()
    
    if result.success:
        return result.stdout or "No packages installed (besides defaults)."
    else:
        return f"Error: {result.error_message or result.stderr}"


@mcp.tool()
def reset_sandbox() -> str:
    """
    Reset the sandbox environment to a clean state.
    
    This removes all installed packages and clears any state.
    Use this if the environment becomes corrupted or you want
    to start fresh.
    
    Returns:
        Status message indicating success or failure.
    """
    logger.info("Resetting sandbox environment")
    result = executor.reset_environment()
    return result.to_string()


@mcp.tool()
def get_sandbox_info() -> str:
    """
    Get information about the sandbox environment.
    
    Returns:
        Information about the Python version and environment location.
    """
    python_version = executor.get_python_version()
    env_path = str(executor.venv_dir)
    
    return f"""Sandbox Environment Info:
- Python Version: {python_version}
- Environment Path: {env_path}
- Status: {'Initialized' if executor._initialized else 'Not initialized (will be created on first use)'}
"""


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Python Code Executor MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio transport (default)
  python -m python_code_executor.server
  
  # Run with SSE transport on port 8000
  python -m python_code_executor.server --sse
  
  # Run with SSE on custom port
  python -m python_code_executor.server --sse --port 3000
"""
    )
    
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE (Server-Sent Events) transport instead of stdio"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind SSE server (default: 0.0.0.0)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the MCP server."""
    args = parse_args()
    
    if args.sse:
        # Configure SSE settings
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        logger.info(f"Starting MCP Server with SSE transport on {args.host}:{args.port}")
        mcp.run(transport="sse")
    else:
        logger.info("Starting MCP Server with stdio transport")
        mcp.run()


if __name__ == "__main__":
    main()

