import streamlit as st
from utils.query_utils import get_schema, generate_sql, run_sql
import pandas as pd
import base64

# Set page config
st.set_page_config(
    page_title="GenAI SQL Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================
# 💅 Custom Styling
# ====================
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    scroll-behavior: smooth;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

h1 {
    font-size: 2.3rem;
    color: #2c3e50;
}

.chat-bubble {
    background-color: #f1f3f6;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    border-left: 5px solid #3b82f6;
    animation: fadeIn 0.6s ease-in;
}

@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}

.spinner::after {
    content: '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏';
    animation: dots 1s steps(10, end) infinite;
    display: inline-block;
    margin-left: 10px;
}

@keyframes dots {
    to {
        content: ' ';
    }
}

/* Floating button */
.fab {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background-color: #3b82f6;
    color: white;
    border-radius: 50%;
    width: 56px;
    height: 56px;
    text-align: center;
    font-size: 30px;
    line-height: 56px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    cursor: pointer;
    z-index: 999;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ====================
# 🧠 Header
# ====================
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Iconic_image_of_a_brain.svg/512px-Iconic_image_of_a_brain.svg.png", width=60)
st.markdown("# GenAI SQL Assistant")
st.markdown("### 💬 Ask questions to your database using natural language. Powered by GPT + SQL.")
st.markdown("Try: `Show me total sales by region in 2023`")
st.markdown("---")

# ====================
# 🎛 Theme toggle
# ====================
theme = st.sidebar.radio("🌗 Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        "<style>body{background-color:#111;color:white}</style>",
        unsafe_allow_html=True
    )

# ====================
# 🧠 Query Input
# ====================
user_input = st.text_input("🗣 Ask your question:")

# Store query history
if "history" not in st.session_state:
    st.session_state["history"] = []

# ====================
# 🚀 Assistant Response
# ====================
if user_input:
    with st.spinner("🤖 Thinking..."):
        schema = get_schema()
        sql = generate_sql(user_input, schema)
        st.session_state.history.append(user_input)

        st.markdown(f'<div class="chat-bubble">🧠 <b>Generated SQL:</b><br><code>{sql}</code></div>', unsafe_allow_html=True)

        result = run_sql(sql)

        if isinstance(result, str):
            st.error(result)
        else:
            st.success("✅ Query successful!")
            st.markdown("### 📋 Table")
            st.dataframe(result, use_container_width=True)

            if result.shape[1] >= 2:
                st.markdown("### 📊 Chart")
                st.bar_chart(result.set_index(result.columns[0]))

            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "query_results.csv", "text/csv")

# ====================
# 📜 Floating FAB with Query History
# ====================
st.markdown("""
<div class="fab" onclick="document.getElementById('history').scrollIntoView({ behavior: 'smooth' });">
    🕘
</div>
""", unsafe_allow_html=True)

if st.session_state["history"]:
    st.markdown("<h4 id='history'>🕘 Query History</h4>", unsafe_allow_html=True)
    for q in reversed(st.session_state["history"][-5:]):
        st.markdown(f"<div class='chat-bubble'>🗨️ {q}</div>", unsafe_allow_html=True)
