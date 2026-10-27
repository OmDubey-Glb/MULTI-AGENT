import json
import subprocess
import sys
import time
from urllib.request import urlopen

import uvicorn


def wait_for_company_api(process: subprocess.Popen, timeout: float = 10.0) -> None:
    """Wait until the local synthetic NovaMart service is ready before serving the UI."""
    deadline = time.monotonic() + timeout
    last_error = "health endpoint did not respond"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("NovaMart mock API exited during startup. Check whether port 9000 is already in use.")
        try:
            with urlopen("http://127.0.0.1:9000/health", timeout=0.5) as response:
                health = json.loads(response.read().decode("utf-8"))
            if health.get("status") == "online" and health.get("data") == "synthetic-only":
                return
            last_error = "health endpoint returned an unexpected response"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.2)
    raise RuntimeError(f"NovaMart mock API did not become ready within {timeout:.0f}s: {last_error}")


def main() -> None:
    company = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "novamart_service.main:app",
        "--host", "127.0.0.1", "--port", "9000",
    ])
    try:
        wait_for_company_api(company)
        print("NovaMart mock company API ready: http://127.0.0.1:9000")
        print("DPDP Erasure Orchestrator: http://127.0.0.1:8000")
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
    finally:
        company.terminate()
        try:
            company.wait(timeout=5)
        except subprocess.TimeoutExpired:
            company.kill()
            company.wait()


if __name__ == "__main__":
    main()
