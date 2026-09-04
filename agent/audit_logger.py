"""
Cryptographically Verifiable, Immutable Audit Trail & Decision Logger.
Maintains full chain-of-custody for all financial and communication actions.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


class AuditLogger:
    def __init__(self, log_file_path: Optional[str] = None):
        if log_file_path:
            self.file_path = Path(log_file_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            self.file_path = base_dir / "logs" / "audit_trail.jsonl"
            
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_hash = "0" * 64
        self.in_memory_records: List[Dict[str, Any]] = []
        
        # If audit file exists, seed last_hash from the last recorded line
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                    if lines:
                        last_line_data = json.loads(lines[-1])
                        if "entry_hash" in last_line_data:
                            self.last_hash = last_line_data["entry_hash"]
            except Exception as e:
                logger.warning("Could not read previous hash from %s: %s", self.file_path, e)

    def record_decision(
        self,
        member_id: str,
        trigger_signal: str,
        diagnostics: Dict[str, Any],
        guardrail_verdict: str,
        guardrail_notes: List[str],
        action_executed: Dict[str, Any],
        outcome_status: str
    ) -> Dict[str, Any]:
        """
        Appends an immutable audit event with chained SHA-256 hash.
        """
        # Always synchronize last_hash with disk tip
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                    if lines:
                        last_line_data = json.loads(lines[-1])
                        if "entry_hash" in last_line_data:
                            self.last_hash = last_line_data["entry_hash"]
            except Exception:
                pass

        timestamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        
        entry_payload = {
            "timestamp": timestamp,
            "member_id": member_id,
            "trigger_signal": trigger_signal,
            "diagnostics": diagnostics,
            "guardrail_verdict": guardrail_verdict,
            "guardrail_notes": guardrail_notes,
            "action_executed": action_executed,
            "outcome_status": outcome_status,
            "previous_hash": self.last_hash
        }

        # Calculate cryptographic hash of current entry
        serialized = json.dumps(entry_payload, sort_keys=True)
        current_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        entry_payload["entry_hash"] = current_hash
        self.last_hash = current_hash

        # Write to disk
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry_payload) + "\n")

        self.in_memory_records.append(entry_payload)
        logger.info("Recorded audit entry for member_id=%s [hash=%s]", member_id, current_hash[:12])
        return entry_payload

    def get_recent_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.in_memory_records[-limit:]

    def verify_integrity(self) -> bool:
        """
        Verifies cryptographic integrity of the entire audit chain.
        """
        if not self.file_path.exists():
            return True

        prev = "0" * 64
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                if not line.strip():
                    continue
                data = json.loads(line)
                stored_hash = data.pop("entry_hash", None)
                data_prev_hash = data.get("previous_hash")
                
                if data_prev_hash != prev:
                    logger.error("Audit chain broken at line %d: previous hash mismatch!", line_idx)
                    return False

                recomputed = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
                if recomputed != stored_hash:
                    logger.error("Audit integrity violation at line %d: content corrupted!", line_idx)
                    return False
                prev = stored_hash

        return True
