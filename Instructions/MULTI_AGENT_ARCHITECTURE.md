# Multi-Agent Architecture Proposal for Utsava Sathi

## Current State
The system currently uses a **single monolithic agent** (`root_agent`) that handles all aspects of festival planning in one go. This works but has limitations:
- All responsibilities in one agent
- Harder to optimize individual components
- Difficult to parallelize work
- Less modular and maintainable

## Proposed Multi-Agent Architecture

Based on common multi-agent patterns (hierarchical, coordinator-based, and specialized agent architectures), we propose breaking the system into **specialized agents** coordinated by a **master orchestrator**.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           Coordinator Agent (Orchestrator)              │
│  - Receives user request                                │
│  - Breaks down task into subtasks                       │
│  - Delegates to specialized agents                       │
│  - Aggregates results                                   │
│  - Validates final FestivalPlan                         │
└─────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│ Research  │ │Preparation│ │ Experience│
│  Agent    │ │   Agent   │ │   Agent   │
└───────────┘ └───────────┘ └───────────┘
        │           │           │
        └───────────┼───────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Content Agent │
            └───────────────┘
```

## Agent Breakdown

### 1. **Coordinator Agent** (Master Orchestrator)
**Purpose**: Orchestrates the entire festival planning workflow

**Responsibilities**:
- Parse user request (festival name, location, family context)
- Break down the task into subtasks
- Delegate work to specialized agents (can run in parallel)
- Collect and validate results from all agents
- Assemble final FestivalPlan JSON
- Generate metadata (timestamp, location, version)

**Input**: User prompt (e.g., "Plan Nuakhai in Bhubaneswar for a family of 3")
**Output**: Complete FestivalPlan JSON

**Tools**: 
- Can call other agents as sub-agents
- `google_search` (for validation/verification)

---

### 2. **Research Agent** (Festival Overview Specialist)
**Purpose**: Research and generate festival overview information

**Responsibilities**:
- Research festival name, local name, significance
- Understand why the festival is celebrated
- Find/create short stories/legends
- Identify themes and cultural context
- Focus on Odisha-first context when relevant

**Input**: Festival name, location context
**Output**: `festival_overview` JSON section:
```json
{
  "name": "string",
  "local_name": "string",
  "why_celebrated": "string",
  "short_story": "string",
  "themes": ["string"]
}
```

**Tools**: 
- `google_search` (primary tool for research)

**Specialization**: Cultural research, festival knowledge, Odisha traditions

---

### 3. **Preparation Agent** (Pre-Festival Planning Specialist)
**Purpose**: Plan all pre-festival activities and preparations

**Responsibilities**:
- Generate ritual preparation steps
- Create puja items checklist
- Plan food preparation items
- Suggest popular places to visit (with context)
- Create timeline schedule (T-7, T-3, T-1 days)
- Determine travel/guest planning needs

**Input**: Festival name, location, family context (from coordinator)
**Output**: `pre_festival` JSON section:
```json
{
  "ritual_preparation_steps": [...],
  "puja_items_checklist": [...],
  "food_preparation": [...],
  "popular_places_to_visit": [...],
  "schedule": {...},
  "guest_or_travel_plan": {...}
}
```

**Tools**: 
- `google_search` (for places, recipes, rituals)

**Specialization**: Logistics, planning, preparation workflows

---

### 4. **Experience Agent** (Festival Day Specialist)
**Purpose**: Plan the actual festival day experience

**Responsibilities**:
- Plan early morning activities
- Plan morning rituals and activities
- Plan mid-day activities
- Plan evening activities
- Generate family-friendly tips (considering family context)

**Input**: Festival name, family context (especially children info)
**Output**: `festival_day` JSON section:
```json
{
  "early_morning": [...],
  "morning": [...],
  "mid_day": [...],
  "evening": [...],
  "family_friendly_tips": [...]
}
```

**Tools**: 
- `google_search` (for day-of rituals, activities)

**Specialization**: Day-of experience, family-friendly planning

---

### 5. **Content Agent** (Shareables Specialist)
**Purpose**: Generate shareable content for social media/messaging

**Responsibilities**:
- Create puja items text (formatted for sharing)
- Create tasks text (formatted for sharing)
- Ensure content is concise and shareable
- Add relevant hashtags

**Input**: Results from Preparation Agent (puja items, tasks)
**Output**: `shareables` JSON section:
```json
{
  "puja_items_text": "string",
  "tasks_text": "string"
}
```

**Tools**: 
- Minimal (mostly text formatting)

**Specialization**: Content generation, formatting, social media optimization

---

## Implementation Strategy

### Phase 1: Basic Multi-Agent Setup
1. Create separate agent files for each specialist
2. Implement Coordinator Agent that calls others sequentially
3. Test with simple festival requests

### Phase 2: Parallel Execution
1. Enable parallel execution of Research, Preparation, and Experience agents
2. Coordinator waits for all to complete
3. Content Agent runs after Preparation Agent (dependency)

### Phase 3: Optimization
1. Add caching for common festivals
2. Add error handling and fallbacks
3. Optimize agent prompts for better results
4. Add validation at each step

## File Structure

```
utsava_agent/
├── __init__.py
├── coordinator.py          # Coordinator Agent
├── agents/
│   ├── __init__.py
│   ├── research_agent.py  # Research Agent
│   ├── preparation_agent.py # Preparation Agent
│   ├── experience_agent.py # Experience Agent
│   └── content_agent.py   # Content Agent
└── agent.py               # Legacy single agent (for backward compat)
```

## Agent Communication Pattern

### Sequential (Phase 1)
```
Coordinator → Research → Preparation → Experience → Content → Coordinator
```

### Parallel (Phase 2)
```
Coordinator
  ├─→ Research Agent (parallel)
  ├─→ Preparation Agent (parallel)
  └─→ Experience Agent (parallel)
      ↓
  Content Agent (after Preparation)
      ↓
  Coordinator (aggregate & validate)
