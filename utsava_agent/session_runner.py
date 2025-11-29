"""
Custom Runner with Session and Memory Management

Extends ADK's InMemoryRunner to integrate session and memory persistence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, List
from google.adk.runners import InMemoryRunner
from google.adk.agents import Agent

from utsava_agent.session_manager import SessionManager
from utsava_agent.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class SessionRunner:
    """
    Runner that integrates session and memory management with ADK agents.
    
    Wraps InMemoryRunner and adds:
    - Session persistence (conversation history)
    - Memory management (short-term and long-term)
    - Context retrieval for agent interactions
    """
    
    def __init__(
        self,
        agent: Agent,
        session_manager: Optional[SessionManager] = None,
        memory_manager: Optional[MemoryManager] = None,
        app_name: str = "utsava_agent",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize SessionRunner.
        
        Args:
            agent: ADK Agent to run
            session_manager: Optional SessionManager instance
            memory_manager: Optional MemoryManager instance
            app_name: Application name for ADK
            session_id: Optional existing session ID
            user_id: Optional user identifier
        """
        self.agent = agent
        self.app_name = app_name
        self.user_id = user_id
        
        # Initialize managers
        self.session_manager = session_manager or SessionManager()
        self.memory_manager = memory_manager or MemoryManager()
        
        # Session handling
        if session_id:
            self.session_id = session_id
            session = self.session_manager.get_session(session_id)
            if not session:
                logger.warning(f"SESSION_NOT_FOUND: Creating new session with provided ID {session_id}")
                self.session_id = self.session_manager.create_session(
                    user_id=user_id,
                    agent_name=agent.name,
                    metadata={"app_name": app_name}
                )
        else:
            self.session_id = self.session_manager.create_session(
                user_id=user_id,
                agent_name=agent.name,
                metadata={"app_name": app_name}
            )
        
        # Create underlying ADK runner
        self.runner = InMemoryRunner(agent=agent, app_name=app_name)
        
        logger.info(
            f"SESSION_RUNNER_INITIALIZED: session_id={self.session_id}, "
            f"user_id={user_id}, agent={agent.name}"
        )
    
    async def run(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with session and memory context.
        
        Args:
            prompt: User prompt
            context: Optional additional context
            
        Returns:
            Dictionary with response and metadata
        """
        # Retrieve relevant memories
        short_term_memories = self.memory_manager.retrieve_short_term_memory(
            session_id=self.session_id,
            limit=10
        )
        
        long_term_memories = []
        if self.user_id:
            long_term_memories = self.memory_manager.retrieve_long_term_memory(
                user_id=self.user_id,
                limit=5
            )
        
        # Retrieve conversation history
        conversation_history = self.session_manager.get_conversation_history(
            session_id=self.session_id,
            limit=10
        )
        
        # Build enhanced prompt with context
        enhanced_prompt = self._build_enhanced_prompt(
            prompt=prompt,
            conversation_history=conversation_history,
            short_term_memories=short_term_memories,
            long_term_memories=long_term_memories,
            context=context
        )
        
        # Store user message in conversation history
        turn_number = self.session_manager.add_conversation_turn(
            session_id=self.session_id,
            role="user",
            content=prompt,
            metadata={"context": context}
        )
        
        # Run the agent
        logger.debug(f"AGENT_RUN_START: session_id={self.session_id}, turn={turn_number}")
        events = await self.runner.run_debug(enhanced_prompt)
        
        # Extract response
        response_text = self._extract_response(events)
        
        # Store assistant response in conversation history
        self.session_manager.add_conversation_turn(
            session_id=self.session_id,
            role="assistant",
            content=response_text,
            turn_number=turn_number + 1,
            metadata={"events_count": len(events)}
        )
        
        # Store in short-term memory (recent interaction)
        self.memory_manager.store_short_term_memory(
            session_id=self.session_id,
            key=f"turn_{turn_number}",
            value={
                "user_prompt": prompt,
                "assistant_response": response_text,
                "turn_number": turn_number
            },
            memory_type="interaction",
            ttl_hours=24.0
        )
        
        logger.info(f"AGENT_RUN_COMPLETE: session_id={self.session_id}, turn={turn_number}")
        
        return {
            "response": response_text,
            "session_id": self.session_id,
            "turn_number": turn_number + 1,
            "events": events,
            "memories_used": {
                "short_term": len(short_term_memories),
                "long_term": len(long_term_memories)
            }
        }
    
    def _build_enhanced_prompt(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        short_term_memories: List[Dict[str, Any]],
        long_term_memories: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build an enhanced prompt with conversation history and memory context.
        
        Args:
            prompt: Original user prompt
            conversation_history: Previous conversation turns
            short_term_memories: Session-specific memories
            long_term_memories: Cross-session memories
            context: Additional context
            
        Returns:
            Enhanced prompt string
        """
        parts = []
        
        # Add conversation history if available
        if conversation_history:
            parts.append("=== Previous Conversation ===")
            for turn in conversation_history[-5:]:  # Last 5 turns
                role = turn.get('role', 'unknown')
                content = turn.get('content', '')
                parts.append(f"{role.capitalize()}: {content}")
            parts.append("")
        
        # Add long-term memories if available
        if long_term_memories:
            parts.append("=== Relevant Context ===")
            for memory in long_term_memories:
                key = memory.get('key', '')
                value = memory.get('value', '')
                if isinstance(value, dict):
                    value = str(value)
                parts.append(f"- {key}: {value}")
            parts.append("")
        
        # Add short-term memories if available
        if short_term_memories:
            parts.append("=== Recent Session Context ===")
            for memory in short_term_memories[:3]:  # Top 3 recent
                key = memory.get('key', '')
                value = memory.get('value', '')
                if isinstance(value, dict):
                    value = str(value)
                parts.append(f"- {key}: {value}")
            parts.append("")
        
        # Add additional context if provided
        if context:
            parts.append("=== Additional Context ===")
            for key, value in context.items():
                parts.append(f"- {key}: {value}")
            parts.append("")
        
        # Add the current prompt
        parts.append("=== Current Request ===")
        parts.append(prompt)
        
        return "\n".join(parts)
    
    def _extract_response(self, events: List[Any]) -> str:
        """
        Extract response text from ADK events.
        
        Args:
            events: List of ADK events
            
        Returns:
            Response text
        """
        response_text = ""
        
        for ev in reversed(events):
            # Try content.parts[0].text (most common in ADK)
            content = getattr(ev, "content", None)
            if content:
                try:
                    parts = getattr(content, "parts", None)
                    if parts:
                        if hasattr(parts, "__iter__") and not isinstance(parts, str):
                            parts_list = list(parts)
                        else:
                            parts_list = [parts]
                        
                        for part in parts_list:
                            part_text = getattr(part, "text", None)
                            if isinstance(part_text, str) and part_text.strip():
                                response_text = part_text.strip()
                                break
                        if response_text:
                            break
                except (AttributeError, TypeError, IndexError):
                    pass
            
            # Try direct text attributes
            if not response_text:
                text = (
                    getattr(ev, "output_text", None) or
                    getattr(ev, "output", None) or
                    getattr(ev, "text", None)
                )
                if isinstance(text, str) and text.strip():
                    response_text = text.strip()
                    break
        
        return response_text
    
    def store_memory(
        self,
        key: str,
        value: Any,
        memory_type: str = "fact",
        importance: float = 0.5,
        is_long_term: bool = True
    ) -> str:
        """
        Store a memory (convenience method).
        
        Args:
            key: Memory key
            value: Memory value
            memory_type: Type of memory
            importance: Importance score (for long-term)
            is_long_term: Whether to store in long-term memory
            
        Returns:
            memory_id
        """
        if is_long_term:
            return self.memory_manager.store_long_term_memory(
                key=key,
                value=value,
                user_id=self.user_id,
                session_id=self.session_id,
                memory_type=memory_type,
                importance=importance
            )
        else:
            return self.memory_manager.store_short_term_memory(
                session_id=self.session_id,
                key=key,
                value=value,
                memory_type=memory_type
            )
    
    def get_session_id(self) -> str:
        """Get the current session ID."""
        return self.session_id
    
    def close_session(self):
        """Close the current session."""
        self.session_manager.close_session(self.session_id)
        logger.info(f"SESSION_CLOSED: session_id={self.session_id}")





