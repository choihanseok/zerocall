import json
import logging
from datetime import UTC, datetime


class SafeJsonFormatter(logging.Formatter):
    def format(self, record):
        # Only explicitly allowlisted metadata is logged, never exception/request payloads.
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "event": getattr(record, "event", "application"),
                "traceId": getattr(record, "trace_id", None),
                "environment": getattr(record, "environment", None),
                "status": getattr(record, "status", None),
                "accountId": getattr(record, "account_id", None),
            },
            ensure_ascii=False,
        )


def get_logger():
    logger = logging.getLogger("zerocall")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeJsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
