"""
Agent Memory Management with SQLite Persistence

Manages long-term and short-term memory for agents, storing facts,
context, and learned information in a SQLite database.
"""

from __future__ import annotations

import sqlite3
import logging
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages agent memory with SQLite persistence.
    
    Stores both short-term (session-specific) and long-term (cross-session)
    memory, allowing agents to recall information across interactions.
    """
    
    def __init__(self, db_path: str | Path = "agent_memory.db"):
        """
        Initialize MemoryManager with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()
        logger.info(f"MEMORY_MANAGER_INITIALIZED: Database at {self.db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Long-term memory table (facts, learned information)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    session_id TEXT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    memory_type TEXT DEFAULT 'fact',
                    importance REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    expires_at TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
                )
            """)
            
            # Short-term memory table (session context, recent events)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS short_term_memory (
                    memory_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    memory_type TEXT DEFAULT 'context',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            # Memory associations (for linking related memories)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id_1 TEXT NOT NULL,
                    memory_id_2 TEXT NOT NULL,
                    association_type TEXT DEFAULT 'related',
                    strength REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (memory_id_1) REFERENCES long_term_memory(memory_id) ON DELETE CASCADE,
                    FOREIGN KEY (memory_id_2) REFERENCES long_term_memory(memory_id) ON DELETE CASCADE,
                    UNIQUE(memory_id_1, memory_id_2)
                )
            """)
            
            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ltm_user_id 
                ON long_term_memory(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ltm_session_id 
                ON long_term_memory(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ltm_key 
                ON long_term_memory(key)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ltm_type 
                ON long_term_memory(memory_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stm_session_id 
                ON short_term_memory(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stm_expires 
                ON short_term_memory(expires_at)
            """)
            
            conn.commit()
            logger.debug("DATABASE_TABLES_CREATED: Memory tables initialized")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"DATABASE_ERROR: {e}")
            raise
        finally:
            conn.close()
    
    def store_long_term_memory(
        self,
        key: str,
        value: Any,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_type: str = "fact",
        importance: float = 0.5,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store information in long-term memory.
        
        Args:
            key: Memory key/identifier
            value: Memory value (will be JSON-serialized)
            user_id: Optional user identifier
            session_id: Optional session identifier
            memory_type: Type of memory ('fact', 'preference', 'skill', etc.)
            importance: Importance score (0.0 to 1.0)
            expires_at: Optional expiration datetime
            metadata: Optional metadata dictionary
            
        Returns:
            memory_id: Unique memory identifier
        """
        memory_id = str(uuid.uuid4())
        value_json = json.dumps(value) if not isinstance(value, str) else value
        metadata_json = json.dumps(metadata) if metadata else None
        expires_str = expires_at.isoformat() if expires_at else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO long_term_memory 
                (memory_id, user_id, session_id, key, value, memory_type, 
                 importance, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (memory_id, user_id, session_id, key, value_json, 
                  memory_type, importance, expires_str, metadata_json))
            conn.commit()
        
        logger.debug(f"LONG_TERM_MEMORY_STORED: memory_id={memory_id}, key={key}, type={memory_type}")
        return memory_id
    
    def retrieve_long_term_memory(
        self,
        key: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories from long-term storage.
        
        Args:
            key: Filter by key (optional)
            user_id: Filter by user (optional)
            session_id: Filter by session (optional)
            memory_type: Filter by type (optional)
            min_importance: Minimum importance score
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memory dictionaries
        """
        query = "SELECT * FROM long_term_memory WHERE 1=1"
        params = []
        
        if key:
            query += " AND key = ?"
            params.append(key)
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        if session_id:
            query += " AND (session_id = ? OR session_id IS NULL)"
            params.append(session_id)
        
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)
        
        query += " AND importance >= ?"
        params.append(min_importance)
        
        query += " AND (expires_at IS NULL OR expires_at > datetime('now'))"
        
        query += " ORDER BY importance DESC, accessed_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory = dict(row)
                # Update access tracking
                cursor.execute("""
                    UPDATE long_term_memory 
                    SET accessed_at = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE memory_id = ?
                """, (memory['memory_id'],))
                
                # Parse JSON values
                try:
                    memory['value'] = json.loads(memory['value'])
                except:
                    pass
                
                if memory.get('metadata'):
                    try:
                        memory['metadata'] = json.loads(memory['metadata'])
                    except:
                        pass
                
                memories.append(memory)
            
            conn.commit()
        
        return memories
    
    def store_short_term_memory(
        self,
        session_id: str,
        key: str,
        value: Any,
        memory_type: str = "context",
        ttl_hours: Optional[float] = 24.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store information in short-term memory (session-specific).
        
        Args:
            session_id: Session identifier
            key: Memory key
            value: Memory value (will be JSON-serialized)
            memory_type: Type of memory ('context', 'event', 'state', etc.)
            ttl_hours: Time-to-live in hours (default 24)
            metadata: Optional metadata dictionary
            
        Returns:
            memory_id: Unique memory identifier
        """
        memory_id = str(uuid.uuid4())
        value_json = json.dumps(value) if not isinstance(value, str) else value
        metadata_json = json.dumps(metadata) if metadata else None
        
        expires_at = None
        if ttl_hours:
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        expires_str = expires_at.isoformat() if expires_at else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO short_term_memory 
                (memory_id, session_id, key, value, memory_type, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (memory_id, session_id, key, value_json, memory_type, 
                  expires_str, metadata_json))
            conn.commit()
        
        logger.debug(f"SHORT_TERM_MEMORY_STORED: memory_id={memory_id}, session_id={session_id}, key={key}")
        return memory_id
    
    def retrieve_short_term_memory(
        self,
        session_id: str,
        key: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories from short-term storage.
        
        Args:
            session_id: Session identifier
            key: Filter by key (optional)
            memory_type: Filter by type (optional)
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memory dictionaries
        """
        query = """
            SELECT * FROM short_term_memory 
            WHERE session_id = ?
            AND (expires_at IS NULL OR expires_at > datetime('now'))
        """
        params = [session_id]
        
        if key:
            query += " AND key = ?"
            params.append(key)
        
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory = dict(row)
                
                # Parse JSON values
                try:
                    memory['value'] = json.loads(memory['value'])
                except:
                    pass
                
                if memory.get('metadata'):
                    try:
                        memory['metadata'] = json.loads(memory['metadata'])
                    except:
                        pass
                
                memories.append(memory)
        
        return memories
    
    def associate_memories(
        self,
        memory_id_1: str,
        memory_id_2: str,
        association_type: str = "related",
        strength: float = 0.5
    ):
        """
        Create an association between two memories.
        
        Args:
            memory_id_1: First memory identifier
            memory_id_2: Second memory identifier
            association_type: Type of association ('related', 'causes', 'similar', etc.)
            strength: Association strength (0.0 to 1.0)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO memory_associations 
                (memory_id_1, memory_id_2, association_type, strength)
                VALUES (?, ?, ?, ?)
            """, (memory_id_1, memory_id_2, association_type, strength))
            conn.commit()
        
        logger.debug(f"MEMORY_ASSOCIATION_CREATED: {memory_id_1} <-> {memory_id_2}")
    
    def get_associated_memories(
        self,
        memory_id: str,
        association_type: Optional[str] = None,
        min_strength: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get memories associated with a given memory.
        
        Args:
            memory_id: Memory identifier
            association_type: Filter by association type (optional)
            min_strength: Minimum association strength
            
        Returns:
            List of associated memories
        """
        query = """
            SELECT m.*, a.association_type, a.strength
            FROM long_term_memory m
            JOIN memory_associations a ON (
                (a.memory_id_1 = ? AND a.memory_id_2 = m.memory_id) OR
                (a.memory_id_2 = ? AND a.memory_id_1 = m.memory_id)
            )
            WHERE a.strength >= ?
        """
        params = [memory_id, memory_id, min_strength]
        
        if association_type:
            query += " AND a.association_type = ?"
            params.append(association_type)
        
        query += " ORDER BY a.strength DESC"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory = dict(row)
                try:
                    memory['value'] = json.loads(memory['value'])
                except:
                    pass
                memories.append(memory)
        
        return memories
    
    def cleanup_expired_memories(self):
        """Remove expired short-term memories."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM short_term_memory 
                WHERE expires_at IS NOT NULL 
                AND expires_at <= datetime('now')
            """)
            deleted = cursor.rowcount
            conn.commit()
        
        if deleted > 0:
            logger.info(f"EXPIRED_MEMORIES_CLEANED: {deleted} short-term memories removed")
    
    def update_memory_importance(
        self,
        memory_id: str,
        importance: float
    ):
        """
        Update the importance score of a memory.
        
        Args:
            memory_id: Memory identifier
            importance: New importance score (0.0 to 1.0)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE long_term_memory 
                SET importance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE memory_id = ?
            """, (importance, memory_id))
            conn.commit()
        
        logger.debug(f"MEMORY_IMPORTANCE_UPDATED: memory_id={memory_id}, importance={importance}")




