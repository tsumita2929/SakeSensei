"""
Sake Sensei - Advanced UI Components

Professional UI components and styling utilities for enhanced UX.
"""

import streamlit as st


def load_custom_css():
    """Load custom CSS for advanced styling and animations."""
    st.markdown(
        """
<style>
    /* ===== Global Styles ===== */
    :root {
        --primary-color: #4A90E2;
        --secondary-color: #C9ADA7;
        --accent-color: #F2CC8F;
        --success-color: #81C784;
        --warning-color: #FFB74D;
        --error-color: #E57373;
        --text-primary: #2C3E50;
        --text-secondary: #5C6B73;
        --bg-primary: #FFFFFF;
        --bg-secondary: #F5F7FA;
        --bg-card: #FFFFFF;
        --border-color: #E1E8ED;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 8px rgba(0,0,0,0.1);
        --shadow-lg: 0 8px 16px rgba(0,0,0,0.15);
        --radius-sm: 4px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ===== Typography ===== */
    .main-header {
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 700;
        color: var(--text-primary);
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: fadeInDown 0.6s ease-out;
    }

    .sub-header {
        font-size: clamp(1rem, 2.5vw, 1.3rem);
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeInUp 0.6s ease-out 0.2s both;
    }

    .section-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid var(--primary-color);
        display: inline-block;
    }

    /* ===== Cards ===== */
    .sake-card {
        background: var(--bg-card);
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        border-left: 5px solid var(--secondary-color);
        box-shadow: var(--shadow-md);
        margin-bottom: 1.5rem;
        transition: var(--transition);
        animation: fadeInUp 0.4s ease-out;
    }

    .sake-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
        border-left-color: var(--primary-color);
    }

    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f7ff 100%);
        padding: 1.25rem;
        border-radius: var(--radius-md);
        border-left: 4px solid var(--primary-color);
        margin: 1.5rem 0;
        box-shadow: var(--shadow-sm);
        animation: slideInLeft 0.5s ease-out;
    }

    .success-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
        border-left-color: var(--success-color);
    }

    .warning-box {
        background: linear-gradient(135deg, #fff3e0 0%, #fef7ef 100%);
        border-left-color: var(--warning-color);
    }

    .error-box {
        background: linear-gradient(135deg, #ffebee 0%, #fef5f6 100%);
        border-left-color: var(--error-color);
    }

    /* ===== Buttons ===== */
    .stButton>button {
        border-radius: var(--radius-md);
        font-weight: 600;
        transition: var(--transition);
        box-shadow: var(--shadow-sm);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }

    .stButton>button:active {
        transform: translateY(0);
    }

    /* ===== Forms ===== */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        border-radius: var(--radius-md);
        border: 2px solid var(--border-color);
        transition: var(--transition);
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>select:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    }

    /* ===== Metrics ===== */
    [data-testid="stMetric"] {
        background: var(--bg-card);
        padding: 1rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        transition: var(--transition);
    }

    [data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
    }

    /* ===== Progress & Loading ===== */
    .stProgress>div>div>div {
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        border-radius: var(--radius-sm);
    }

    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(74, 144, 226, 0.3);
        border-radius: 50%;
        border-top-color: var(--primary-color);
        animation: spin 0.8s linear infinite;
    }

    /* ===== Animations ===== */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }

    @keyframes bounce {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-10px);
        }
    }

    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
    }

    /* Hide default page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--primary-color);
        font-weight: 600;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--bg-secondary);
        padding: 0.5rem;
        border-radius: var(--radius-md);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-md);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }

    /* ===== Expander ===== */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
        font-weight: 600;
        transition: var(--transition);
    }

    .streamlit-expanderHeader:hover {
        background-color: var(--primary-color);
        color: white;
    }

    /* ===== Toast Notifications ===== */
    .toast-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        animation: slideInRight 0.4s ease-out;
        z-index: 9999;
        max-width: 400px;
    }

    .toast-success {
        background: linear-gradient(135deg, var(--success-color), #66BB6A);
        color: white;
    }

    .toast-error {
        background: linear-gradient(135deg, var(--error-color), #EF5350);
        color: white;
    }

    .toast-info {
        background: linear-gradient(135deg, var(--primary-color), #42A5F5);
        color: white;
    }

    /* ===== Badges ===== */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }

    .badge-primary {
        background-color: var(--primary-color);
        color: white;
    }

    .badge-success {
        background-color: var(--success-color);
        color: white;
    }

    .badge-warning {
        background-color: var(--warning-color);
        color: white;
    }

    .badge-secondary {
        background-color: var(--secondary-color);
        color: white;
    }

    /* ===== Rating Stars ===== */
    .rating-stars {
        display: inline-flex;
        gap: 0.25rem;
        font-size: 1.5rem;
    }

    .star-filled {
        color: var(--accent-color);
    }

    .star-empty {
        color: var(--border-color);
    }

    /* ===== Responsive Design ===== */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }

        .sub-header {
            font-size: 1rem;
        }

        .sake-card {
            padding: 1rem;
        }

        [data-testid="stMetric"] {
            padding: 0.75rem;
        }
    }

    /* ===== Accessibility ===== */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border-width: 0;
    }

    :focus-visible {
        outline: 3px solid var(--primary-color);
        outline-offset: 2px;
    }

    /* ===== Dark Mode Support ===== */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-primary: #E8EAED;
            --text-secondary: #BDC1C6;
            --bg-primary: #1A1D21;
            --bg-secondary: #2D3135;
            --bg-card: #23262A;
            --border-color: #3C4043;
        }
    }
</style>
""",
        unsafe_allow_html=True,
    )


