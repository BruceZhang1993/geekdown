import asyncio

from geekdown.commands import Command


async def main():
    await Command.init().run()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
