
import argparse
import asyncio
import uvicorn
from dotenv import load_dotenv

load_dotenv()  # Load .env before any settings are initialised

from src.scheduler.orchestrator import ReportOrchestrator


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--api", action="store_true")
    parser.add_argument("--pipeline", action="store_true")

    args = parser.parse_args()

    if args.api:
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )

    elif args.pipeline:
        orchestrator = ReportOrchestrator()

        asyncio.run(
            orchestrator.run(report_type="closing")  # valid: pre_market | midday | closing | deep_analysis
        )

    else:
        print("Use --api or --pipeline")


if __name__ == "__main__":
    main()