# PR Logs

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
