import streamlit as st
import os
import subprocess
import json
import threading
import time
import sys
from groq import Groq
from dotenv import load_dotenv
from genie.testbed import load

# Load environment variables from .env file
load_dotenv()

# --- Groq Client ---
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = Groq(api_key=st.secrets.GROQ_API_KEY)

# --- MCP Server Management ---
def start_mcp_server(testbed_file):
    if "mcp_proc" in st.session_state and st.session_state.mcp_proc:
        st.session_state.mcp_proc.terminate()
        st.session_state.mcp_proc.wait()

    env = os.environ.copy()
    env["PYATS_TESTBED_PATH"] = testbed_file
    server_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "server.py")
    proc = subprocess.Popen(
        # ["venv/bin/python3", "server.py"],
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
        env=env
    )
    st.session_state.mcp_proc = proc
    threading.Thread(target=log_stderr, args=(proc,), daemon=True).start()
    time.sleep(1)
    initialize_mcp()
    st.session_state.tools = get_tool_list()
    st.session_state.openai_tools = [tool_to_openai(t) for t in st.session_state.tools]

def log_stderr(proc):
    for line in proc.stderr:
        print(f"[MCP STDERR] {line.strip()}", file=sys.stderr)

# --- JSON-RPC & Tool Conversion ---
request_id_counter = 0
def next_id():
    global request_id_counter
    request_id_counter += 1
    return request_id_counter

def mcp_send(obj: dict):
    if "mcp_proc" in st.session_state and st.session_state.mcp_proc.stdin:
        st.session_state.mcp_proc.stdin.write(json.dumps(obj) + "\n")
        st.session_state.mcp_proc.stdin.flush()

def mcp_recv(timeout=180):
    if "mcp_proc" in st.session_state and st.session_state.mcp_proc.stdout:
        start = time.time()
        while time.time() - start < timeout:
            line = st.session_state.mcp_proc.stdout.readline()
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
            time.sleep(0.05)
    raise TimeoutError("No response from MCP server")

def initialize_mcp():
    mcp_send({"jsonrpc": "2.0", "id": next_id(), "method": "initialize", "params": {"protocolVersion": "2024-11-05"}})
    time.sleep(0.1)
    mcp_send({"jsonrpc": "2.0", "method": "notifications/initialized"})

def get_tool_list() -> list:
    rid = next_id()
    mcp_send({"jsonrpc": "2.0", "id": rid, "method": "tools/list"})
    while True:
        resp = mcp_recv()
        if resp.get("id") == rid:
            return resp.get("result", {}).get("tools", [])

def call_tool(name: str, args: dict) -> dict:
    rid = next_id()
    mcp_send({"jsonrpc": "2.0", "id": rid, "method": "tools/call", "params": {"name": name, "arguments": args}})
    while True:
        resp = mcp_recv()
        if resp.get("id") == rid:
            if "error" in resp:
                raise RuntimeError(resp["error"])
            return resp.get("result", {})

def tool_to_openai(tool: dict) -> dict:
    schema = tool.get("inputSchema", {})
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }
    }

# --- Streamlit App ---
def main():
    if "initialized" not in st.session_state:
        st.session_state.messages = []
        st.session_state.initialized = True
    
    if "device_type" not in st.session_state:
        st.session_state.device_type = "Device"

    st.title(f"{st.session_state.device_type} Chat Interface")

    st.sidebar.title("Controls")

    testbed_template = """
    devices:
      YOUR_DEVICE_NAME_HERE: # e.g., 'Catalyst L3 Switch'
        type: router
        os: iosxe
        platform: DEVICE_TYPE_HERE # e.g., 'cisco_ios', 'Cat8000v'
        credentials:
          default:
            username: your_username
            password: your_password
        connections:
          cli:
            protocol: ssh
            ip: your_device_ip_or_hostname
    """
    st.sidebar.download_button(
        label="Download Testbed Template",
        data=testbed_template,
        file_name="testbed_template.yaml",
        mime="text/yaml"
    )

    uploaded_file = st.sidebar.file_uploader(
        "Upload Your Testbed File",
        type=["yaml"],
    )

    if uploaded_file is not None:
        if st.session_state.get("current_testbed") != uploaded_file.name:
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.current_testbed = uploaded_file.name
            st.session_state.messages = []

            testbed = load(uploaded_file.name)
            device_name = list(testbed.devices.keys())[0]
            st.session_state.device_name = device_name
            st.session_state.device_type = testbed.devices[device_name].type.capitalize()

            start_mcp_server(testbed_file=uploaded_file.name)
            st.rerun()
    else:
        st.info("Please upload a testbed file to begin.")
        return

    if st.sidebar.button("Clear Chat and Reset"):
        st.session_state.messages = []
        if "current_testbed" in st.session_state:
            if os.path.exists(st.session_state.current_testbed):
                os.remove(st.session_state.current_testbed)
            del st.session_state["current_testbed"]
        if "device_name" in st.session_state:
            del st.session_state["device_name"]
        if "device_type" in st.session_state:
            del st.session_state["device_type"]

        if "mcp_proc" in st.session_state and st.session_state.mcp_proc:
            st.session_state.mcp_proc.terminate()
            st.session_state.mcp_proc.wait()
            del st.session_state["mcp_proc"]

        st.rerun()

    st.sidebar.write(f"Using testbed: `{st.session_state.current_testbed}`")
    st.sidebar.write(f"Device: `{st.session_state.device_name}`")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask the router something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            system_prompt = (
                f"You are a Cisco network automation expert using pyATS. "
                f"You are connected to a device named '{st.session_state.device_name}'. "
                f"When you need to run a command, use this device name. "
                "You can run commands like 'show ip interface brief', apply configurations, etc. "
                "Call the appropriate tool and always use the correct device_name."
            )

            messages_for_api = [{"role": "system", "content": system_prompt}] + st.session_state.messages

            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages_for_api,
                tools=st.session_state.openai_tools,
                tool_choice="auto"
            )
            choice = response.choices[0].message

            if choice.tool_calls:
                fname = choice.tool_calls[0].function.name
                args = json.loads(choice.tool_calls[0].function.arguments)
                with st.spinner(f"Running: `{fname}({args})`..."):
                    tool_result = call_tool(fname, args)
                response_str = tool_result.get('content', [{}])[0].get('text', '{}')
                response_data = json.loads(response_str)

                summary_messages = messages_for_api + [
                    {"role": "assistant", "content": None, "tool_calls": choice.tool_calls},
                    {"role": "tool", "tool_call_id": choice.tool_calls[0].id, "name": fname, "content": json.dumps(response_data)}
                ]
                final_response = client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=summary_messages)
                summary = final_response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": summary})
                st.rerun()
            else:
                st.session_state.messages.append({"role": "assistant", "content": choice.content})
                st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
