from __future__ import annotations

import html
import streamlit as st


def apply_theme():
    st.markdown(
        """
<style>
:root {
  --bg:#f5f7fb; --surface:#fff; --line:#e7ebf2; --text:#111827;
  --muted:#6b7280; --blue:#2563eb; --blue2:#dbeafe;
  --green:#059669; --red:#dc2626; --gold:#b78a3a;
}
html, body, [class*="css"] {
  font-family: Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
}
.stApp { background:var(--bg); color:var(--text); }
.block-container { max-width:1440px; padding:1.5rem 2rem 4rem; }
header[data-testid="stHeader"] { background:rgba(245,247,251,.9); backdrop-filter:blur(12px); }
section[data-testid="stSidebar"] {
  background:#111827; border-right:0; min-width:250px;
}
section[data-testid="stSidebar"] > div { padding:1.2rem 1rem; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#cbd5e1; }
[data-testid="stSidebar"] .stRadio > label { display:none; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap:4px; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
  border-radius:10px; padding:10px 12px; color:#cbd5e1; transition:.15s;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover { background:#1f2937; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
  background:#1d4ed8; color:#fff; font-weight:700;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) p { color:#fff; }
.planx-brand { display:flex; align-items:center; gap:10px; margin:0 0 28px; }
.planx-brand-mark {
  width:38px; height:38px; border-radius:11px; display:flex;
  align-items:center; justify-content:center; background:linear-gradient(135deg,#2563eb,#60a5fa);
  color:#fff; font-size:20px; font-weight:800; box-shadow:0 8px 20px rgba(37,99,235,.3);
}
.planx-brand-title { color:#fff; font-size:20px; font-weight:800; letter-spacing:-.04em; }
.planx-brand-sub { color:#94a3b8; font-size:11px; margin-top:2px; }
.planx-hero {
  background:linear-gradient(135deg,#fff 0%,#fff 45%,#eef5ff 100%);
  border:1px solid var(--line); border-radius:20px; padding:28px 30px;
  margin-bottom:18px; box-shadow:0 12px 32px rgba(15,23,42,.045);
}
.planx-eyebrow { color:var(--blue); font-size:11px; font-weight:800; letter-spacing:.12em; margin-bottom:7px; }
.planx-hero h1 { margin:0; color:var(--text); font-size:34px; line-height:1.2; font-weight:800; letter-spacing:-.045em; }
.planx-hero p { margin:9px 0 0; color:var(--muted); font-size:14px; max-width:760px; }
.planx-card {
  background:#fff; border:1px solid var(--line); border-radius:15px; padding:18px 20px;
  min-height:112px; box-shadow:0 7px 22px rgba(15,23,42,.035);
}
.planx-card-title { color:var(--muted); font-size:12px; font-weight:700; margin-bottom:8px; }
.planx-card-value { color:var(--text); font-size:24px; font-weight:800; letter-spacing:-.035em; font-variant-numeric:tabular-nums; }
.planx-card-note { color:#94a3b8; font-size:11px; margin-top:7px; }
.planx-empty {
  background:#fff; border:1px dashed #cbd5e1; border-radius:14px; padding:22px; color:var(--muted);
}
.planx-source {
  display:inline-flex; align-items:center; gap:5px; padding:4px 9px; border-radius:999px;
  font-size:10px; font-weight:700; border:1px solid #e2e8f0; background:#f8fafc; color:#64748b;
}
.planx-status-ok { color:#047857; background:#ecfdf5; border-color:#a7f3d0; }
.planx-status-wait { color:#92400e; background:#fffbeb; border-color:#fde68a; }
.planx-status-bad { color:#b91c1c; background:#fef2f2; border-color:#fecaca; }
[data-testid="stMetric"] {
  background:#fff; border:1px solid var(--line); border-radius:15px; padding:15px 17px;
  box-shadow:0 7px 22px rgba(15,23,42,.035);
}
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stMetricValue"] { color:var(--text); font-weight:800; }
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color:var(--line) !important; border-radius:15px !important; background:#fff;
  box-shadow:0 7px 22px rgba(15,23,42,.03);
}
.stButton > button, .stFormSubmitButton > button {
  min-height:43px; border-radius:10px; font-weight:700;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background:var(--blue); border-color:var(--blue);
}
.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div { border-radius:10px !important; }
.stTextInput input { min-height:44px; }
.stTabs [data-baseweb="tab-list"] { gap:5px; }
.stTabs [data-baseweb="tab"] { border-radius:9px; padding:9px 12px; }
.stDataFrame { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
h1,h2,h3,h4 { color:var(--text); letter-spacing:-.035em; }
hr { border-color:var(--line) !important; }
@media (max-width:900px) {
  .block-container { padding:1rem 1rem 3rem; }
  .planx-hero { padding:22px 20px; }
  .planx-hero h1 { font-size:28px; }
}
</style>
""",
        unsafe_allow_html=True,
    )


def brand():
    st.markdown(
        """
<div class="planx-brand">
  <div class="planx-brand-mark">↗</div>
  <div>
    <div class="planx-brand-title">StockDash</div>
    <div class="planx-brand-sub">DATA TO INSIGHT</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, eyebrow: str = "STOCKDASH"):
    st.markdown(
        f"""
<div class="planx-hero">
  <div class="planx-eyebrow">{html.escape(eyebrow)}</div>
  <h1>{html.escape(title)}</h1>
  <p>{html.escape(subtitle)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def card(title: str, value: str, note: str = "", status: str = ""):
    status_html = f'<div class="planx-card-note">{html.escape(status)}</div>' if status else ""
    st.markdown(
        f"""
<div class="planx-card">
  <div class="planx-card-title">{html.escape(title)}</div>
  <div class="planx-card-value">{html.escape(value)}</div>
  <div class="planx-card-note">{html.escape(note)}</div>
  {status_html}
</div>
""",
        unsafe_allow_html=True,
    )


def empty_state(title: str, message: str):
    st.markdown(
        f"""
<div class="planx-empty">
  <strong style="color:#334155">{html.escape(title)}</strong><br>
  <span>{html.escape(message)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def source_badge(label: str, state: str = "wait"):
    cls = {"ok":"planx-status-ok", "bad":"planx-status-bad"}.get(state, "planx-status-wait")
    st.markdown(
        f'<span class="planx-source {cls}">{html.escape(label)}</span>',
        unsafe_allow_html=True,
    )
