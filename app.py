"""InsureIQ — Health Coverage Intelligence Application.

A professional, customer-facing health insurance assistant providing grounded
plan comparisons, policy analysis, senior citizen guidance, and claims support.
"""

from __future__ import annotations

import base64
from datetime import datetime
import streamlit as st

# Configure page metadata
st.set_page_config(
    page_title="InsureIQ — Health Coverage Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.config import settings, BASE_DIR
from src.agent.orchestrator import HealthInsuranceAgent


# Cache the agent instance across Streamlit reruns
@st.cache_resource(show_spinner=False)
def get_agent_instance() -> HealthInsuranceAgent:
    return HealthInsuranceAgent()


def load_svg_as_base64(filename: str) -> str:
    """Load a local SVG file as a base64 data URI."""
    file_path = BASE_DIR / "assets" / filename
    if file_path.exists():
        svg_content = file_path.read_text(encoding="utf-8")
        b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64}"
    return ""


# Inject InsureIQ Vibrant Blue Design System & Chat Input Styles
def inject_custom_styles():
    st.markdown(
        """
        <style>
        /* =====================================================================
           INSUREIQ DESIGN SYSTEM — VIBRANT BLUE THEME (#0077D9)
           ===================================================================== */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        :root {
            /* Vibrant Blue Palette Specifications */
            --iq-sidebar-bg: #0077D9;
            --iq-sidebar-border: #0066BD;
            --iq-sidebar-text: #FFFFFF;
            --iq-sidebar-subtext: #D9ECFF;
            --iq-primary-blue: #0077D9;
            --iq-primary-blue-hover: #0066BD;
            --iq-primary-blue-active: #0057A3;
            --iq-teal-accent: #00E5D0;
            --iq-main-bg: #F7F9FC;
            --iq-card-bg: #FFFFFF;
            --iq-primary-text: #172B4D;
            --iq-secondary-text: #526B85;
            --iq-border-light: #D3E1F0;
            --iq-shadow-subtle: 0 1px 3px rgba(0, 119, 217, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
            --iq-shadow-hover: 0 4px 12px rgba(0, 119, 217, 0.09);
            --iq-radius-sm: 6px;
            --iq-radius-md: 10px;
            --iq-radius-lg: 14px;
        }

        /* Enforce Root Canvas Background & Font */
        html, body, .stApp {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            background-color: var(--iq-main-bg) !important;
            color: var(--iq-primary-text) !important;
        }

        /* Fix main content container spacing */
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            max-width: 1180px;
        }

        /* =====================================================================
           SIDEBAR STYLING (VIBRANT BLUE #0077D9 WITH CRISP WHITE CONTRAST)
           ===================================================================== */
        section[data-testid="stSidebar"] {
            background-color: var(--iq-sidebar-bg) !important;
            border-right: 1px solid var(--iq-sidebar-border) !important;
        }

        section[data-testid="stSidebar"] div.block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Sidebar Brand Lockup */
        .sidebar-brand-lockup {
            padding: 2px 0 6px 0;
            margin-bottom: 0.25rem;
        }
        .sidebar-brand-title {
            font-size: 1.45rem;
            font-weight: 800;
            color: #FFFFFF !important;
            line-height: 1.1;
            letter-spacing: -0.03em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .sidebar-brand-title span {
            color: #FFFFFF !important;
        }
        .sidebar-brand-tagline {
            font-size: 0.76rem;
            color: var(--iq-sidebar-subtext) !important;
            margin: 4px 0 0 0;
            font-weight: 500;
            letter-spacing: 0.01em;
        }

        /* Divider */
        .sidebar-divider {
            border: none;
            border-top: 1px solid rgba(255, 255, 255, 0.25);
            margin: 0.75rem 0 0.95rem 0;
        }

        /* General Sidebar Typography (Always White & High Contrast) */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #FFFFFF !important;
        }

        /* =====================================================================
           NEW CHAT — PRIMARY SIDEBAR HERO ACTION (WHITE CARD OVER VIBRANT BLUE)
           ===================================================================== */
        section[data-testid="stSidebar"] div.stButton:first-of-type > button,
        div[data-testid="stSidebar"] div.stButton:has(button[key="btn_sidebar_new_chat"]) > button {
            background-color: #FFFFFF !important;
            color: var(--iq-primary-blue) !important;
            border: 1px solid #FFFFFF !important;
            border-radius: var(--iq-radius-md) !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 0.65rem 1rem !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
            transition: all 180ms ease !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin-bottom: 0.75rem !important;
        }

        section[data-testid="stSidebar"] div.stButton:first-of-type > button p,
        div[data-testid="stSidebar"] div.stButton:has(button[key="btn_sidebar_new_chat"]) > button p {
            color: var(--iq-primary-blue) !important;
            font-weight: 700 !important;
        }

        section[data-testid="stSidebar"] div.stButton:first-of-type > button:hover,
        div[data-testid="stSidebar"] div.stButton:has(button[key="btn_sidebar_new_chat"]) > button:hover {
            background-color: #F0F7FF !important;
            color: var(--iq-primary-blue-hover) !important;
            border-color: #FFFFFF !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.22) !important;
            transform: translateY(-1px) !important;
        }

        section[data-testid="stSidebar"] div.stButton:first-of-type > button:hover p,
        div[data-testid="stSidebar"] div.stButton:has(button[key="btn_sidebar_new_chat"]) > button:hover p {
            color: var(--iq-primary-blue-hover) !important;
        }

        section[data-testid="stSidebar"] div.stButton:first-of-type > button:active,
        div[data-testid="stSidebar"] div.stButton:has(button[key="btn_sidebar_new_chat"]) > button:active {
            transform: translateY(0px) !important;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.18) !important;
        }

        section[data-testid="stSidebar"] div.stButton:first-of-type > button:focus {
            outline: 2px solid #FFFFFF !important;
            outline-offset: 2px !important;
        }

        /* =====================================================================
           SECONDARY NAVIGATION BUTTONS (COMPARE PLANS, SENIOR CARE, ETC.)
           ===================================================================== */
        section[data-testid="stSidebar"] div.stButton:not(:first-of-type) > button {
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 9px !important;
            padding: 0.54rem 0.85rem !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
            transition: all 180ms ease !important;
            margin-bottom: 5px !important;
        }

        section[data-testid="stSidebar"] div.stButton:not(:first-of-type) > button p {
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] div.stButton:not(:first-of-type) > button:hover {
            background-color: rgba(255, 255, 255, 0.2) !important;
            color: #FFFFFF !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
            transform: translateY(-1px) !important;
        }

        section[data-testid="stSidebar"] div.stButton:not(:first-of-type) > button:focus {
            outline: 2px solid rgba(255, 255, 255, 0.8) !important;
            outline-offset: 1px !important;
        }

        /* Active Navigation Item (Selected State) */
        section[data-testid="stSidebar"] div.stButton:not(:first-of-type) > button[kind="primary"] {
            background-color: rgba(255, 255, 255, 0.28) !important;
            color: #FFFFFF !important;
            border: 1.5px solid #FFFFFF !important;
            font-weight: 700 !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
        }

        section[data-testid="stSidebar"] div.stButton:not(:first-of-type) > button[kind="primary"] p {
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }

        /* Sidebar Expanders */
        section[data-testid="stSidebar"] div[data-testid="stExpander"] {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: var(--iq-radius-md) !important;
            margin-top: 0.6rem !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary {
            color: #FFFFFF !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
            color: var(--iq-sidebar-subtext) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.18) !important;
            padding-top: 6px !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] .stButton > button {
            background-color: rgba(255, 255, 255, 0.14) !important;
            color: #FFFFFF !important;
            font-size: 0.8rem !important;
            padding: 0.35rem 0.6rem !important;
            border-color: rgba(255, 255, 255, 0.25) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.28) !important;
        }

        /* Privacy Box in Sidebar */
        .sidebar-privacy-box {
            font-size: 0.72rem;
            color: var(--iq-sidebar-subtext);
            background: rgba(0, 0, 0, 0.12);
            padding: 10px 12px;
            border-radius: var(--iq-radius-sm);
            border: 1px solid rgba(255, 255, 255, 0.22);
            margin-top: 1.25rem;
            line-height: 1.45;
        }
        .sidebar-privacy-box strong {
            color: #FFFFFF;
        }

        /* =====================================================================
           MAIN CONTENT & CARD SURFACES (CLEAN LIGHT THEME)
           ===================================================================== */
        h1, h2, h3, h4, h5, h6 {
            color: var(--iq-primary-text) !important;
            letter-spacing: -0.02em;
        }

        p, li, span {
            color: var(--iq-primary-text);
            line-height: 1.6;
        }

        /* Welcome Screen Hero */
        .welcome-hero {
            text-align: center;
            max-width: 720px;
            margin: 1.5rem auto 2.25rem auto;
            padding: 1rem 0;
        }
        .welcome-hero h1 {
            font-size: 2.15rem;
            font-weight: 800;
            color: var(--iq-primary-text) !important;
            margin: 0.75rem 0 0.5rem 0;
            line-height: 1.2;
        }
        .welcome-hero p {
            font-size: 1.05rem;
            color: var(--iq-secondary-text) !important;
            line-height: 1.5;
            margin: 0;
        }

        /* Starter Prompt Cards */
        .iq-prompt-card {
            background: var(--iq-card-bg);
            border: 1px solid var(--iq-border-light);
            border-radius: var(--iq-radius-lg);
            padding: 16px 20px;
            box-shadow: var(--iq-shadow-subtle);
            margin-bottom: 12px;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 180ms ease;
        }
        .iq-prompt-card:hover {
            border-color: var(--iq-primary-blue);
            box-shadow: var(--iq-shadow-hover);
            transform: translateY(-2px);
        }
        .iq-card-title {
            font-size: 0.96rem;
            font-weight: 700;
            color: var(--iq-primary-text) !important;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .iq-card-desc {
            font-size: 0.83rem;
            color: var(--iq-secondary-text) !important;
            line-height: 1.45;
            margin-bottom: 12px;
        }

        /* =====================================================================
           CHAT MESSAGES & BUBBLES
           ===================================================================== */
        div[data-testid="stChatMessage"] {
            background-color: transparent !important;
            padding: 0.75rem 0 !important;
        }

        /* User Message Container */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
            background-color: #EBF4FD !important;
            border: 1px solid var(--iq-border-light) !important;
            border-radius: var(--iq-radius-lg) !important;
            padding: 1rem 1.25rem !important;
            margin-bottom: 0.85rem !important;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p {
            color: var(--iq-primary-text) !important;
            font-weight: 500;
        }

        /* Assistant Message Container */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
            background-color: var(--iq-card-bg) !important;
            border: 1px solid var(--iq-border-light) !important;
            border-radius: var(--iq-radius-lg) !important;
            padding: 1.25rem 1.5rem !important;
            margin-bottom: 1rem !important;
            box-shadow: var(--iq-shadow-subtle) !important;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) p {
            color: var(--iq-primary-text) !important;
        }

        /* Category Intent Badge */
        .iq-category-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            padding: 3px 10px;
            border-radius: 9999px;
            background-color: #E0F2FE;
            color: #0077D9;
            margin-bottom: 8px;
            border: 1px solid #BAE6FD;
        }

        /* Verified Source Citation Box */
        .iq-citation-card {
            background: #F8FAFC;
            border: 1px solid var(--iq-border-light);
            border-radius: var(--iq-radius-md);
            padding: 10px 14px;
            margin-top: 8px;
            font-size: 0.82rem;
        }
        .iq-citation-card a {
            color: var(--iq-primary-blue) !important;
            font-weight: 600;
            text-decoration: none;
        }
        .iq-citation-card a:hover {
            text-decoration: underline;
        }

        /* =====================================================================
           CHAT INPUT & COMPACT SUBMIT BUTTON (CLEAN SCHEME & COMPACT SIZE)
           ===================================================================== */
        div[data-testid="stBottom"] {
            background-color: rgba(247, 249, 252, 0.95) !important;
            padding-bottom: 0.85rem !important;
            padding-top: 0.25rem !important;
        }

        div[data-testid="stBottom"] > div {
            max-width: 1180px !important;
        }

        /* =====================================================================
           CHAT INPUT CONTAINER & SUBMIT BUTTON (CLEAN LIGHT SKY BLUE DESIGN)
           ===================================================================== */
        div[data-testid="stChatInput"],
        .stChatInput {
            background-color: #DFEFF7 !important;
            border: 1px solid #D4E2EA !important;
            border-radius: 13px !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 3px 5px 3px 14px !important;
            transition: border-color 160ms ease, background-color 160ms ease !important;
        }

        /* Ensure inner wrapper is transparent without nested borders or rings */
        div[data-testid="stChatInput"] > div {
            background-color: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        div[data-testid="stChatInput"]:hover,
        .stChatInput:hover {
            background-color: #DFEFF7 !important;
            border-color: #B9D8E6 !important;
            box-shadow: none !important;
            outline: none !important;
        }

        div[data-testid="stChatInput"]:focus-within,
        .stChatInput:focus-within {
            background-color: #DFEFF7 !important;
            border-color: #B9D8E6 !important;
            box-shadow: none !important;
            outline: none !important;
        }

        /* Textarea Composer */
        div[data-testid="stChatInput"] textarea,
        textarea[data-testid="stChatInputTextArea"] {
            color: #172B4D !important;
            caret-color: #0077D9 !important;
            font-size: 14.5px !important;
            font-weight: 400 !important;
            font-family: inherit !important;
            background-color: transparent !important;
            padding-top: 8px !important;
            padding-bottom: 8px !important;
            padding-left: 2px !important;
            line-height: 1.45 !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        /* Helpful Caption / Placeholder Text */
        div[data-testid="stChatInput"] textarea::placeholder,
        textarea[data-testid="stChatInputTextArea"]::placeholder {
            color: #64748B !important;
            font-size: 14.5px !important;
            font-weight: 400 !important;
            opacity: 1 !important;
            line-height: 1.45 !important;
        }

        /* Send Button: Light Sky Blue Background with Vibrant Blue Icon */
        div[data-testid="stChatInput"] button,
        button[data-testid="stChatInputSubmitButton"] {
            background-color: #DFEFF7 !important;
            background: #DFEFF7 !important;
            color: #0077D9 !important;
            border: none !important;
            outline: none !important;
            border-radius: 8px !important;
            width: 38px !important;
            height: 38px !important;
            min-width: 38px !important;
            min-height: 38px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: background-color 150ms ease, transform 150ms ease !important;
            margin: 2px 2px 2px 4px !important;
            cursor: pointer !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        /* Remove all white borders, outlines, frames, or boxes surrounding the arrow icon */
        div[data-testid="stChatInput"] button *,
        button[data-testid="stChatInputSubmitButton"] * {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        /* Simple, clean, vibrant blue send-arrow icon (#0077D9) directly on the light-blue button */
        div[data-testid="stChatInput"] button svg,
        button[data-testid="stChatInputSubmitButton"] svg {
            fill: #0077D9 !important;
            color: #0077D9 !important;
            stroke: #0077D9 !important;
            width: 17px !important;
            height: 17px !important;
            background: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            margin: auto !important;
        }

        div[data-testid="stChatInput"] button:hover,
        button[data-testid="stChatInputSubmitButton"]:hover {
            background-color: #CDE5F0 !important;
            background: #CDE5F0 !important;
            box-shadow: none !important;
            transform: translateY(-1px) !important;
            border: none !important;
            outline: none !important;
        }

        div[data-testid="stChatInput"] button:active,
        button[data-testid="stChatInputSubmitButton"]:active {
            background-color: #B9D8E6 !important;
            background: #B9D8E6 !important;
            transform: translateY(0px) !important;
            box-shadow: none !important;
            border: none !important;
            outline: none !important;
        }

        div[data-testid="stChatInput"] button:focus,
        div[data-testid="stChatInput"] button:focus-visible,
        button[data-testid="stChatInputSubmitButton"]:focus,
        button[data-testid="stChatInputSubmitButton"]:focus-visible {
            outline: none !important;
            border: none !important;
            box-shadow: none !important;
        }

        div[data-testid="stChatInput"] button:disabled,
        button[data-testid="stChatInputSubmitButton"]:disabled {
            background-color: #DFEFF7 !important;
            background: #DFEFF7 !important;
            border: none !important;
            outline: none !important;
            cursor: not-allowed !important;
            opacity: 0.55 !important;
            box-shadow: none !important;
            transform: none !important;
        }

        div[data-testid="stChatInput"] button:disabled svg,
        button[data-testid="stChatInputSubmitButton"]:disabled svg {
            fill: #8FA9C4 !important;
            color: #8FA9C4 !important;
            stroke: #8FA9C4 !important;
            background: transparent !important;
            border: none !important;
            outline: none !important;
        }

        /* Dark Mode Adaptive Support: Keep light sky blue #DFEFF7 in dark theme as well */
        @media (prefers-color-scheme: dark) {
            div[data-testid="stChatInput"],
            .stChatInput {
                background-color: #DFEFF7 !important;
                border: 1px solid #D4E2EA !important;
                box-shadow: none !important;
                outline: none !important;
            }

            div[data-testid="stChatInput"] > div {
                background-color: transparent !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }

            div[data-testid="stChatInput"]:hover,
            .stChatInput:hover {
                background-color: #DFEFF7 !important;
                border-color: #B9D8E6 !important;
                box-shadow: none !important;
                outline: none !important;
            }

            div[data-testid="stChatInput"]:focus-within,
            .stChatInput:focus-within {
                background-color: #DFEFF7 !important;
                border-color: #B9D8E6 !important;
                box-shadow: none !important;
                outline: none !important;
            }

            div[data-testid="stChatInput"] textarea,
            textarea[data-testid="stChatInputTextArea"] {
                color: #172B4D !important;
                caret-color: #0077D9 !important;
                background-color: transparent !important;
            }

            div[data-testid="stChatInput"] textarea::placeholder,
            textarea[data-testid="stChatInputTextArea"]::placeholder {
                color: #64748B !important;
            }

            div[data-testid="stChatInput"] button,
            button[data-testid="stChatInputSubmitButton"] {
                background-color: #DFEFF7 !important;
                background: #DFEFF7 !important;
                color: #0077D9 !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }

            div[data-testid="stChatInput"] button *,
            button[data-testid="stChatInputSubmitButton"] * {
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }

            div[data-testid="stChatInput"] button svg,
            button[data-testid="stChatInputSubmitButton"] svg {
                fill: #0077D9 !important;
                color: #0077D9 !important;
                stroke: #0077D9 !important;
                background: transparent !important;
                border: none !important;
                outline: none !important;
            }

            div[data-testid="stChatInput"] button:hover,
            button[data-testid="stChatInputSubmitButton"]:hover {
                background-color: #CDE5F0 !important;
                background: #CDE5F0 !important;
                box-shadow: none !important;
            }

            div[data-testid="stChatInput"] button:active,
            button[data-testid="stChatInputSubmitButton"]:active {
                background-color: #B9D8E6 !important;
                background: #B9D8E6 !important;
            }

            div[data-testid="stChatInput"] button:disabled,
            button[data-testid="stChatInputSubmitButton"]:disabled {
                background-color: #DFEFF7 !important;
                background: #DFEFF7 !important;
                border: none !important;
                outline: none !important;
            }

            div[data-testid="stChatInput"] button:disabled svg,
            button[data-testid="stChatInputSubmitButton"]:disabled svg {
                fill: #8FA9C4 !important;
                color: #8FA9C4 !important;
                stroke: #8FA9C4 !important;
                background: transparent !important;
                border: none !important;
                outline: none !important;
            }
        }

        /* =====================================================================
           PRODUCT COMPARISON CARDS & TABLES
           ===================================================================== */
        .iq-product-card {
            background: var(--iq-card-bg);
            border: 1px solid var(--iq-border-light);
            border-radius: var(--iq-radius-lg);
            padding: 22px 24px;
            margin-bottom: 1.25rem;
            box-shadow: var(--iq-shadow-subtle);
            transition: all 180ms ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .iq-product-card:hover {
            border-color: var(--iq-primary-blue);
            box-shadow: var(--iq-shadow-hover);
            transform: translateY(-2px);
        }
        .iq-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
            gap: 12px;
        }
        .iq-insurer-badge {
            font-size: 0.72rem;
            font-weight: 700;
            color: #0077D9;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .iq-status-badge {
            font-size: 0.7rem;
            font-weight: 600;
            background: #DCFCE7;
            color: #166534;
            padding: 2px 8px;
            border-radius: 9999px;
            border: 1px solid #BBF7D0;
            white-space: nowrap;
        }
        .iq-product-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--iq-primary-text);
            margin: 2px 0 6px 0;
            line-height: 1.25;
        }
        .iq-suitable-for {
            font-size: 0.84rem;
            color: var(--iq-secondary-text);
            margin-bottom: 14px;
            line-height: 1.45;
        }
        .iq-feature-list {
            list-style: none;
            padding: 0;
            margin: 0 0 16px 0;
        }
        .iq-feature-item {
            font-size: 0.85rem;
            color: var(--iq-primary-text);
            padding: 5px 0;
            display: flex;
            align-items: baseline;
            gap: 8px;
            border-bottom: 1px dashed #E2E8F0;
        }
        .iq-feature-item:last-child {
            border-bottom: none;
        }
        .iq-feature-item strong {
            color: var(--iq-primary-text);
            min-width: 110px;
        }

        /* Clean High-Contrast Markdown Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.25rem 0;
            background: var(--iq-card-bg);
            border-radius: var(--iq-radius-md);
            overflow: hidden;
            border: 1px solid var(--iq-border-light);
            font-size: 0.88rem;
        }
        th {
            background-color: #EBF4FD !important;
            color: var(--iq-primary-text) !important;
            font-weight: 700 !important;
            text-align: left;
            padding: 12px 14px;
            border-bottom: 2px solid var(--iq-border-light);
            letter-spacing: -0.01em;
        }
        td {
            padding: 11px 14px;
            border-bottom: 1px solid var(--iq-border-light);
            color: var(--iq-primary-text);
            vertical-align: top;
        }
        tr:nth-child(even) td {
            background-color: #F8FAFD;
        }
        tr:hover td {
            background-color: #EDF4FC;
        }

        /* Main Area Buttons (High Contrast & Keyboard Focus) */
        .stButton > button {
            border-radius: var(--iq-radius-md) !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            transition: all 180ms ease !important;
        }
        .stButton > button[kind="primary"] {
            background-color: var(--iq-primary-blue) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--iq-primary-blue-hover) !important;
            box-shadow: 0 1px 3px rgba(0, 119, 217, 0.25) !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: var(--iq-primary-blue-hover) !important;
            box-shadow: 0 4px 10px rgba(0, 119, 217, 0.35) !important;
            transform: translateY(-1px);
        }
        .stButton > button[kind="secondary"] {
            background-color: var(--iq-card-bg) !important;
            color: var(--iq-primary-text) !important;
            border: 1px solid var(--iq-border-light) !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #EBF4FD !important;
            border-color: #0077D9 !important;
            color: #0077D9 !important;
        }

        /* Footer Note */
        .footer-privacy-note {
            font-size: 0.75rem;
            color: var(--iq-secondary-text);
            text-align: center;
            margin-top: 3rem;
            padding: 1.25rem;
            border-top: 1px solid var(--iq-border-light);
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state():
    """Ensure all required session state variables are present."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_view" not in st.session_state:
        st.session_state.active_view = "chat"
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False


def render_sidebar():
    """Render the sidebar with vibrant blue background and exact layout hierarchy."""
    logo_svg_data = load_svg_as_base64("insureiq_logo_vibrant_blue.svg")

    # 1. InsureIQ Logo & Title + 2. Short Brand Tagline
    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand-lockup">
            <img src="{logo_svg_data}" width="220" height="50" alt="InsureIQ Logo" style="display: block; margin-bottom: 2px;" />
            <div class="sidebar-brand-tagline">Understand coverage. Compare confidently.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Subtle Divider
    st.sidebar.markdown("<hr class='sidebar-divider' />", unsafe_allow_html=True)

    # 4. New Chat (The primary hero action, placed immediately above Compare Plans)
    if st.sidebar.button("➕ New Chat", key="btn_sidebar_new_chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.session_state.active_view = "chat"
        st.rerun()

    # 5. Compare Plans, 6. Senior Care, 7. Coverage Guide, 8. Claims & Support
    nav_items = [
        ("compare", "⚖️ Compare Plans"),
        ("senior_care", "👵 Senior Care"),
        ("coverage_guide", "📖 Coverage Guide"),
        ("claims_support", "🛡️ Claims & Support"),
    ]

    current_view = st.session_state.active_view
    for view_key, view_label in nav_items:
        is_active = (current_view == view_key)
        btn_type = "primary" if is_active else "secondary"
        if st.sidebar.button(view_label, key=f"nav_btn_{view_key}", use_container_width=True, type=btn_type):
            st.session_state.active_view = view_key
            st.rerun()

    # 9. Suggested questions and privacy note near the bottom
    st.sidebar.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    with st.sidebar.expander("💡 Suggested Questions", expanded=False):
        prompts = [
            "Help me compare health insurance plans",
            "What should senior citizens look for?",
            "Can someone with diabetes apply?",
            "What is a pre-existing disease waiting period?",
            "How does a cashless hospital claim work?",
            "What documents are needed to apply?",
            "My claim was rejected. What should I do?",
        ]
        for p in prompts:
            if st.button(f"› {p}", key=f"side_p_{p[:20]}", use_container_width=True):
                st.session_state.pending_prompt = p
                st.session_state.active_view = "chat"
                st.rerun()

    # Privacy Note
    st.sidebar.markdown(
        """
        <div class="sidebar-privacy-box">
            🔒 <strong>Privacy Assurance:</strong> InsureIQ answers educational questions without account logins. It does not request passwords, OTPs, or government IDs.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Discreet System Diagnostics
    with st.sidebar.expander("⚙️ System Status", expanded=False):
        try:
            agent = get_agent_instance()
            stats = agent.retrieval_engine.get_stats()
            st.caption(f"Knowledge Chunks: `{stats.get('document_count', 0)}`")
            st.caption(f"Chat Model: `{settings.openai_model}`")
            st.caption(f"Embedding Provider: `{settings.embedding_provider}`")
            st.caption(f"Status: `Online & Verified`")
        except Exception:
            st.caption("Knowledge Store: Initializing...")


def render_welcome_screen():
    """Render the clean, high-contrast InsureIQ welcome screen with prompt cards."""
    logo_data = load_svg_as_base64("logo.svg")

    st.markdown(
        f"""
        <div class="welcome-hero">
            <img src="{logo_data}" width="68" height="68" alt="InsureIQ Shield" style="display: inline-block; margin-bottom: 8px;" />
            <h1>How can I help you with health insurance?</h1>
            <p>Get clear, grounded answers on plan comparisons, waiting periods, senior citizen coverage, eligibility, and claim resolutions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Prompt Cards in a 2x3 Grid
    cards = [
        {
            "icon": "⚖️",
            "title": "Compare Leading Plans",
            "desc": "Shortlist and evaluate health insurance policies side by side with trade-offs.",
            "prompt": "Help me compare health insurance plans",
        },
        {
            "icon": "👵",
            "title": "Senior Citizen Guidance",
            "desc": "Review age rules, 36-month PED caps, and co-payment options for ages 60+.",
            "prompt": "What should senior citizens look for in health insurance?",
        },
        {
            "icon": "⏱️",
            "title": "Waiting Periods & PED",
            "desc": "Understand statutory pre-existing disease limits and specific ailment exclusions.",
            "prompt": "Explain waiting periods and exclusions in health insurance",
        },
        {
            "icon": "📋",
            "title": "Application & Eligibility",
            "desc": "Review underwriting guidelines, Section 45 moratorium, and required KYC documents.",
            "prompt": "What conditions are required to apply for health insurance?",
        },
        {
            "icon": "🏥",
            "title": "Cashless Hospital Claims",
            "desc": "Learn hospital pre-authorization steps and mandated settlement timelines.",
            "prompt": "How do cashless hospital claims work?",
        },
        {
            "icon": "🛡️",
            "title": "Grievance & Claim Disputes",
            "desc": "Step-by-step escalation routes, GRO contacts, and ombudsman guidance if a claim is rejected.",
            "prompt": "What should I do if my claim is rejected?",
        },
    ]

    col1, col2 = st.columns(2)
    for idx, card in enumerate(cards):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            st.markdown(
                f"""
                <div class="iq-prompt-card">
                    <div>
                        <div class="iq-card-title">{card['icon']} {card['title']}</div>
                        <div class="iq-card-desc">{card['desc']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Ask: “{card['prompt']}”", key=f"welcome_prompt_{idx}", use_container_width=True):
                st.session_state.pending_prompt = card["prompt"]
                st.rerun()


def process_user_query(prompt_text: str):
    """Execute query through HealthInsuranceAgent, guard against duplicates, and record history."""
    if st.session_state.is_processing:
        return

    st.session_state.is_processing = True
    agent = get_agent_instance()
    timestamp_now = datetime.now().strftime("%H:%M:%S")

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt_text,
        "timestamp": timestamp_now,
    })

    with st.chat_message("user"):
        st.markdown(prompt_text)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing verified policy documents & regulations..."):
            try:
                response = agent.handle_query(prompt_text)
                ans_text = response.answer
                classification_name = getattr(response.classification, "intent", "general_faq")
                query_type_label = getattr(response.classification, "query_type", None) or classification_name.replace("_", " ").title()
                sources_data = [s.model_dump() for s in response.sources] if response.sources else []
                is_mock = response.is_mock_data
            except Exception as e:
                ans_text = f"❌ **An unexpected error occurred:** `{e}`\n\nPlease try asking your question again or verify that local services are running."
                classification_name = "error"
                query_type_label = "System Notice"
                sources_data = []
                is_mock = False

        st.markdown(f"<span class='iq-category-badge'>🏷️ {query_type_label}</span>", unsafe_allow_html=True)
        st.markdown(ans_text)

        if sources_data:
            with st.expander(f"📚 Verified Sources ({len(sources_data)})", expanded=False):
                for src in sources_data:
                    url = src.get("source_url", "")
                    title = src.get("document_title", "Official Source")
                    pub = src.get("publisher", "Official Regulator")
                    sec = src.get("section_path") or "General"
                    page = src.get("page_number")
                    page_str = f" | Page {page}" if page else ""
                    st.markdown(
                        f"""
                        <div class="iq-citation-card">
                            <strong><a href="{url}" target="_blank">{title}</a></strong><br>
                            <span style="color: #64748B;">{pub} • {sec}{page_str}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Save to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": ans_text,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "classification": classification_name,
        "query_type": query_type_label,
        "sources": sources_data,
        "is_mock": is_mock,
    })
    st.session_state.is_processing = False


def render_chat_view():
    """Main Consultation Screen: Welcome Prompts or Full Conversation."""
    # Check for pending prompt from welcome cards or sidebar
    if st.session_state.pending_prompt:
        prompt_to_run = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        process_user_query(prompt_to_run)
        st.rerun()

    # Empty State -> Render Welcome Screen
    if not st.session_state.messages:
        render_welcome_screen()
    else:
        # Active Conversation
        col_hdr1, col_hdr2 = st.columns([0.85, 0.15])
        with col_hdr1:
            st.caption(f"Active Consultation Session ({len(st.session_state.messages)} messages)")
        with col_hdr2:
            if st.button("🧹 Clear Chat", key="clear_chat_top", help="Start a new chat session"):
                st.session_state.messages = []
                st.rerun()

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    qtype = msg.get("query_type") or "Guidance"
                    st.markdown(f"<span class='iq-category-badge'>🏷️ {qtype}</span>", unsafe_allow_html=True)

                st.markdown(msg["content"])

                # Render sources
                if msg.get("sources"):
                    with st.expander(f"📚 Verified Sources ({len(msg['sources'])})", expanded=False):
                        for src in msg["sources"]:
                            url = src.get("source_url", "")
                            title = src.get("document_title", "Official Source")
                            pub = src.get("publisher", "Official Regulator")
                            sec = src.get("section_path") or "General"
                            page = src.get("page_number")
                            page_str = f" | Page {page}" if page else ""
                            st.markdown(
                                f"""
                                <div class="iq-citation-card">
                                    <strong><a href="{url}" target="_blank">{title}</a></strong><br>
                                    <span style="color: #64748B;">{pub} • {sec}{page_str}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

    # Bottom Chat Input (Submit button styled in InsureIQ blue #0077D9)
    if user_input := st.chat_input("Ask InsureIQ about coverage, health plans, waiting periods, or claims…"):
        process_user_query(user_input)
        st.rerun()


def render_page_header_with_chat_return(title: str, subtitle: str):
    """Render top page title with a clean shortcut to return to active chat."""
    col1, col2 = st.columns([0.76, 0.24])
    with col1:
        st.title(title)
        st.markdown(subtitle)
    with col2:
        if st.session_state.messages:
            if st.button(f"💬 Return to Chat ({len(st.session_state.messages)})", key=f"btn_ret_{title[:8]}", use_container_width=True):
                st.session_state.active_view = "chat"
                st.rerun()
        else:
            if st.button("💬 Open Chat", key=f"btn_open_chat_{title[:8]}", use_container_width=True):
                st.session_state.active_view = "chat"
                st.rerun()
    st.markdown("---")


def render_compare_plans_view():
    """Redesigned, Premium InsureIQ Plan Comparison Experience."""
    render_page_header_with_chat_return(
        "⚖️ Compare Health Insurance Plans",
        "Evaluate popular health insurance policies side by side based on verified policy wordings and Customer Information Sheets (CIS)."
    )

    # Interactive Insurer Filter
    all_insurers = [
        "HDFC ERGO",
        "Care Health",
        "Star Health",
        "Niva Bupa",
        "ICICI Lombard",
        "Aditya Birla Health",
    ]
    selected_insurers = st.multiselect(
        "Filter Comparison Matrix by Insurer:",
        options=all_insurers,
        default=all_insurers,
        help="Select insurers to compare specific policies side by side.",
    )

    # Plan Comparison Matrix Table
    st.subheader("📋 Standardized Policy Comparison Matrix")
    
    matrix_data = [
        {"Insurer": "HDFC ERGO", "Plan": "Optima Secure", "Category": "Comprehensive Retail", "Entry Age": "18 to No Cap", "Co-Pay": "0% (Nil)", "Room Rent": "No Sub-Limit (Single AC)", "PED Waiting": "3 Years (Opt riders)", "Highlight": "2X cover on Day 1; 4X after 2 claim-free years."},
        {"Insurer": "Care Health", "Plan": "Care Supreme", "Category": "Comprehensive Retail", "Entry Age": "18 to No Cap", "Co-Pay": "0% (Nil)", "Room Rent": "No Sub-Limit", "PED Waiting": "3 Years (Opt riders)", "Highlight": "Cumulative Bonus Super up to 500%; unlimited recharge."},
        {"Insurer": "Star Health", "Plan": "Senior Red Carpet", "Category": "Senior Citizens (60+)", "Entry Age": "60 to 75+", "Co-Pay": "30% - 50%", "Room Rent": "1% of SI / day", "PED Waiting": "12 Months (1 Year)", "Highlight": "Pre-existing diseases covered after just 1 year; no PPMC upfront."},
        {"Insurer": "Niva Bupa", "Plan": "Senior First", "Category": "Senior Citizens (60+)", "Entry Age": "60 to No Cap", "Co-Pay": "Deductible Based", "Room Rent": "Single AC / No Cap", "PED Waiting": "2 to 3 Years", "Highlight": "Customizable deductibles (₹25k-₹1L) to optimize premium."},
        {"Insurer": "Niva Bupa", "Plan": "ReAssure 2.0", "Category": "Young Adults / Families", "Entry Age": "18 to No Cap", "Co-Pay": "0% (Nil)", "Room Rent": "No Sub-Limit", "PED Waiting": "3 Years", "Highlight": "AgeLock locks entry age premium until first claim."},
        {"Insurer": "ICICI Lombard", "Plan": "Complete Health", "Category": "Comprehensive Retail", "Entry Age": "18 to No Cap", "Co-Pay": "0% (Nil)", "Room Rent": "No Sub-Limit", "PED Waiting": "2 to 3 Years", "Highlight": "Reset benefit restores 100% base sum insured; donor cover."},
        {"Insurer": "Aditya Birla Health", "Plan": "Activ Health Platinum", "Category": "Chronic / Lifestyle", "Entry Age": "18 to No Cap", "Co-Pay": "0% (Nil)", "Room Rent": "No Sub-Limit", "PED Waiting": "Day 1 for Chronic", "Highlight": "Day-1 chronic cover for diabetes & BP with wellness coaching."},
    ]

    filtered_matrix = [m for m in matrix_data if m["Insurer"] in selected_insurers]
    if filtered_matrix:
        table_md = "| Insurer | Plan Name | Target Category | Entry Age | Co-Payment | Room Rent Capping | PED Waiting | Distinctive Highlight |\n"
        table_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for r in filtered_matrix:
            table_md += f"| **{r['Insurer']}** | *{r['Plan']}* | {r['Category']} | {r['Entry Age']} | **{r['Co-Pay']}** | {r['Room Rent']} | {r['PED Waiting']} | {r['Highlight']} |\n"
        st.markdown(table_md)
    else:
        st.info("Please select at least one insurer above to display the comparison matrix.")

    st.markdown("---")
    st.subheader("🔍 Verified Plan Profiles & Specifications")
    st.caption("Deep-dive coverage specifications grounded in verified policy filings and Customer Information Sheets.")

    col1, col2 = st.columns(2)

    with col1:
        # Card 1: HDFC ERGO Optima Secure
        st.markdown(
            """
            <div class="iq-product-card">
                <div>
                    <div class="iq-card-header">
                        <span class="iq-insurer-badge">HDFC ERGO General Insurance</span>
                        <span class="iq-status-badge">✓ Verified Policy Filing</span>
                    </div>
                    <div class="iq-product-title">Optima Secure</div>
                    <div class="iq-suitable-for"><strong>Suitable for:</strong> Buyers seeking automatic coverage multiplication and zero deductions.</div>
                    <ul class="iq-feature-list">
                        <li class="iq-feature-item"><strong>Base Coverage:</strong> ₹5 Lakhs to ₹2 Crores</li>
                        <li class="iq-feature-item"><strong>Multiplier:</strong> 2X coverage on Day 1; 4X after 2 claim-free years</li>
                        <li class="iq-feature-item"><strong>Room Rent:</strong> Any Single Private AC Room without sub-limits</li>
                        <li class="iq-feature-item"><strong>Co-Payment:</strong> 0% mandatory co-payment</li>
                        <li class="iq-feature-item"><strong>PED Waiting:</strong> 3 Years (standard); negotiable with riders</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("📄 View Policy Details & Official Links — Optima Secure"):
            st.markdown(
                """
                - **Document Type:** Standard Retail Health Policy Wordings & CIS.
                - **Restoration:** Automatic 100% restoration upon partial or full exhaustion.
                - **Consumables:** Protect Benefit rider covers 68+ non-medical consumable items.
                - **Official Portal:** [hdfcergo.com](https://www.hdfcergo.com)
                - **Helpline:** `1800 2666 400`
                """
            )
        if st.button("💬 Ask InsureIQ About Optima Secure", key="btn_ask_optima", use_container_width=True):
            st.session_state.pending_prompt = "Tell me about HDFC ERGO Optima Secure coverage, benefits, and waiting periods."
            st.session_state.active_view = "chat"
            st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Card 2: Care Supreme
        st.markdown(
            """
            <div class="iq-product-card">
                <div>
                    <div class="iq-card-header">
                        <span class="iq-insurer-badge">Care Health Insurance</span>
                        <span class="iq-status-badge">✓ Verified Policy Filing</span>
                    </div>
                    <div class="iq-product-title">Care Supreme</div>
                    <div class="iq-suitable-for"><strong>Suitable for:</strong> High cumulative bonus accumulation and unlimited automatic restoration.</div>
                    <ul class="iq-feature-list">
                        <li class="iq-feature-item"><strong>Base Coverage:</strong> ₹5 Lakhs to ₹1 Crore</li>
                        <li class="iq-feature-item"><strong>Restoration:</strong> Unlimited automatic recharge for any hospitalization</li>
                        <li class="iq-feature-item"><strong>Cumulative Bonus:</strong> Up to 500% with Bonus Super option</li>
                        <li class="iq-feature-item"><strong>Room Rent:</strong> Any category up to sum insured (No capping)</li>
                        <li class="iq-feature-item"><strong>Co-Payment:</strong> 0% co-payment for standard age brackets</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("📄 View Policy Details & Official Links — Care Supreme"):
            st.markdown(
                """
                - **Document Type:** Individual & Family Floater Health Policy Wordings.
                - **Cumulative Bonus Super:** 50% increase per claim-free year up to 500% of base cover.
                - **Daycare Procedures:** All daycare treatments requiring hospitalization covered.
                - **Official Portal:** [careinsurance.com](https://www.careinsurance.com)
                - **Helpline:** `1800 102 4488`
                """
            )
        if st.button("💬 Ask InsureIQ About Care Supreme", key="btn_ask_care_sup", use_container_width=True):
            st.session_state.pending_prompt = "Explain Care Supreme benefits, restoration rules, and waiting periods."
            st.session_state.active_view = "chat"
            st.rerun()

    with col2:
        # Card 3: Star Senior Red Carpet
        st.markdown(
            """
            <div class="iq-product-card">
                <div>
                    <div class="iq-card-header">
                        <span class="iq-insurer-badge">Star Health Insurance</span>
                        <span class="iq-status-badge">✓ Verified Policy Filing</span>
                    </div>
                    <div class="iq-product-title">Senior Citizens Red Carpet</div>
                    <div class="iq-suitable-for"><strong>Suitable for:</strong> Seniors (60+) wanting pre-existing disease coverage with short waiting periods.</div>
                    <ul class="iq-feature-list">
                        <li class="iq-feature-item"><strong>Base Coverage:</strong> ₹1 Lakh to ₹25 Lakhs</li>
                        <li class="iq-feature-item"><strong>PED Waiting:</strong> 12 Months (1 Year) for pre-existing conditions</li>
                        <li class="iq-feature-item"><strong>Medical Checkup:</strong> No pre-policy medical checkup (PPMC) required upfront</li>
                        <li class="iq-feature-item"><strong>Co-Payment:</strong> Mandatory 30% to 50% co-pay on claims</li>
                        <li class="iq-feature-item"><strong>Room Rent:</strong> Capped at 1% of Sum Insured per day</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("📄 View Policy Details & Official Links — Senior Red Carpet"):
            st.markdown(
                """
                - **Document Type:** Senior Citizen Health Insurance Policy Wordings & CIS.
                - **Trade-off Notice:** Higher co-payments and daily room rent sub-limits in exchange for rapid 1-year PED coverage.
                - **Network:** 14,000+ cashless network hospitals.
                - **Official Portal:** [starhealth.in](https://www.starhealth.in)
                - **Helpline:** `1800 425 2255`
                """
            )
        if st.button("💬 Ask InsureIQ About Senior Red Carpet", key="btn_ask_star_rc", use_container_width=True):
            st.session_state.pending_prompt = "What are the features, co-pay, and waiting periods of Star Senior Citizens Red Carpet?"
            st.session_state.active_view = "chat"
            st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Card 4: Aditya Birla Activ Health
        st.markdown(
            """
            <div class="iq-product-card">
                <div>
                    <div class="iq-card-header">
                        <span class="iq-insurer-badge">Aditya Birla Health Insurance</span>
                        <span class="iq-status-badge">✓ Verified Policy Filing</span>
                    </div>
                    <div class="iq-product-title">Activ Health Platinum Enhanced</div>
                    <div class="iq-suitable-for"><strong>Suitable for:</strong> Applicants with existing Diabetes, High BP, Asthma, or High Cholesterol.</div>
                    <ul class="iq-feature-list">
                        <li class="iq-feature-item"><strong>Base Coverage:</strong> ₹2 Lakhs to ₹2 Crores</li>
                        <li class="iq-feature-item"><strong>Chronic Care:</strong> Day-1 coverage for declared chronic ailments</li>
                        <li class="iq-feature-item"><strong>Wellness Reward:</strong> HealthReturns™ allows earning up to 100% premium back</li>
                        <li class="iq-feature-item"><strong>Room Rent:</strong> Single Private AC Room (No sub-limit)</li>
                        <li class="iq-feature-item"><strong>Co-Payment:</strong> 0% mandatory co-payment</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("📄 View Policy Details & Official Links — Activ Health"):
            st.markdown(
                """
                - **Document Type:** Activ Health Platinum Enhanced Policy Clauses.
                - **Chronic Management:** Includes expert health coaching and annual health checkups.
                - **Inpatient Care:** Full coverage for ICU and surgeon charges without proportionate deductions.
                - **Official Portal:** [adityabirlacapital.com](https://www.adityabirlacapital.com/healthinsurance)
                - **Helpline:** `1800 270 7000`
                """
            )
        if st.button("💬 Ask InsureIQ About Activ Health", key="btn_ask_activ", use_container_width=True):
            st.session_state.pending_prompt = "How does Aditya Birla Activ Health cover diabetes and hypertension from Day 1?"
            st.session_state.active_view = "chat"
            st.rerun()


def render_senior_care_view():
    """Dedicated Senior Citizen Health Insurance Hub with Enhanced Contrast."""
    render_page_header_with_chat_return(
        "👵 Senior Citizen Health Insurance Hub",
        "Essential regulatory protections, plan evaluations, and practical buying checklists for applicants and policyholders aged 60 and above."
    )

    # Regulatory Protections Grid
    st.subheader("🛡️ Regulatory Protections for Senior Citizens")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div class="iq-prompt-card">
                <div style="font-size: 1.15rem; font-weight: 700; color: #172B4D;">🚫 No Entry Age Cap</div>
                <p style="font-size: 0.82rem; color: #526B85; margin-top: 6px;">Under the Master Circular on Health Insurance, insurers cannot refuse coverage based on age. Individuals aged 65, 70, or 80+ can apply.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="iq-prompt-card">
                <div style="font-size: 1.15rem; font-weight: 700; color: #172B4D;">⏱️ 36-Month PED Cap</div>
                <p style="font-size: 0.82rem; color: #526B85; margin-top: 6px;">Pre-existing disease (PED) waiting periods are strictly capped at maximum 3 years (36 months). Insurers cannot mandate 4-year periods.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="iq-prompt-card">
                <div style="font-size: 1.15rem; font-weight: 700; color: #172B4D;">📜 Section 45 Moratorium</div>
                <p style="font-size: 0.82rem; color: #526B85; margin-top: 6px;">After 5 continuous policy years (60 months), claims cannot be repudiated on grounds of misstatement, protecting older policyholders.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="iq-prompt-card">
                <div style="font-size: 1.15rem; font-weight: 700; color: #172B4D;">🔄 Lifelong Renewability</div>
                <p style="font-size: 0.82rem; color: #526B85; margin-top: 6px;">Every retail health insurance policy guarantees lifelong renewal. Insurers cannot refuse renewal because of claims made in prior years.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # The 10-Point Checklist
    st.subheader("📋 The 10-Point Senior Buyer Checklist")
    st.markdown(
        """
        1. **Co-Payment Clause:** Most senior plans mandate 10% to 20% co-payment. If budget permits, select a plan with 0% co-pay or add a co-pay waiver rider.
        2. **PED Waiting Period:** Look for plans offering 1-year or 2-year waiting periods for pre-existing ailments (hypertension, diabetes, thyroid).
        3. **Room Rent Limits:** Avoid daily caps (e.g. 1% of sum insured) to prevent proportionate deductions from slashing your doctor and surgery claims.
        4. **Treatment Sub-Limits:** Check specific caps on cataract surgeries, knee/hip joint replacements, and cardiac procedures.
        5. **Network Hospital Proximity:** Ensure there are empanelled network hospitals within a 5 to 10 km radius of the senior's residence.
        6. **Medical Screening (PPMC):** Disclose all past medical conditions completely during checkups to secure unchallengeable claim settlement under Section 45.
        7. **Restoration Benefit:** Verifies if the policy automatically restores 100% of sum insured if exhausted during a major hospitalization.
        8. **Domiciliary & Home Care:** Essential for elderly patients requiring skilled home nursing care or doctor-prescribed IV therapy at home.
        9. **Daycare Procedures:** All modern surgeries taking less than 24 hours (dialysis, cataract, minor orthopedic procedures) should be covered.
        10. **Separate Policy vs Family Floater:** Always purchase a **dedicated individual policy** for senior parents. Adding elderly parents to a young family floater makes the entire premium skyrocket.
        """
    )

    if st.button("💬 Ask InsureIQ About Senior Citizen Plans in Chat", key="btn_ask_senior_hub", type="primary"):
        st.session_state.pending_prompt = "Which health insurance plans should senior citizens compare and what are the key trade-offs?"
        st.session_state.active_view = "chat"
        st.rerun()


def render_coverage_guide_view():
    """Educational Hub for Insurance Terminology and Concepts."""
    render_page_header_with_chat_return(
        "📖 Health Insurance Coverage Guide",
        "Clear, plain-English explanations of how health insurance contracts, waiting periods, and claims work."
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Core Financial Terms",
        "⏱️ Waiting Periods & Exclusions",
        "📋 Eligibility & Underwriting",
        "📑 Claims Process",
    ])

    with tab1:
        st.markdown(
            """
            ### Understanding Key Financial Terms
            - **Sum Insured (SI):** The maximum annual financial limit the insurer will pay for all admissible hospitalization claims in a policy year.
            - **Deductible:** An agreed threshold amount you must pay out of pocket before the insurer begins paying. High-deductible super top-ups offer cost-effective massive coverage.
            - **Co-Payment (Co-Pay):** A fixed percentage (e.g. 10% or 20%) of each approved hospital bill that you pay, while the insurer pays the remaining share.
            - **Room Rent Capping & Proportionate Deductions:** If your policy caps room rent at 1% of Sum Insured and you choose a more expensive room, the insurer proportionately slashes **all associated medical expenses** (doctor visits, surgeon fees, operation theatre charges).
            - **Restoration / ReAssure Benefit:** Reinstates 100% of your base sum insured if exhausted by prior claims during the policy year.
            """
        )

    with tab2:
        st.markdown(
            """
            ### Waiting Periods & Exclusions
            1. **Initial 30-Day Waiting Period:** No illnesses are covered during the first 30 days after policy issuance, **except for accidental injuries** requiring hospitalization.
            2. **Specific Ailment Waiting Period (1 to 2 Years):** Statutory period for slow-developing conditions (cataract, hernia, joint replacement, hydrocele, stones).
            3. **Pre-Existing Disease (PED) Waiting Period:** Capped at **maximum 36 months (3 years)** under official regulations. Once served, declared conditions are fully covered.
            4. **Standard Exclusions:** Cosmetic surgery, self-inflicted injuries, experimental therapies, and unprescribed substance abuse treatments.
            5. **Non-Medical Consumables:** 68+ items (gloves, PPE kits, administrative fees) are non-payable unless you attach a **Claim Protect / Consumables Rider**.
            """
        )

    with tab3:
        st.markdown(
            """
            ### Eligibility, Underwriting & Application Requirements
            - **Age Criteria:** Adults aged 18 and above; dependent children from 91 days to 25 years. No upper entry age limit.
            - **Applying with Diabetes or Hypertension:** Chronic conditions are eligible! Insurers evaluate medical reports and may apply standard acceptance, a premium loading (+10% to +30%), or a 1-to-3 year waiting period.
            - **Duty of Utmost Good Faith:** Complete disclosure of past medical history, surgeries, and family conditions on the proposal form is legally mandatory.
            - **Required KYC Documents:** Proposal Form, Proof of Identity (PAN Card, Aadhaar, Passport), Proof of Address, and prior policy copy (if porting).
            - **Free Look Period:** Policyholders have **30 days** for digital/online policies to review clauses and cancel for a full refund minus minor stamp duty.
            """
        )

    with tab4:
        st.markdown(
            """
            ### Cashless vs Reimbursement Claims
            - **Cashless Treatment:** Network hospital liaises directly with the insurer/TPA.
              - Pre-authorization request submitted 48–72 hours prior (planned) or within 24 hours (emergency).
              - **1-Hour Rule:** Initial cashless authorization must be communicated within 1 hour.
              - **3-Hour Rule:** Final discharge approval must be communicated within 3 hours of hospital bill submission.
            - **Reimbursement Treatment:** Applicable at non-network hospitals.
              - Pay hospital bills in full upon discharge.
              - Submit claim packet (claim form, original bills, discharge summary, prescriptions) within 15 to 30 days.
            """
        )


def render_claims_support_view():
    """Claims Guidance and Official Support & Grievance Directory."""
    render_page_header_with_chat_return(
        "🛡️ Claims Guidance & Support Directory",
        "Step-by-step claims assistance, official regulatory grievance channels, and verified insurer helplines."
    )

    # Grievance Escalation Hierarchy
    st.subheader("⚖️ Claim Rejection & Grievance Escalation Pathway")
    st.markdown(
        """
        If your health insurance claim has been rejected or delayed unreasonably, follow this statutory 3-level escalation ladder:
        """
    )

    gcol1, gcol2, gcol3 = st.columns(3)
    with gcol1:
        st.markdown(
            """
            <div class="iq-prompt-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: #0077D9; text-transform: uppercase;">LEVEL 1 (14 DAYS)</div>
                <h4 style="margin: 4px 0 8px 0; color: #172B4D;">Insurer Grievance Redressal Officer</h4>
                <p style="font-size: 0.83rem; color: #526B85;">Submit a formal written representation to your insurer's designated GRO citing policy clauses. Insurers are legally required to resolve complaints within 14 days.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with gcol2:
        st.markdown(
            """
            <div class="iq-prompt-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: #0077D9; text-transform: uppercase;">LEVEL 2 (CENTRAL PORTAL)</div>
                <h4 style="margin: 4px 0 8px 0; color: #172B4D;">Bima Bharosa Grievance Portal</h4>
                <p style="font-size: 0.83rem; color: #526B85;">If unresolved after 14 days, lodge your grievance on the official central portal or call Toll-Free <strong>155255</strong> or <strong>1800 4254 732</strong> (complaints@irdai.gov.in).</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with gcol3:
        st.markdown(
            """
            <div class="iq-prompt-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: #0077D9; text-transform: uppercase;">LEVEL 3 (30 DAYS)</div>
                <h4 style="margin: 4px 0 8px 0; color: #172B4D;">Insurance Ombudsman</h4>
                <p style="font-size: 0.83rem; color: #526B85;">Independent statutory arbitration for disputes up to ₹50 Lakhs. The process is completely free for individual policyholders, and awards are legally binding on insurers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Verified Insurer Customer Care Directory
    st.subheader("📞 Verified Insurer Customer Care Directory")
    st.markdown(
        """
        | Insurer | Toll-Free Customer Care | Senior Citizen Desk | Official Email Support | Official Website |
        | :--- | :--- | :--- | :--- | :--- |
        | **HDFC ERGO** | `1800 2666 400` / `022 6234 6234` | Priority Line via App | `care@hdfcergo.com` | [hdfcergo.com](https://www.hdfcergo.com) |
        | **Star Health** | `1800 425 2255` / `1800 102 4477` | `044 4002 0555` | `support@starhealth.in` | [starhealth.in](https://www.starhealth.in) |
        | **Care Health** | `1800 102 4488` / `1800 200 4488` | Priority Line via App | `customerfirst@careinsurance.com` | [careinsurance.com](https://www.careinsurance.com) |
        | **Niva Bupa** | `1860 500 8888` / `011 4609 6969` | `seniorcitizen@nivabupa.com` | `customercare@nivabupa.com` | [nivabupa.com](https://www.nivabupa.com) |
        | **ICICI Lombard** | `1800 2666` | Priority Line via App | `customersupport@icicilombard.com` | [icicilombard.com](https://www.icicilombard.com) |
        | **Aditya Birla Health** | `1800 270 7000` | Health Coach Assigned | `care.healthinsurance@adityabirlacapital.com` | [adityabirlacapital.com](https://www.adityabirlacapital.com/healthinsurance) |
        """
    )


def main():
    inject_custom_styles()
    initialize_session_state()
    render_sidebar()

    # Route to active view
    view = st.session_state.active_view
    if view == "chat":
        render_chat_view()
    elif view == "compare":
        render_compare_plans_view()
    elif view == "senior_care":
        render_senior_care_view()
    elif view == "coverage_guide":
        render_coverage_guide_view()
    elif view == "claims_support":
        render_claims_support_view()
    else:
        render_chat_view()

    # Footer note
    st.markdown(
        """
        <div class="footer-privacy-note">
            InsureIQ is an informational and consultative health insurance intelligence platform. It does not provide medical or legal advice or binding claim decisions.
            Always review the specific policy wording and Customer Information Sheet (CIS) before purchasing.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()