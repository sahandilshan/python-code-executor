"""
Sandbox executor module for running Python code in isolation.
"""

import os
import sys
import venv
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a code execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    error_message: Optional[str] = None

    def to_string(self) -> str:
        """Convert result to a human-readable string."""
        if self.error_message:
            return f"Error: {self.error_message}"
        
        output_parts = []
        if self.stdout.strip():
            output_parts.append(self.stdout)
        if self.stderr.strip():
            output_parts.append(f"[STDERR]:\n{self.stderr}")
        
        if not output_parts:
            return "Code executed successfully (no output)."
        
        return "\n".join(output_parts)


class SandboxExecutor:
    """
    Manages a sandboxed Python virtual environment for code execution.
    
    This class creates and manages an isolated virtual environment
    where user-provided Python code can be executed safely.
    """
    
    DEFAULT_TIMEOUT = 60  # seconds
    DEFAULT_VENV_NAME = ".sandbox_env"
    
    def __init__(
        self,
        venv_dir: Optional[Path] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the sandbox executor.
        
        Args:
            venv_dir: Path to the virtual environment directory.
                     Defaults to .sandbox_env in the package directory.
            timeout: Default execution timeout in seconds.
        """
        if venv_dir is None:
            # Create venv in user's home directory to avoid permission issues
            venv_dir = Path.home() / ".python_executor_sandbox"
        
        self.venv_dir = Path(venv_dir)
        self.timeout = timeout
        self._initialized = False
    
    @property
    def python_path(self) -> Path:
        """Get the path to the Python interpreter in the sandbox."""
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"
    
    @property
    def pip_path(self) -> Path:
        """Get the path to pip in the sandbox."""
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "pip.exe"
        return self.venv_dir / "bin" / "pip"
    
    def ensure_initialized(self) -> bool:
        """
        Ensure the virtual environment exists and is ready.
        
        Returns:
            True if initialization succeeded, False otherwise.
        """
        if self._initialized and self.venv_dir.exists():
            return True
        
        if not self.venv_dir.exists():
            logger.info(f"Creating sandbox environment at: {self.venv_dir}")
            try:
                venv.create(str(self.venv_dir), with_pip=True, clear=True)
                logger.info("Sandbox environment created successfully")
            except Exception as e:
                logger.error(f"Failed to create sandbox environment: {e}")
                return False
        
        # Verify the Python executable exists
        if not self.python_path.exists():
            logger.error(f"Python executable not found at: {self.python_path}")
            return False
        
        self._initialized = True
        return True
    
    def execute_code(
        self,
        code: str,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute Python code in the sandbox.
        
        Args:
            code: Python code to execute.
            timeout: Execution timeout in seconds (overrides default).
        
        Returns:
            ExecutionResult with execution details.
        """
        if not self.ensure_initialized():
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message="Failed to initialize sandbox environment"
            )
        
        timeout = timeout or self.timeout
        
        # Create a temporary file for the code
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = Path(f.name)
            
            # Execute the code
            result = subprocess.run(
                [str(self.python_path), str(temp_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(temp_file.parent)  # Run in temp directory
            )
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message=f"Execution timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.exception("Unexpected error during code execution")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message=f"System error: {str(e)}"
            )
        finally:
            # Clean up temp file
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
    
    def install_packages(self, packages: list[str]) -> ExecutionResult:
        """
        Install packages into the sandbox environment.
        
        Args:
            packages: List of package names to install.
        
        Returns:
            ExecutionResult with installation details.
        """
        if not self.ensure_initialized():
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message="Failed to initialize sandbox environment"
            )
        
        if not packages:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message="No packages specified"
            )
        
        try:
            cmd = [
                str(self.python_path), "-m", "pip", "install",
                "--disable-pip-version-check",
                *packages
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for installations
            )
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message="Package installation timed out after 5 minutes"
            )
        except Exception as e:
            logger.exception("Unexpected error during package installation")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message=f"System error: {str(e)}"
            )
    
    def list_packages(self) -> ExecutionResult:
        """
        List installed packages in the sandbox.
        
        Returns:
            ExecutionResult with package list.
        """
        if not self.ensure_initialized():
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message="Failed to initialize sandbox environment"
            )
        
        try:
            result = subprocess.run(
                [str(self.python_path), "-m", "pip", "list", "--format=columns"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message=f"System error: {str(e)}"
            )
    
    def reset_environment(self) -> ExecutionResult:
        """
        Reset the sandbox by deleting and recreating the virtual environment.
        
        Returns:
            ExecutionResult indicating success or failure.
        """
        try:
            if self.venv_dir.exists():
                logger.info(f"Removing existing sandbox at: {self.venv_dir}")
                shutil.rmtree(self.venv_dir)
            
            self._initialized = False
            
            if self.ensure_initialized():
                return ExecutionResult(
                    success=True,
                    stdout="Sandbox environment has been reset successfully.",
                    stderr="",
                    return_code=0
                )
            else:
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="",
                    return_code=-1,
                    error_message="Failed to recreate sandbox environment"
                )
        
        except Exception as e:
            logger.exception("Failed to reset sandbox environment")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error_message=f"Failed to reset environment: {str(e)}"
            )
    
    def get_python_version(self) -> str:
        """Get the Python version in the sandbox."""
        if not self.ensure_initialized():
            return "Unknown (sandbox not initialized)"
        
        try:
            result = subprocess.run(
                [str(self.python_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception:
            return "Unknown"
