import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import ipaddress as ipaddr
from mcp.server.fastmcp import FastMCP

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SubnetFastMCPServer")

# --- Load Environment Variables ---
load_dotenv()

# --- Pydantic Model for Input Validation ---
class SubnetInput(BaseModel):
    cidr: str = Field(..., description="Network in CIDR notation, e.g. 192.168.1.0/24")

# --- Initialize FastMCP ---
mcp = FastMCP("Subnet Calculator MCP")

# --- Define the subnet_calculator tool ---
@mcp.tool(
    name="subnet_calculator",
    description="Calculate network details plus previous and next subnets"
)
async def subnet_calculator(cidr: str) -> dict:
    """
    Calculates network address, broadcast address, usable hosts, prefix length,
    and previous/next subnets of the same size.

    Args:
        cidr: Network in CIDR notation (e.g., '192.168.1.0/24')

    Returns:
        JSON-formatted string containing all subnet details
    """
    logger.info("🚀 Tool triggered with CIDR: %s", cidr)
    try:
        network = ipaddr.IPv4Network(cidr, strict=False)
        size = network.num_addresses 
        base = int(network.network_address)

        prev_sub = ipaddr.IPv4Network(f"{ipaddr.IPv4Address(base - size)}/{network.prefixlen}")
        next_sub = ipaddr.IPv4Network(f"{ipaddr.IPv4Address(base + size)}/{network.prefixlen}")

        MAX_HOST_PREVIEW = 10  # Safety net: limit number of hosts shown

        usable_hosts = [
            str(ip)
            for i, ip in enumerate(network)
            if ip not in (network.network_address, network.broadcast_address) and i < MAX_HOST_PREVIEW + 1
        ]

        result = {
            # Core network details
            "network_address": str(network.network_address),
            "broadcast_address": str(network.broadcast_address),
            "netmask": str(network.netmask),
            "wildcard_mask": str(network.hostmask),
            "prefix_length": network.prefixlen,
            "with_netmask": str(network.with_netmask),
            "with_hostmask": str(network.with_hostmask),

            # Address count and ranges
            "num_addresses": network.num_addresses,
            "usable_hosts_count": max(0, network.num_addresses - 2),
            "usable_hosts_preview": usable_hosts,
            "first_usable": (str(list(network)[1]) if network.num_addresses >= 2 else None),
            "last_usable": (str(list(network)[-2]) if network.num_addresses >= 2 else None),
            "address_range": (
                f"{list(network)[1]} - {list(network)[-2]}" 
                if network.num_addresses >= 2 else "N/A"
            ),

            # Subnet navigation
            "previous_subnet": str(prev_sub),
            "next_subnet": str(next_sub),

            # Binary & host info
            "host_bits": 32 - network.prefixlen,
            "total_bits": 32,

            # Boolean flags
            "is_private": network.is_private,
            "is_global": network.is_global,
            "is_link_local": network.is_link_local,
            "is_multicast": network.is_multicast,
            "is_loopback": network.is_loopback,
            "is_reserved": network.is_reserved,
            "is_unspecified": network.is_unspecified,

            # Optional enhancements
            "summary": f"CIDR {cidr} has {network.num_addresses} total addresses "
                       f"with {max(0, network.num_addresses - 2)} usable hosts "
                       f"({network.prefixlen} prefix, {32 - network.prefixlen} host bits).",
            "note": f"Showing first {MAX_HOST_PREVIEW} usable hosts only (capped for large subnets)."
        }

        logger.info(f"Calculated result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in subnet_calculator tool: {e}", exc_info=True)
        return {"error": str(e)}
    
# --- Main entrypoint ---
if __name__ == "__main__":
    logger.info(f"Starting Subnet Calculator MCP in stdio mode")
    # Use stdio transport instead of HTTP
    mcp.run(transport="stdio")