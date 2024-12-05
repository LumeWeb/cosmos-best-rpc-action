import asyncio
from dataclasses import dataclass
from typing import List, Optional
import aiohttp
import time

@dataclass
class NodeStatus:
    url: str
    latency: float
    block_height: int
    catching_up: bool
    error: Optional[str] = None

class RPCTester:
    def __init__(self, timeout: int = 5, max_block_lag: int = 10):
        self.timeout = timeout
        self.max_block_lag = max_block_lag

    async def test_node(self, session: aiohttp.ClientSession, url: str) -> NodeStatus:
        """Test a single RPC node."""
        start_time = time.monotonic()
        try:
            async with session.get(f"{url}/status", timeout=self.timeout) as response:
                if response.status != 200:
                    return NodeStatus(url=url, latency=999999, block_height=0,
                                   catching_up=True, error="Non-200 response")

                data = await response.json()
                end_time = time.monotonic()
                latency = (end_time - start_time) * 1000  # Convert to ms

                sync_info = data.get("result", {}).get("sync_info", {})
                block_height = int(sync_info.get("latest_block_height", 0))
                catching_up = sync_info.get("catching_up", True)

                return NodeStatus(
                    url=url,
                    latency=latency,
                    block_height=block_height,
                    catching_up=catching_up
                )

        except Exception as e:
            return NodeStatus(url=url, latency=999999, block_height=0,
                            catching_up=True, error=str(e))

    async def test_nodes(self, nodes: List[str]) -> Optional[NodeStatus]:
        """Test all nodes and return the best one."""
        async with aiohttp.ClientSession() as session:
            # Test all nodes concurrently
            tasks = [self.test_node(session, node) for node in nodes]
            results = await asyncio.gather(*tasks)

            # Filter out failed nodes
            valid_nodes = [r for r in results if not r.error]
            if not valid_nodes:
                return None

            # Find highest block height
            max_height = max(n.block_height for n in valid_nodes)
            min_acceptable_height = max_height - self.max_block_lag

            # Filter nodes by block height and sync status
            candidates = [
                n for n in valid_nodes
                if n.block_height >= min_acceptable_height and not n.catching_up
            ]

            if not candidates:
                return None

            # Return the node with lowest latency
            return min(candidates, key=lambda x: x.latency)