from __future__ import annotations

import asyncio
import json
import textwrap
from typing import Dict, Any, List
import logging
import os
import sys
from pathlib import Path

import requests
import streamlit as st

# Ensure project root is on sys.path so other local modules can be imported if needed
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# Warm color palette: saffron, marigold, deep green
COLORS = {
    "saffron": "#F97316",
    "saffron_light": "#FB923C",
    "saffron_bg": "#FFF7ED",
    "marigold": "#F59E0B",
    "marigold_light": "#FCD34D",
    "deep_green": "#166534",
    "deep_green_light": "#16A34A",
    "deep_green_bg": "#F0FDF4",
}


def render_theme_chips(themes: List[str]) -> None:
    """Render festival themes as rounded colored chips in one line."""
    colors = [COLORS["saffron"], COLORS["marigold"], COLORS["deep_green_light"], "#0EA5E9", "#A855F7"]
    
    # Build HTML string
    chips_html = ""
    for i, theme in enumerate(themes):
        color = colors[i % len(colors)]
        # Escape any HTML in theme text
        theme_escaped = theme.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        chips_html += f'<span style="display:inline-block;padding:6px 14px;margin:4px 6px 4px 0;border-radius:999px;background:{color}22;color:{color};font-size:0.85rem;font-weight:500;border:1px solid {color}44;white-space:nowrap;flex-shrink:0;">{theme_escaped}</span>'
    
    # Wrap in container div
    container_html = f'<div style="white-space:nowrap;overflow-x:auto;display:flex;flex-wrap:nowrap;align-items:center;">{chips_html}</div>'
    st.markdown(container_html, unsafe_allow_html=True)


