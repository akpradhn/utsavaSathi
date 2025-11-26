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
🎉 Identifies upcoming festivals based on Indian lunar/solar calendar  
🪔 Provides step-by-step rituals and custom puja item checklists  
🛍️ Generates smart shopping lists with estimated costs  
🚆 Plans travel and guest arrangements  
📅 Gives timeline reminders (T-7, T-3, T-1, T-0)  
🧠 Learns unique family traditions and preferences over time  
💬 Supports natural conversation through an orchestrating AI agent  

The system currently supports a curated set of major festivals such as:  
- Makar Sankranti  
- Maha Shivratri  
- Holi  
- Raja Parba *(Odisha specific)*  
- Rath Yatra *(Odisha specific)*  
- Janmashtami  
- Durga Puja  
- Diwali  
- Kartika Purnima  
- Christmas / New Year  

**Evaluation Metrics**
- Checklist completeness  
- Timeline correctness  
- Budget estimation accuracy  
- User satisfaction rating  

This demonstrates how intelligent agents can **augment everyday Indian family life**.

---

## 🧩 What You Created — Architecture Overview  

### **Agent Roles**
| Agent | Responsibility |
|-------|----------------|
| Festival Calendar Agent | Determines relevant festivals and timelines |
| Ritual & Checklist Agent | Produces cultural rituals + puja item lists |
| Shopping & Budget Agent | Converts items → structured lists + estimated cost |
| Travel & Guest Agent | Plans logistics and guest requirements |
| Memory Agent | Stores preferences for future personalization |
| Coordinator Agent | Orchestrates everything and interacts with the user |

### **Tools & Knowledge Base**
- Festival metadata: offline CSV/JSON  
- Puja checklist templates: JSON knowledge base  
- Family profile data: local JSON/SQLite store  
- Budget model: rule-based price estimation  

### **Workflow**
1. User selects festival / timeframe  
2. Orchestrator delegates to relevant agents  
3. Agents return insights → merged into a single plan  
4. Plan delivered with options to customize & share  
5. Preferences saved for next festival

---

## 🎬 Demo (Screenshots / Video placeholder)

> 📌 *Screenshots / GIF of demo will be added here after coding implementation.*  

Example showcase:
- User asks: *“Plan Diwali for 4 people with guests visiting”*
- System outputs:
  - Ritual checklist
  - Shopping list & budget
  - Cleaning + decoration tasks
  - Travel/guest plan
  - Timeline reminders
  - Final shareable plan

---

## 🧪 The Build — Tools & Technologies Used  
- **Python**
- **Google AI Agents / Gemini API**
- **JSON + SQLite** for lightweight storage  
- **Streamlit / Gradio** *(optional UI for demo)*  
- **Custom evaluation using golden festival cases**  

Development Steps:
- Defined festival dataset & templates  
- Implemented specialized agents  
- Created planning logic + orchestration  
- Added memory & evaluation  
- Designed scalable output format  

---

## 🚀 If I Had More Time…  

Planned enhancements:  
- Expand coverage to **all Indian states & festivals**  
- **Multi-language support** (Odia, Hindi, Bengali, Tamil)  
- Real-time APIs: grocery pricing, bookings  
- Calendar export + push notifications  
- WhatsApp sharing of checklists  
- Voice support for elderly  
- AR ritual guidance using device camera  

✨ Long-term vision:  
> “A complete cultural celebration operating system for Indian households.”

---

## 🙌 Thank You!
Excited to share Utsava Sathi with the world —  
**Celebrate More, Worry Less!**
