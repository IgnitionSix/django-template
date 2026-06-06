import logging

from background_task import background


logger = logging.getLogger(__name__)


@background()
def example_background_task(email):
    logger.info("Running example background task for %s", email)
