#!/usr/bin/env python3

import os
import subprocess
import sys
import time
from typing import Dict, Optional, Tuple

# Neo4j container configuration
CONTAINER_NAME = "genealogy-neo4j"
NEO4J_PORTS: Dict[int, int] = {
    7474: 7474,  # Browser interface
    7687: 7687,  # Bolt connection
}

def get_neo4j_password() -> str:
    """Get Neo4j password from environment variable."""
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        print("Error: NEO4J_PASSWORD environment variable not set")
        sys.exit(1)
    return password

def check_container_exists() -> bool:
    """Check if the Neo4j container exists."""
    result = subprocess.run(
        ["podman", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    return CONTAINER_NAME in result.stdout

def check_container_running() -> bool:
    """Check if the Neo4j container is running."""
    result = subprocess.run(
        ["podman", "ps", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    return CONTAINER_NAME in result.stdout

def start_container():
    """Start the Neo4j container."""
    if check_container_running():
        print(f"Container {CONTAINER_NAME} is already running")
        return

    if not check_container_exists():
        print(f"Container {CONTAINER_NAME} does not exist. Creating...")
        create_container()

    print(f"Starting container {CONTAINER_NAME}...")
    subprocess.run(["podman", "start", CONTAINER_NAME])
    print("Container started successfully")

def stop_container():
    """Stop the Neo4j container."""
    if not check_container_running():
        print(f"Container {CONTAINER_NAME} is not running")
        return

    print(f"Stopping container {CONTAINER_NAME}...")
    subprocess.run(["podman", "stop", CONTAINER_NAME])
    print("Container stopped successfully")

def remove_container():
    """Remove the Neo4j container."""
    if check_container_running():
        print(f"Stopping container {CONTAINER_NAME}...")
        subprocess.run(["podman", "stop", CONTAINER_NAME])

    if check_container_exists():
        print(f"Removing container {CONTAINER_NAME}...")
        subprocess.run(["podman", "rm", CONTAINER_NAME])
        print("Container removed successfully")
    else:
        print(f"Container {CONTAINER_NAME} does not exist")

def create_container():
    """Create the Neo4j container."""
    # Build the ports string
    ports = " ".join([f"-p {host}:{container}" for host, container in NEO4J_PORTS.items()])

    # Get Neo4j password from environment
    password = get_neo4j_password()

    # Create the container
    command = f"podman run --name {CONTAINER_NAME} {ports} -e NEO4J_AUTH=neo4j/{password} -d neo4j:latest"
    subprocess.run(command, shell=True)
    print("Container created successfully")

def check_status():
    """Check the status of the Neo4j container."""
    if not check_container_exists():
        print(f"Container {CONTAINER_NAME} does not exist")
        return

    if check_container_running():
        print(f"Container {CONTAINER_NAME} is running")
        print(f"Browser interface: http://localhost:{list(NEO4J_PORTS.keys())[0]}")
        print(f"Bolt connection: bolt://localhost:{list(NEO4J_PORTS.keys())[1]}")
        print("Username: neo4j")
        print("Password: ********")
    else:
        print(f"Container {CONTAINER_NAME} exists but is not running")

def main():
    """Main function to handle command-line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python manage_neo4j.py [status|start|stop|remove]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "status":
        check_status()
    elif command == "start":
        start_container()
    elif command == "stop":
        stop_container()
    elif command == "remove":
        remove_container()
    else:
        print("Invalid command. Use: status, start, stop, or remove")
        sys.exit(1)

if __name__ == "__main__":
    main() 