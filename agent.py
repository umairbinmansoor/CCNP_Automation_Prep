import os
import subprocess
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# --- Load Environment Variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Start MCP subprocess ---
FASTMCP_CMD = ["python3", "server.py"]  # Adjust to your MCP server script

mcp_proc = subprocess.Popen(
    FASTMCP_CMD,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0  # Unbuffered
)

import threading

def log_stderr(proc):
    for line in proc.stderr:
        print("[MCP STDERR]", line.strip())

threading.Thread(target=log_stderr, args=(mcp_proc,), daemon=True).start()

# JSON-RPC ID counter
request_id = 0

def initialize_mcp():
    """Initialize MCP server with required handshake."""
    global request_id
    request_id += 1
    
    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "subnet-agent",
                "version": "1.0.0"
            }
        }
    }
    
    mcp_proc.stdin.write(json.dumps(init_request) + "\n")
    mcp_proc.stdin.flush()
    print(f"[AGENT] Sent initialize: {init_request}")
    
    # Wait for response
    time.sleep(0.1)  # Give server time to respond
    
    # Send initialized notification
    request_id += 1
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    
    mcp_proc.stdin.write(json.dumps(initialized_notification) + "\n")
    mcp_proc.stdin.flush()
    print(f"[AGENT] Sent initialized notification")

def call_subnet_calculator(cidr: str) -> dict:
    global request_id
    request_id += 1
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": "subnet_calculator",
            "arguments": {"cidr": cidr}
        }
    }

    mcp_proc.stdin.write(json.dumps(request) + "\n")
    mcp_proc.stdin.flush()

    print(f"[AGENT] Sent to MCP: {request}")

    # Read response with timeout
    start_time = time.time()
    timeout = 10  # 10 second timeout
    
    while time.time() - start_time < timeout:
        if mcp_proc.stdout.readable():
            line = mcp_proc.stdout.readline()
            if line.strip():
                print("[MCP STDOUT RAW]", line.strip())
                try:
                    response = json.loads(line)
                    if response.get("id") == request_id:
                        if "error" in response:
                            raise RuntimeError(f"MCP Error: {response['error']}")
                        return response.get("result", {})
                except json.JSONDecodeError as e:
                    print(f"[AGENT] JSON decode error: {e}")
                    continue
        time.sleep(0.1)
    
    raise RuntimeError("Timeout waiting for MCP response")

def react_agent():
    """Main interactive loop with OpenAI and FastMCP."""
    
    # Initialize MCP server
    print("[AGENT] Initializing MCP server...")
    initialize_mcp()
    time.sleep(1)  # Give server time to initialize
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful network assistant who explains CIDR notation IP addresses to users in detail. "
                "When asked for subnet calculations, call the `subnet_calculator` tool. Use the tool to get detailed subnet information for a given CIDR and then explain the results in a human-readable format. Please break down the fields to help the user understand the subnet details."
            )
        }
    ]

    while True:
        user_input = input("\nCIDR (or 'exit'): ").strip()
        if user_input.lower() == "exit":
            print("Exiting.")
            break

        messages.append({"role": "user", "content": user_input})
        print(f"[AGENT] User input: {user_input}")
        
        # Ask the model
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            functions=[
                {
                    "name": "subnet_calculator",
                    "description": "Calculate subnet details for a given CIDR",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cidr": {
                                "type": "string",
                                "description": "CIDR like 192.168.0.0/24"
                            }
                        },
                        "required": ["cidr"]
                    }
                }
            ],
            function_call="auto"
        )

        choice = response.choices[0].message
        print(f"[AGENT] OpenAI replied: {choice}")

        # Check if a tool call is required
        if choice.function_call is not None:
            args = json.loads(choice.function_call.arguments)
            cidr = args["cidr"]

            try:
                # Call MCP tool
                tool_result = call_subnet_calculator(cidr)

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": choice.function_call
                })

                messages.append({
                    "role": "function",
                    "name": "subnet_calculator",
                    "content": json.dumps(tool_result)
                })

                # Ask model for final human-readable answer
                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                print("\nAgent:", final_response.choices[0].message.content)
                messages.append({"role": "assistant", "content": final_response.choices[0].message.content})

            except Exception as e:
                print(f"[AGENT] Error calling MCP tool: {e}")
                error_msg = f"Sorry, I encountered an error calculating the subnet: {e}"
                print("\nAgent:", error_msg)
                messages.append({"role": "assistant", "content": error_msg})

        else:
            print("\nAgent:", choice.content)
            messages.append({"role": "assistant", "content": choice.content})

if __name__ == "__main__":
    try:
        react_agent()
    finally:
        # Clean up subprocess
        if mcp_proc:
            mcp_proc.terminate()
            mcp_proc.wait()