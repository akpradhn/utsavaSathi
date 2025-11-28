# PR Logs

---

## 2025-11-29T01:28:00+0530

### PR Title

**Multi-Agent System Integration: Coordinator with Specialized Agents**

### Description

This PR implements a complete multi-agent architecture for Utsava Sathi, transforming the system from a single-agent to a coordinator-based multi-agent system with specialized agents for different aspects of festival planning.

#### ✅ Multi-Agent Architecture

**Coordinator Agent** (`utsava_agent/coordinator.py`)
- Orchestrates all specialized agents using ADK's `AgentTool`
- Delegates tasks to specialized agents based on user request
- Assembles final FestivalPlan JSON from all agent outputs
- Uses `gemini-2.5-flash-lite` model
- Removed `google_search` tool (incompatible with other tools in Gemini 1.x)

**Specialized Agents** (all using `gemini-2.5-flash-lite`)

1. **Research Agent** (`utsava_agent/agents/research_agent.py`)
   - Fetches comprehensive festival overview
   - Returns 10 fields: name, local_name, origin_story, why_celebrated, themes, symbolism, key_values, family_roles, odisha_flavour, greetings
   - Uses JSON response format for structured output
   - ✅ Tested and validated

2. **Preparation Agent** (`utsava_agent/agents/preparation_agent.py`)
   - Plans pre-festival activities and rituals
   - Returns structured JSON with:
     - Ritual preparation steps
     - Puja items checklist
     - Food preparation guidelines
     - Popular places to visit
     - Schedule (T-7, T-3, T-1 days)
     - Guest/travel planning
   - ✅ Tested and validated

3. **Experience Agent** (`utsava_agent/agents/experience_agent.py`)
   - Plans festival day timeline and activities
   - Returns structured JSON with:
     - Early morning activities
     - Morning activities
     - Mid-day activities
     - Evening activities
     - Family-friendly tips
   - ✅ Tested and validated

4. **Content Agent** (`utsava_agent/agents/content_agent.py`)
   - Generates shareable text content for social media/messaging
   - Returns formatted text for:
     - Puja items (ready to share on WhatsApp/social media)
     - Tasks list (ready to share on WhatsApp/social media)
   - ✅ Tested and validated

#### ✅ Testing Infrastructure

Created comprehensive test scripts for each agent:
- `test_research_agent.py` - Validates all 10 festival overview fields
- `test_preparation_agent.py` - Validates pre-festival planning structure
- `test_experience_agent.py` - Validates festival day timeline
- `test_content_agent.py` - Validates shareable content format
- `test_coordinator.py` - End-to-end coordinator testing

All individual agent tests pass successfully.

#### ✅ Integration

- Updated `utsava_agent/__init__.py` to export coordinator and all specialized agents
- `ui/api.py` already configured to use `coordinator_agent` when `use_multi_agent=True`
- Falls back to `root_agent` if multi-agent unavailable

#### ⚠️ Known Limitations

- `gemini-2.5-flash-lite` does NOT support function calling
- `AgentTool` requires function calling to invoke agents as tools
- Coordinator currently uses `gemini-2.5-flash-lite` (as per requirements)
- This may prevent agent-to-agent calls via `AgentTool` until model support is added

**Workaround Options:**
- Use alternative orchestration mechanism (e.g., sequential manual calls)
- Consider `ParallelAgent` for concurrent execution
- Wait for `gemini-2.5-flash-lite` function calling support

#### 📁 Files Created

**Agent Files:**
- `utsava_agent/agents/research_agent.py`
- `utsava_agent/agents/preparation_agent.py`
- `utsava_agent/agents/experience_agent.py`
- `utsava_agent/agents/content_agent.py`
- `utsava_agent/agents/_shared.py` (shared utilities)
- `utsava_agent/agents/__init__.py`
- `utsava_agent/coordinator.py`

