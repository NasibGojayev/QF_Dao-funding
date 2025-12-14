from django.shortcuts import render

import logging
logger = logging.getLogger(__name__)

def my_view(request):
    logger.info("View accessed by user")
    logger.debug("Debug info")
    logger.error("Something went wrong!")
