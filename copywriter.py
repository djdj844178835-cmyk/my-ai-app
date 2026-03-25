import streamlit as st
import openai
import base64

# --- 1. 核心配置 ---
NEW_API_KEY = "sk-vU5dTGQDuUVDxoqI2E8tYOyQfG5a8tpEWEoe3csyQ9VNMmVB"
BASE_URL = "https://new.xiaweiliang.cn/v1"

# 默认选项已改为 1 额度的 Flash
MODELS = [
    "[A渠道][1额度/次]gemini-3-flash-preview-maxthinking",
    "[A渠道][12额度/次]gemini-3.1-pro-preview-maxthinking-search",
    "[A渠道][2额度/次][抗截断]gemini-3-flash-preview-maxthinking",
]

# 页面配置：设置宽屏模式
st.set_page_config(page_title="私人AI助手", page_icon="🤖", layout="wide")

# --- 已经彻底删除了密码验证逻辑 ---

st.title("🚀 流式对话 AI 助手")

# 侧边栏设置
with st.sidebar:
    st.header("⚙️ 设置")
    selected_model = st.selectbox("选择 AI 大脑", MODELS)
    uploaded_file = st.file_uploader("上传图片/PDF/TXT", type=["png", "jpg", "jpeg", "pdf", "txt"])
    if st.button("🧹 清空对话"):
        st.session_state.messages = [{"role": "system", "content": "你是一个专业助手，请详尽回复。"}]
        st.rerun()

# 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "你是一个专业助手，请详尽回复。"}]

# 在网页上显示历史消息
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            if isinstance(m["content"], list):
                # 兼容旧版本数据结构
                text_msg = next((i["text"] for i in m["content"] if i["type"] == "text"), "附件内容")
                st.markdown(text_msg)
            else:
                st.markdown(m["content"])

# 聊天输入框
if prompt := st.chat_input("在此输入您的问题..."):
    user_payload = [{"type": "text", "text": prompt}]
    
    # 如果上传了文件，将其转为 Base64 编码发给 AI
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        if uploaded_file.type.startswith("image"):
            img_b64 = base64.b64encode(file_bytes).decode('utf-8')
            user_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
        elif uploaded_file.type == "application/pdf":
            pdf_b64 = base64.b64encode(file_bytes).decode('utf-8')
            user_payload.append({"type": "image_url", "image_url": {"url": f"data:application/pdf;base64,{pdf_b64}"}})
        elif uploaded_file.type == "text/plain":
            user_payload[0]["text"] += f"\n附件文本内容：\n{file_bytes.decode('utf-8')}"
    
    st.session_state.messages.append({"role": "user", "content": user_payload})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 呼叫 AI 接口
    with st.chat_message("assistant"):
        client = openai.OpenAI(api_key=NEW_API_KEY, base_url=BASE_URL)
        message_placeholder = st.empty()
        full_response = ""
        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=st.session_state.messages,
                stream=True,
                max_tokens=4000
            )
            # 实现打字机流式效果
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"连接出错，请检查网络或Key: {str(e)}")
