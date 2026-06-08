"""EduAI-Guard — AI Ethics Self-Audit System for University Students.

A Streamlit application that helps students evaluate their AI usage
across eight ethical dimensions and generate disclosure statements.
"""

from __future__ import annotations

import os
from html import escape
from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
import streamlit as st

from data_analyzer import ACCEPTANCE_USE_OPTIONS, AI_USE_OPTIONS, analyze_survey_data, read_csv_flexible
from report_generator import generate_markdown_report
from rules import DIMENSION_LABELS, calculate_risk
from statement_generator import generate_statement
from utils import DEFAULT_SURVEY_PATH, append_feedback, ensure_project_dirs, read_feedback_records, summarize_feedback


# ═══════════════════════════════════════════════════════════════════════
# Design Tokens
# ═══════════════════════════════════════════════════════════════════════

BLUE_600 = "#2563EB"
BLUE_500 = "#3B82F6"
BLUE_100 = "#DBEAFE"
BLUE_50 = "#EFF6FF"
TEAL_600 = "#0D9488"
AMBER_600 = "#D97706"
ROSE_600 = "#E11D48"
EMERALD_600 = "#059669"
SLATE_900 = "#0F172A"
SLATE_700 = "#334155"
SLATE_500 = "#64748B"
SLATE_200 = "#E2E8F0"
SLATE_100 = "#F1F5F9"
SLATE_50 = "#F8FAFC"
WHITE = "#FFFFFF"
APP_FONT_STACK = '"Times New Roman", "Songti SC", "STSong", "SimSun", serif'

DIMENSION_META: Dict[str, Dict[str, str]] = {
    "学术诚信": {
        "icon": "01",
        "short": "学术诚信",
        "desc": "AI 是否替代核心思考、论证、代码或实验过程",
        "color": BLUE_600,
    },
    "数据隐私": {
        "icon": "02",
        "short": "数据隐私",
        "desc": "是否上传个人信息、同学资料、聊天记录或未公开材料",
        "color": TEAL_600,
    },
    "内容可靠": {
        "icon": "03",
        "short": "内容可靠",
        "desc": "是否核查事实、参考文献、数据、公式和代码",
        "color": EMERALD_600,
    },
    "偏见公平": {
        "icon": "04",
        "short": "偏见公平",
        "desc": "工具差异、时间压力和课堂训练不足带来的公平问题",
        "color": AMBER_600,
    },
    "透明披露": {
        "icon": "05",
        "short": "透明披露",
        "desc": "是否主动说明 AI 使用范围并承担最终责任",
        "color": "#7C3AED",
    },
    "学习主体": {
        "icon": "06",
        "short": "学习主体",
        "desc": "学生是否仍能独立解释核心观点、代码和结论",
        "color": "#0891B2",
    },
    "责任证据": {
        "icon": "07",
        "short": "责任证据",
        "desc": "是否保留 prompt、草稿、修改记录和核查证据",
        "color": "#4F46E5",
    },
    "版权授权": {
        "icon": "08",
        "short": "版权授权",
        "desc": "资料、图片、论文和同学作品是否有明确授权",
        "color": "#BE123C",
    },
}

RISK_LEVELS: Dict[str, Dict[str, str]] = {
    "低风险": {
        "bg": "#ECFDF5",
        "fg": EMERALD_600,
        "border": "#A7F3D0",
        "icon": "低",
        "tag_bg": "#D1FAE5",
        "desc": "AI 使用方式较为规范，继续保持",
    },
    "中风险": {
        "bg": "#FFFBEB",
        "fg": AMBER_600,
        "border": "#FDE68A",
        "icon": "中",
        "tag_bg": "#FEF3C7",
        "desc": "存在部分风险，建议参考修改建议进行调整",
    },
    "高风险": {
        "bg": "#FFF7ED",
        "fg": "#EA580C",
        "border": "#FDBA74",
        "icon": "高",
        "tag_bg": "#FFEDD5",
        "desc": "风险较高，请认真考虑调整 AI 使用方式",
    },
    "严重风险": {
        "bg": "#FEF2F2",
        "fg": ROSE_600,
        "border": "#FECACA",
        "icon": "严",
        "tag_bg": "#FEE2E2",
        "desc": "存在严重风险，建议重新完成核心内容",
    },
}

NAV_ITEMS: List[Tuple[str, str, str]] = [
    ("首页", "01", "home"),
    ("调研数据概览", "02", "survey"),
    ("AI 使用伦理自查", "03", "self-check"),
    ("AI 使用声明生成", "04", "statement"),
    ("自查报告下载", "05", "report"),
    ("用户反馈", "06", "feedback"),
    ("项目说明", "07", "about"),
]
NAV_LABELS = [item[0] for item in NAV_ITEMS]
PAGE_SLUGS = {item[0]: item[2] for item in NAV_ITEMS}
SLUG_TO_PAGE = {v: k for k, v in PAGE_SLUGS.items()}

WIZARD_STEPS = [
    ("基本信息", "作业类型、场景与规则"),
    ("AI 使用方式", "AI 参与环节"),
    ("数据与授权", "上传内容与资料授权"),
    ("核查与主体", "事实核查与独立解释"),
    ("披露与背景", "声明、压力与自检清单"),
]

ETHICAL_CHECK_OPTIONS = [
    "我能独立解释作业的核心观点、代码或结论",
    "我没有让 AI 编造实验数据、访谈数据或问卷数据",
    "我没有上传同学作业、聊天记录、个人身份信息",
    "我已核查 AI 生成的事实、公式、代码和引用",
    "我保留了草稿、修改过程或关键 prompt",
    "如果课程要求，我会主动声明 AI 使用",
]


# ═══════════════════════════════════════════════════════════════════════
# CSS Framework
# ═══════════════════════════════════════════════════════════════════════

