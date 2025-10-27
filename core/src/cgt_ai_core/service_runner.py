import asyncio
import logging

from cgt_ai_core.service import Service

LOGGER = logging.getLogger(__name__)


async def run_service(service: Service):
    try:
        await service.run()
    except asyncio.CancelledError as exc:
        LOGGER.exception('Run cancelled', exc_info=exc)
    except Exception as exc:
        LOGGER.exception('Unhandled exception', exc_info=exc)
    finally:
        await service.stop()
