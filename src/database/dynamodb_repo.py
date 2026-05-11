"""DynamoDB persistence for market intelligence payloads."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key

from src.utils.config import get_settings
from src.utils.logger import AgentLogger

logger = AgentLogger("dynamodb_repo")


# ── Type Conversion Utilities ──────────────────────────────────────────────────

def convert_floats(data: Any) -> Any:
    """
    Recursively sanitizes data for DynamoDB compatibility.
    
    Handles:
    - float → Decimal (for precision)
    - NaN → None (invalid for DynamoDB)
    - Infinity → None (invalid for DynamoDB)
    - -Infinity → None (invalid for DynamoDB)
    
    DynamoDB's number type does not support:
    - IEEE 754 floating point (use Decimal instead)
    - NaN (Not a Number)
    - Infinity values
    
    These commonly appear from:
    - Failed API responses (missing prices)
    - Division by zero (percent_change calculations)
    - Empty pandas DataFrames
    - Aggregation errors in collectors
    
    Args:
        data: Any Python object (dict, list, float, etc.)
    
    Returns:
        The same structure with all floats sanitized and converted
    """
    if isinstance(data, float):
        # Handle invalid float values (NaN, Infinity, -Infinity)
        if math.isnan(data) or math.isinf(data):
            logger.warning(
                "invalid_numeric_value_detected",
                value=str(data),
                type="nan" if math.isnan(data) else "infinity"
            )
            return None
        
        return Decimal(str(data))
    
    elif isinstance(data, dict):
        return {
            key: convert_floats(value)
            for key, value in data.items()
        }
    
    elif isinstance(data, list):
        return [
            convert_floats(item)
            for item in data
        ]
    
    return data


# ── Repository ─────────────────────────────────────────────────────────────────

class DynamoRepository:
    """
    Manages persistence of market intelligence reports and sentiment data to DynamoDB.
    
    Features:
    - Conditional enablement via settings
    - Automatic float → Decimal conversion for numeric compatibility
    - Sanitization of invalid float values (NaN, Infinity)
    - TTL-based expiration for cost optimization
    - Structured keys for efficient querying
    
    Error Handling:
    - Gracefully handles missing data
    - Logs all failures for debugging
    - Continues pipeline if DynamoDB is disabled
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = self.settings.enable_dynamodb
        self.resource = (
            boto3.resource("dynamodb", region_name=self.settings.aws_region)
            if self.enabled
            else None
        )
        logger.info(
            "DynamoDB repository initialized",
            enabled=self.enabled,
            region=self.settings.aws_region if self.enabled else "N/A"
        )

    def save_report(self, report: Dict[str, Any]) -> None:
        """
        Persists a market intelligence report to DynamoDB.
        
        Stores reports with:
        - Partition key: REPORT#{report_type} (for filtering by type)
        - Sort key: TS#{generated_at} (for time-series queries)
        - TTL: 30 days (auto-delete old reports, saves costs)
        - Full payload: nested market data with auto-sanitized numerics
        
        Data Flow:
        1. Accept report dict (may contain NaN/Infinity)
        2. Wrap in DynamoDB item structure
        3. Recursively sanitize all floats
        4. Persist to table
        
        Args:
            report: Dictionary containing report data
                   (must have 'report_type', 'report_id', 'generated_at')
        """
        if not self.enabled or self.resource is None:
            logger.debug("DynamoDB disabled, skipping report save")
            return

        try:
            table = self.resource.Table(self.settings.dynamodb_reports_table)

            item = {
                "pk": f"REPORT#{report['report_type']}",
                "sk": f"TS#{report['generated_at']}",
                "report_id": report["report_id"],
                "payload": report,
                "ttl": int(datetime.now(timezone.utc).timestamp()) + 60 * 60 * 24 * 30,
            }

            # Sanitize all floats (converts NaN/Infinity to None, floats to Decimal)
            clean_item = convert_floats(item)

            table.put_item(Item=clean_item)
            logger.info(
                "report_saved",
                report_id=report["report_id"],
                report_type=report.get("report_type")
            )
        
        except KeyError as exc:
            logger.error(
                "report_missing_required_field",
                missing_field=str(exc),
                report_id=report.get("report_id")
            )
            raise
        
        except Exception as exc:
            logger.error(
                "failed_to_save_report",
                report_id=report.get("report_id"),
                error=str(exc),
                error_type=type(exc).__name__
            )
            raise

    def save_sentiment(self, report_type: str, sentiment: str) -> None:
        """
        Persists sentiment analysis results to DynamoDB.
        
        Stores with:
        - Partition key: SENTIMENT (global for all sentiments)
        - Sort key: ISO timestamp (for time-series analysis)
        - TTL: 90 days (longer retention for trend analysis)
        
        Use Case:
        - Track sentiment trends over 3 months
        - Identify market psychology shifts
        - Correlate sentiment with price movements
        
        Args:
            report_type: Type of report (e.g., "stock", "crypto", "market")
            sentiment: Sentiment classification (e.g., "bullish", "bearish", "neutral")
        """
        if not self.enabled or self.resource is None:
            logger.debug("DynamoDB disabled, skipping sentiment save")
            return

        try:
            table = self.resource.Table(self.settings.dynamodb_sentiment_table)
            now = datetime.now(timezone.utc)

            item = {
                "pk": "SENTIMENT",
                "sk": now.isoformat(),
                "report_type": report_type,
                "sentiment": sentiment,
                "ttl": int(now.timestamp()) + 60 * 60 * 24 * 90,
            }

            table.put_item(Item=item)
            logger.info(
                "sentiment_saved",
                report_type=report_type,
                sentiment=sentiment,
                timestamp=now.isoformat()
            )
        
        except Exception as exc:
            logger.error(
                "failed_to_save_sentiment",
                report_type=report_type,
                sentiment=sentiment,
                error=str(exc),
                error_type=type(exc).__name__
            )
            raise

    def get_latest_report(self, report_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent report of a given type.
        
        Query Strategy:
        - Uses partition key (REPORT#{type}) for efficient lookup
        - Reverse sort order to get newest first
        - Limit 1 for performance
        
        Args:
            report_type: Type of report to retrieve
        
        Returns:
            Report payload if found, None otherwise
        """
        if not self.enabled or self.resource is None:
            logger.debug("DynamoDB disabled, returning None")
            return None

        try:
            table = self.resource.Table(self.settings.dynamodb_reports_table)

            response = table.query(
                KeyConditionExpression=Key("pk").eq(f"REPORT#{report_type}"),
                ScanIndexForward=False,  # Reverse order (newest first)
                Limit=1,
            )
            items = response.get("Items", [])
            
            if items:
                logger.info(
                    "report_retrieved",
                    report_type=report_type,
                    report_id=items[0].get("report_id")
                )
                return items[0]["payload"]
            
            logger.debug("no_report_found", report_type=report_type)
            return None
        
        except Exception as exc:
            logger.error(
                "failed_to_retrieve_report",
                report_type=report_type,
                error=str(exc),
                error_type=type(exc).__name__
            )
            return None

    def get_sentiment_history(
        self,
        report_type: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieves historical sentiment records for analysis.
        
        Use Cases:
        - Detect sentiment trend reversals
        - Correlate sentiment with price movements
        - Build sentiment models
        
        Query Performance:
        - Uses scan (full table) with filter
        - Better approach: use GSI with report_type as partition key
        
        Args:
            report_type: Filter by report type
            limit: Maximum number of records to return
        
        Returns:
            List of sentiment records sorted by timestamp (newest first)
        """
        if not self.enabled or self.resource is None:
            logger.debug("DynamoDB disabled, returning empty list")
            return []

        try:
            table = self.resource.Table(self.settings.dynamodb_sentiment_table)

            response = table.scan(
                FilterExpression=Key("report_type").eq(report_type),
                Limit=limit
            )
            items = response.get("Items", [])
            
            # Sort by timestamp, newest first
            items.sort(
                key=lambda x: x.get("sk", ""),
                reverse=True
            )
            
            logger.info(
                "sentiment_history_retrieved",
                report_type=report_type,
                count=len(items)
            )
            return items
        
        except Exception as exc:
            logger.error(
                "failed_to_retrieve_sentiment_history",
                report_type=report_type,
                error=str(exc),
                error_type=type(exc).__name__
            )
            return []

    def batch_save_reports(self, reports: list[Dict[str, Any]]) -> None:
        """
        Batch saves multiple reports for better throughput.
        
        Performance:
        - Groups writes into batches of 25 (DynamoDB limit)
        - Reduces round-trips vs individual puts
        - ~25x faster for bulk operations
        
        Args:
            reports: List of report dictionaries
        """
        if not self.enabled or self.resource is None:
            logger.debug("DynamoDB disabled, skipping batch save")
            return

        if not reports:
            logger.debug("No reports to batch save")
            return

        try:
            table = self.resource.Table(self.settings.dynamodb_reports_table)
            
            with table.batch_writer(
                batch_size=25,
                overwrite_by_pkeys=["pk", "sk"]
            ) as batch:
                for report in reports:
                    item = {
                        "pk": f"REPORT#{report['report_type']}",
                        "sk": f"TS#{report['generated_at']}",
                        "report_id": report["report_id"],
                        "payload": report,
                        "ttl": int(datetime.now(timezone.utc).timestamp()) + 60 * 60 * 24 * 30,
                    }
                    
                    clean_item = convert_floats(item)
                    batch.put_item(Item=clean_item)
            
            logger.info("batch_reports_saved", count=len(reports))
        
        except Exception as exc:
            logger.error(
                "failed_to_batch_save_reports",
                count=len(reports),
                error=str(exc),
                error_type=type(exc).__name__
            )
            raise