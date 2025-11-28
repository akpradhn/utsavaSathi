"""
Agent Session Management with SQLite Persistence

Manages agent sessions, storing conversation history and session metadata
in a SQLite database for persistence across requests.
"""

from __future__ import annotations

import sqlite3
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages agent sessions with SQLite persistence.
    
    Stores session metadata, conversation history, and allows retrieval
    of past conversations for context-aware agent interactions.
    """
    
    def __init__(self, db_path: str | Path = "agent_sessions.db"):
        """
        Initialize SessionManager with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()
        logger.info(f"SESSION_MANAGER_INITIALIZED: Database at {self.db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    agent_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
                    UNIQUE(session_id, turn_number, role)
                )
            """)
            
            # Users table (optional, for multi-user support)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
                ON sessions(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_status 
                ON sessions(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_session_id 
                ON conversation_history(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_timestamp 
                ON conversation_history(timestamp)
            """)
            
            conn.commit()
            logger.debug("DATABASE_TABLES_CREATED: Sessions, conversation_history, and users tables initialized")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"DATABASE_ERROR: {e}")
            raise
        finally:
            conn.close()
    
    def create_session(
        self,
        user_id: Optional[str] = None,
        agent_name: str = "utsava_sathi",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new agent session.
        
        Args:
            user_id: Optional user identifier
            agent_name: Name of the agent for this session
            metadata: Optional metadata dictionary
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, agent_name, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, user_id, agent_name, metadata_json))
            conn.commit()
        
        logger.info(f"SESSION_CREATED: session_id={session_id}, user_id={user_id}, agent={agent_name}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dictionary or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            
            if row:
                session = dict(row)
                if session.get('metadata'):
                    try:
                        session['metadata'] = json.loads(session['metadata'])
                    except:
                        pass
                return session
        return None
    
    def update_session(
        self,
        session_id: str,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update session information.
        
        Args:
            session_id: Session identifier
            status: New status (e.g., 'active', 'completed', 'archived')
            metadata: Updated metadata dictionary
        """
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
        
        if metadata:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(session_id)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE sessions 
                    SET {', '.join(updates)}
                    WHERE session_id = ?
                """, params)
                conn.commit()
            
            logger.debug(f"SESSION_UPDATED: session_id={session_id}")
    
    def add_conversation_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        turn_number: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a conversation turn to the session history.
        
        Args:
            session_id: Session identifier
            role: Role of the speaker ('user' or 'assistant')
            content: Message content
            turn_number: Optional turn number (auto-incremented if not provided)
            metadata: Optional metadata dictionary
            
        Returns:
            turn_number: The turn number assigned
        """
        if turn_number is None:
            # Get the next turn number
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COALESCE(MAX(turn_number), 0) + 1 
                    FROM conversation_history 
                    WHERE session_id = ?
                """, (session_id,))
                turn_number = cursor.fetchone()[0]
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO conversation_history 
                (session_id, turn_number, role, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, turn_number, role, content, metadata_json))
            conn.commit()
        
        # Update session timestamp
        self.update_session(session_id)
        
        logger.debug(f"CONVERSATION_TURN_ADDED: session_id={session_id}, turn={turn_number}, role={role}")
        return turn_number
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        before_turn: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of turns to retrieve
            before_turn: Only retrieve turns before this number
            
        Returns:
            List of conversation turns ordered by turn_number
        """
        query = """
            SELECT * FROM conversation_history 
            WHERE session_id = ?
        """
        params = [session_id]
        
        if before_turn:
            query += " AND turn_number < ?"
            params.append(before_turn)
        
        query += " ORDER BY turn_number ASC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                turn = dict(row)
                if turn.get('metadata'):
                    try:
                        turn['metadata'] = json.loads(turn['metadata'])
                    except:
                        pass
                history.append(turn)
        
        return history
    
    def get_sessions_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            status: Filter by status (optional)
            limit: Maximum number of sessions to retrieve
            
        Returns:
            List of session dictionaries
        """
        query = "SELECT * FROM sessions WHERE user_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                session = dict(row)
                if session.get('metadata'):
                    try:
                        session['metadata'] = json.loads(session['metadata'])
                    except:
                        pass
                sessions.append(session)
        
        return sessions
    
    def close_session(self, session_id: str):
        """
        Close a session by setting status to 'completed'.
        
        Args:
            session_id: Session identifier
        """
        self.update_session(session_id, status='completed')
        logger.info(f"SESSION_CLOSED: session_id={session_id}")
    
    def delete_session(self, session_id: str):
        """
        Delete a session and all its conversation history.
        
        Args:
            session_id: Session identifier
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        
        logger.info(f"SESSION_DELETED: session_id={session_id}")


# Import json at module level
import json




