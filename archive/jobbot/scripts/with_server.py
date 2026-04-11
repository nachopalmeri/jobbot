#!/usr/bin/env python3
"""
with_server.py - Server lifecycle manager for web application testing

Starts one or more servers, waits for them to be ready, runs a command,
then cleanly shuts down all servers.

Usage:
  python scripts/with_server.py --server "npm run dev" --port 5173 -- python test.py
  python scripts/with_server.py \
    --server "cd api && uvicorn main:app --port 8000" --port 8000 \
    --server "cd frontend && npm run dev" --port 5173 \
    -- python test_e2e.py
"""

import argparse
import subprocess
import sys
import time
import socket
import signal
import os
from typing import List, Tuple


def is_port_open(port: int, host: str = "localhost", timeout: float = 1.0) -> bool:
    """Check if a port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def wait_for_port(port: int, host: str = "localhost", timeout: float = 30.0) -> bool:
    """Wait for a port to become available."""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(port, host):
            return True
        time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Manage server lifecycle for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single server:
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python test.py

  Multiple servers:
    python scripts/with_server.py \\
      --server "cd backend && python server.py" --port 8000 \\
      --server "cd frontend && npm run dev" --port 5173 \\
      -- python test_e2e.py

  Custom timeout:
    python scripts/with_server.py --server "npm start" --port 3000 --timeout 60 -- npm test
"""
    )
    
    parser.add_argument(
        "--server",
        action="append",
        dest="servers",
        help="Server command to run (can be specified multiple times)"
    )
    parser.add_argument(
        "--port",
        action="append",
        dest="ports",
        type=int,
        help="Port to wait for (corresponds to --server order)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds to wait for servers (default: 30)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to check for port availability (default: localhost)"
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run after servers are ready (everything after this is the command)"
    )
    
    args = parser.parse_args()
    
    if not args.servers:
        parser.print_help()
        sys.exit(0)
    
    if args.ports and len(args.ports) != len(args.servers):
        print("Error: Number of --port arguments must match number of --server arguments")
        sys.exit(1)
    
    processes: List[subprocess.Popen] = []
    
    def cleanup(signum=None, frame=None):
        """Clean up all server processes."""
        print("\n[STOP] Shutting down servers...")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        if signum:
            sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        # Start all servers
        print(f"[START] Starting {len(args.servers)} server(s)...")
        for i, cmd in enumerate(args.servers):
            print(f"  [{i+1}] {cmd}")
            
            # Use shell=True for complex commands with &&
            use_shell = "&&" in cmd or "||" in cmd or ";" in cmd
            if use_shell:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(proc)
        
        # Wait for ports to be ready
        if args.ports:
            print(f"\n[WAIT] Waiting for ports to be ready (timeout: {args.timeout}s)...")
            for i, port in enumerate(args.ports):
                if not wait_for_port(port, args.host, args.timeout):
                    print(f"[ERROR] Timeout waiting for port {port}")
                    cleanup()
                    sys.exit(1)
                print(f"  [OK] Port {port} is ready")
        else:
            print("\n[WAIT] Waiting 3s for servers to start (no ports specified)...")
            time.sleep(3)
        
        print("[READY] All servers ready!\n")
        
        # Run the command
        if args.command:
            cmd = args.command
            print(f"[RUN] Running: {' '.join(cmd)}\n")
            result = subprocess.run(cmd)
            exit_code = result.returncode
        else:
            print("[INFO] No command specified. Servers will run until interrupted (Ctrl+C).")
            print("   Press Ctrl+C to stop.\n")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                exit_code = 0
        
        cleanup()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
