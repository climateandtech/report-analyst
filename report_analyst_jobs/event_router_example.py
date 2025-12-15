"""
Example usage of Event-Action Router

Shows how to use the router with YAML configuration.
"""

import asyncio
import logging

from report_analyst_jobs.event_router import EventRouter

logger = logging.getLogger(__name__)


async def main():
    """Example: Start event router from YAML configuration"""
    # Load router from YAML file (event_routing.yaml)
    router = EventRouter.from_yaml()

    # Or specify custom path
    # router = EventRouter.from_yaml("path/to/custom_routing.yaml")

    # Connect to NATS
    await router.connect()

    # Print routing table for inspection
    print("\nRouting Table:")
    for rule in router.get_routing_table():
        print(f"  {rule['pattern']:30} -> {rule['action']:20} (priority: {rule['priority']})")

    # Start processing events
    print("\nStarting event router...")
    await router.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
