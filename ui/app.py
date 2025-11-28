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


def render_theme_chips(themes: List[str]) -> None:
    """Render festival themes as rounded colored chips."""
    chip_html = ""
    colors = ["#ea580c", "#f97316", "#16a34a", "#0ea5e9", "#a855f7"]
    for i, theme in enumerate(themes):
        color = colors[i % len(colors)]
        chip_html += f"""
        <span style="
            display:inline-block;
            padding:4px 10px;
            margin:3px;
            border-radius:999px;
            background:{color}22;
            color:{color};
            font-size:0.8rem;
        ">{theme}</span>
        """
    st.markdown(chip_html, unsafe_allow_html=True)


def render_festival_overview(data: Dict[str, Any]) -> None:
    st.markdown("### 🪔 Festival Overview")
    name = data.get("name", "")
    local_name = data.get("local_name", "")
    title = f"{name} · {local_name}" if local_name else name

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown(f"## {title}")
        st.markdown(f"**Why celebrated:** {data.get('why_celebrated', '')}")
        with st.expander("📖 Short Story"):
            st.write(data.get("short_story", ""))
        st.markdown("**Themes:**")
        render_theme_chips(data.get("themes", []))
    with col_right:
        st.markdown(
            """
            <div style="
                background:linear-gradient(135deg,#f97316,#fb923c);
                border-radius:16px;
                padding:16px;
                text-align:center;
                color:white;
            ">
              <div style="font-size:2rem;">🎉</div>
              <div style="font-weight:600;">Festival Illustration</div>
              <div style="font-size:0.8rem;opacity:0.9;">(Placeholder – use festival-specific art later)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_pre_festival(data: Dict[str, Any]) -> None:
    st.markdown("### 🪔 Pre‑Festival Preparation")
    steps = data.get("ritual_preparation_steps", [])
    puja_items = data.get("puja_items_checklist", [])
    food = data.get("food_preparation", [])
    places = data.get("popular_places_to_visit", [])
    schedule = data.get("schedule", {})
    travel = data.get("guest_or_travel_plan", {})

    tab_steps, tab_puja, tab_food, tab_places, tab_schedule, tab_travel = st.tabs(
        ["🧹 Ritual Steps", "🛕 Puja Items", "🍽️ Food", "🧭 Places", "🗓️ Schedule", "🚆 Guests / Travel"]
    )

    with tab_steps:
        for s in steps:
            st.checkbox(s, value=False)

    with tab_puja:
        st.markdown("**Puja Items Checklist**")
        icons = ["🪔", "🌸", "🕯️", "🍚", "🌿"]
        for i, item in enumerate(puja_items):
            icon = icons[i % len(icons)]
            st.markdown(f"- {icon} {item}")

    with tab_food:
        for dish in food:
            with st.expander(f"🍛 {dish.split('(')[0].strip()}"):
                st.write(dish)

    with tab_places:
        for place in places:
            name = place.get("place", "")
            suggestion = place.get("suggestion", "")
            st.markdown(f"**📍 {name}**")
            st.write(suggestion)
            query = name.replace(" ", "+")
            st.markdown(
                f"[Open in Google Maps](https://www.google.com/maps/search/?api=1&query={query})",
                unsafe_allow_html=False,
            )
            st.markdown("---")

    with tab_schedule:
        st.markdown("**Timeline**")
        def bullet(day_label: str, icon: str, items: List[str]) -> None:
            if not items:
                return
            st.markdown(f"**{icon} {day_label}**")
            for it in items:
                st.markdown(f"- {it}")

        bullet("T‑7 days", "📅", schedule.get("T-7_days", []))
        bullet("T‑3 days", "📆", schedule.get("T-3_days", []))
        bullet("T‑1 day", "⏰", schedule.get("T-1_day", []))

    with tab_travel:
        is_travel = bool(travel.get("is_travel_suggested", False))
        note = travel.get("note", "")
        badge_color = "#16a34a" if is_travel else "#f97316"
        badge_text = "Travel Recommended" if is_travel else "Local Celebration"
        st.markdown(
            f"""
            <span style="
                display:inline-block;
                padding:4px 12px;
                border-radius:999px;
                background:{badge_color}22;
                color:{badge_color};
                font-weight:600;
                font-size:0.85rem;
            ">{badge_text}</span>
            """,
            unsafe_allow_html=True,
        )
        st.write(note)


def render_festival_day(data: Dict[str, Any]) -> None:
    st.markdown("### 📅 Festival‑Day Experience")

    def section(title: str, icon: str, items: List[str]) -> None:
        st.markdown(f"**{icon} {title}**")
        for it in items:
            st.markdown(f"- {it}")

    section("Early Morning", "🌅", data.get("early_morning", []))
    section("Morning", "🌞", data.get("morning", []))
    section("Mid‑day", "🌤️", data.get("mid_day", []))
    section("Evening", "🌙", data.get("evening", []))

    tips = data.get("family_friendly_tips", [])
    if tips:
        st.markdown(
            """
            <div style="
                margin-top:0.75rem;
                padding:0.75rem 1rem;
                border-radius:12px;
                background:#022c22;
                border:1px solid #16a34a55;
            ">
              <div style="font-weight:600;margin-bottom:4px;">👨‍👩‍👧 Family‑friendly tips</div>
            """,
            unsafe_allow_html=True,
        )
        for tip in tips:
            st.markdown(f"- {tip}")
        st.markdown("</div>", unsafe_allow_html=True)


def render_copy_button(label: str, text: str, key: str) -> None:
    """Render a HTML+JS button that copies `text` to clipboard."""
    safe_text = text.replace("\\", "\\\\").replace("`", "\\`").replace('"', '\\"')
    html = f"""
    <button onclick="navigator.clipboard.writeText('{safe_text}');"
            style="margin-right:8px;padding:6px 14px;border-radius:999px;
                   background:#4f46e5;color:white;border:none;cursor:pointer;">
      {label}
    </button>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_shareables(data: Dict[str, Any]) -> None:
    st.markdown("### 📲 Shareables")

    puja_text = data.get("puja_items_text", "")
    tasks_text = data.get("tasks_text", "")

    st.markdown("**Puja Checklist**")
    render_copy_button("Copy Puja Checklist", puja_text, "copy_puja")
    st.code(puja_text or "(empty)", language="markdown")

    st.markdown("**Task List**")
    render_copy_button("Copy Task List", tasks_text, "copy_tasks")
    st.code(tasks_text or "(empty)", language="markdown")

    # WhatsApp share link placeholder
    base_msg = textwrap.shorten(tasks_text or puja_text or "", width=300, placeholder="...")
    import urllib.parse

    wa_text = urllib.parse.quote_plus(base_msg or "Utsava Sathi festival plan.")
    wa_url = f"https://wa.me/?text={wa_text}"
    st.markdown(f"[Share via WhatsApp]({wa_url})")


def render_metadata(data: Dict[str, Any]) -> None:
    st.markdown("---")
    gen = data.get("generated_at", "")
    loc = data.get("location_context", "")
    ver = data.get("agent_version", "")
    lang = data.get("language", "")
    st.markdown(
        f"Generated at: **{gen}** • {loc} • {ver} • {lang}",
    )


def main() -> None:
    st.set_page_config(
        page_title="Utsava Sathi – Odisha Festival Planner",
        layout="wide",
        page_icon="🪔",
    )

    default_json = '''{
  "festival_overview": {
    "name": "Nuakhai",
    "local_name": "Nuakhai Parab / Nabanna",
    "why_celebrated": "Nuakhai is an agricultural festival celebrated in Odisha to mark the consumption of the season's first harvested crops, especially rice. It's a thanksgiving to Mother Earth and the deities for a good harvest.",
    "short_story": "Nuakhai, meaning 'new food', is deeply rooted in the agrarian culture of Odisha. Legend has it that the festival was started in the 14th century by Raja Ramai Deo to encourage farming. It signifies a new beginning, unity, and gratitude for nature's bounty. The celebration involves offering the first grains to the presiding deity, followed by a family feast and exchange of greetings.",
    "themes": [
      "Harvest Festival",
      "Gratitude",
      "New Beginnings",
      "Family Unity",
      "Agricultural Prosperity"
    ]
  },
  "pre_festival": {
    "ritual_preparation_steps": [
      "Clean and decorate the house (Safa Sutura and Lipa Puchha).",
      "Adorn verandahs and mud walls with 'Jhuti' (rice powder designs).",
      "Purchase new clothes for all family members.",
      "Prepare for traditional dishes, especially sweets (Pitha) and savory items.",
      "Families living away often plan to return to their native places for the festival."
    ],
    "puja_items_checklist": [
      "Newly harvested rice (Nua Dhan)",
      "Fruits",
      "Flowers",
      "Sandalwood paste",
      "Incense sticks",
      "Camphor",
      "Diyas (oil lamps)",
      "New clothes for deities (optional)",
      "Sweets and other prasad items"
    ],
    "food_preparation": [
      "Prepare traditional sweets like Arisa Pitha, Manda Pitha, Kakara Pitha.",
      "Make savory dishes like Ghanta Tarkari, Bhendi Kardi Khatta.",
      "Prepare rice pudding (Kheeri) and Muga Rasabara.",
      "Non-vegetarian dishes, especially mutton curry, are also prepared by some families.",
      "Ensure fresh, locally sourced ingredients are used."
    ],
    "popular_places_to_visit": [
      {
        "place": "Lingaraj Temple",
        "suggestion": "Visit early in the morning for a serene experience. Families can offer prayers and witness the temple's grandeur."
      },
      {
        "place": "Mukteswara Temple",
        "suggestion": "Known for its intricate Kalinga architecture, it's a beautiful and peaceful place for a family visit."
      },
      {
        "place": "Nandankanan Zoological Park",
        "suggestion": "A great place for children to see a variety of animals and enjoy a day out. Offers a 'zoo safari' experience."
      },
      {
        "place": "Ekamra Kanan Botanical Garden",
        "suggestion": "Explore diverse plant collections. It's a peaceful spot for a family picnic and has play areas for kids."
      },
      {
        "place": "Regional Science Centre",
        "suggestion": "Engaging interactive exhibits and shows for children, making learning fun."
      }
    ],
    "schedule": {
      "T-7_days": [
        "Begin house cleaning and minor repairs.",
        "Start planning the menu for the festival feast.",
        "Purchase necessary ingredients for sweets and dishes."
      ],
      "T-3_days": [
        "Buy new clothes for the family.",
        "Decorate the house with 'Jhuti' or other traditional art.",
        "Prepare some sweets or savories that can be stored."
      ],
      "T-1_day": [
        "Finalize all food preparations.",
        "Prepare the puja items.",
        "Ensure all family members are ready and comfortable for the next day.",
        "If traveling from afar, ensure travel arrangements are complete."
      ]
    },
    "guest_or_travel_plan": {
      "is_travel_suggested": true,
      "note": "It is customary for family members, even those living in cities, to return to their native villages or homes to celebrate Nuakhai with their elders and the extended family."
    }
  },
  "festival_day": {
    "early_morning": [
      "Wake up early and take a ritual bath.",
      "Wear new clothes.",
      "Perform morning prayers and offer the 'Nua' (newly harvested rice) to the household deity or the presiding deity of the area/village."
    ],
    "morning": [
      "The eldest member of the family distributes the 'Nua' (prasad) to all family members.",
      "The family partakes in the feast, starting with the new rice and traditional dishes.",
      "Junior members of the family offer greetings and seek blessings from elders ('Nuakhai Juhar')."
    ],
    "mid_day": [
      "Enjoy the festive meal with family.",
      "Relax and spend quality time together.",
      "Some families might visit local temples to offer prayers."
    ],
    "evening": [
      "Exchange greetings and well wishes with relatives, friends, and neighbors ('Nuakhai Juhar').",
      "Participate in community gatherings or 'Nuakhai Bhetghat' which may include folk dances and songs.",
      "Enjoy the festive atmosphere and the shared joy of the harvest."
    ],
    "family_friendly_tips": [
      "Involve the child in simple pre-festival activities like decorating or helping with mild food prep.",
      "Explain the significance of Nuakhai in a way the child can understand.",
      "During the festival day, keep the rituals engaging for the child, perhaps by explaining the meaning of 'Nuakhai Juhar'.",
      "Visit family-friendly places like Nandankanan Zoological Park or Ekamra Kanan Botanical Garden for a day out.",
      "Ensure the child gets to taste traditional sweets and dishes prepared for the festival."
    ]
  },
  "shareables": {
    "puja_items_text": "For Nuakhai, you'll need the newly harvested rice (Nua Dhan), along with offerings like fruits, flowers, incense, and camphor. Don't forget new clothes for prayers and delicious prasad items. #Nuakhai #OdishaFestival #HarvestFestival",
    "tasks_text": "Get ready for Nuakhai! Clean and decorate your home, buy new clothes, and prepare delicious traditional dishes. Families often travel back home for this special harvest festival. #NuakhaiPrep #FestivalVibes #OdishaCulture"
  },
  "metadata": {
    "generated_at": "2025-11-28T11:53:13.800978Z",
    "location_context": "Bhubaneswar, Odisha, India",
    "agent_version": "utsava_sathi_festival_planner",
    "language": "en"
  }
}'''

    left, right = st.columns([1, 2])

    with left:
        st.markdown("#### Ask Utsava Sathi")
        prompt = st.text_area(
            "Describe your festival request:",
            value="Plan Nuakhai in Bhubaneswar for a family of 3 with one small child.",
            height=120,
        )
        use_agent = st.button("✨ Generate via Gemini Agent")

        import json as _json

        plan: Dict[str, Any] = {}

        if use_agent and prompt.strip():
            with st.spinner("Calling Utsava Sathi API..."):
                try:
                    logging.info(f"Calling Utsava Sathi API with prompt: {prompt.strip()}")
                    resp = requests.post(
                        "http://127.0.0.1:8006/plan",
                        json={
                          "prompt": prompt.strip(),
                          "use_multi_agent": True
                        },
                        timeout=60,
                    )
                    resp.raise_for_status()
                    plan = resp.json()
                    st.success("FestivalPlan generated from agent.")
                except requests.exceptions.Timeout as e:
                    st.error(f"API call timed out after 60 seconds: {e}")
                except requests.exceptions.ConnectionError as e:
                    st.error(f"Could not connect to API server. Is it running? Error: {e}")
                except requests.exceptions.HTTPError as e:
                    st.error(f"API returned an error (HTTP {resp.status_code}): {e}")
                except requests.exceptions.RequestException as e:
                    st.error(f"API request failed: {e}")
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON response from API: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    plan = {}


    with right:
        if plan:
            render_festival_overview(plan.get("festival_overview", {}))
            render_pre_festival(plan.get("pre_festival", {}))
            render_festival_day(plan.get("festival_day", {}))
            render_shareables(plan.get("shareables", {}))
            render_metadata(plan.get("metadata", {}))
        else:
            st.info("Awaiting valid FestivalPlan JSON or agent output...")


if __name__ == "__main__":
    main()


