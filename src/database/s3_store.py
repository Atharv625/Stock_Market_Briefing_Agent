"""S3 archival store for report JSON snapshots."""

from __future__ import annotations

import json
from typing import Any, Dict

import boto3

from src.utils.config import get_settings


class S3ArchiveStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = boto3.client("s3", region_name=self.settings.aws_region)

    def put_report(self, report: Dict[str, Any]) -> str:
        report_id = report["report_id"]
        key = f"reports/{report['report_type']}/{report_id}.json"
        self.client.put_object(
            Bucket=self.settings.s3_cache_bucket,
            Key=key,
            Body=json.dumps(report, default=str).encode("utf-8"),
            ContentType="application/json",
        )
        return key
