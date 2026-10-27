import subprocess
import sys

import uvicorn


def main() -> None:
    company = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "novamart_service.main:app",
        "--host", "127.0.0.1", "--port", "9000",
    ])
    try:
        print("NovaMart mock company API: http://127.0.0.1:9000")
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
