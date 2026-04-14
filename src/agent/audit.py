"""Structured audit logger — records every tool call with its inputs and output summary."""

import json
import logging
from datetime import datetime, timezone

_logger = logging.getLogger("logistics.audit")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [AUDIT] %(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


class AuditLogger:
    def log_tool_call(
        self,
        *,
        session_id: str,
        tool_name: str,
        inputs: dict,
        output_summary: str,
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "tool": tool_name,
            "inputs": inputs,
            "output_summary": output_summary[:500],
        }
        _logger.info(json.dumps(record, ensure_ascii=False))
