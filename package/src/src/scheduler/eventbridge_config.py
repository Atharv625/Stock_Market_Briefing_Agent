"""EventBridge schedule metadata."""

SCHEDULES = {
    "pre_market": "cron(30 2 ? * MON-FRI *)",
    "midday": "cron(30 7 ? * MON-FRI *)",
    "closing": "cron(30 10 ? * MON-FRI *)",
    "deep_analysis": "cron(30 14 ? * MON-FRI *)",
}
