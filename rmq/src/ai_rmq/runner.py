import asyncio

from typing import Any, Coroutine


def run_service(main: Coroutine[Any, Any, Any]) -> Any:
    # Pika's asyncio adapter relies on add_reader/add_writer, which Windows' default ProactorEventLoop doesn't support.
    # Pika <1.4 silently switched the global event loop policy to a selector loop on import; 1.4+ requires the caller
    # to choose one explicitly. SelectorEventLoop is already the default on other platforms, so this is a no-op there.
    return asyncio.run(main, loop_factory=asyncio.SelectorEventLoop)
