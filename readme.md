# **Utsava Sathi**
### *Smart Festival Planning Assistant*

---

## 📌 Problem Statement  
India is known for its vibrant festival culture — with many celebrations occurring month after month. For families, especially working parents in urban setups like Odisha, festival preparation becomes stressful due to:  
- Last-minute rush for **puja essentials**, clothes, and groceries  
- Forgetting rituals or necessary items  
- Budget overshooting without visibility  
- Travel coordination for hometown visits or guests  
- Difficulty aligning responsibilities across family members  

The culture, emotion, and community connection behind festivals are deeply valued — but **the planning often becomes chaotic**. This results in unnecessary stress during times meant for joy and togetherness.

**The problem**: There is no single digital solution today that understands Indian festival traditions *and* provides intelligent planning assistance tailored to each family’s needs.

**Utsava Sathi aims to bridge this gap** by bringing structure and personalization to festival planning so families can focus on celebrating, not stressing.

---

## 🤖 Why Agents?  
Festival planning involves **multi-step, dynamic decision-making**:  
- Identify upcoming festivals  
- Retrieve correct rituals and cultural variations  
- Generate personalized checklists and budgets  
- Assist with travel decisions and logistics  
- Track preferences to improve over time  

This isn’t a single prompt → single answer task. It requires:  
✔ Memory of past behaviors  
✔ Tool usage (calendar, checklist, pricing logic)  
✔ Ability to adapt to each festival scenario  
✔ Delegation of subtasks to specialized capabilities  

A **multi-agent system** allows these capabilities to work collaboratively:  
- Each agent has a **focused role**  
- The **orchestrator** ensures tasks are completed in sequence  
- The system retains **context and cultural knowledge**  

➡️ This makes agents the most natural and scalable approach for real-life festival planning automation.

---

## 🛠️ Project Description  
**Utsava Sathi** is a smart festival planning assistant for Indian families, designed with a **multi-agent architecture** to automate and simplify festival preparation.

It:  
🎉 Researches any Indian festival with cultural context and Odisha-specific details  
🪔 Provides step-by-step rituals and comprehensive puja item checklists  
🍽️ Suggests traditional food preparation and recipes  
🧭 Recommends popular places to visit (family-friendly when applicable)  
📅 Gives timeline reminders (T-7, T-3, T-1 days before festival)  
⏰ Plans festival day activities by time (early morning, morning, mid-day, evening)  
💬 Supports natural language requests through multi-agent orchestration  
🧠 Maintains session history and memory for personalization  
📋 Generates shareable content for messaging and social media  

**Festival Coverage:**  
The system can handle **any Indian festival** in real-time, not just a predefined list. Using Google Search integration and multi-agent orchestration, it dynamically researches and plans for festivals including (but not limited to):

- **Pan-India Festivals**: Makar Sankranti, Maha Shivratri, Holi, Janmashtami, Durga Puja, Diwali, Kartika Purnima, Christmas / New Year
- **Regional Festivals**: Raja Parba, Rath Yatra *(Odisha specific)*, Pongal, Onam, Baisakhi, and many more
- **Local & Community Festivals**: Any regional or community-specific celebration

The multi-agent system's robust architecture ensures accurate planning for any festival by:
- Real-time research via Google Search
- Cultural context awareness (especially Odisha traditions)
- Adaptive planning based on festival type and family context
- Comprehensive coverage of rituals, food, places, and timelines  

**Current Features**
- ✅ Multi-agent orchestration with Google ADK
- ✅ Session persistence (SQLite)
- ✅ Memory management (short-term & long-term)
- ✅ Beautiful Streamlit UI with tabbed sections
- ✅ FastAPI backend with error handling
- ✅ JSON schema validation
- ✅ Natural language processing
- ✅ Google Search integration for real-time information  

This demonstrates how intelligent agents can **augment everyday Indian family life**.

---

## 🧩 What You Created — Architecture Overview  

### **Multi-Agent System Architecture**

The system uses **Google ADK (Agent Development Kit)** with a coordinator orchestrating specialized agents:

