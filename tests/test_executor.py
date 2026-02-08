"""Tests for the SandboxExecutor."""

import pytest
from python_code_executor.executor import SandboxExecutor, ExecutionResult


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""
    
    def test_success_with_output(self):
        result = ExecutionResult(
            success=True,
            stdout="Hello, World!",
            stderr="",
            return_code=0
        )
        assert "Hello, World!" in result.to_string()
    
    def test_success_no_output(self):
        result = ExecutionResult(
            success=True,
            stdout="",
            stderr="",
            return_code=0
        )
        assert "successfully" in result.to_string().lower()
    
    def test_with_stderr(self):
        result = ExecutionResult(
            success=True,
            stdout="output",
            stderr="warning message",
            return_code=0
        )
        output = result.to_string()
        assert "output" in output
        assert "[STDERR]" in output
        assert "warning message" in output
    
    def test_error_message(self):
        result = ExecutionResult(
            success=False,
            stdout="",
            stderr="",
            return_code=-1,
            error_message="Something went wrong"
        )
        assert "Something went wrong" in result.to_string()


class TestSandboxExecutor:
    """Tests for SandboxExecutor."""
    
    @pytest.fixture
    def executor(self, tmp_path):
        """Create an executor with a temporary venv directory."""
        return SandboxExecutor(venv_dir=tmp_path / "test_sandbox")
    
    def test_simple_execution(self, executor):
        """Test executing simple Python code."""
        result = executor.execute_code("print('Hello, Test!')")
        assert result.success
        assert "Hello, Test!" in result.stdout
    
    def test_math_execution(self, executor):
        """Test executing code with math."""
        result = executor.execute_code("print(2 + 2)")
        assert result.success
        assert "4" in result.stdout
    
    def test_import_stdlib(self, executor):
        """Test importing standard library modules."""
        result = executor.execute_code("import math; print(math.pi)")
        assert result.success
        assert "3.14" in result.stdout
    
    def test_syntax_error(self, executor):
        """Test handling syntax errors."""
        result = executor.execute_code("print('unclosed")
        assert not result.success
        assert result.return_code != 0
    
    def test_runtime_error(self, executor):
        """Test handling runtime errors."""
        result = executor.execute_code("raise ValueError('test error')")
        assert not result.success
        assert "ValueError" in result.stderr
    
    def test_timeout(self, executor):
        """Test execution timeout."""
        result = executor.execute_code(
            "import time; time.sleep(10)",
            timeout=1
        )
        assert not result.success
        assert "timed out" in result.error_message.lower()
    
    def test_get_python_version(self, executor):
        """Test getting Python version."""
        version = executor.get_python_version()
        assert "Python" in version or "python" in version.lower()
    
    def test_list_packages(self, executor):
        """Test listing packages."""
        result = executor.list_packages()
        assert result.success
        # pip should always be installed
        assert "pip" in result.stdout.lower()
    
    def test_reset_environment(self, executor):
        """Test resetting the environment."""
        # First ensure initialized
        executor.ensure_initialized()
        assert executor.venv_dir.exists()
        
        # Reset
        result = executor.reset_environment()
        assert result.success
        assert executor.venv_dir.exists()  # Should be recreated
