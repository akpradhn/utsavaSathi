# ADK Quick Start Guide

## Prerequisites

1. **Install google-adk**:
   ```bash
   pip install google-adk
   ```

2. **Set up environment**:
   ```bash
   # Make sure .env file exists with GOOGLE_API_KEY
   # Or set environment variable:
   export GOOGLE_API_KEY="your_api_key_here"
   ```

## Quick Test

### Step 1: Verify Setup
```bash
python3 verify_agents.py
```

This will check that:
- google-adk is installed
- All agents can be imported
- Agents are properly configured

### Step 2: Start ADK Web Interface
```bash
./test_adk.sh
```

Or manually:
```bash
adk web --port 8000
```

### Step 3: Test in Browser
1. Open http://localhost:8000 in your browser
2. Select **`utsava_agent`** app
3. Choose **`utsava_coordinator`** agent
4. Enter test prompt:
   ```
   Plan Nuakhai in Bhubaneswar for a family of 3 with one small child.
   ```

## What to Expect

### Coordinator Agent Workflow
When you use `utsava_coordinator`, you'll see:

1. **Coordinator receives request**
2. **Tool calls appear**:
   - `call_research_agent` - Gets festival overview
   - `call_preparation_agent` - Gets pre-festival plan
   - `call_experience_agent` - Gets festival day plan
   - `call_content_agent` - Gets shareables
3. **Final JSON assembled** with all sections

### Response Structure
```json
{
  "festival_overview": { ... },
  "pre_festival": { ... },
  "festival_day": { ... },
  "shareables": { ... },
  "metadata": { ... }
}
```

## Testing Individual Agents

You can also test each specialized agent:

1. **Research Agent**: `festival_research_agent`
   - Prompt: `Research Nuakhai in Bhubaneswar. Return festival_overview JSON.`

2. **Preparation Agent**: `festival_preparation_agent`
   - Prompt: `Plan pre-festival for Nuakhai in Bhubaneswar for family of 3. Return pre_festival JSON.`

3. **Experience Agent**: `festival_experience_agent`
   - Prompt: `Plan festival day for Nuakhai in Bhubaneswar for family of 3. Return festival_day JSON.`

4. **Content Agent**: `festival_content_agent`
   - Prompt: `Create shareables. Puja items: ["Rice", "Fruits"]. Tasks: ["Clean house"]. Return shareables JSON.`

## Troubleshooting

### "No module named 'google'"
```bash
pip install google-adk
```

### "API_KEY_MISSING"
Set in `.env` file:
```
GOOGLE_API_KEY=your_key_here
```

Or export:
```bash
export GOOGLE_API_KEY="your_key_here"
```

### Agent not appearing in ADK
1. Check `verify_agents.py` output
2. Ensure you're in the project directory
3. Restart ADK web interface

### Tool calls failing
- Check logs in ADK interface
- Verify all agents are initialized
- Check API key is valid

## Next Steps

- Compare single agent vs multi-agent results
- Test with different festivals
- Observe execution timeline in ADK
- Check tool call details

For more details, see `ADK_TESTING_GUIDE.md`.