def _inject_styles() -> None:
    """Inject the complete design system CSS into the Streamlit app."""
    st.markdown(
        f"""
<style>
/* ========================= DESIGN TOKENS ========================= */
:root {{
  --blue-600: {BLUE_600};
  --blue-500: {BLUE_500};
  --blue-100: {BLUE_100};
  --blue-50: {BLUE_50};
  --teal: {TEAL_600};
  --amber: {AMBER_600};
  --rose: {ROSE_600};
  --emerald: {EMERALD_600};
  --purple: #7C3AED;

  --text: {SLATE_900};
  --text-secondary: {SLATE_700};
  --text-muted: {SLATE_500};
  --border: {SLATE_200};
  --border-light: {SLATE_100};
  --surface: {WHITE};
  --surface-alt: {SLATE_50};
  --bg: {SLATE_50};
  --bg-alt: {SLATE_100};
  --sidebar-bg: linear-gradient(180deg, {WHITE} 0%, var(--blue-50) 100%);
  --sidebar-status-bg: rgba(255,255,255,0.82);
  --input-bg: {WHITE};
  --input-text: {SLATE_900};
  --input-placeholder: {SLATE_500};
  --chart-bg: {WHITE};
  --chart-grid: {BLUE_50};
  --focus-ring: rgba(37,99,235,0.12);

  --radius-sm: 6px;
  --radius: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.06), 0 4px 10px rgba(0,0,0,0.04);
  --shadow-xl: 0 20px 50px rgba(0,0,0,0.08), 0 8px 20px rgba(0,0,0,0.04);
  --shadow-blue: 0 12px 32px rgba(37,99,235,0.12);

  --font-sans: {APP_FONT_STACK};
  --font-serif: {APP_FONT_STACK};

  --transition: 180ms ease;
  --transition-slow: 280ms ease;
}}

/* ========================= GLOBAL RESETS ========================= */
html, body {{
  background: var(--bg);
  color: var(--text);
}}

.stApp {{
  background:
    linear-gradient(90deg, rgba(37,99,235,0.025) 1px, transparent 1px),
    linear-gradient(180deg, rgba(37,99,235,0.02) 1px, transparent 1px),
    var(--bg);
  background-size: 40px 40px;
  color: var(--text);
  font-family: var(--font-sans);
}}
.stApp * {{ font-family: var(--font-sans); }}

header[data-testid="stHeader"] {{
  background: transparent !important;
}}

/* Streamlit uses Material icon ligatures for sidebar collapse, expanders,
   help icons, and several controls. Keep those fonts intact so icon names
   such as keyboard_arrow_down never render as visible text. */
.stApp .material-icons,
.stApp .material-icons-outlined,
.stApp .material-icons-round,
.stApp .material-icons-sharp,
.stApp .material-symbols-outlined,
.stApp .material-symbols-rounded,
.stApp .material-symbols-sharp,
.stApp [data-testid="stIconMaterial"],
.stApp [data-testid="stIconMaterial"] *,
.stApp span[class*="material-icons"],
.stApp span[class*="material-symbols"] {{
  font-family: "Material Symbols Rounded", "Material Symbols Outlined",
               "Material Symbols Sharp", "Material Icons" !important;
  font-weight: normal !important;
  font-style: normal !important;
  font-size: inherit;
  line-height: 1 !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  white-space: nowrap !important;
  word-wrap: normal !important;
  direction: ltr;
  -webkit-font-feature-settings: "liga";
  -webkit-font-smoothing: antialiased;
  font-feature-settings: "liga";
}}
.block-container {{ padding: 1.5rem 2rem 3rem; max-width: 1240px; }}

h1, h2, h3, h4, h5, h6 {{
  color: var(--text);
  letter-spacing: -0.01em;
}}

/* ========================= SIDEBAR ========================= */
section[data-testid="stSidebar"] {{
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
}}

section[data-testid="stSidebar"] [role="radiogroup"] {{
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 4px;
}}

section[data-testid="stSidebar"] [role="radiogroup"] label {{
  border-radius: var(--radius);
  padding: 9px 12px;
  transition: background var(--transition), transform var(--transition);
  font-size: 0.92rem;
  font-weight: 500;
  color: var(--text-secondary) !important;
  border: 1px solid transparent;
}}

section[data-testid="stSidebar"] [role="radiogroup"] label p,
section[data-testid="stSidebar"] [role="radiogroup"] label span:not([class*="material-icons"]):not([class*="material-symbols"]) {{
  color: var(--text-secondary) !important;
}}

section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
  background: rgba(37,99,235,0.06);
  transform: translateX(3px);
  border-color: rgba(37,99,235,0.12);
}}

section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"],
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background: linear-gradient(135deg, rgba(37,99,235,0.10), rgba(37,99,235,0.05));
  color: var(--blue-600) !important;
  font-weight: 700;
  border-color: rgba(37,99,235,0.20);
  box-shadow: var(--shadow-sm);
}}

section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] p,
section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] span:not([class*="material-icons"]):not([class*="material-symbols"]),
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p,
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span:not([class*="material-icons"]):not([class*="material-symbols"]) {{
  color: var(--blue-600) !important;
}}

/* ========================= BRAND BLOCK ========================= */
.brand-block {{
  display: flex;
  align-items: center;
  gap: 13px;
  margin: 4px 0 16px 0;
  padding: 6px 0;
}}

.brand-icon {{
  width: 44px;
  height: 44px;
  border-radius: var(--radius);
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, {BLUE_600}, #1D4ED8);
  color: white;
  font-size: 0.82rem;
  font-weight: 900;
  letter-spacing: 0.03em;
  box-shadow: 0 10px 24px rgba(37,99,235,0.28);
  flex-shrink: 0;
}}

.brand-name {{
  font-weight: 800;
  font-size: 1.1rem;
  color: var(--text);
  line-height: 1.15;
  letter-spacing: -0.01em;
}}

.brand-sub {{
  color: var(--text-muted);
  font-size: 0.78rem;
  margin-top: 3px;
}}

.sidebar-divider {{
  height: 1px;
  background: linear-gradient(90deg, var(--border), transparent);
  margin: 12px 0 16px 0;
}}

/* ========================= SIDEBAR STATUS ========================= */
.sidebar-status {{
  display: flex;
  gap: 10px;
  align-items: center;
  border: 1px solid var(--border);
  background: var(--sidebar-status-bg);
  border-radius: var(--radius);
  padding: 12px 14px;
  margin-top: 18px;
  backdrop-filter: blur(8px);
}}

.sidebar-status-title {{
  color: var(--text-muted);
  font-size: 0.76rem;
  font-weight: 600;
}}

.sidebar-status-mark {{
  width: 30px;
  height: 30px;
  border-radius: 99px;
  display: grid;
  place-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  font-size: 0.82rem;
  font-weight: 900;
  flex-shrink: 0;
}}

.sidebar-status-level {{
  font-weight: 800;
  font-size: 0.95rem;
  margin-top: 2px;
}}

/* ========================= HERO PANEL ========================= */
.hero-panel {{
  position: relative;
  display: grid;
  grid-template-columns: minmax(0,1fr) 340px;
  gap: 24px;
  align-items: center;
  overflow: hidden;
  border: 1px solid rgba(37,99,235,0.14);
  background:
    linear-gradient(120deg, rgba(37,99,235,0.06), transparent 40%),
    linear-gradient(300deg, rgba(37,99,235,0.04), transparent 50%),
    linear-gradient(135deg, {WHITE} 0%, {BLUE_50} 60%, #DBEAFE 100%);
  padding: 32px 36px;
  border-radius: var(--radius-lg);
  margin: 4px 0 20px 0;
  box-shadow: var(--shadow-blue);
}}

.hero-grid {{
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(37,99,235,0.07) 1px, transparent 1px),
    linear-gradient(180deg, rgba(37,99,235,0.05) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(90deg, black, transparent 70%);
}}

.hero-content, .hero-console {{ position: relative; z-index: 1; }}

.hero-kicker {{
  display: inline-block;
  color: var(--blue-600);
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 8px;
  padding: 3px 10px;
  background: rgba(37,99,235,0.08);
  border-radius: 99px;
}}

.hero-title {{
  color: var(--text);
  font-size: 2.8rem;
  line-height: 1.22;
  font-weight: 900;
  margin-bottom: 6px;
  letter-spacing: -0.02em;
}}

.hero-subtitle {{
  color: var(--text-secondary);
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 12px;
}}

.hero-copy {{
  color: var(--text-muted);
  max-width: 640px;
  line-height: 1.75;
  font-size: 0.95rem;
}}

.hero-actions {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 22px;
}}

.btn-primary, .btn-ghost {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 22px;
  border-radius: var(--radius);
  text-decoration: none !important;
  font-weight: 700;
  font-size: 0.94rem;
  transition: transform var(--transition), box-shadow var(--transition),
              background var(--transition), border-color var(--transition);
}}

.btn-primary {{
  color: white !important;
  background: linear-gradient(135deg, {BLUE_600}, #1D4ED8);
  box-shadow: 0 10px 24px rgba(37,99,235,0.28);
}}

.btn-primary:hover {{
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(37,99,235,0.32);
}}

.btn-ghost {{
  color: var(--blue-600) !important;
  border: 1.5px solid rgba(37,99,235,0.22);
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(4px);
}}

.btn-ghost:hover {{
  border-color: rgba(37,99,235,0.45);
  background: rgba(255,255,255,0.9);
  transform: translateY(-2px);
}}

/* ========================= HERO CONSOLE ========================= */
.hero-console {{
  border: 1px solid rgba(37,99,235,0.18);
  background: rgba(255,255,255,0.85);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: 0 16px 40px rgba(37,99,235,0.10);
  backdrop-filter: blur(12px);
}}

.console-bar {{
  display: flex;
  gap: 7px;
  margin-bottom: 18px;
}}

.console-bar span {{
  width: 10px;
  height: 10px;
  border-radius: 99px;
  background: var(--blue-100);
}}

.console-bar span:first-child {{ background: {BLUE_500}; }}

.signal-line {{
  display: grid;
  grid-template-columns: 90px 1fr;
  align-items: center;
  gap: 12px;
  margin: 13px 0;
}}

.signal-line b {{
  color: var(--text);
  font-size: 0.88rem;
  font-weight: 600;
}}

.signal-line i {{
  height: 10px;
  border-radius: 99px;
  background: {SLATE_100};
  position: relative;
  overflow: hidden;
}}

.signal-line i::after {{
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: var(--w);
  border-radius: inherit;
  background: linear-gradient(90deg, {BLUE_600}, {BLUE_500});
  animation: signalGrow 800ms ease both;
}}

@keyframes signalGrow {{
  from {{ transform: translateX(-100%); }}
  to   {{ transform: translateX(0); }}
}}

/* ========================= SECTION HEADERS ========================= */
.page-header {{
  border-left: 4px solid var(--blue-600);
  padding: 12px 0 16px 18px;
  margin-top: 10px;
  margin-bottom: 22px;
  overflow: visible;
}}

.page-header .eyebrow {{
  display: block;
  color: var(--blue-600);
  font-weight: 800;
  font-size: 0.8rem;
  line-height: 1.35;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 0 0 6px 0;
  padding-top: 1px;
}}

.page-header h1 {{
  margin: 0 0 6px 0;
  font-size: 1.9rem;
  line-height: 1.25;
  font-weight: 850;
}}

.page-header p {{
  color: var(--text-muted);
  margin: 0;
  line-height: 1.65;
  font-size: 0.95rem;
}}

.section-title {{
  margin: 28px 0 12px 0;
  color: var(--text);
  font-size: 1.08rem;
  font-weight: 750;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.section-title::before {{
  content: "";
  width: 4px;
  height: 20px;
  background: var(--blue-600);
  border-radius: 2px;
}}

.page-divider {{
  height: 1px;
  background: linear-gradient(90deg, var(--border), transparent);
  margin: 24px 0 8px 0;
}}

/* ========================= STAT CARDS ========================= */
.stat-card {{
  min-height: 108px;
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent, {BLUE_600});
  background: var(--surface);
  border-radius: var(--radius);
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: var(--shadow);
  transition: transform var(--transition), box-shadow var(--transition);
}}

.stat-card:hover {{
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}}

.stat-icon {{
  width: 44px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: color-mix(in srgb, var(--accent, {BLUE_600}) 12%, white);
  color: var(--accent, {BLUE_600});
  font-size: 0.9rem;
  font-weight: 900;
  flex-shrink: 0;
}}

.stat-value {{
  color: var(--text);
  font-size: 1.7rem;
  line-height: 1.1;
  font-weight: 850;
}}

.stat-label {{
  color: var(--text-muted);
  font-size: 0.84rem;
  line-height: 1.35;
  margin-top: 4px;
}}

/* ========================= DIMENSION CARDS ========================= */
.dimension-card {{
  min-height: 170px;
  border: 1px solid var(--border);
  border-top: 4px solid var(--dim-color, {BLUE_600});
  background: var(--surface);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow);
  transition: transform var(--transition), box-shadow var(--transition);
}}

.dimension-card:hover {{
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}}

.dimension-icon {{
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: var(--radius-sm);
  margin-bottom: 14px;
  font-size: 0.76rem;
  font-weight: 900;
  letter-spacing: 0.02em;
}}

.dimension-name {{
  color: var(--text);
  font-weight: 750;
  font-size: 1rem;
  margin-bottom: 8px;
}}

.dimension-copy {{
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.55;
}}

/* ========================= QUICK NAV GRID ========================= */
.quick-nav-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 12px;
  margin: 18px 0 22px 0;
}}

.quick-nav-card {{
  display: block;
  min-height: 128px;
  padding: 18px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: linear-gradient(180deg, {WHITE} 0%, var(--surface-alt) 100%);
  text-decoration: none !important;
  color: var(--text) !important;
  box-shadow: var(--shadow);
  transition: transform var(--transition), border-color var(--transition),
              box-shadow var(--transition);
}}

.quick-nav-card:hover {{
  transform: translateY(-3px);
  border-color: rgba(37,99,235,0.35);
  box-shadow: var(--shadow-lg);
}}

.quick-nav-card .num {{
  color: var(--blue-600);
  font-weight: 900;
  font-size: 0.8rem;
}}

.quick-nav-card strong {{
  display: block;
  margin: 10px 0 6px 0;
  font-size: 1.02rem;
  font-weight: 700;
}}

.quick-nav-card em {{
  display: block;
  color: var(--text-muted);
  font-style: normal;
  line-height: 1.5;
  font-size: 0.86rem;
}}

/* ========================= PROCESS STEPS ========================= */
.process-list {{
  display: grid;
  grid-template-columns: repeat(5, minmax(0,1fr));
  gap: 10px;
  margin-bottom: 18px;
}}

.process-step {{
  min-height: 120px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  padding: 16px;
  box-shadow: var(--shadow-sm);
  transition: transform var(--transition);
}}

.process-step:hover {{ transform: translateY(-2px); }}

.process-step .step-num {{
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 99px;
  background: linear-gradient(135deg, {BLUE_600}, #1D4ED8);
  color: white;
  font-weight: 800;
  font-size: 0.82rem;
  margin-bottom: 12px;
}}

.process-step p {{
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
  font-size: 0.88rem;
}}

/* ========================= ETHICS NOTE ========================= */
.ethics-note {{
  border: 1px solid rgba(37,99,235,0.18);
  background: var(--blue-50);
  color: var(--text-secondary);
  border-radius: var(--radius);
  padding: 14px 18px;
  line-height: 1.7;
  font-weight: 550;
  font-size: 0.9rem;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}}

.ethics-note::before {{
  content: "i";
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 99px;
  background: var(--blue-600);
  color: white;
  font-size: 0.82rem;
  font-weight: 900;
  flex-shrink: 0;
  margin-top: 1px;
}}

.ethics-note a {{
  color: var(--blue-600) !important;
  font-weight: 750;
  margin-left: 6px;
}}

/* ========================= LEAD COPY ========================= */
.lead-copy {{
  color: var(--text-muted);
  font-size: 0.98rem;
  line-height: 1.8;
  margin: 10px 0 16px 0;
  max-width: 900px;
}}

/* ========================= WIZARD ========================= */
.wizard-container {{
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  box-shadow: var(--shadow-md);
  margin-bottom: 20px;
}}

.wizard-steps {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  position: relative;
}}

.wizard-steps::before {{
  content: "";
  position: absolute;
  top: 18px;
  left: 8%;
  right: 8%;
  height: 2px;
  background: var(--border);
  z-index: 0;
}}

.wizard-step-item {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
  flex: 1;
  text-align: center;
}}

.wizard-step-dot {{
  width: 36px;
  height: 36px;
  border-radius: 99px;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 0.85rem;
  background: var(--surface);
  border: 2px solid var(--border);
  color: var(--text-muted);
  transition: all var(--transition);
}}

.wizard-step-item.active .wizard-step-dot {{
  background: {BLUE_600};
  border-color: {BLUE_600};
  color: white;
  box-shadow: 0 6px 16px rgba(37,99,235,0.30);
}}

.wizard-step-item.done .wizard-step-dot {{
  background: var(--emerald);
  border-color: var(--emerald);
  color: white;
}}

.wizard-step-label {{
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted);
}}

.wizard-step-item.active .wizard-step-label,
.wizard-step-item.done .wizard-step-label {{
  color: var(--text);
}}

.wizard-step-sublabel {{
  font-size: 0.7rem;
  color: var(--text-muted);
  display: none;
}}

.wizard-step-item.active .wizard-step-sublabel {{
  display: block;
}}

.wizard-progress {{
  margin-bottom: 22px;
}}

.wizard-nav {{
  display: flex;
  gap: 10px;
  justify-content: space-between;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--border-light);
}}

/* ========================= FORM STYLING ========================= */
div[data-testid="stForm"] {{
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-md);
}}

.stButton > button,
.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button {{
  border-radius: var(--radius) !important;
  border: none !important;
  background: linear-gradient(135deg, {BLUE_600}, #1D4ED8) !important;
  color: white !important;
  font-weight: 700 !important;
  padding: 10px 24px !important;
  transition: transform var(--transition), box-shadow var(--transition),
              opacity var(--transition) !important;
  font-size: 0.94rem !important;
}}

.stButton > button:hover,
.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {{
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(37,99,235,0.22);
}}

.stButton > button:active,
div[data-testid="stFormSubmitButton"] > button:active {{
  transform: translateY(0);
}}

/* Secondary / ghost buttons */
.stButton > button[kind="secondary"] {{
  background: var(--surface) !important;
  color: var(--blue-600) !important;
  border: 1.5px solid var(--border) !important;
  box-shadow: none !important;
}}

.stButton > button[kind="secondary"]:hover {{
  border-color: rgba(37,99,235,0.35) !important;
  background: var(--blue-50) !important;
}}

/* ========================= INPUT STYLING ========================= */
textarea, input,
div[data-baseweb="select"] > div,
div[data-baseweb="multiselect"] > div {{
  border-radius: var(--radius) !important;
  border-color: var(--border) !important;
  background: var(--input-bg) !important;
  color: var(--input-text) !important;
}}

textarea::placeholder,
input::placeholder {{
  color: var(--input-placeholder) !important;
  opacity: 1 !important;
}}

div[data-testid="stTextArea"] {{
  margin-bottom: 12px;
}}

div[data-testid="stTextArea"] label {{
  min-height: 24px;
  line-height: 1.45 !important;
  align-items: center !important;
  gap: 6px;
  white-space: normal !important;
}}

div[data-testid="stTextArea"] textarea {{
  line-height: 1.65 !important;
  padding: 12px 14px !important;
  min-height: 120px;
  resize: vertical;
}}

details[data-testid="stExpander"] summary {{
  min-height: 46px;
  align-items: center !important;
}}

details[data-testid="stExpander"] summary p {{
  line-height: 1.45 !important;
  margin: 0 !important;
}}

details[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {{
  line-height: 1.55;
}}

div[data-baseweb="select"] > div:hover,
div[data-baseweb="multiselect"] > div:hover,
textarea:hover, input:hover {{
  border-color: rgba(37,99,235,0.3) !important;
}}

div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="multiselect"] > div:focus-within,
textarea:focus, input:focus {{
  border-color: {BLUE_600} !important;
  box-shadow: 0 0 0 3px var(--focus-ring) !important;
}}

/* ========================= CHART CONTAINERS ========================= */
.chart-box {{
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius);
  padding: 16px 18px 10px 18px;
  box-shadow: var(--shadow);
  margin-bottom: 14px;
}}

.chart-box h3 {{
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text);
}}

.chart-box .caption {{
  color: var(--text-muted);
  font-size: 0.82rem;
  margin-top: 6px;
  line-height: 1.5;
}}

.option-legend {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 6px 10px;
  margin: 8px 0 12px 0;
}}

.option-legend-item {{
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr);
  align-items: start;
  gap: 8px;
  color: var(--text-muted);
  font-size: 0.82rem;
  line-height: 1.45;
}}

.option-code {{
  display: inline-flex;
  width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: {BLUE_50};
  color: {BLUE_600};
  font-weight: 700;
  font-family: "Times New Roman", serif;
}}

/* ========================= RISK RESULT ========================= */
.risk-summary {{
  border-radius: var(--radius-lg);
  padding: 22px 26px;
  margin: 18px 0 14px 0;
  border: 1.5px solid var(--risk-border);
  background: var(--risk-bg);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px 20px;
  align-items: center;
}}

.risk-summary .risk-badge {{
  grid-row: span 2;
  width: 64px;
  height: 64px;
  border-radius: 99px;
  display: grid;
  place-items: center;
  color: var(--risk-fg);
  font-size: 1.2rem;
  font-weight: 900;
  background: white;
  box-shadow: var(--shadow-md);
}}

.risk-summary .risk-label {{
  font-size: 0.82rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

.risk-summary .risk-level {{
  font-size: 1.7rem;
  font-weight: 900;
  line-height: 1.15;
  color: var(--risk-fg);
}}

.risk-summary .risk-score {{
  color: var(--text-muted);
  font-size: 0.9rem;
}}

/* ========================= LIST CARDS ========================= */
.list-card-group {{
  display: grid;
  gap: 8px;
  margin-bottom: 10px;
}}

.list-card {{
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius);
  padding: 13px 16px;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.92rem;
  box-shadow: var(--shadow-sm);
  transition: transform var(--transition);
}}

.list-card:hover {{ transform: translateX(3px); }}

.explanation-list .list-card {{
  border-left: 4px solid var(--amber);
}}

.suggestion-list .list-card {{
  border-left: 4px solid var(--emerald);
}}

.rule-list .list-card {{
  border-left: 4px solid var(--rose);
}}

/* ========================= INSIGHT ITEMS ========================= */
.insight-item {{
  border-left: 4px solid var(--blue-600);
  background: var(--surface);
  border-radius: 0 var(--radius) var(--radius) 0;
  padding: 13px 16px;
  margin: 8px 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.92rem;
  box-shadow: var(--shadow-sm);
}}

/* ========================= INFO GRID ========================= */
.info-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 14px;
  margin-top: 8px;
}}

.info-panel {{
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform var(--transition);
}}

.info-panel:hover {{ transform: translateY(-2px); }}

.info-panel .info-num {{
  color: var(--blue-600);
  font-weight: 900;
  font-size: 0.82rem;
}}

.info-panel h3 {{
  margin: 8px 0 8px 0;
  font-size: 1.14rem;
  font-weight: 750;
}}

.info-panel p {{
  color: var(--text-muted);
  line-height: 1.7;
  margin: 0;
  font-size: 0.92rem;
}}

/* ========================= REFERENCE STRIP ========================= */
.reference-strip {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}}

.reference-strip a {{
  border: 1px solid var(--border);
  color: var(--blue-600) !important;
  background: var(--surface);
  text-decoration: none !important;
  border-radius: var(--radius);
  padding: 10px 16px;
  font-weight: 700;
  font-size: 0.9rem;
  transition: all var(--transition);
}}

.reference-strip a:hover {{
  border-color: rgba(37,99,235,0.35);
  background: var(--blue-50);
  transform: translateY(-2px);
}}

/* ========================= FEEDBACK FORM ========================= */
.feedback-preview {{
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-top: 16px;
  box-shadow: var(--shadow-sm);
}}

/* ========================= DARK MODE ========================= */
@media (prefers-color-scheme: dark) {{
  :root {{
    color-scheme: dark;
    --text: #F8FAFC;
    --text-secondary: #E2E8F0;
    --text-muted: #CBD5E1;
    --border: #475569;
    --border-light: #334155;
    --surface: #172033;
    --surface-alt: #111827;
    --bg: #0B1120;
    --bg-alt: #111827;
    --sidebar-bg: linear-gradient(180deg, #151E2F 0%, #0B1120 100%);
    --sidebar-status-bg: rgba(15,23,42,0.86);
    --input-bg: #0F172A;
    --input-text: #F8FAFC;
    --input-placeholder: #94A3B8;
    --chart-bg: #111827;
    --chart-grid: #334155;
    --focus-ring: rgba(96,165,250,0.28);
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.35);
    --shadow: 0 1px 3px rgba(0,0,0,0.36), 0 1px 2px rgba(0,0,0,0.28);
    --shadow-md: 0 8px 18px rgba(0,0,0,0.34);
    --shadow-lg: 0 16px 36px rgba(0,0,0,0.38);
    --shadow-xl: 0 24px 56px rgba(0,0,0,0.42);
    --shadow-blue: 0 18px 46px rgba(37,99,235,0.18);
  }}

  .stApp {{
    background:
      linear-gradient(90deg, rgba(37,99,235,0.04) 1px, transparent 1px),
      linear-gradient(180deg, rgba(37,99,235,0.03) 1px, transparent 1px),
      var(--bg);
  }}

  body,
  [data-testid="stAppViewContainer"] {{
    background: var(--bg) !important;
  }}

  .block-container {{
    padding-top: 1rem;
  }}

  header[data-testid="stHeader"] {{
    min-height: 0 !important;
    height: 0 !important;
    background: transparent !important;
    color: var(--text) !important;
    pointer-events: none;
  }}

  header[data-testid="stHeader"] [data-testid="stToolbar"] {{
    display: block !important;
    height: 0 !important;
    min-height: 0 !important;
    pointer-events: none;
  }}

  header[data-testid="stHeader"] [data-testid="stToolbarActions"],
  header[data-testid="stHeader"] [data-testid="stBaseButton-header"],
  header[data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"]:not([data-testid="stExpandSidebarButton"]) {{
    display: none !important;
  }}

  header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] {{
    position: fixed !important;
    left: 14px !important;
    top: 14px !important;
    z-index: 1000002 !important;
    width: 38px !important;
    height: 38px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    visibility: visible !important;
    pointer-events: auto !important;
    border: 1px solid rgba(96,165,250,0.42) !important;
    border-radius: 10px !important;
    background: rgba(15,23,42,0.92) !important;
    color: #DBEAFE !important;
    box-shadow: 0 10px 28px rgba(0,0,0,0.34), 0 0 0 1px rgba(37,99,235,0.16) !important;
  }}

  header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"]:hover {{
    background: rgba(37,99,235,0.34) !important;
    border-color: rgba(147,197,253,0.7) !important;
  }}

  header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] span,
  header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {{
    color: #DBEAFE !important;
    visibility: visible !important;
  }}

  section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button[data-testid="stBaseButton-headerNoPadding"] {{
    visibility: visible !important;
    opacity: 1 !important;
    width: 34px !important;
    height: 34px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 10px !important;
    border: 1px solid rgba(96,165,250,0.35) !important;
    background: rgba(15,23,42,0.54) !important;
    color: #DBEAFE !important;
    box-shadow: 0 8px 18px rgba(0,0,0,0.22) !important;
  }}

  section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button[data-testid="stBaseButton-headerNoPadding"]:hover {{
    background: rgba(37,99,235,0.28) !important;
    border-color: rgba(147,197,253,0.62) !important;
  }}

  section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button[data-testid="stBaseButton-headerNoPadding"] span,
  section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button[data-testid="stBaseButton-headerNoPadding"] [data-testid="stIconMaterial"] {{
    color: #DBEAFE !important;
    visibility: visible !important;
  }}

  .stApp [data-testid="stMarkdownContainer"],
  .stApp [data-testid="stMarkdownContainer"] p,
  .stApp [data-testid="stMarkdownContainer"] li,
  .stApp label,
  .stApp span:not([class*="material-icons"]):not([class*="material-symbols"]) {{
    color: inherit;
  }}

  .hero-panel {{
    background:
      linear-gradient(120deg, rgba(96,165,250,0.13), transparent 42%),
      linear-gradient(300deg, rgba(20,184,166,0.08), transparent 52%),
      linear-gradient(135deg, #172033 0%, #111827 58%, #0B1120 100%);
    border-color: rgba(96,165,250,0.26);
  }}

  .quick-nav-card {{
    background: linear-gradient(180deg, #172033 0%, #111827 100%);
  }}

  .stat-card, .dimension-card, .chart-box, .info-panel,
  .process-step, .list-card, .insight-item, .wizard-container,
  .feedback-preview, div[data-testid="stForm"] {{
    background: var(--surface);
  }}

  .hero-console {{
    background: rgba(15,23,42,0.88);
    border-color: rgba(96,165,250,0.24);
  }}

  .btn-ghost {{
    background: rgba(15,23,42,0.72);
    border-color: rgba(96,165,250,0.34);
    color: #BFDBFE !important;
  }}

  .btn-ghost:hover {{
    background: rgba(30,41,59,0.92);
    border-color: rgba(96,165,250,0.55);
  }}

  .signal-line i {{ background: #334155; }}

  section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: rgba(96,165,250,0.12);
    border-color: rgba(96,165,250,0.22);
  }}

  section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"],
  section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
    background: rgba(96,165,250,0.18);
    border-color: rgba(96,165,250,0.38);
    color: #DBEAFE !important;
  }}

  section[data-testid="stSidebar"] [role="radiogroup"] label,
  section[data-testid="stSidebar"] [role="radiogroup"] label p,
  section[data-testid="stSidebar"] [role="radiogroup"] label span:not([class*="material-icons"]):not([class*="material-symbols"]) {{
    color: var(--text-secondary) !important;
  }}

  section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] p,
  section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] span:not([class*="material-icons"]):not([class*="material-symbols"]),
  section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p,
  section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span:not([class*="material-icons"]):not([class*="material-symbols"]) {{
    color: #DBEAFE !important;
  }}

  .brand-name,
  .wizard-step-item.active .wizard-step-label,
  .wizard-step-item.done .wizard-step-label {{
    color: var(--text);
  }}

  .sidebar-divider,
  .page-divider {{
    background: linear-gradient(90deg, var(--border), transparent);
  }}

  .hero-kicker,
  .quick-nav-card .num,
  .info-panel .info-num,
  .reference-strip a,
  .ethics-note a {{
    color: #93C5FD !important;
  }}

  .ethics-note {{
    background: rgba(37,99,235,0.14);
    border-color: rgba(96,165,250,0.26);
    color: var(--text-secondary);
  }}

  .stat-icon,
  .option-code {{
    background: rgba(96,165,250,0.16);
    color: #BFDBFE;
  }}

  .dimension-icon {{
    background: color-mix(in srgb, var(--dim-color, {BLUE_600}) 24%, transparent) !important;
  }}

  .risk-summary {{
    background: color-mix(in srgb, var(--risk-fg) 16%, #0F172A) !important;
    border-color: color-mix(in srgb, var(--risk-fg) 46%, #334155) !important;
  }}

  .risk-summary .risk-badge {{
    background: rgba(15,23,42,0.84);
  }}

  textarea, input,
  div[data-baseweb="select"] > div,
  div[data-baseweb="multiselect"] > div {{
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
    border-color: var(--border) !important;
  }}

  div[data-testid="stTextAreaRootElement"],
  div[data-baseweb="textarea"],
  div[data-baseweb="base-input"] {{
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
    border-color: var(--border) !important;
  }}

  div[data-testid="stTextAreaRootElement"]:hover,
  div[data-baseweb="textarea"]:hover,
  div[data-baseweb="base-input"]:hover {{
    background: var(--input-bg) !important;
    border-color: rgba(147,197,253,0.44) !important;
  }}

  div[data-testid="stTextAreaRootElement"]:focus-within,
  div[data-baseweb="textarea"]:focus-within,
  div[data-baseweb="base-input"]:focus-within {{
    background: var(--input-bg) !important;
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.22) !important;
  }}

  div[data-baseweb="select"] span,
  div[data-baseweb="multiselect"] span,
  div[data-baseweb="select"] input,
  div[data-baseweb="multiselect"] input,
  div[data-baseweb="select"] [value],
  div[data-baseweb="multiselect"] [value] {{
    color: var(--input-text) !important;
  }}

  div[data-baseweb="select"] svg,
  div[data-baseweb="multiselect"] svg,
  div[data-baseweb="select"] svg *,
  div[data-baseweb="multiselect"] svg * {{
    color: #BFDBFE !important;
    fill: currentColor !important;
  }}

  div[data-baseweb="select"] svg path[fill="none"],
  div[data-baseweb="multiselect"] svg path[fill="none"] {{
    fill: none !important;
  }}

  div[data-baseweb="popover"],
  div[data-baseweb="popover"] ul,
  div[data-baseweb="popover"] [role="listbox"],
  div[role="listbox"],
  ul[role="listbox"] {{
    background: #0F172A !important;
    color: var(--input-text) !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 18px 44px rgba(0,0,0,0.38) !important;
  }}

  div[data-baseweb="popover"],
  div[data-baseweb="popover"] *,
  div[role="option"],
  li[role="option"],
  div[role="option"] *,
  li[role="option"] * {{
    color: var(--input-text) !important;
  }}

  div[role="option"],
  li[role="option"] {{
    background: #0F172A !important;
    border-color: transparent !important;
  }}

  div[role="option"]:hover,
  li[role="option"]:hover,
  div[role="option"][aria-selected="true"],
  li[role="option"][aria-selected="true"] {{
    background: rgba(96,165,250,0.18) !important;
  }}

  span[data-baseweb="tag"],
  div[data-baseweb="tag"] {{
    background: rgba(37,99,235,0.34) !important;
    color: #DBEAFE !important;
    border: 1px solid rgba(147,197,253,0.28) !important;
  }}

  span[data-baseweb="tag"] *,
  div[data-baseweb="tag"] * {{
    color: #DBEAFE !important;
  }}

  section[data-testid="stFileUploaderDropzone"] {{
    background: rgba(15,23,42,0.86) !important;
    border: 1.5px dashed rgba(147,197,253,0.48) !important;
    color: var(--text-secondary) !important;
  }}

  section[data-testid="stFileUploaderDropzone"]:hover {{
    background: rgba(30,41,59,0.94) !important;
    border-color: rgba(147,197,253,0.72) !important;
  }}

  section[data-testid="stFileUploaderDropzone"] *,
  [data-testid="stFileUploaderDropzoneInstructions"],
  [data-testid="stFileUploaderDropzoneInstructions"] * {{
    color: var(--text-secondary) !important;
  }}

  section[data-testid="stFileUploaderDropzone"] svg {{
    color: #BFDBFE !important;
    fill: currentColor !important;
  }}

  section[data-testid="stFileUploaderDropzone"] svg path[fill="none"] {{
    fill: none !important;
  }}

  section[data-testid="stFileUploaderDropzone"] button {{
    background: rgba(37,99,235,0.22) !important;
    border: 1px solid rgba(147,197,253,0.42) !important;
    color: #DBEAFE !important;
  }}

  section[data-testid="stFileUploaderDropzone"] button * {{
    color: #DBEAFE !important;
  }}

  div[data-testid="stExpander"] > details {{
    background: var(--surface) !important;
    border-color: var(--border) !important;
  }}

  div[data-testid="stExpander"] > details > summary,
  div[data-testid="stExpander"] > details > summary *,
  div[data-testid="stExpander"] [data-testid="stExpanderToggleIcon"],
  div[data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] * {{
    background: var(--surface) !important;
    color: var(--text) !important;
    fill: currentColor !important;
  }}

  div[data-testid="stExpander"] [data-testid="stExpanderDetails"],
  div[data-testid="stExpander"] > details > div {{
    background: var(--surface) !important;
    color: var(--text-secondary) !important;
  }}

  div[data-testid="stTextArea"] textarea {{
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
    border-color: var(--border) !important;
  }}

  div[data-testid="stTextArea"] textarea:hover,
  div[data-testid="stTextArea"] textarea:focus {{
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
  }}

  div[data-testid="stTabs"] button,
  div[data-testid="stTabs"] button *,
  button[data-testid="stTab"],
  button[data-testid="stTab"] * {{
    color: var(--text-secondary) !important;
  }}

  div[data-testid="stTabs"] button:hover,
  div[data-testid="stTabs"] button:hover *,
  button[data-testid="stTab"]:hover,
  button[data-testid="stTab"]:hover * {{
    color: #DBEAFE !important;
  }}

  div[data-testid="stTabs"] button[aria-selected="true"],
  div[data-testid="stTabs"] button[aria-selected="true"] *,
  button[data-testid="stTab"][aria-selected="true"],
  button[data-testid="stTab"][aria-selected="true"] * {{
    color: #93C5FD !important;
  }}

  div[data-testid="stTabs"] [role="tablist"] {{
    border-color: var(--border) !important;
  }}

  div[data-testid="stTabs"] button[aria-selected="true"] {{
    border-bottom-color: #60A5FA !important;
  }}

  .stAlert {{
    background: rgba(30,41,59,0.92) !important;
    color: var(--text-secondary) !important;
  }}

  .stDataFrame,
  div[data-testid="stDataFrame"] {{
    color: var(--text);
  }}

  .stButton > button[kind="secondary"] {{
    background: var(--surface) !important;
    color: #BFDBFE !important;
    border-color: var(--border) !important;
  }}

  .stButton > button[kind="secondary"]:hover,
  .stButton > button[kind="secondary"]:focus,
  button[data-testid="stBaseButton-secondary"]:hover,
  button[data-testid="stBaseButton-secondary"]:focus {{
    background: rgba(37,99,235,0.22) !important;
    color: #DBEAFE !important;
    border-color: rgba(147,197,253,0.55) !important;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.18) !important;
  }}

  .stButton > button[kind="secondary"] *,
  button[data-testid="stBaseButton-secondary"] * {{
    color: inherit !important;
  }}

  .stDownloadButton > button,
  div[data-testid="stDownloadButton"] button {{
    background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(147,197,253,0.38) !important;
    box-shadow: 0 12px 24px rgba(37,99,235,0.24) !important;
  }}

  .stDownloadButton > button:hover,
  .stDownloadButton > button:focus,
  div[data-testid="stDownloadButton"] button:hover,
  div[data-testid="stDownloadButton"] button:focus {{
    background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
    color: #FFFFFF !important;
    border-color: rgba(191,219,254,0.56) !important;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.20), 0 14px 26px rgba(37,99,235,0.26) !important;
  }}

  .stDownloadButton > button *,
  div[data-testid="stDownloadButton"] button * {{
    color: inherit !important;
  }}

  .stDownloadButton > button,
  div[data-testid="stFormSubmitButton"] > button,
  .stButton > button {{
    box-shadow: 0 10px 22px rgba(37,99,235,0.22);
  }}

  .js-plotly-plot .main-svg {{
    background: transparent !important;
  }}

  .js-plotly-plot .bg,
  .js-plotly-plot .bglayer rect {{
    fill: var(--chart-bg) !important;
  }}

  .js-plotly-plot text {{
    fill: var(--text-secondary) !important;
  }}

  .js-plotly-plot .gtitle,
  .js-plotly-plot .xtitle,
  .js-plotly-plot .ytitle,
  .js-plotly-plot .legendtext {{
    fill: var(--text) !important;
  }}

  .js-plotly-plot .xgrid,
  .js-plotly-plot .ygrid,
  .js-plotly-plot .angularaxisgrid,
  .js-plotly-plot .radialaxisgrid,
  .js-plotly-plot .gridlayer path {{
    stroke: var(--chart-grid) !important;
  }}

  .js-plotly-plot .legend .bg {{
    fill: rgba(15,23,42,0.88) !important;
    stroke: var(--border) !important;
  }}
}}

/* ========================= RESPONSIVE ========================= */
@media (max-width: 960px) {{
  .hero-panel {{
    grid-template-columns: 1fr;
  }}
  .hero-console {{ display: none; }}
  .hero-title {{ font-size: 2rem; }}
  .quick-nav-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .process-list {{ grid-template-columns: 1fr; }}
  .info-grid {{ grid-template-columns: 1fr; }}
}}

@media (max-width: 640px) {{
  .block-container {{ padding: 0.8rem 1rem 2rem; }}
  .hero-panel {{ padding: 20px; }}
  .hero-title {{ font-size: 1.5rem; }}
  .quick-nav-grid {{ grid-template-columns: 1fr; }}
  .stat-card {{ min-height: auto; }}
  .dimension-card {{ min-height: auto; }}
  .wizard-steps {{ flex-direction: column; gap: 10px; }}
  .wizard-steps::before {{ display: none; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# Reusable UI Components
# ═══════════════════════════════════════════════════════════════════════

def _stat_card(value: str, label: str, icon: str, color: str) -> str:
    """Render a single stat card as HTML. Caller wraps in st.markdown with unsafe_allow_html."""
    return f"""
<div class="stat-card" style="--accent:{color}">
  <div class="stat-icon">{icon}</div>
  <div>
    <div class="stat-value">{value}</div>
    <div class="stat-label">{label}</div>
  </div>
</div>"""


def _dimension_card(name: str, meta: Dict[str, str]) -> str:
    """Render a single dimension card."""
    return f"""
<div class="dimension-card" style="--dim-color:{meta['color']}">
  <div class="dimension-icon" style="background:{meta['color']}15;color:{meta['color']}">{meta['icon']}</div>
  <div class="dimension-name">{name}</div>
  <div class="dimension-copy">{meta['desc']}</div>
</div>"""


def _page_header(eyebrow: str, title: str, description: str) -> str:
    """Render a standard page header."""
    return f"""
<div class="page-header">
  <span class="eyebrow">{eyebrow}</span>
  <h1>{title}</h1>
  <p>{description}</p>
</div>"""


def _list_cards(title: str, items: List[str], card_class: str) -> None:
    """Render a titled list of cards with a specific CSS class."""
    if not items:
        return
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='list-card-group {card_class}'>"
        + "".join(f"<div class='list-card'>{item}</div>" for item in items)
        + "</div>",
        unsafe_allow_html=True,
    )


LETTER_CODES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _split_prefixed_option(label: str) -> Tuple[str | None, str]:
    """Return the option code and clean label for values like 'A.每天都用'."""
    stripped = label.strip()
    if len(stripped) >= 2 and stripped[0].isalpha() and stripped[1] in {".", "．"}:
        return stripped[0].upper(), stripped[2:].strip()
    return None, stripped


def _coded_data(
    data: Dict[str, Any],
    option_order: List[str] | None = None,
) -> Tuple[Dict[str, Any], List[Tuple[str, str]]]:
    """Convert verbose survey labels to A/B/C labels for compact chart axes."""
    labels = option_order or list(data.keys())
    coded: Dict[str, Any] = {}
    legend: List[Tuple[str, str]] = []

    for index, label in enumerate(labels):
        if label not in data:
            continue
        prefixed_code, clean_label = _split_prefixed_option(label)
        code = prefixed_code or LETTER_CODES[index]
        coded[code] = data[label]
        legend.append((code, clean_label))

    return coded, legend


def _render_option_legend(items: List[Tuple[str, str]]) -> None:
    """Render a compact legend for A/B/C coded survey charts."""
    if not items:
        return
    st.markdown(
        "<div class='option-legend'>"
        + "".join(
            f"<div class='option-legend-item'><span class='option-code'>{escape(code)}</span>"
            f"<span>{escape(label)}</span></div>"
            for code, label in items
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def _plotly_coded_bar(
    data: Dict[str, Any],
    title: str,
    orientation: str = "h",
    option_order: List[str] | None = None,
) -> None:
    """Render a bar chart with A/B/C axis codes and a full option legend."""
    coded, legend = _coded_data(data, option_order)
    _plotly_bar(coded, title, orientation=orientation)
    _render_option_legend(legend)


def _plotly_bar(
    data: Dict[str, Any],
    title: str,
    orientation: str = "h",
) -> None:
    """Render an interactive Plotly bar chart."""
    if not data:
        st.info("暂无可展示数据。")
        return

    labels = list(data.keys())
    values = list(data.values())
    numeric_values = [
        float(value) if isinstance(value, (int, float)) else 0.0
        for value in values
    ]
    max_value = max(numeric_values) if numeric_values else 0.0
    value_axis_range = [0, max(max_value * 1.18, max_value + 6, 1)]

    if orientation == "h":
        labels = labels[::-1]
        values = values[::-1]

    palette = [BLUE_600, BLUE_500, "#60A5FA", BLUE_100, TEAL_600, EMERALD_600]
    bar_colors = [palette[i % len(palette)] for i in range(len(values))]

    fig = go.Figure()
    if orientation == "h":
        fig.add_trace(go.Bar(
            y=labels, x=values,
            orientation="h",
            marker=dict(color=bar_colors, line=dict(color="white", width=1)),
            text=values,
            textposition="outside",
            textfont=dict(color=SLATE_700, size=12),
            cliponaxis=False,
            hovertemplate="%{{y}}: %{{x}}<extra></extra>",
        ))
    else:
        fig.add_trace(go.Bar(
            x=labels, y=values,
            marker=dict(color=bar_colors, line=dict(color="white", width=1)),
            text=values,
            textposition="outside",
            textfont=dict(color=SLATE_700, size=12),
            cliponaxis=False,
            hovertemplate="%{{x}}: %{{y}}<extra></extra>",
        ))

    xaxis_config = dict(showgrid=True, gridcolor=BLUE_50, zeroline=False, automargin=True)
    yaxis_config = dict(showgrid=False, zeroline=False, automargin=True)
    if orientation == "h":
        xaxis_config["range"] = value_axis_range
        margin = dict(l=10, r=88, t=64, b=18)
    else:
        yaxis_config.update({"range": value_axis_range, "showgrid": True, "gridcolor": BLUE_50})
        xaxis_config.update({"showgrid": False, "tickangle": -12})
        margin = dict(l=24, r=28, t=68, b=58)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=SLATE_900, family=APP_FONT_STACK)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=margin,
        xaxis=xaxis_config,
        yaxis=yaxis_config,
        showlegend=False,
        height=max(300, len(labels) * 35),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _plotly_stacked_bar(
    data: Dict[str, Dict[str, int]],
    title: str,
    option_order: List[str] | None = None,
) -> None:
    """Render a stacked horizontal bar chart for acceptance data."""
    if not data:
        st.info("暂无可展示数据。")
        return

    labels = [label for label in (option_order or list(data.keys())) if label in data]
    coded_labels = []
    legend: List[Tuple[str, str]] = []
    for index, label in enumerate(labels):
        prefixed_code, clean_label = _split_prefixed_option(label)
        code = prefixed_code or LETTER_CODES[index]
        coded_labels.append(code)
        legend.append((code, clean_label))

    allowed = [data[l].get("允许", 0) for l in labels]
    declared = [data[l].get("允许但需要说明", 0) for l in labels]
    denied = [data[l].get("不允许", 0) for l in labels]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=coded_labels, x=allowed, name="允许",
        customdata=labels,
        orientation="h",
        marker=dict(color=BLUE_600, line=dict(color="white", width=1)),
        hovertemplate="%{{customdata}}<br>允许: %{{x}}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=coded_labels, x=declared, name="允许但需说明",
        customdata=labels,
        orientation="h",
        marker=dict(color=BLUE_100, line=dict(color="white", width=1)),
        hovertemplate="%{{customdata}}<br>允许但需说明: %{{x}}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=coded_labels, x=denied, name="不允许",
        customdata=labels,
        orientation="h",
        marker=dict(color=SLATE_200, line=dict(color="white", width=1)),
        hovertemplate="%{{customdata}}<br>不允许: %{{x}}<extra></extra>",
    ))

    fig.update_layout(
        barmode="stack",
        title=dict(text=title, font=dict(size=14, color=SLATE_900, family=APP_FONT_STACK)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=True, gridcolor=BLUE_50, zeroline=False, title="人数"),
        yaxis=dict(showgrid=False, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=max(320, len(labels) * 38),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    _render_option_legend(legend)


def _wrap_radar_label(label: str) -> str:
    """Split long Chinese polar labels so Plotly does not clip them."""
    if "<br>" in label:
        return label
    if label.endswith("风险") and len(label) > 4:
        return f"{label[:-2]}<br>风险"
    if len(label) > 5:
        midpoint = len(label) // 2
        return f"{label[:midpoint]}<br>{label[midpoint:]}"
    return label


def _plotly_radar(scores: Dict[str, int], labels: Dict[str, str]) -> None:
    """Render a radar/spider chart for the risk dimensions."""
    ordered_keys = [key for key in labels.keys() if key in scores]
    ordered_keys.extend(key for key in scores.keys() if key not in ordered_keys)
    full_theta = [labels.get(k, k) for k in ordered_keys]
    theta = [_wrap_radar_label(label) for label in full_theta]
    r = [scores.get(k, 0) for k in ordered_keys]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r,
        theta=theta,
        customdata=full_theta,
        fill="toself",
        fillcolor="rgba(37,99,235,0.18)",
        line=dict(color=BLUE_600, width=3, shape="spline"),
        marker=dict(color=BLUE_600, size=8),
        name="风险评分",
        hovertemplate="%{{customdata}}: %{{r}}分<extra></extra>",
    ))

    # Add a subtle reference ring at 50
    fig.add_trace(go.Scatterpolar(
        r=[50 for _ in ordered_keys],
        theta=theta,
        customdata=full_theta,
        mode="lines",
        line=dict(color=SLATE_200, width=1.5, dash="dash"),
        name="中线 (50)",
        hovertemplate="%{{customdata}}中线: 50<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            domain=dict(x=[0.12, 0.88], y=[0.12, 0.88]),
            radialaxis=dict(
                visible=True,
                range=[0, 105],
                tickfont=dict(size=10, color=SLATE_500),
                gridcolor=SLATE_100,
                ticks="",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color=SLATE_900, family=APP_FONT_STACK),
                gridcolor=SLATE_100,
            ),
            bgcolor="white",
        ),
        showlegend=False,
        margin=dict(l=78, r=78, t=58, b=58),
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════════════════
# Page: Home
# ═══════════════════════════════════════════════════════════════════════

def render_home() -> None:
    """Render the landing / home page."""
    # Hero
    st.markdown(
        f"""
<div class="hero-panel">
  <div class="hero-grid"></div>
  <div class="hero-content">
    <div class="hero-kicker">AI Ethics · Self-Audit · Governance</div>
    <div class="hero-title">EduAI-Guard</div>
    <div class="hero-subtitle">面向高校学生的大模型学习使用伦理自查与声明生成系统</div>
    <div class="hero-copy">
      以调研证据为底色，把学术诚信、隐私保护、可靠核查、公平风险、透明披露、
      学习主体、责任证据和版权授权
      组织成一条清晰的学习伦理路径。系统不简单判断学生"能不能用 AI"，
      而是帮助学生看见 AI 参与学习任务时的边界、证据、责任和披露方式。
    </div>
    <div class="hero-actions">
      <a class="btn-primary" href="?page=self-check" target="_self">开始伦理自查</a>
      <a class="btn-ghost" href="?page=survey" target="_self">浏览调研数据</a>
    </div>
  </div>
  <div class="hero-console" aria-hidden="true">
    <div class="console-bar"><span></span><span></span><span></span></div>
    <div class="signal-line"><b>学术诚信</b><i style="--w:78%"></i></div>
    <div class="signal-line"><b>数据隐私</b><i style="--w:64%"></i></div>
    <div class="signal-line"><b>内容可靠</b><i style="--w:84%"></i></div>
    <div class="signal-line"><b>学习主体</b><i style="--w:70%"></i></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Lead copy
    st.markdown(
        """
<div class="lead-copy">
  所有评分在本地完成，不调用外部 API，适合作为课程项目展示和个人作业提交前的伦理检查。
  系统覆盖学术诚信、数据隐私、内容可靠、偏见公平、透明披露、学习主体、责任证据和版权授权八个核心维度。
</div>
""",
        unsafe_allow_html=True,
    )

    # Quick nav
    st.markdown(
        """
<div class="quick-nav-grid">
  <a class="quick-nav-card" href="?page=survey" target="_self">
    <span class="num">01</span>
    <strong>调研数据概览</strong>
    <em>查看 79 份问卷背后的 AI 使用模式与关键发现</em>
  </a>
  <a class="quick-nav-card" href="?page=self-check" target="_self">
    <span class="num">02</span>
    <strong>AI 使用伦理自查</strong>
    <em>填写场景，获得八维风险评分与可执行建议</em>
  </a>
  <a class="quick-nav-card" href="?page=statement" target="_self">
    <span class="num">03</span>
    <strong>AI 使用声明生成</strong>
    <em>生成可附在作业末尾的正式透明披露文本</em>
  </a>
  <a class="quick-nav-card" href="?page=report" target="_self">
    <span class="num">04</span>
    <strong>自查报告下载</strong>
    <em>导出 Markdown 报告用于个人留档或课程展示</em>
  </a>
</div>
""",
        unsafe_allow_html=True,
    )

    # Key stats
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(_stat_card("79", "调研有效样本", "样本", BLUE_600), unsafe_allow_html=True)
    with c2:
        st.markdown(_stat_card("77.2%", "每天使用 AI", "频率", BLUE_500), unsafe_allow_html=True)
    with c3:
        st.markdown(_stat_card("79.7%", "DDL 救火经常/偶尔", "压力", AMBER_600), unsafe_allow_html=True)

    # Eight dimensions
    st.markdown("<div class='section-title'>八维伦理画像</div>", unsafe_allow_html=True)
    dimension_items = list(DIMENSION_META.items())
    for start in range(0, len(dimension_items), 4):
        cols = st.columns(4)
        for col, (name, meta) in zip(cols, dimension_items[start:start + 4]):
            with col:
                st.markdown(_dimension_card(name, meta), unsafe_allow_html=True)

    # Process
    st.markdown("<div class='section-title'>使用流程</div>", unsafe_allow_html=True)
    steps_text = [
        "选择作业类型<br>与使用场景",
        "勾选 AI 使用方式<br>和上传资料类型",
        "填写核查、披露<br>与超纲情况",
        "查看综合风险等级<br>八维评分与建议",
        "生成声明并下载<br>伦理自查报告",
    ]
    st.markdown(
        "<div class='process-list'>"
        + "".join(
            f"<div class='process-step'><div class='step-num'>{i}</div><p>{t}</p></div>"
            for i, t in enumerate(steps_text, 1)
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    # Ethics note
    st.markdown(
        """
<div class="ethics-note">
  <span>
    本系统不收集个人敏感信息；风险评估基于本地规则模型，仅供学习和伦理自查使用；
    最终作业责任由提交者本人承担。
    <a href="?page=about" target="_self">了解更多 →</a>
  </span>
</div>
""",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# Page: Survey Overview
# ═══════════════════════════════════════════════════════════════════════

def render_survey_overview() -> None:
    """Render the survey data overview page with interactive Plotly charts."""
    st.markdown(
        _page_header(
            "Survey Evidence",
            "调研数据概览",
            "基于 79 份高校学生问卷，展示 AI 使用频率、用途分布、场景接受度与公平压力因素。"
        ),
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "上传 CSV 文件（可选）", type=["csv"],
        help="未上传时使用 data/metadata_sample.csv 中的脱敏样例数据"
    )

    try:
        df = read_csv_flexible(uploaded) if uploaded else read_csv_flexible(DEFAULT_SURVEY_PATH)
        analysis = analyze_survey_data(df)
    except Exception as exc:
        st.error(f"读取或分析 CSV 时出错：{exc}")
        st.warning("请检查文件编码和表头是否与问卷字段一致。")
        return

    if analysis["missing_fields"]:
        st.warning("以下字段不存在，相关统计已跳过：" + "；".join(analysis["missing_fields"]))

    # ── Core Metrics ──
    st.markdown("<div class='section-title'>核心指标</div>", unsafe_allow_html=True)
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(_stat_card(str(analysis["sample_size"]), "有效样本数量", "样本", BLUE_600), unsafe_allow_html=True)
    with mc2:
        st.markdown(
            _stat_card(
                str(analysis["frequency_distribution"].get("A.每天都用", 0)),
                "每天使用 AI（人）", "高频", BLUE_500,
            ),
            unsafe_allow_html=True,
        )
    with mc3:
        st.markdown(
            _stat_card(
                f"{analysis['training_gap_combined']['rate']:.1f}%",
                "超纲经常/偶尔", "训练", BLUE_100 if analysis['training_gap_combined']['rate'] < 50 else AMBER_600,
            ),
            unsafe_allow_html=True,
        )
    with mc4:
        st.markdown(
            _stat_card(
                f"{analysis['ddl_pressure_combined']['rate']:.1f}%",
                "DDL 救火经常/偶尔", "压力", AMBER_600,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div class='page-divider'></div>", unsafe_allow_html=True)

    # ── Usage Behavior ──
    st.markdown("<div class='section-title'>使用行为分析</div>", unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        _plotly_coded_bar(analysis["frequency_distribution"], "AI 使用频率分布", orientation="v")
        st.caption("每天使用 AI 的学生占比最高，生成式 AI 已深入日常学习。")
    with right:
        _plotly_coded_bar(analysis["ai_use_counts"], "AI 用途选择频率", option_order=AI_USE_OPTIONS)
        st.caption("查资料、解释概念、列提纲和代码/公式辅助是主要使用方式。")

    st.markdown("<div class='page-divider'></div>", unsafe_allow_html=True)

    # ── Scenario Acceptance ──
    st.markdown("<div class='section-title'>不同场景下的 AI 用法接受度</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["作业场景", "论文场景", "考试场景"])
    with tab1:
        _plotly_stacked_bar(analysis["homework_acceptance"], "作业场景接受度", option_order=ACCEPTANCE_USE_OPTIONS)
        st.caption("总结要点/列提纲接受度最高，生成核心内容争议最大。")
    with tab2:
        _plotly_stacked_bar(analysis["paper_acceptance"], "论文场景接受度", option_order=ACCEPTANCE_USE_OPTIONS)
        st.caption("翻译/外语学习接受度最高，生成核心内容争议最大。")
    with tab3:
        _plotly_stacked_bar(analysis["exam_acceptance"], "考试场景接受度", option_order=ACCEPTANCE_USE_OPTIONS)
        st.caption("考试场景整体更谨慎，生成核心内容反对人数最多。")

    st.markdown("<div class='page-divider'></div>", unsafe_allow_html=True)

    # ── Fairness & Pressure ──
    st.markdown("<div class='section-title'>公平与压力因素</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        _plotly_coded_bar(analysis["tool_distribution"], "工具类型分布", orientation="v")
        _plotly_coded_bar(analysis["tool_impact_distribution"], "工具强弱差异影响", orientation="v")
    with c2:
        _plotly_coded_bar(analysis["training_gap_distribution"], "超纲情况", orientation="v")
        _plotly_coded_bar(analysis["ddl_pressure_distribution"], "DDL 救火情况", orientation="v")

    st.markdown("<div class='page-divider'></div>", unsafe_allow_html=True)

    # ── Insights ──
    st.markdown("<div class='section-title'>调研关键启示</div>", unsafe_allow_html=True)
    for insight in analysis["insights"]:
        st.markdown(f'<div class="insight-item">{insight}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# Page: AI Ethics Self-Check (Multi-step Wizard)
# ═══════════════════════════════════════════════════════════════════════

def _init_wizard_state() -> None:
    """Initialise wizard-related session state keys."""
    defaults: Dict[str, Any] = {
        "wizard_step": 1,
        "wiz_assignment_type": "课程论文",
        "wiz_scenario": "普通作业",
        "wiz_teacher_rule": "允许但需要说明",
        "wiz_tool_type": "免费 / 基础 AI 工具",
        "wiz_ai_uses": ["查资料 / 解释概念"],
        "wiz_uploaded_contents": ["普通题目要求"],
        "wiz_material_authorization": "只使用普通题目或自有资料",
        "wiz_fact_check": "全部核查",
        "wiz_reference_check": "没有生成参考文献",
        "wiz_process_record": "保留完整草稿和修改记录",
        "wiz_agency_level": "能独立解释核心思路",
        "wiz_disclosure": "主动声明",
        "wiz_time_pressure": "无明显时间压力",
        "wiz_training_gap": "没有",
        "wiz_ethical_checks": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _wizard_step_indicator(current: int) -> None:
    """Render the wizard step indicator bar."""
    steps_html = ""
    for i, (label, sub) in enumerate(WIZARD_STEPS, 1):
        if i < current:
            state = "done"
            dot = "✓"
        elif i == current:
            state = "active"
            dot = str(i)
        else:
            state = ""
            dot = str(i)
        steps_html += f"""
<div class="wizard-step-item {state}">
  <div class="wizard-step-dot">{dot}</div>
  <div class="wizard-step-label">{label}</div>
  <div class="wizard-step-sublabel">{sub}</div>
</div>"""

    st.markdown(
        f"""
<div class="wizard-container">
  <div class="wizard-steps">{steps_html}</div>
  <div class="wizard-progress">
""",
        unsafe_allow_html=True,
    )
    progress_value = min(max(current / len(WIZARD_STEPS), 0.0), 1.0)
    st.progress(progress_value)
    st.markdown("</div>", unsafe_allow_html=True)


def _wizard_step_1() -> None:
    """Step 1: Basic assignment info."""
    st.markdown("#### 基本信息")
    st.caption("请描述你的作业类型、使用场景和教师给出的 AI 规则。")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.wiz_assignment_type = st.selectbox(
            "作业类型",
            ["课程论文", "实验报告", "代码作业", "英语写作", "PPT / 汇报", "考试复习", "其他"],
            index=["课程论文", "实验报告", "代码作业", "英语写作", "PPT / 汇报", "考试复习", "其他"].index(
                st.session_state.wiz_assignment_type
            ) if st.session_state.wiz_assignment_type in ["课程论文", "实验报告", "代码作业", "英语写作", "PPT / 汇报", "考试复习", "其他"] else 0,
            key="wiz_select_assignment",
        )
        st.session_state.wiz_scenario = st.selectbox(
            "使用场景",
            ["普通作业", "课程论文", "考试 / 测验", "课堂展示", "科研训练", "其他"],
            index=["普通作业", "课程论文", "考试 / 测验", "课堂展示", "科研训练", "其他"].index(
                st.session_state.wiz_scenario
            ) if st.session_state.wiz_scenario in ["普通作业", "课程论文", "考试 / 测验", "课堂展示", "科研训练", "其他"] else 0,
            key="wiz_select_scenario",
        )
    with c2:
        st.session_state.wiz_teacher_rule = st.selectbox(
            "教师是否明确说明 AI 使用规则",
            ["明确允许", "允许但需要说明", "明确禁止", "没有说明", "不确定"],
            index=["明确允许", "允许但需要说明", "明确禁止", "没有说明", "不确定"].index(
                st.session_state.wiz_teacher_rule
            ) if st.session_state.wiz_teacher_rule in ["明确允许", "允许但需要说明", "明确禁止", "没有说明", "不确定"] else 1,
            key="wiz_select_teacher",
        )
        st.session_state.wiz_tool_type = st.selectbox(
            "主要使用的 AI 工具类型",
            ["免费 / 基础 AI 工具", "付费 / 进阶 AI 工具", "多种类型混用"],
            index=["免费 / 基础 AI 工具", "付费 / 进阶 AI 工具", "多种类型混用"].index(
                st.session_state.wiz_tool_type
            ) if st.session_state.wiz_tool_type in ["免费 / 基础 AI 工具", "付费 / 进阶 AI 工具", "多种类型混用"] else 0,
            key="wiz_select_tool",
        )


def _wizard_step_2() -> None:
    """Step 2: AI usage details."""
    st.markdown("#### AI 使用方式")
    st.caption("勾选你在本次作业中使用 AI 的具体方式。")

    st.session_state.wiz_ai_uses = st.multiselect(
        "AI 使用方式（可多选）",
        [
            "查资料 / 解释概念",
            "总结要点 / 列提纲",
            "润色改写表达",
            "翻译 / 外语学习",
            "代码 / 公式推导辅助",
            "生成部分段落",
            "生成作业 / 论文核心内容",
            "生成参考文献",
            "生成实验数据",
            "代写核心分析与结论",
            "其他",
        ],
        default=st.session_state.wiz_ai_uses,
        key="wiz_multi_uses",
    )


def _wizard_step_3() -> None:
    """Step 3: Data upload and authorization."""
    st.markdown("#### 数据与授权")
    st.caption("说明上传给 AI 的资料类型，以及这些资料是否具有明确授权。")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.wiz_uploaded_contents = st.multiselect(
            "上传给 AI 的内容（可多选）",
            [
                "未上传资料",
                "普通题目要求",
                "课程 PPT / 讲义",
                "自己的草稿",
                "自己的实验数据",
                "同学作业 / 同学资料",
                "聊天记录",
                "个人身份信息",
                "未公开研究材料",
                "其他",
            ],
            default=st.session_state.wiz_uploaded_contents,
            key="wiz_multi_uploads",
        )
    with c2:
        st.session_state.wiz_material_authorization = st.selectbox(
            "资料版权与授权情况",
            ["只使用普通题目或自有资料", "使用课程资料但仅用于理解", "上传未授权教材/论文/图片", "上传同学作品或未公开材料", "不确定资料授权"],
            index=["只使用普通题目或自有资料", "使用课程资料但仅用于理解", "上传未授权教材/论文/图片", "上传同学作品或未公开材料", "不确定资料授权"].index(
                st.session_state.wiz_material_authorization
            ) if st.session_state.wiz_material_authorization in ["只使用普通题目或自有资料", "使用课程资料但仅用于理解", "上传未授权教材/论文/图片", "上传同学作品或未公开材料", "不确定资料授权"] else 0,
            key="wiz_select_authorization",
        )


def _wizard_step_4() -> None:
    """Step 4: Verification and learning agency."""
    st.markdown("#### 核查与主体")
    st.caption("说明你对 AI 输出的核查程度，以及是否仍能独立解释核心内容。")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.wiz_fact_check = st.selectbox(
            "是否对 AI 输出进行核查",
            ["全部核查", "部分核查", "基本未核查", "不确定"],
            index=["全部核查", "部分核查", "基本未核查", "不确定"].index(
                st.session_state.wiz_fact_check
            ) if st.session_state.wiz_fact_check in ["全部核查", "部分核查", "基本未核查", "不确定"] else 0,
            key="wiz_select_fact",
        )
        st.session_state.wiz_reference_check = st.selectbox(
            "是否核查参考文献",
            ["没有生成参考文献", "已逐条核查", "只核查部分", "未核查", "AI 生成了不存在的参考文献但我还没处理"],
            index=["没有生成参考文献", "已逐条核查", "只核查部分", "未核查", "AI 生成了不存在的参考文献但我还没处理"].index(
                st.session_state.wiz_reference_check
            ) if st.session_state.wiz_reference_check in ["没有生成参考文献", "已逐条核查", "只核查部分", "未核查", "AI 生成了不存在的参考文献但我还没处理"] else 0,
            key="wiz_select_ref",
        )
    with c2:
        st.session_state.wiz_process_record = st.selectbox(
            "是否保留个人思考和修改过程",
            ["保留完整草稿和修改记录", "保留部分记录", "没有保留", "不确定"],
            index=["保留完整草稿和修改记录", "保留部分记录", "没有保留", "不确定"].index(
                st.session_state.wiz_process_record
            ) if st.session_state.wiz_process_record in ["保留完整草稿和修改记录", "保留部分记录", "没有保留", "不确定"] else 0,
            key="wiz_select_process",
        )
        st.session_state.wiz_agency_level = st.selectbox(
            "是否能独立解释核心思路",
            ["能独立解释核心思路", "需要参考 AI 才能解释", "基本无法脱离 AI 解释", "直接复制 AI 输出"],
            index=["能独立解释核心思路", "需要参考 AI 才能解释", "基本无法脱离 AI 解释", "直接复制 AI 输出"].index(
                st.session_state.wiz_agency_level
            ) if st.session_state.wiz_agency_level in ["能独立解释核心思路", "需要参考 AI 才能解释", "基本无法脱离 AI 解释", "直接复制 AI 输出"] else 0,
            key="wiz_select_agency",
        )


def _wizard_step_5() -> None:
    """Step 5: Disclosure, background, and ethical checklist."""
    st.markdown("#### 披露与风险背景")
    st.caption("说明声明意愿、时间压力、课堂训练差距，并完成伦理符合性自检。")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.wiz_disclosure = st.selectbox(
            "是否准备声明 AI 使用",
            ["主动声明", "按教师要求声明", "不打算声明", "不确定"],
            index=["主动声明", "按教师要求声明", "不打算声明", "不确定"].index(
                st.session_state.wiz_disclosure
            ) if st.session_state.wiz_disclosure in ["主动声明", "按教师要求声明", "不打算声明", "不确定"] else 0,
            key="wiz_select_disclosure",
        )
        st.session_state.wiz_time_pressure = st.selectbox(
            "是否存在时间压力",
            ["无明显时间压力", "有一些时间压力", "DDL 临近，主要靠 AI 救火"],
            index=["无明显时间压力", "有一些时间压力", "DDL 临近，主要靠 AI 救火"].index(
                st.session_state.wiz_time_pressure
            ) if st.session_state.wiz_time_pressure in ["无明显时间压力", "有一些时间压力", "DDL 临近，主要靠 AI 救火"] else 0,
            key="wiz_select_time",
        )
    with c2:
        st.session_state.wiz_training_gap = st.selectbox(
            "是否觉得作业要求超过课堂训练",
            ["没有", "有一些", "明显超过课堂训练"],
            index=["没有", "有一些", "明显超过课堂训练"].index(
                st.session_state.wiz_training_gap
            ) if st.session_state.wiz_training_gap in ["没有", "有一些", "明显超过课堂训练"] else 0,
            key="wiz_select_training",
        )
        st.session_state.wiz_ethical_checks = st.multiselect(
            "伦理符合性自检（请选择已经做到的事项）",
            ETHICAL_CHECK_OPTIONS,
            default=st.session_state.wiz_ethical_checks,
            key="wiz_multi_ethics",
        )


def _collect_wizard_input() -> Dict[str, Any]:
    """Build the user_input dict from wizard session state."""
    return {
        "assignment_type": st.session_state.wiz_assignment_type,
        "scenario": st.session_state.wiz_scenario,
        "teacher_rule": st.session_state.wiz_teacher_rule,
        "tool_type": st.session_state.wiz_tool_type,
        "ai_uses": st.session_state.wiz_ai_uses,
        "uploaded_contents": st.session_state.wiz_uploaded_contents,
        "material_authorization": st.session_state.wiz_material_authorization,
        "fact_check": st.session_state.wiz_fact_check,
        "reference_check": st.session_state.wiz_reference_check,
        "process_record": st.session_state.wiz_process_record,
        "agency_level": st.session_state.wiz_agency_level,
        "disclosure": st.session_state.wiz_disclosure,
        "time_pressure": st.session_state.wiz_time_pressure,
        "training_gap": st.session_state.wiz_training_gap,
        "ethical_checks": st.session_state.wiz_ethical_checks,
    }


def _run_analysis() -> None:
    """Compute risk, generate statement & report, store in session state."""
    user_input = _collect_wizard_input()
    risk_result = calculate_risk(user_input)
    statement = generate_statement(user_input, risk_result)
    report = generate_markdown_report(user_input, risk_result, statement)
    st.session_state["last_user_input"] = user_input
    st.session_state["last_risk_result"] = risk_result
    st.session_state["last_statement"] = statement
    st.session_state["last_report"] = report


def _render_risk_result() -> None:
    """Display the risk analysis result with radar chart, explanations, and suggestions."""
    risk = st.session_state["last_risk_result"]
    statement = st.session_state["last_statement"]
    report = st.session_state["last_report"]

    level = risk["final_level"]
    score = risk["final_score"]
    cfg = RISK_LEVELS.get(level, RISK_LEVELS["中风险"])

    # Risk summary badge
    st.markdown(
        f"""
<div class="risk-summary" style="--risk-bg:{cfg['bg']};--risk-border:{cfg['border']};--risk-fg:{cfg['fg']}">
  <div class="risk-badge">{cfg['icon']}</div>
  <div>
    <div class="risk-label">综合风险等级</div>
    <div class="risk-level">{level}</div>
  </div>
  <div>
    <div class="risk-score">综合评分 <strong>{score}</strong> 分 · {risk.get('level_description', cfg['desc'])}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Radar chart + Statement
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("##### 八维风险雷达图")
        _plotly_radar(risk["dimension_scores"], risk.get("dimension_labels", DIMENSION_LABELS))
    with col2:
        st.markdown("##### AI 使用声明")
        st.text_area("声明文本", statement, height=240, key="result_statement_area",
                      help="此声明可复制到作业末尾。")

    # Dimension score breakdown
    st.markdown("<div class='section-title'>八维评分详情</div>", unsafe_allow_html=True)
    labeled = {
        DIMENSION_LABELS.get(k, k): v
        for k, v in risk["dimension_scores"].items()
    }
    _plotly_bar(labeled, "八维风险评分", orientation="h")

    # Lists
    _list_cards("主要风险解释", risk.get("explanations", []), "explanation-list")
    _list_cards("修改建议", risk.get("suggestions", []), "suggestion-list")
    if risk.get("triggered_rules"):
        _list_cards("触发的特殊规则", risk["triggered_rules"], "rule-list")

    # Download
    st.download_button(
        "下载 Markdown 自查报告",
        data=report.encode("utf-8-sig"),
        file_name="eduai_guard_report.md",
        mime="text/markdown",
    )


def render_self_check() -> None:
    """Render the AI ethics self-check page with multi-step wizard."""
    st.markdown(
        _page_header(
            "Risk Self-Audit",
            "AI 使用伦理自查",
            "通过五步向导填写作业场景、AI 参与程度、授权、核查和披露背景，生成可解释的八维风险画像。"
        ),
        unsafe_allow_html=True,
    )

    _init_wizard_state()
    step = st.session_state.wizard_step
    total_steps = len(WIZARD_STEPS)

    # Show step indicator
    _wizard_step_indicator(step)

    # Render current step
    if step == 1:
        _wizard_step_1()
    elif step == 2:
        _wizard_step_2()
    elif step == 3:
        _wizard_step_3()
    elif step == 4:
        _wizard_step_4()
    elif step == 5:
        _wizard_step_5()

    # Navigation buttons
    st.markdown('<div class="wizard-nav">', unsafe_allow_html=True)
    bn_cols = st.columns([1, 1, 1])

    with bn_cols[0]:
        if step > 1:
            if st.button("← 上一步", key="wiz_prev", use_container_width=True):
                st.session_state.wizard_step = step - 1
                st.rerun()

    with bn_cols[2]:
        if step < total_steps:
            if st.button("下一步 →", key="wiz_next", use_container_width=True):
                st.session_state.wizard_step = step + 1
                st.rerun()
        else:
            if st.button("开始分析", key="wiz_analyze", use_container_width=True):
                _run_analysis()
                st.session_state.wizard_step = total_steps + 1
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # close wizard-container

    # Reset wizard
    if step > total_steps:
        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
        if st.button("重新自查", key="wiz_reset"):
            st.session_state.wizard_step = 1
            st.rerun()

    # Show results if analysis is done
    if st.session_state.get("last_risk_result") and step > total_steps:
        _render_risk_result()


# ═══════════════════════════════════════════════════════════════════════
# Page: Statement Generator
# ═══════════════════════════════════════════════════════════════════════

def render_statement_page() -> None:
    """Render the AI usage statement generation page."""
    st.markdown(
        _page_header(
            "Disclosure Draft",
            "AI 使用声明生成",
            "把 AI 工具参与范围、核查责任和个人修改过程转化为可以放进作业末尾的正式披露文本。"
        ),
        unsafe_allow_html=True,
    )

    if st.session_state.get("last_statement"):
        st.markdown("##### 最近一次自查生成的声明")
        st.text_area("声明文本", st.session_state["last_statement"], height=140, key="stmt_recent")

    with st.expander("快速生成简化声明", expanded=True):
        st.caption("无需完整自查即可快速生成一份 AI 使用声明。")

        c1, c2 = st.columns(2)
        with c1:
            quick_type = st.selectbox(
                "作业类型",
                ["课程论文", "实验报告", "代码作业", "英语写作", "PPT / 汇报"],
                key="quick_assignment",
            )
            quick_uses = st.multiselect(
                "AI 使用方式",
                ["查资料 / 解释概念", "总结要点 / 列提纲", "润色改写表达",
                 "代码 / 公式推导辅助", "生成作业 / 论文核心内容"],
                default=["润色改写表达"],
                key="quick_uses",
            )
        with c2:
            quick_disclosure = st.selectbox(
                "声明意愿",
                ["主动声明", "按教师要求声明", "不打算声明", "不确定"],
                key="quick_disclosure",
            )

        if st.button("生成简化声明", key="quick_generate"):
            user_input: Dict[str, Any] = {
                "assignment_type": quick_type,
                "scenario": "普通作业",
                "teacher_rule": "允许但需要说明",
                "tool_type": "免费 / 基础 AI 工具",
                "ai_uses": quick_uses,
                "uploaded_contents": ["普通题目要求"],
                "fact_check": "全部核查",
                "reference_check": "没有生成参考文献",
                "process_record": "保留部分记录",
                "disclosure": quick_disclosure,
                "time_pressure": "无明显时间压力",
                "training_gap": "没有",
            }
            risk = calculate_risk(user_input)
            statement = generate_statement(user_input, risk)
            st.text_area("生成结果", statement, height=160, key="quick_result")


# ═══════════════════════════════════════════════════════════════════════
# Page: Report Download
# ═══════════════════════════════════════════════════════════════════════

def render_report_download() -> None:
    """Render the report download page."""
    st.markdown(
        _page_header(
            "Audit Report",
            "自查报告下载",
            "下载包含输入、风险等级、八维评分、解释、建议和 AI 使用声明的 Markdown 报告。"
        ),
        unsafe_allow_html=True,
    )

    report = st.session_state.get("last_report")
    if not report:
        st.warning("尚未生成自查报告。请先进入「AI 使用伦理自查」页面完成一次分析。")
        return

    st.markdown(report)
    st.download_button(
        "下载 Markdown 报告",
        data=report.encode("utf-8-sig"),
        file_name="eduai_guard_report.md",
        mime="text/markdown",
    )


# ═══════════════════════════════════════════════════════════════════════
# Page: User Feedback
# ═══════════════════════════════════════════════════════════════════════

def render_feedback() -> None:
    """Render the user feedback page."""
    st.markdown(
        _page_header(
            "User Feedback",
            "用户反馈",
            "反馈将保存在当前项目的 `data/feedback.csv`，用于改进体验和校准规则。"
        ),
        unsafe_allow_html=True,
    )

    with st.form("feedback_form"):
        st.markdown("##### 你的使用体验")
        c1, c2 = st.columns(2)
        with c1:
            helpfulness = st.selectbox(
                "系统是否有帮助？",
                ["很有帮助", "有一些帮助", "一般", "没有帮助"],
            )
            useful_feature = st.selectbox(
                "哪个功能最有用？",
                ["风险评分", "风险解释", "修改建议", "AI 使用声明", "报告下载", "调研数据展示"],
            )
        with c2:
            willingness = st.selectbox(
                "是否愿意在作业中声明 AI 使用？",
                ["愿意", "看课程要求", "不愿意", "不确定"],
            )
        comment = st.text_area(
            "开放建议",
            placeholder="例如：希望加入学校政策库、教师端功能、更多课程类型规则等",
        )
        submitted = st.form_submit_button("提交反馈")

    if submitted:
        append_feedback({
            "helpfulness": helpfulness,
            "useful_feature": useful_feature,
            "willingness": willingness,
            "comment": comment,
        })
        st.success("反馈已保存到本地 data/feedback.csv，感谢你的贡献。")

    with st.expander("反馈后台查看（管理员）", expanded=False):
        st.caption("反馈数据保存在当前项目目录中。请通过 Streamlit secrets 或 EDUAI_ADMIN_PASSWORD 配置管理密码。")
        admin_password = _feedback_admin_password()
        if not admin_password:
            st.info("反馈后台尚未启用。请先配置管理密码并重启应用。")
        else:
            password = st.text_input("管理密码", type="password", key="feedback_admin_password")
            if password:
                if password == admin_password:
                    records = read_feedback_records()
                    summary = summarize_feedback(records)
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("反馈总数", summary["total"])
                    with m2:
                        st.metric("很有帮助", summary["helpfulness"].get("很有帮助", 0))
                    with m3:
                        st.metric("愿意声明", summary["willingness"].get("愿意", 0))

                    if records:
                        st.markdown("##### 原始反馈记录")
                        st.dataframe(records, use_container_width=True)
                        st.markdown("##### 反馈分布")
                        st.json(summary)
                    else:
                        st.info("当前还没有用户反馈记录。")
                else:
                    st.error("管理密码不正确。")


def _feedback_admin_password() -> str:
    try:
        secret_password = st.secrets.get("admin_password", None)
    except Exception:
        secret_password = None
    return str(secret_password or os.environ.get("EDUAI_ADMIN_PASSWORD", "")).strip()


# ═══════════════════════════════════════════════════════════════════════
# Page: Project Info
# ═══════════════════════════════════════════════════════════════════════

def render_project_info() -> None:
    """Render the about / project info page."""
    st.markdown(
        _page_header(
            "Project Rationale",
            "项目说明",
            "项目定位、伦理维度、调研依据和工程实现说明。"
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="info-grid">
  <div class="info-panel">
    <div class="info-num">01</div>
    <h3>项目定位</h3>
    <p>EduAI-Guard 是面向高校学生的生成式 AI 学习使用伦理自查工具。
    它不判断学生"能不能用 AI"，而是帮助学生理解不同使用方式背后的风险边界，
    将 UNESCO、NIST AI RMF 和中国生成式 AI 治理要求中的宏观原则转化为可操作的自查流程。</p>
  </div>
  <div class="info-panel">
    <div class="info-num">02</div>
    <h3>八维伦理设计</h3>
    <p>系统关注学术诚信、数据隐私、内容可靠、偏见公平、透明披露、学习主体、责任证据和版权授权八个核心维度。
    每个维度都有对应的规则库和评分逻辑，所有风险计算完全在本地完成，不调用外部 API，
    评分过程可追溯、可解释。</p>
  </div>
  <div class="info-panel">
    <div class="info-num">03</div>
    <h3>调研驱动</h3>
    <p>项目以 79 份高校学生问卷作为背景依据，重点回应高频使用 AI（77.2% 每天使用）、
    核心内容生成争议、工具差异和 DDL 压力（79.7%）等问题。</p>
  </div>
  <div class="info-panel">
    <div class="info-num">04</div>
    <h3>工程实现</h3>
    <p>系统使用 Streamlit、pandas、Plotly 和本地规则库构建，支持交互式图表、
    多步向导式自查流程和雷达图可视化。测试覆盖风险规则、数据分析和页面渲染。</p>
  </div>
</div>
<div class="reference-strip">
  <a href="?page=survey" target="_self">查看调研数据</a>
  <a href="?page=self-check" target="_self">进入伦理自查</a>
  <a href="?page=statement" target="_self">生成 AI 使用声明</a>
</div>
""",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# App Entry Point
# ═══════════════════════════════════════════════════════════════════════

def _page_from_query() -> str:
    """Resolve the current page from URL query params."""
    raw = st.query_params.get("page", "home")
    if isinstance(raw, list):
        raw = raw[0] if raw else "home"
    return SLUG_TO_PAGE.get(str(raw), "首页")


def _init_state() -> None:
    """Initialise core session state keys."""
    for key in ["last_user_input", "last_risk_result", "last_statement", "last_report"]:
        if key not in st.session_state:
            st.session_state[key] = None


def main() -> None:
    """Main entry point for the EduAI-Guard Streamlit application."""
    ensure_project_dirs()

    st.set_page_config(
        page_title="EduAI-Guard",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_styles()
    _init_state()

    requested_page = _page_from_query()

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(
            f"""
<div class="brand-block">
  <div class="brand-icon">EG</div>
  <div>
    <div class="brand-name">EduAI-Guard</div>
    <div class="brand-sub">AI 伦理自查系统</div>
  </div>
</div>
<div class="sidebar-divider"></div>
""",
            unsafe_allow_html=True,
        )

        page = st.radio(
            "页面导航",
            NAV_LABELS,
            index=NAV_LABELS.index(requested_page) if requested_page in NAV_LABELS else 0,
            format_func=lambda name: name,
            label_visibility="hidden",
        )

        # Sidebar status card
        if st.session_state.get("last_risk_result"):
            risk = st.session_state["last_risk_result"]
            level = risk["final_level"]
            cfg = RISK_LEVELS.get(level, RISK_LEVELS["中风险"])
            st.markdown(
                f"""
<div class="sidebar-status">
  <span class="sidebar-status-mark" style="color:{cfg['fg']}">{cfg['icon']}</span>
  <div>
    <div class="sidebar-status-title">上次自查结果</div>
    <div class="sidebar-status-level" style="color:{cfg['fg']}">{level} · {risk['final_score']} 分</div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

    # ── Page Router ──
    page_routes = {
        "首页": render_home,
        "调研数据概览": render_survey_overview,
        "AI 使用伦理自查": render_self_check,
        "AI 使用声明生成": render_statement_page,
        "自查报告下载": render_report_download,
        "用户反馈": render_feedback,
        "项目说明": render_project_info,
    }

    renderer = page_routes.get(page, render_project_info)
    renderer()


if __name__ == "__main__":
    main()