def render_rating_stars(rating: float, max_rating: int = 5) -> str:
    """
    Render rating stars.

    Args:
        rating: Rating value (0-max_rating)
        max_rating: Maximum rating value

    Returns:
        HTML string with star icons
    """
    stars_html = (
        '<div class="rating-stars" role="img" aria-label=f"{rating} out of {max_rating} stars">'
    )

    for i in range(max_rating):
        if i < int(rating):
            stars_html += '<span class="star-filled">★</span>'
        elif i < rating:
            stars_html += '<span class="star-filled">☆</span>'  # Half star
        else:
            stars_html += '<span class="star-empty">☆</span>'

    stars_html += "</div>"
    return stars_html


def render_badge(text: str, badge_type: str = "primary") -> str:
    """
    Render a badge.

    Args:
        text: Badge text
        badge_type: Badge style (primary, success, warning, secondary)

    Returns:
        HTML string with badge
    """
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def render_loading_spinner(text: str = "読み込み中...") -> str:
    """
    Render a loading spinner.

    Args:
        text: Loading text

    Returns:
        HTML string with spinner
    """
    return f"""
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <div class="loading-spinner"></div>
        <span>{text}</span>
    </div>
    """


def show_toast(message: str, toast_type: str = "info"):
    """
    Show a toast notification.

    Args:
        message: Notification message
        toast_type: Type of toast (success, error, info)
    """
    st.toast(message, icon="✅" if toast_type == "success" else "ℹ️")


def render_progress_bar(progress: float, label: str = "", show_percentage: bool = True) -> None:
    """
    Render an enhanced progress bar.

    Args:
        progress: Progress value (0.0 to 1.0)
        label: Progress label
        show_percentage: Whether to show percentage
    """
    if label:
        st.markdown(f"**{label}**")

    st.progress(progress)

    if show_percentage:
        st.caption(f"{int(progress * 100)}%")


def render_stat_card(label: str, value: str, delta: str | None = None, icon: str = "📊") -> None:
    """
    Render a custom stat card.

    Args:
        label: Stat label
        value: Stat value
        delta: Delta value (optional)
        icon: Icon emoji
    """
    delta_html = (
        f'<div style="color: var(--success-color); font-size: 0.875rem;">{delta}</div>'
        if delta
        else ""
    )

    st.markdown(
        f"""
    <div style="
        background: var(--bg-card);
        padding: 1rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        text-align: center;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.5rem;">{label}</div>
        <div style="font-size: 1.75rem; font-weight: 700; color: var(--primary-color);">{value}</div>
        {delta_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_feature_card(title: str, description: str, icon: str, link: str | None = None) -> None:
    """
    Render a feature card.

    Args:
        title: Feature title
        description: Feature description
        icon: Icon emoji
        link: Optional link
    """
    link_html = (
        f'<a href="{link}" style="color: var(--primary-color); text-decoration: none; font-weight: 600;">詳しく見る →</a>'
        if link
        else ""
    )

    st.markdown(
        f"""
    <div class="sake-card" style="text-align: center;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">{title}</h3>
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">{description}</p>
        {link_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_timeline_item(
    date: str, title: str, description: str, icon: str = "📅", is_completed: bool = True
) -> None:
    """
    Render a timeline item.

    Args:
        date: Item date
        title: Item title
        description: Item description
        icon: Icon emoji
        is_completed: Whether the item is completed
    """
    status_color = "var(--success-color)" if is_completed else "var(--text-secondary)"

    st.markdown(
        f"""
    <div style="
        display: flex;
        gap: 1rem;
        padding: 1rem;
        border-left: 3px solid {status_color};
        margin-bottom: 1rem;
    ">
        <div style="font-size: 1.5rem;">{icon}</div>
        <div style="flex: 1;">
            <div style="font-size: 0.875rem; color: var(--text-secondary);">{date}</div>
            <h4 style="color: var(--text-primary); margin: 0.25rem 0;">{title}</h4>
            <p style="color: var(--text-secondary); margin: 0;">{description}</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
