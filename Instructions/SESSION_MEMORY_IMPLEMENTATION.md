# Agent Sessions and Memory Management Implementation

## Overview

This implementation adds persistent session and memory management to the Utsava Sathi agent system using SQLite databases. This enables:

- **Conversation Continuity**: Agents can maintain context across multiple interactions
- **Long-term Memory**: Store and recall user preferences, facts, and learned information
- **Session Management**: Track and manage user sessions with conversation history

## Architecture

### Components

1. **SessionManager** (`utsava_agent/session_manager.py`)
   - Manages agent sessions and conversation history
   - Stores session metadata, user associations, and conversation turns
   - SQLite database: `agent_sessions.db`

2. **MemoryManager** (`utsava_agent/memory_manager.py`)
   - Manages short-term (session-specific) and long-term (cross-session) memory
   - Stores facts, preferences, context, and associations between memories
   - SQLite database: `agent_memory.db`

3. **SessionRunner** (`utsava_agent/session_runner.py`)
   - Custom runner that wraps ADK's `InMemoryRunner`
   - Integrates session and memory management with agent execution
   - Automatically retrieves relevant context and memories for each interaction

4. **API Integration** (`ui/api.py`)
   - Updated to support optional `session_id` and `user_id` parameters
   - Automatically uses `SessionRunner` when session/user ID is provided
   - Falls back to `InMemoryRunner` for stateless requests

## Database Schema

### Sessions Database (`agent_sessions.db`)

#### `sessions` table
- `session_id` (TEXT, PRIMARY KEY)
- `user_id` (TEXT, FOREIGN KEY)
- `agent_name` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- `status` (TEXT) - 'active', 'completed', 'archived'
- `metadata` (TEXT, JSON)

#### `conversation_history` table
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `session_id` (TEXT, FOREIGN KEY)
- `turn_number` (INTEGER)
- `role` (TEXT) - 'user' or 'assistant'
- `content` (TEXT)
- `timestamp` (TIMESTAMP)
- `metadata` (TEXT, JSON)

#### `users` table
- `user_id` (TEXT, PRIMARY KEY)
- `created_at` (TIMESTAMP)
- `metadata` (TEXT, JSON)

### Memory Database (`agent_memory.db`)

#### `long_term_memory` table
- `memory_id` (TEXT, PRIMARY KEY)
- `user_id` (TEXT)
- `session_id` (TEXT, FOREIGN KEY)
- `key` (TEXT)
- `value` (TEXT, JSON)
- `memory_type` (TEXT) - 'fact', 'preference', 'skill', etc.
- `importance` (REAL) - 0.0 to 1.0
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- `accessed_at` (TIMESTAMP)
- `access_count` (INTEGER)
- `expires_at` (TIMESTAMP, optional)
- `metadata` (TEXT, JSON)

#### `short_term_memory` table
- `memory_id` (TEXT, PRIMARY KEY)
- `session_id` (TEXT, FOREIGN KEY)
- `key` (TEXT)
- `value` (TEXT, JSON)
- `memory_type` (TEXT) - 'context', 'event', 'state', etc.
- `created_at` (TIMESTAMP)
- `expires_at` (TIMESTAMP, optional)
- `metadata` (TEXT, JSON)

#### `memory_associations` table
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `memory_id_1` (TEXT, FOREIGN KEY)
- `memory_id_2` (TEXT, FOREIGN KEY)
- `association_type` (TEXT) - 'related', 'causes', 'similar', etc.
- `strength` (REAL) - 0.0 to 1.0
- `created_at` (TIMESTAMP)

## Usage

### Basic Usage (Stateless)

```python
POST /plan
{
  "prompt": "Plan Diwali in Mumbai for a family of 4",
  "use_multi_agent": false
}
```

### Session-Based Usage (Stateful)

