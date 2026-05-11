import asyncio

from src.scheduler.orchestrator import ReportOrchestrator


async def main():

    orchestrator = ReportOrchestrator()

    result = await orchestrator.run(
        report_type="closing"
    )

    return result


def lambda_handler(event, context):

    try:

        result = asyncio.run(main())

        return {
            "statusCode": 200,
            "body": result
        }

    except Exception as e:

        return {
            "statusCode": 500,
            "body": str(e)
        }