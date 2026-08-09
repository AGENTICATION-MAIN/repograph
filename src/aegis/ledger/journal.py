"""
Persistent SQLite and In-Memory Merkle Ledger Journal.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from typing import List, Optional

from aegis.ledger.merkle import MerkleLedger, MerkleRecord

logger = logging.getLogger("aegis.journal")


class LedgerJournal:
    """
    Persistent SQLite storage layer for Merkle Ledger records.
    Maintains a persistent connection for in-memory and file-based databases.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self._conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ledger_records (
                    idx INTEGER PRIMARY KEY,
                    record_id TEXT UNIQUE NOT NULL,
                    timestamp REAL NOT NULL,
                    prev_hash TEXT NOT NULL,
                    intent_id TEXT UNIQUE NOT NULL,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    arguments_hash TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    violations_count INTEGER NOT NULL,
                    leaf_hash TEXT UNIQUE NOT NULL,
                    signature TEXT NOT NULL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_session ON ledger_records(session_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_agent ON ledger_records(agent_id)")
            conn.commit()

    def persist_record(self, record: MerkleRecord) -> None:
        """Saves a record to the persistent SQLite table."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO ledger_records (
                    idx, record_id, timestamp, prev_hash, intent_id, agent_id,
                    session_id, tool_name, arguments_hash, decision, reason,
                    violations_count, leaf_hash, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.index,
                record.record_id,
                record.timestamp,
                record.prev_hash,
                record.intent_id,
                record.agent_id,
                record.session_id,
                record.tool_name,
                record.arguments_hash,
                record.decision,
                record.reason,
                record.violations_count,
                record.leaf_hash,
                record.signature,
            ))
            conn.commit()

    def load_all_records(self) -> List[MerkleRecord]:
        """Loads all records ordered by index."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM ledger_records ORDER BY idx ASC")
            rows = cur.fetchall()

            records = []
            for r in rows:
                rec = MerkleRecord(
                    index=r[0],
                    record_id=r[1],
                    timestamp=r[2],
                    prev_hash=r[3],
                    intent_id=r[4],
                    agent_id=r[5],
                    session_id=r[6],
                    tool_name=r[7],
                    arguments_hash=r[8],
                    decision=r[9],
                    reason=r[10],
                    violations_count=r[11],
                    leaf_hash=r[12],
                    signature=r[13],
                )
                records.append(rec)
            return records

    def close(self) -> None:
        """Closes the underlying SQLite connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
