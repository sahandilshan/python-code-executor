# Python Code Executor MCP Server

An MCP (Model Context Protocol) server that provides secure Python code execution capabilities within an isolated sandbox environment.

## Features

- 🔒 **Isolated Execution**: Code runs in a dedicated virtual environment
- 📦 **Package Management**: Install and manage packages in the sandbox
- ⏱️ **Timeout Protection**: Configurable execution timeouts prevent runaway scripts
- 🔄 **Environment Reset**: Easily reset the sandbox to a clean state
- 📋 **Detailed Output**: Get stdout, stderr, and execution status
- 🐳 **Docker Support**: Run in a container for maximum isolation

---

## Quick Start with Docker

### Option 1: Docker Compose (Recommended) 🔒

Docker Compose is the **recommended approach** because it includes security hardening out of the box:

```bash
docker compose up -d --build
```

**Security features included automatically:**

| Security Feature | What it does |
|------------------|--------------|
| `cap_drop: ALL` | Drops all Linux capabilities (prevents privilege escalation) |
| `security_opt: no-new-privileges` | Prevents gaining new privileges via setuid/setgid |
| `resources.limits` | Limits CPU (2 cores) and memory (2GB) to prevent DoS |
| `read_only: false` | Can be set to `true` for stricter isolation |
| Non-root user | Container runs as `executor` user, not root |

**Manage the container:**

```bash
# View logs
docker compose logs -f

# Stop
docker compose down

# Restart with fresh build
docker compose up -d --build --force-recreate
```

---

### Option 2: Plain Docker (Simple)

If you prefer not to use Docker Compose, you can use the Dockerfile directly:

```bash
# Build the image
docker build -t python-executor .

# Run with basic security
docker run -d \
  --name python-executor \
  -p 8000:8000 \
  --restart unless-stopped \
  python-executor
```

**For production, add security flags manually:**

```bash
docker run -d \
  --name python-executor \
  -p 8000:8000 \
  --restart unless-stopped \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --memory 2g \
  --cpus 2 \
  python-executor
```

> ⚠️ **Note**: Without these flags, the container runs with default Docker permissions which are less restrictive.

---

## Configure Gemini CLI

Add to your `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "python-executor": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

---

## Installation (Without Docker)

### From Source

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd python-code-executor
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

### Running Locally

```bash
# With stdio transport (default)
python -m python_code_executor.server

# With SSE transport (for remote connections)
python -m python_code_executor.server --sse

# SSE on custom port
python -m python_code_executor.server --sse --port 3000
```

### Local Gemini CLI Config (stdio)

```json
{
  "mcpServers": {
    "python-executor": {
      "command": "python",
      "args": ["-m", "python_code_executor.server"],
      "cwd": "D:\\projects\\python-code-executor"
    }
  }
}
```

---

## Available Tools

### `execute_python`
Execute Python code in the sandbox.

```python
execute_python("print('Hello, World!')")
execute_python("import math; print(math.sqrt(16))")
```

**Parameters:**
- `code` (str): The Python code to execute
- `timeout` (int, optional): Max execution time in seconds (default: 60, max: 300)

### `install_package`
Install Python packages into the sandbox.

```python
install_package("numpy")
install_package("pandas matplotlib seaborn")
install_package("requests>=2.28.0")
```

### `list_installed_packages`
List all installed packages in the sandbox.

### `reset_sandbox`
Reset the sandbox to a clean state (removes all installed packages).

### `get_sandbox_info`
Get information about the sandbox environment (Python version, path, status).

---

## Architecture

### With Docker (Recommended)

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│   MCP Client    │     │            Docker Container              │
│  (Gemini/Claude)│     │  ┌──────────────┐    ┌────────────────┐  │
│                 │◄───►│  │  MCP Server  │───►│  Sandbox Env   │  │
│                 │ SSE │  │  (port 8000) │    │  (Python 3.12) │  │
└─────────────────┘     │  └──────────────┘    └────────────────┘  │
                        └──────────────────────────────────────────┘
```

### Without Docker

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MCP Client    │────►│   MCP Server     │────►│   Sandbox Env   │
│  (Gemini/Claude)│stdio│  (server.py)     │     │ (~/.sandbox)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Security Comparison

| Feature | Docker Compose | Plain Docker | No Docker |
|---------|----------------|--------------|-----------|
| File system isolation | ✅ Complete | ✅ Complete | ❌ None |
| Capability dropping | ✅ Automatic | ⚠️ Manual flags | ❌ N/A |
| Resource limits | ✅ Automatic | ⚠️ Manual flags | ❌ None |
| Non-root execution | ✅ Yes | ✅ Yes | ⚠️ Depends |
| Privilege escalation prevention | ✅ Automatic | ⚠️ Manual flags | ❌ None |
| Network isolation | ✅ Configurable | ✅ Configurable | ❌ None |

---

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Project Structure

```
python-code-executor/
├── python_code_executor/
│   ├── __init__.py
│   ├── server.py      # MCP server (stdio + SSE)
│   └── executor.py    # Sandbox execution logic
├── tests/
│   └── test_executor.py
├── Dockerfile         # Container definition
├── docker-compose.yml # Secure container config
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## Troubleshooting

### Docker Issues

**Container won't start:**
```bash
docker compose logs
docker compose down
docker compose build --no-cache
docker compose up -d
```

**Port already in use:**
```bash
# Change port mapping
docker compose down
# Edit docker-compose.yml: ports: "3000:8000"
docker compose up -d
```

### Windows Issues

**Python not found**: Use Docker instead (recommended), or specify full path to Python executable.

---

## License

MIT License - see LICENSE file for details.
