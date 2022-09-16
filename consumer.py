import asyncio
from curses.ascii import ACK
from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN

async def run(loop):
    # Use borrowed connection for NATS then mount NATS Streaming
    # client on top.
    nc = NATS()
    await nc.connect()

    # Start session with NATS Streaming cluster.
    sc = STAN()
    await sc.connect("test-cluster", "client", nats=nc, loop=loop)

    # Synchronous Publisher, does not return until an ack
    # has been received from NATS Streaming.

    total_messages = 0
    future = asyncio.Future(loop=loop)
    async def cb(msg):
        nonlocal future
        nonlocal total_messages
        print("Received a message (seq={}): {}".format(msg.seq, msg.data))
        msg.ack()
        total_messages += 1

    # Subscribe to get all messages since beginning.
    sub = await sc.subscribe("poc.public.test_table", cb=cb, start_at='last_received')
    await asyncio.wait_for(future,timeout=None, loop=loop)

    # Stop receiving messages
    await sub.unsubscribe()

    # Close NATS Streaming session
    await sc.close()

    # We are using a NATS borrowed connection so we need to close manually.
    await nc.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()