```

## Benefits of Multi-Agent Architecture

1. **Specialization**: Each agent focuses on one domain, leading to better results
2. **Parallelization**: Research, Preparation, and Experience can run simultaneously
3. **Maintainability**: Easier to update/improve individual agents
4. **Scalability**: Can add new agents (e.g., Translation Agent, Validation Agent)
5. **Debugging**: Easier to identify which part failed
6. **Reusability**: Agents can be reused in other contexts
7. **Testing**: Can test each agent independently

## ADK Implementation Notes

### Using ADK Sub-Agents
ADK supports agents calling other agents. The Coordinator can:
- Define other agents as "tools" or sub-agents
- Use `Agent` instances that can be invoked
- Pass context between agents

### Example Coordinator Pattern
```python
coordinator = Agent(
    name="utsava_coordinator",
    model=Gemini(...),
    instruction="You coordinate festival planning...",
    tools=[
        research_agent,      # Sub-agent
        preparation_agent,    # Sub-agent
        experience_agent,    # Sub-agent
        content_agent,       # Sub-agent
        google_search
    ]
)
```

## Migration Path

1. **Keep existing `root_agent`** for backward compatibility
2. **Create new `coordinator_agent`** that uses multi-agent approach
3. **Update API** to use coordinator (with feature flag)
4. **Test and compare** results
5. **Gradually migrate** users to multi-agent system
6. **Deprecate** single agent once stable

## Next Steps

1. ✅ Review and approve architecture
2. Create `agents/` directory structure
3. Implement Research Agent first (simplest, most independent)
4. Implement Preparation Agent
5. Implement Experience Agent
6. Implement Content Agent
7. Implement Coordinator Agent
8. Update API to support both modes
9. Add tests for each agent
10. Document agent interfaces and contracts

