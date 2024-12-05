import os
import sys
import asyncio
import aiohttp
from rpc_tester import RPCTester

async def fetch_nodes(url: str) -> list[str]:
    """Fetch list of nodes from URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to fetch nodes list: {response.status}")
            text = await response.text()
            return [line.strip() for line in text.split('\n') if line.strip()]

def write_output(key: str, value: str):
    """Write to GITHUB_OUTPUT environment file."""
    output_file = os.getenv('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"{key}={value}\n")

async def main():
    # Get inputs
    nodes_url = os.getenv('INPUT_NODES_URL')
    timeout = int(os.getenv('INPUT_TIMEOUT', '5'))
    max_block_lag = int(os.getenv('INPUT_MAX_BLOCK_LAG', '10'))

    if not nodes_url:
        print("Error: nodes-url input is required")
        sys.exit(1)

    try:
        # Fetch nodes list
        nodes = await fetch_nodes(nodes_url)
        if not nodes:
            print("Error: No nodes found in the provided URL")
            sys.exit(1)

        # Test nodes
        tester = RPCTester(timeout=timeout, max_block_lag=max_block_lag)
        best_node = await tester.test_nodes(nodes)

        if not best_node:
            print("Error: No suitable nodes found")
            sys.exit(1)

        # Write outputs
        write_output('best-node', best_node.url)
        write_output('latency', str(int(best_node.latency)))
        write_output('block-height', str(best_node.block_height))

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())