def render_festival_overview(data: Dict[str, Any]) -> None:
    """Render the festival overview hero card."""
    
    # Hero card container
    with st.container():
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            name = data.get("name", "")
            local_name = data.get("local_name", "")
            title = f"{name}"
            if local_name:
                title += f" · {local_name}"
            
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, {COLORS['saffron']}, {COLORS['marigold']});
                    padding: 24px;
                    border-radius: 16px;
                    margin-bottom: 16px;
                    color: white;
                ">
                    <h1 style="margin:0; color:white; font-size:2.2rem;">{title}</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            why_celebrated = data.get("why_celebrated", "")
            if why_celebrated:
                st.markdown(f"**Why celebrated:** {why_celebrated}")
            
            # Story expander
            short_story = data.get("short_story", "")
            if short_story:
                with st.expander("📖 Read the Story", expanded=False):
                    st.write(short_story)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Themes
            themes = data.get("themes", [])
            if themes:
                st.markdown("**Themes:**")
                render_theme_chips(themes)
            
            # Symbolism
            symbolism = data.get("symbolism", [])
            if symbolism:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Symbolism:**")
                icons = ["🌾", "🪔", "🎉", "🌸", "🍚", "🕯️", "🌿"]
                for i, symbol in enumerate(symbolism):
                    icon = icons[i % len(icons)]
                    st.markdown(
                        f"""
                        <div style="
                            margin-bottom: 14px;
                            padding: 12px 16px;
                            background: {COLORS['saffron_bg']};
                            border-radius: 8px;
                            border-left: 3px solid {COLORS['saffron']};
                            display: flex;
                            align-items: center;
                            gap: 12px;
                        ">
                            <span style="font-size: 1.4rem; flex-shrink: 0;">{icon}</span>
                            <span style="color: #333; font-size: 0.95rem; line-height: 1.5; flex: 1;">{symbol}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            
            # Family Roles
            family_roles = data.get("family_roles", {})
            if family_roles:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Family Roles:**")
                if family_roles.get("elders"):
                    st.markdown(
                        f"""
                        <div style="
                            margin-bottom: 16px;
                            padding: 12px;
                            background: {COLORS['saffron_bg']};
                            border-radius: 8px;
                            border-left: 4px solid {COLORS['saffron']};
                        ">
                            <div style="font-size: 1.3rem; margin-bottom: 6px;">👴 <strong>Elders</strong></div>
                            <div style="color: #555; font-size: 0.9rem; line-height: 1.5; padding-left: 28px;">
                                {family_roles['elders']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                if family_roles.get("parents"):
                    st.markdown(
                        f"""
                        <div style="
                            margin-bottom: 16px;
                            padding: 12px;
                            background: {COLORS['saffron_bg']};
                            border-radius: 8px;
                            border-left: 4px solid {COLORS['saffron']};
                        ">
                            <div style="font-size: 1.3rem; margin-bottom: 6px;">👨‍👩‍👧 <strong>Parents</strong></div>
                            <div style="color: #555; font-size: 0.9rem; line-height: 1.5; padding-left: 28px;">
                                {family_roles['parents']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                if family_roles.get("children"):
                    st.markdown(
                        f"""
                        <div style="
                            margin-bottom: 16px;
                            padding: 12px;
                            background: {COLORS['saffron_bg']};
                            border-radius: 8px;
                            border-left: 4px solid {COLORS['saffron']};
                        ">
                            <div style="font-size: 1.3rem; margin-bottom: 6px;">🧒 <strong>Children</strong></div>
                            <div style="color: #555; font-size: 0.9rem; line-height: 1.5; padding-left: 28px;">
                                {family_roles['children']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            
            # Greetings
            greetings = data.get("greetings", [])
            if greetings:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Greetings:**")
                for greeting in greetings:
                    st.markdown(
                        f"""
                        <div style="
                            display: inline-block;
                            padding: 8px 16px;
                            margin: 4px 8px 4px 0;
                            border-radius: 8px;
                            background: {COLORS['saffron_bg']};
                            border: 1px solid {COLORS['saffron']}44;
                            color: {COLORS['saffron']};
                            font-weight: 500;
                        ">
                            🙏 {greeting}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        
    with col_right:
            # Festival illustration placeholder
        st.markdown(
                f"""
            <div style="
                    background: linear-gradient(135deg, {COLORS['saffron_bg']}, {COLORS['deep_green_bg']});
                    border-radius: 16px;
                    padding: 32px 16px;
                    text-align: center;
                    border: 2px solid {COLORS['saffron']}44;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                ">
                    <div style="font-size:4rem; margin-bottom:12px;">🪔</div>
                    <div style="font-weight:600; color:{COLORS['deep_green']}; font-size:1.1rem;">
                        {name if name else "Festival"}
                    </div>
                    <div style="font-size:0.85rem; color:#666; margin-top:8px;">
                        Odisha Festival
                    </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_pre_festival(data: Dict[str, Any]) -> None:
    """Render pre-festival preparation section."""
    st.markdown("### 🪔 Pre‑Festival Preparation")
    
    # Tabs for different sections
    tab_steps, tab_puja, tab_food, tab_places, tab_timeline, tab_travel = st.tabs(
        ["🧹 Steps", "🛕 Puja Items", "🍽️ Food", "🧭 Places to Visit", "📅 Timeline", "🚆 Travel"]
    )

    with tab_steps:
        steps = data.get("ritual_preparation_steps", [])
        if steps:
            for i, step in enumerate(steps, 1):
                st.markdown(f"☐ **{i}.** {step}")

    with tab_puja:
        puja_items = data.get("puja_items_checklist", [])
        if puja_items:
            col1, col2 = st.columns(2)
            mid = len(puja_items) // 2 + len(puja_items) % 2
            with col1:
                for item in puja_items[:mid]:
                    st.markdown(f"🪔 {item}")
            with col2:
                for item in puja_items[mid:]:
                    st.markdown(f"🪔 {item}")

    with tab_food:
        food = data.get("food_preparation", [])
        if food:
            for dish in food:
                st.markdown(
                    f"""
                    <div style="
                        background: {COLORS['saffron_bg']};
                        padding: 12px 16px;
                        border-radius: 8px;
                        margin-bottom: 8px;
                        border-left: 4px solid {COLORS['saffron']};
                    ">
                        🍛 {dish}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_places:
        places = data.get("popular_places_to_visit", [])
        if places:
            for idx, place in enumerate(places, 1):
                name = place.get("place", "")
                suggestion = place.get("suggestion", "")
                query = name.replace(" ", "+")
                
            st.markdown(
                    f"""
                    <div style="
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        padding: 20px;
                        margin-bottom: 20px;
                        border-left: 4px solid {COLORS['deep_green_light']};
                    ">
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            margin-bottom: 12px;
                        ">
                            <div style="
                                font-weight: 600;
                                color: {COLORS['deep_green']};
                                font-size: 1.1rem;
                                display: flex;
                                align-items: center;
                                gap: 8px;
                            ">
                                <span>📍</span>
                                <span>{name}</span>
                            </div>
                        </div>
                        <div style="
                            color: #555;
                            font-size: 0.95rem;
                            line-height: 1.6;
                            margin-bottom: 12px;
                            padding-left: 28px;
                        ">
                            {suggestion}
                        </div>
                        <div style="padding-left: 28px;">
                            <a href="https://www.google.com/maps/search/?api=1&query={query}" 
                               target="_blank"
                               style="
                                   color: {COLORS['deep_green_light']};
                                   text-decoration: none;
                                   font-weight: 500;
                                   font-size: 0.9rem;
                               ">
                                🗺️ Open in Google Maps →
                            </a>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No places to visit information available")

    with tab_timeline:
        # Schedule timeline - Layout: T-3 and T-1 side by side, T-7 below spanning full width
        schedule = data.get("schedule", {})
        if schedule:
            st.markdown("#### 📅 Timeline")
            
            # Top row: T-3 and T-1 side by side
            col_t3, col_t1 = st.columns(2)
            
            with col_t3:
                t3_items = schedule.get("T-3_days", [])
                if t3_items:
                    items_html = "".join([f"<li style='margin-bottom: 8px; color: #555; line-height: 1.5;'>{item}</li>" for item in t3_items])
                    st.markdown(
                        f"""
                        <div style="
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            overflow: hidden;
                            margin-bottom: 16px;
                        ">
                            <div style="
                                background: {COLORS['saffron']};
                                padding: 12px 16px;
                                color: white;
                                font-weight: 600;
                                font-size: 0.95rem;
                                display: flex;
                                align-items: center;
                                gap: 8px;
                            ">
                                <span>📅</span>
                                <span>T-3 days</span>
                            </div>
                            <div style="padding: 16px;">
                                <ul style="margin: 0; padding-left: 20px; list-style-type: disc;">
                                    {items_html}
                                </ul>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            
            with col_t1:
                t1_items = schedule.get("T-1_day", [])
                if t1_items:
                    items_html = "".join([f"<li style='margin-bottom: 8px; color: #555; line-height: 1.5;'>{item}</li>" for item in t1_items])
                    st.markdown(
                        f"""
                        <div style="
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            overflow: hidden;
                            margin-bottom: 16px;
                        ">
                            <div style="
                                background: {COLORS['deep_green_light']};
                                padding: 12px 16px;
                                color: white;
                                font-weight: 600;
                                font-size: 0.95rem;
                                display: flex;
                                align-items: center;
                                gap: 8px;
                            ">
                                <span>⏰</span>
                                <span>T-1 day</span>
                            </div>
                            <div style="padding: 16px;">
                                <ul style="margin: 0; padding-left: 20px; list-style-type: disc;">
                                    {items_html}
                                </ul>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            
            # Bottom: T-7 spanning full width
            t7_items = schedule.get("T-7_days", [])
            if t7_items:
                items_html = "".join([f"<li style='margin-bottom: 8px; color: #555; line-height: 1.5;'>{item}</li>" for item in t7_items])
                st.markdown(
                    f"""
                    <div style="
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        overflow: hidden;
                        margin-bottom: 16px;
                    ">
                        <div style="
                            background: {COLORS['saffron']};
                            padding: 12px 16px;
                            color: white;
                            font-weight: 600;
                            font-size: 0.95rem;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                        ">
                            <span>📅</span>
                            <span>T-7 days</span>
                        </div>
                        <div style="padding: 16px;">
                            <ul style="margin: 0; padding-left: 20px; list-style-type: disc;">
                                {items_html}
                            </ul>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No timeline schedule available")

    with tab_travel:
        # Travel plan info box
        travel = data.get("guest_or_travel_plan", {})
        if travel.get("is_travel_suggested", False):
            note = travel.get("note", "")
            st.markdown(
                f"""
                <div style="
                    background: {COLORS['deep_green_bg']};
                    padding: 20px;
                    border-radius: 12px;
                    border-left: 4px solid {COLORS['deep_green_light']};
                    margin-top: 16px;
                ">
                    <div style="font-weight:600; color:{COLORS['deep_green']}; margin-bottom:12px; font-size:1.1rem;">
                        🚆 Travel Recommended
                    </div>
                    <div style="color:#555; line-height:1.6;">
                        {note}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No travel recommendations for this festival")


def render_festival_day(data: Dict[str, Any]) -> None:
    """Render festival day experience with card-style sections."""
    st.markdown("### 📅 Festival‑Day Experience")

    # Timeline blocks with card styling
    timeline_sections = [
        ("Early Morning", "🌅", data.get("early_morning", []), COLORS["saffron"]),
        ("Morning", "🌞", data.get("morning", []), COLORS["marigold"]),
        ("Mid Day", "🌤️", data.get("mid_day", []), COLORS["deep_green_light"]),
        ("Evening", "🌙", data.get("evening", []), "#0EA5E9"),
    ]
    
    for title, icon, items, color in timeline_sections:
        if items:
            items_html = "".join([f"<li style='margin-bottom: 10px; color: #555; line-height: 1.5;'>{item}</li>" for item in items])
            st.markdown(
                f"""
                <div style="
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    overflow: hidden;
                    margin-bottom: 20px;
                ">
                    <div style="
                        background: {color};
                        padding: 14px 18px;
                        color: white;
                        font-weight: 600;
                        font-size: 1rem;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    ">
                        <span style="font-size: 1.3rem;">{icon}</span>
                        <span>{title}</span>
                    </div>
                    <div style="padding: 18px;">
                        <ul style="margin: 0; padding-left: 20px; list-style-type: disc;">
                            {items_html}
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    # Family tips info box
    tips = data.get("family_friendly_tips", [])
    if tips:
        st.markdown(
            f"""
            <div style="
                background: {COLORS['deep_green_bg']};
                padding: 20px;
                border-radius: 12px;
                border: 2px solid {COLORS['deep_green_light']}44;
                margin-top: 16px;
            ">
                <div style="font-weight:600; color:{COLORS['deep_green']}; font-size:1.1rem; margin-bottom:12px;">
                    👨‍👩‍👧 Family Tips
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for tip in tips:
            st.markdown(f"💡 {tip}")


def render_shareables(data: Dict[str, Any], pre_festival_data: Dict[str, Any]) -> None:
    """Render shareable content with copy buttons."""
    st.markdown("### 📲 Shareables")

    # Get puja items from pre_festival data
    puja_items = pre_festival_data.get("puja_items_checklist", [])
    puja_text = "\n".join([f"• {item}" for item in puja_items]) if puja_items else ""
    
    tasks_text = data.get("tasks_text", "")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Things to purchase**")
        if puja_text:
            # Use HTML/JS for copy functionality
            safe_text = puja_text.replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
            st.markdown(
                f"""
                <button onclick="navigator.clipboard.writeText('{safe_text}'); alert('Copied to clipboard!');" 
                        style="
                            background-color: {COLORS['saffron']};
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 8px;
                            cursor: pointer;
                            margin-bottom: 8px;
                        ">
                    📋 Copy to clipboard
                </button>
                """,
                unsafe_allow_html=True,
            )
            st.text_area("Puja Items", value=puja_text, height=120, key="puja_display", label_visibility="collapsed")
        else:
            st.info("No puja items available")
    
    with col2:
        st.markdown("**Tasks – Share Text**")
        if tasks_text:
            # Use HTML/JS for copy functionality
            safe_text = tasks_text.replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
            st.markdown(
                f"""
                <button onclick="navigator.clipboard.writeText('{safe_text}'); alert('Copied to clipboard!');" 
                        style="
                            background-color: {COLORS['saffron']};
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 8px;
                            cursor: pointer;
                            margin-bottom: 8px;
                        ">
                    📋 Copy to clipboard
                </button>
                """,
                unsafe_allow_html=True,
            )
            st.text_area("Tasks Share Text", value=tasks_text, height=120, key="tasks_display", label_visibility="collapsed")
        else:
            st.info("No tasks text available")


def render_metadata(data: Dict[str, Any]) -> None:
    """Render metadata footer."""
    gen = data.get("generated_at", "")
    loc = data.get("location_context", "")
    ver = data.get("agent_version", "")
    
    # Format generated_at if it's a timestamp
    if gen:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(gen.replace("Z", "+00:00"))
            gen = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    
    st.markdown(
        f"""
        <div style="
            text-align: center;
            color: #666;
            font-size: 0.85rem;
            padding: 16px;
        ">
            Generated at • {gen} • {loc} • {ver}
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Utsava Sathi - Nuakhai",
        layout="wide",
        page_icon="🪔",
    )

    # Custom CSS for warm palette
    st.markdown(
        f"""
        <style>
        .main {{
            background-color: #FFFBF5;
        }}
        .stButton>button {{
            background-color: {COLORS['saffron']};
            color: white;
            border-radius: 8px;
            border: none;
            padding: 8px 16px;
        }}
        .stButton>button:hover {{
            background-color: {COLORS['saffron_light']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 2])

    with left:
        st.markdown("#### Ask Utsava Sathi")
        prompt = st.text_area(
            "Describe your festival request:",
            value="Plan Nuakhai in Bhubaneswar for a family of 3 with one small child.",
            height=120,
        )
        use_agent = st.button("✨ Generate via Gemini Agent")

        plan: Dict[str, Any] = {}

        if use_agent and prompt.strip():
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.info("🔄 Initializing multi-agent system...")
            
            try:
                logging.info(f"Calling Utsava Sathi API with prompt: {prompt.strip()}")
                progress_bar.progress(10)
                status_text.info("🔄 Calling coordinator agent...")
                
                resp = requests.post(
                    "http://127.0.0.1:8006/plan",
                    json={
                        "prompt": prompt.strip(),
                        "use_multi_agent": True
                    },
                    timeout=180,  # Increased timeout for multi-agent execution
                )
                progress_bar.progress(90)
                status_text.info("✅ Processing response...")
                
                resp.raise_for_status()
                plan = resp.json()
                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()
                st.success("✅ FestivalPlan generated from agent!")
            except requests.exceptions.Timeout as e:
                progress_bar.empty()
                status_text.empty()
                st.error(
                    f"⏱️ API call timed out after 180 seconds. "
                    f"The multi-agent system may be taking longer than expected. "
                    f"Please try again or use a simpler query."
                )
                st.info("💡 Tip: The multi-agent system calls 4 agents sequentially, which can take time.")
                plan = {}
            except requests.exceptions.ConnectionError as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"🔌 Could not connect to API server. Is it running on http://127.0.0.1:8006?")
                st.info("💡 Make sure the API server is running: `cd ui && uvicorn api:app --port 8006`")
                plan = {}
            except requests.exceptions.HTTPError as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ API returned an error (HTTP {resp.status_code}): {e}")
                plan = {}
            except requests.exceptions.RequestException as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ API request failed: {e}")
                plan = {}
            except json.JSONDecodeError as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Invalid JSON response from API: {e}")
                plan = {}
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Unexpected error: {e}")
                plan = {}

    with right:
        # Try to load sample data if no plan from API
        if not plan:
            sample_path = ROOT_DIR / "sample_data" / "nuakhai.json"
            if sample_path.exists():
                try:
                    with open(sample_path, "r", encoding="utf-8") as f:
                        plan = json.load(f)
                    st.info("📄 Displaying sample data from nuakhai.json")
                except Exception as e:
                    st.warning(f"Could not load sample data: {e}")
        
        if plan:
            # Create tabs for main sections
            tab_overview, tab_prefestival, tab_festivalday, tab_shareables = st.tabs([
                "🪔 Overview",
                "📋 Pre-Festival",
                "📅 Festival Day",
                "📲 Shareables"
            ])
            
            with tab_overview:
                render_festival_overview(plan.get("festival_overview", {}))
                render_metadata(plan.get("metadata", {}))
            
            with tab_prefestival:
                render_pre_festival(plan.get("pre_festival", {}))
            
            with tab_festivalday:
                render_festival_day(plan.get("festival_day", {}))
            
            with tab_shareables:
                render_shareables(plan.get("shareables", {}), plan.get("pre_festival", {}))
        else:
            st.info("Awaiting valid FestivalPlan JSON or agent output...")


if __name__ == "__main__":
    main()