```python
# First request - creates new session
POST /plan
{
  "prompt": "Plan Diwali in Mumbai for a family of 4",
  "use_multi_agent": false,
  "user_id": "user_123"
}

# Response includes session_id
{
  "festival_overview": {...},
  "pre_festival": {...},
  "festival_day": {...},
  "shareables": {...},
  "metadata": {...},
  "_session_metadata": {
    "session_id": "abc-123-def-456",
    "turn_number": 1
  }
}

# Subsequent requests - use same session_id
POST /plan
{
  "prompt": "What about the puja items?",
  "use_multi_agent": false,
  "session_id": "abc-123-def-456",
  "user_id": "user_123"
}
```

### Memory Storage

```python
from utsava_agent.memory_manager import MemoryManager

memory_manager = MemoryManager()

# Store long-term memory
memory_id = memory_manager.store_long_term_memory(
    key="user_preference",
    value={"favorite_festival": "Diwali", "location": "Mumbai"},
    user_id="user_123",
    memory_type="preference",
    importance=0.8
)

# Store short-term memory (session-specific)
memory_id = memory_manager.store_short_term_memory(
    session_id="abc-123",
    key="current_context",
    value={"festival": "Diwali", "family_size": 4},
    memory_type="context",
    ttl_hours=24.0
)
```

## Features

### Session Management

- **Automatic Session Creation**: Sessions are created automatically when `user_id` is provided
- **Conversation History**: All user and assistant messages are stored with turn numbers
- **Session Status**: Track active, completed, or archived sessions
- **Session Retrieval**: Get all sessions for a user or specific session details

### Memory Management

- **Short-term Memory**: Session-specific context that expires after TTL
- **Long-term Memory**: Cross-session facts and preferences with importance scoring
- **Memory Associations**: Link related memories for better context retrieval
- **Access Tracking**: Track how often memories are accessed for importance updates
- **Automatic Cleanup**: Expired short-term memories are automatically removed

### Context Enhancement

When using `SessionRunner`, the agent automatically receives:

1. **Conversation History**: Last 5 conversation turns
2. **Long-term Memories**: Top 5 most important memories for the user
3. **Short-term Memories**: Top 3 recent session-specific memories
4. **Additional Context**: Any context provided in the request

This context is automatically injected into the prompt to provide continuity and relevant information.

## API Endpoints

### POST /plan

**Request:**
```json
{
  "prompt": "string",
  "use_multi_agent": false,
  "session_id": "string (optional)",
  "user_id": "string (optional)"
}
```

**Response:**
```json
{
  "festival_overview": {...},
  "pre_festival": {...},
  "festival_day": {...},
  "shareables": {...},
  "metadata": {...},
  "_session_metadata": {
    "session_id": "string",
    "turn_number": 1
  }
}
```

## Implementation Details

### SessionRunner Workflow

1. **Initialization**
   - Create or retrieve session
   - Initialize memory managers

2. **Context Retrieval**
   - Get conversation history (last 10 turns)
   - Get short-term memories (session-specific, last 10)
   - Get long-term memories (user-specific, top 5 by importance)

3. **Prompt Enhancement**
   - Build enhanced prompt with context
   - Include conversation history
   - Include relevant memories
   - Include additional context if provided

4. **Agent Execution**
   - Run agent with enhanced prompt
   - Extract response from events

5. **Storage**
   - Store user message in conversation history
   - Store assistant response in conversation history
   - Store interaction in short-term memory
   - Update memory access tracking

## Benefits

1. **Conversation Continuity**: Agents remember previous interactions in the same session
2. **Personalization**: Long-term memory enables personalized responses based on user preferences
3. **Context Awareness**: Agents can reference previous conversations and learned facts
4. **Scalability**: SQLite provides efficient storage and retrieval for large conversation histories
5. **Flexibility**: Works with both single-agent and multi-agent systems

## Future Enhancements

- [ ] Memory importance auto-update based on usage patterns
- [ ] Semantic search for memory retrieval
- [ ] Memory summarization for long conversations
- [ ] Cross-session memory associations
- [ ] Memory expiration policies
- [ ] Session analytics and insights

## References

- [ADK Agent Sessions (Kaggle)](https://www.kaggle.com/code/kaggle5daysofai/day-3a-agent-sessions)
- [ADK Agent Memory (Kaggle)](https://www.kaggle.com/code/kaggle5daysofai/day-3b-agent-memory)