```
Coordinator Agent (gemini-2.5-flash-lite)
  ├── Research Agent ✅
  ├── Preparation Agent ✅
  ├── Experience Agent ✅
  └── Content Agent ✅
```

### **Agent Roles**
| Agent | Responsibility | Model | Tools |
|-------|----------------|-------|-------|
| **Coordinator Agent** | Orchestrates all agents, assembles final FestivalPlan JSON | gemini-2.5-flash-lite | AgentTool (calls other agents) |
| **Research Agent** | Researches festival overview (name, story, themes, symbolism, cultural context) | gemini-2.5-flash-lite | google_search |
| **Preparation Agent** | Plans pre-festival activities (rituals, puja items, food, places, schedule, travel) | gemini-2.5-flash-lite | google_search |
| **Experience Agent** | Plans festival day timeline (early morning, morning, mid-day, evening activities) | gemini-2.5-flash-lite | google_search |
| **Content Agent** | Generates shareable text content (puja items list, tasks list) | gemini-2.5-flash-lite | None (content formatting only) |

### **Persistence & Memory**
- **Session Manager** (SQLite): Stores conversation history, session metadata, user associations
- **Memory Manager** (SQLite): Manages short-term (session-specific) and long-term (cross-session) memory for personalization

### **Tools & Knowledge Base**
- **Google ADK**: Agent Development Kit for building multi-agent systems
- **Gemini API**: Google's LLM for agent intelligence
- **SQLite**: Session and memory persistence (`agent_sessions.db`, `agent_memory.db`)
- **JSON Schema**: Strict FestivalPlan output format
- **Google Search**: Integrated search tool for real-time festival information

### **Workflow**
1. User provides natural language request (e.g., "Plan Nuakhai in Bhubaneswar for family of 3")
2. Coordinator Agent parses request and delegates to specialized agents:
   - Calls **Research Agent** → Festival overview (name, story, themes, symbolism, etc.)
   - Calls **Preparation Agent** → Pre-festival plan (rituals, items, food, places, schedule)
   - Calls **Experience Agent** → Festival day timeline (activities by time of day)
   - Calls **Content Agent** → Shareable content (formatted text for messaging)
3. Coordinator assembles all results into complete FestivalPlan JSON
4. Plan delivered via Streamlit UI with beautiful visualization
5. Session and memory saved for future personalization

### **Project Structure**
```
utsavaSathi/
├── utsava_agent/
│   ├── agent.py                    # Legacy single agent (backward compatible)
│   ├── coordinator.py              # Coordinator agent (orchestrates all agents)
│   ├── session_manager.py          # SQLite session management
│   ├── memory_manager.py           # SQLite memory management
│   ├── session_runner.py          # Custom ADK runner with session/memory
│   └── agents/
│       ├── research_agent.py      # Festival overview research
│       ├── preparation_agent.py   # Pre-festival planning
│       ├── experience_agent.py    # Festival day experience
│       └── content_agent.py       # Shareable content generation
├── ui/
│   ├── api.py                      # FastAPI backend
│   └── app.py                      # Streamlit UI
├── sample_data/
│   └── nuakhai.json                # Sample festival plan
└── Instructions/
    └── readme.md                   # This file
```

---

## 🎬 Demo & Usage

### **Prerequisites**

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables:**
   - Create a `.env` file in the project root
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```
     or
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

3. **Make run.sh Executable (if needed):**
   ```bash
   chmod +x run.sh
   ```

### **Running the System**

**Quick Start (Recommended):**

Simply run the provided script which starts both the API server and Streamlit UI:

```bash
./run.sh
```

This script will:
- ✅ Activate your virtual environment (if present)
- ✅ Start the FastAPI backend server on `http://127.0.0.1:8006`
- ✅ Launch the Streamlit UI (will open in your browser)
- ✅ Handle cleanup when you press `Ctrl+C`

**Manual Start (Alternative):**

If you prefer to run services separately:

