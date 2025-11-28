# Multi-Agent Implementation - Agent-to-Agent Calls

## Implementation Complete ✅

The multi-agent system with agent-to-agent calls has been implemented. The coordinator agent can now call specialized agents as tools.

## File Structure

```
utsava_agent/
├── __init__.py                    # Exports root_agent and coordinator_agent
├── agent.py                       # Legacy single agent (backward compatible)
├── coordinator.py                 # Coordinator agent (orchestrates all agents)
├── agent_tool.py                  # Custom tool for agent-to-agent calls
├── agents/
│   ├── __init__.py               # Exports all specialized agents
│   ├── _shared.py                # Shared utilities (API key, retry config)
│   ├── research_agent.py        # Festival overview research
│   ├── preparation_agent.py     # Pre-festival planning
│   ├── experience_agent.py      # Festival day experience
│   └── content_agent.py         # Shareable content generation
└── IMPLEMENTATION_EXAMPLE.py     # Reference example (can be removed)
```

## How It Works

### 1. Specialized Agents
Each specialized agent is a standalone ADK Agent:
- **Research Agent**: Researches festival overview (name, story, themes)
- **Preparation Agent**: Plans pre-festival activities (rituals, food, places, schedule)
- **Experience Agent**: Plans festival day activities (morning to evening)
- **Content Agent**: Generates shareable text content

### 2. Agent Tool Wrapper
`agent_tool.py` provides `create_agent_tool()` which:
- Wraps an ADK Agent as a callable tool
- Handles async execution within sync tool context
- Extracts JSON responses from agent events
- Provides error handling and logging

### 3. Coordinator Agent
`coordinator.py` creates the coordinator that:
- Has all specialized agents as tools
- Receives user requests
- Delegates tasks to appropriate agents
- Assembles final FestivalPlan JSON
- Adds metadata

### 4. API Integration
`ui/api.py` has been updated to:
- Support both single-agent and multi-agent modes
- Use `use_multi_agent` flag in requests
- Gracefully fallback to single agent if multi-agent unavailable
- Log which mode is being used

## Usage

### API Request (Single Agent - Default)
```json
{
  "prompt": "Plan Nuakhai in Bhubaneswar for a family of 3 with one small child"
}
```

### API Request (Multi-Agent)
```json
{
  "prompt": "Plan Nuakhai in Bhubaneswar for a family of 3 with one small child",
  "use_multi_agent": true
}
```

### Direct Python Usage
```python
from utsava_agent.coordinator import coordinator_agent
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(agent=coordinator_agent, app_name="utsava_agent")
events = await runner.run_debug("Plan Nuakhai in Bhubaneswar for a family of 3")
```

## Agent-to-Agent Call Flow

```
User Request
    ↓
Coordinator Agent
    ↓
    ├─→ Research Agent (via call_research_agent tool)
    │   └─→ Returns: festival_overview JSON
    │
    ├─→ Preparation Agent (via call_preparation_agent tool)
    │   └─→ Returns: pre_festival JSON
    │
    ├─→ Experience Agent (via call_experience_agent tool)
    │   └─→ Returns: festival_day JSON
    │
    └─→ Content Agent (via call_content_agent tool)
        └─→ Returns: shareables JSON
    ↓
Coordinator assembles all results
    ↓
Final FestivalPlan JSON
```

## Technical Details

### Async Handling
- ADK tools must be synchronous
- `create_agent_tool()` wraps async agent execution
- Handles event loop management (existing loops, new loops, thread pools)
- Ensures compatibility with ADK's tool system

### Error Handling
- Each agent tool has try-catch blocks
- Failures return error JSON instead of crashing
- Coordinator can handle partial failures
- Logging at each step for debugging

### JSON Extraction
- Extracts text from ADK events using multiple strategies
- Handles different event structures
- Cleans markdown code fences
- Fixes common JSON escaping issues

## Testing

To test the multi-agent system:

1. **Start the API**:
   ```bash
   ./run.sh
   ```

2. **Test with curl**:
   ```bash
   curl -X POST http://127.0.0.1:8006/plan \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Plan Nuakhai in Bhubaneswar for a family of 3",
       "use_multi_agent": true
     }'
   ```

3. **Check logs** for agent calls:
   - Look for "AGENT_TOOL_CALL" messages
   - Verify all 4 agents are called
   - Check final JSON assembly

## Benefits

1. **Specialization**: Each agent focuses on one domain
2. **Modularity**: Easy to update individual agents
3. **Debugging**: Clear separation of concerns
4. **Scalability**: Easy to add new agents
5. **Maintainability**: Smaller, focused code files

## Migration Path

1. ✅ Multi-agent system implemented
2. ✅ API supports both modes
3. ⏳ Test and compare results
4. ⏳ Gradually migrate users
5. ⏳ Monitor performance
6. ⏳ Optimize based on usage

## Next Steps

1. Test the multi-agent system with various festival requests
2. Compare results with single-agent mode
3. Optimize agent prompts based on results
4. Add caching for common festivals
5. Add validation at each agent step
6. Consider parallel execution optimization

## Notes

- The single agent (`root_agent`) remains available for backward compatibility
- Multi-agent mode is opt-in via `use_multi_agent` flag
- All agents use the same Gemini model and API key
- Agent tools handle async/sync conversion automatically

