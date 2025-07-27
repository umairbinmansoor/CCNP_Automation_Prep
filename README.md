# CCNP Automation Prep

This repository is designed to help you prepare for the new CCNP Automation exam, focusing on practical automation skills and concepts from the "Designing, Deploying and Managing Network Automation Systems v2.0 (350-901)" blueprint, especially Section 4.0.

## Repository Structure

- **01_Subnet_Calculator/**  
  Contains a Python-based subnet calculator tool. This tool helps you quickly determine subnet ranges, masks, and other network details, which is essential for network automation tasks and scripting.

- **02_pyATS/**  
  Includes sample scripts and testbeds using Cisco's pyATS framework for automated network testing. These examples demonstrate how to automate network validation, configuration checks, and operational state verification.

## MCP Server and ReACT Agents

- **MCP (Model Context Protocol) Server:**  
  A Python FastAPI-based server that provides network information to AI agents. It acts as a backend for automation tasks, exposing APIs for retrieving and updating network data.

- **ReACT Agents:**  
  Conversational agents leveraging LLMs (Large Language Models) to interact with the MCP server. These agents can answer network-related questions, assist with automation workflows, and demonstrate how AI can be integrated into network operations.

## How to Use

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CCNP_Automation_Prep.git
cd CCNP_Automation_Prep
```

### 2. Set Up a Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements

Each folder contains its own `requirements.txt`. For example, to install dependencies for the Subnet Calculator:

```bash
cd 01_Subnet_Calculator
pip install -r requirements.txt
```

Repeat for other folders as needed.

### 4. Run the Subnet Calculator

```bash
cd 01_Subnet_Calculator
python server.py
```
- The Subnet Calculator runs as a server and takes a CIDR IP address as input (e.g., `192.168.1.0/24`).
- Use the web interface or API (as documented in the folder) to get subnet details.

### 5. Use pyATS for Automated Testing and Conversational Control

```bash
cd ../02_pyATS
pip install -r requirements.txt
python server.py
```
- The pyATS folder includes a server that allows you to interact with your network topology using natural language.
- You can "talk" to your topology: ask questions, request tests, or automate tasks via the conversational interface.
- The included testbed YAML is pre-configured for Cisco DevNet Sandbox CML.
    - Reserve a CML sandbox at [Cisco DevNet Sandbox](https://devnetsandbox.cisco.com/).
    - Connect via VPN as instructed by the sandbox.
    - On each device, enable SSH:
        - `crypto key generate rsa`
        - Configure SSH and user credentials as needed.
    - Update the testbed YAML with your device IPs if necessary.

---

This repository is a hands-on resource for network engineers preparing for the CCNP Automation exam, providing practical examples and code to build your automation skills.
```bash
cd ../folder_with_mcp_server
pip install -r requirements.txt
python server.py
```
- The MCP server exposes APIs for network data.
- You can interact with it using the provided ReACT agent or your own scripts.

### 7. Use the ReACT Agent

- The ReACT agent connects to the MCP server and allows conversational interaction for network automation tasks.
- Follow the instructions in the agent's folder to start and use it.

---

This repository is a hands-on resource for network engineers preparing for the CCNP Automation exam, providing practical examples and code to build your automation skills.


