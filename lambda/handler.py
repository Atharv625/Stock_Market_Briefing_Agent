"""Lambda entrypoint compatibility wrapper."""

from src.scheduler.lambda_handlers import scheduled_report_handler


def handler(event, context):
    return scheduled_report_handler(event, context)