**Test Files:**
- `test_research_agent.py`
- `test_preparation_agent.py`
- `test_experience_agent.py`
- `test_content_agent.py`
- `test_coordinator.py`

**Documentation:**
- `MULTI_AGENT_INTEGRATION_STATUS.md`
- `PM_MESSAGE.md`

#### 📁 Files Modified

- `utsava_agent/__init__.py` - Added exports for coordinator and specialized agents

#### 🎯 Benefits

- **Modularity**: Each agent handles a specific domain, making maintenance easier
- **Scalability**: Can add more specialized agents in the future
- **Quality**: Specialized agents provide more focused, accurate outputs
- **Testability**: Individual agents can be tested independently

---

## 2025-11-28T21:17:08+0530

### PR Title

**Add run script and .gitignore for improved development workflow**

### Description

This PR adds essential development tooling to improve the project setup and workflow:

#### ✅ Run Script (`run.sh`)
- Created a shell script to easily start both the FastAPI backend and Streamlit frontend
- Automatically activates virtual environment if present (`.venv` or `venv`)
- Starts FastAPI server on port 8006 in the background
- Starts Streamlit app in the foreground
- Includes proper cleanup handling on exit (Ctrl+C stops both services)
- Provides colored output and error checking

**Usage:**
```bash
./run.sh
```

#### ✅ .gitignore
- Added comprehensive `.gitignore` file for Python projects
- Excludes virtual environments (`.venv/`, `venv/`, etc.)
- Excludes environment files (`.env`)
- Excludes IDE files (`.vscode/`, `.idea/`, etc.)
- Excludes Python artifacts (`__pycache__/`, `*.pyc`, etc.)
- Excludes build/distribution files
- Excludes OS-specific files (`.DS_Store`)
- Excludes test coverage and temporary files

These changes make it easier for developers to:
- Quickly start the application with a single command
- Avoid accidentally committing sensitive files (`.env`) or unnecessary files (virtual environments, IDE configs)

---

## 2025-11-28T18:17:08+0530

### PR Title

**Utsava Sathi – Gemini-powered Odisha-first Festival Planner (ADK Agent)**

### Description

This PR rebuilds the Utsava Sathi project as an **online, Gemini-powered multi-agent system** aligned with the patterns from the Google AI Agents Intensive.

#### ✅ Gemini + ADK Integration

- Added `utsava_agent/agent.py` with a single `root_agent` named `utsava_sathi_festival_planner`.
- Uses:

  ```python
  Gemini(model="gemini-2.5-flash-lite", api_key=GOOGLE_API_KEY, retry_options=retry_config)
  ```

- Enables `google_search` as a tool for current / grounded information.
- Reads `GOOGLE_API_KEY` / `GEMINI_API_KEY` from `.env` or the environment using `python-dotenv`.

#### ✅ Strict FestivalPlan Schema

The root agent is instructed to always return a **single JSON object** with this top-level structure:

- `festival_overview`
- `pre_festival`
- `festival_day`
- `shareables`
- `metadata`

The schema is embedded verbatim in the system instructions so Gemini must:

- Use **exact key names**.
- Fill all required keys (empty lists allowed, but no omissions).
- Avoid extra top-level fields or wrapping the JSON in text.

#### ✅ Project Reset for Online Mode

- Removed the previous offline Python-only coordinator and local data-dependent agents.
- Shifted the architecture to be **ADK- and Gemini-centric**, using Search for grounding and reasoning instead of static CSV/JSON files.

---

### How to Run

```bash
cd utsavaSathi
export GOOGLE_API_KEY="your_gemini_api_key"  # or set GEMINI_API_KEY / use .env
adk web --port 8000
```

In the ADK UI:

1. Select the **`utsava_agent`** app.
2. Choose the **`utsava_sathi_festival_planner`** agent.
3. Ask, for example:

   > Plan Kartika Purnima in Bhubaneswar for a family of 4 with a small child.

You should receive a fully-populated `FestivalPlan` JSON response matching the required schema.