1. **Start the API Server:**
   ```bash
   cd ui
   uvicorn api:app --host 127.0.0.1 --port 8006
   ```

2. **In a new terminal, launch the Streamlit UI:**
   ```bash
   streamlit run ui/app.py
   ```

### **Making a Request**

1. **Open the Streamlit UI** (usually at `http://localhost:8501`)
2. **Enter a natural language prompt**, for example:
   - *"Plan Nuakhai in Bhubaneswar for a family of 3 with one child"*
   - *"Plan Diwali for 4 people with guests visiting"*
   - *"Plan Rath Yatra in Puri for a family of 5"*

3. **The multi-agent system will automatically:**
   - Research festival overview (name, story, themes, symbolism)
   - Plan pre-festival activities (rituals, puja items, food, places, timeline)
   - Plan festival day experience (time-based activities)
   - Generate shareable content

4. **View the beautiful, organized plan** in the Streamlit UI with all sections displayed

### **Example Output Structure**
- **Festival Overview**: Hero card with name, local name, story, themes, symbolism, family roles, greetings
- **Pre-Festival**: Tabs for steps, puja items, food, places to visit, timeline (T-7, T-3, T-1), travel recommendations
- **Festival Day**: Vertical timeline with activities for early morning, morning, mid-day, evening, plus family tips
- **Shareables**: Copy-to-clipboard text areas for puja items and tasks
- **Metadata**: Generation timestamp, location context, agent version

---

## 🧪 The Build — Tools & Technologies Used  

### **Core Technologies**
- **Python 3.9+**
- **Google ADK (Agent Development Kit)**: Framework for building multi-agent systems
- **Google Gemini API**: LLM powering all agents (gemini-2.5-flash-lite)
- **FastAPI**: REST API backend for agent execution
- **Streamlit**: Interactive web UI for visualizing festival plans
- **SQLite**: Session and memory persistence
- **Pydantic**: Request/response validation

### **Key Dependencies**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
google-adk>=0.2.0
google-generativeai>=0.8.0
streamlit>=1.39.0
python-dotenv>=1.0.1
```

### **Development Steps Completed**
1. ✅ **Multi-Agent Architecture**: Implemented coordinator + 4 specialized agents
2. ✅ **Agent-to-Agent Communication**: Using ADK's `AgentTool` for agent orchestration
3. ✅ **Session Management**: SQLite-based conversation history tracking
4. ✅ **Memory Management**: Short-term and long-term memory for personalization
5. ✅ **FastAPI Backend**: `/plan` endpoint with session and memory support
6. ✅ **Streamlit UI**: Beautiful, tabbed interface with:
   - Festival Overview (hero card, themes, symbolism, family roles, greetings)
   - Pre-Festival Planning (steps, puja items, food, places, timeline, travel)
   - Festival Day Timeline (time-based activities)
   - Shareables (copy-to-clipboard text areas)
   - Metadata footer
7. ✅ **JSON Schema**: Strict FestivalPlan output format validation
8. ✅ **Error Handling**: Robust error handling for API calls and JSON parsing  

---

## 🚀 Future Enhancements  

Planned improvements:  
- **Budget Estimation**: Add shopping list cost estimation  
- **Festival Calendar**: Auto-detect upcoming festivals based on Indian calendar  
- **Multi-language support**: Odia, Hindi, Bengali, Tamil  
- **Real-time APIs**: Grocery pricing, travel bookings  
- **Calendar Integration**: Export to Google Calendar + push notifications  
- **WhatsApp Integration**: Direct sharing of checklists via WhatsApp API  
- **Voice Interface**: Voice support for hands-free planning  
- **AR Ritual Guidance**: Camera-based AR for step-by-step ritual guidance  
- **Family Collaboration**: Multi-user support with role-based task assignment  
- **Recipe Integration**: Detailed cooking instructions with video links  

✨ Long-term vision:  
> “A complete cultural celebration operating system for Indian households.”

---

## 🙌 Thank You!
Excited to share Utsava Sathi with the world —  
**Celebrate More, Worry Less!**
