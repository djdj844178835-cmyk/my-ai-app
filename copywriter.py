import streamlit as st
import openai
import base64

# --- 1. 核心配置 ---
NEW_API_KEY = "sk-vU5dTGQDuUVDxoqI2E8tYOyQfG5a8tpEWEoe3csyQ9VNMmVB"
BASE_URL = "https://new.xiaweiliang.cn/v1"

MODELS = [
    "[A渠道][12额度/次]gemini-3.1-pro-preview-maxthinking-search",
    "[A渠道][1额度/次]gemini-3-flash-preview-maxthinking",
    "[A渠道][2额度/次][抗截断]gemini-3-flash-preview-maxthinking",
]

st.set_page_config(page_title="私人全能AI助手", page_icon="🤖")

# --- 2. 访问密码 ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 私人系统")
    pwd = st.text_input("请输入访问密码", type="password")
    if st.button("进入"):
        if pwd == "666888":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密码错误")
    st.stop()

# --- 3. 界面布局 ---
st.title("🚀 流式对话 AI 助手")
with st.sidebar:
    st.header("⚙️ 设置")
    selected_model = st.selectbox("选择 AI 大脑", MODELS)
    # 支持图片、PDF、TXT
    uploaded_file = st.file_uploader("上传文件 (图片/PDF/TXT)", type=["png", "jpg", "jpeg", "pdf", "txt"])
    
    if uploaded_file:
        if uploaded_file.type.startswith("image"):
            st.image(uploaded_file, caption="图片预览", use_container_width=True)
        else:
            st.success(f"📄 已载入: {uploaded_file.name}")
    
    if st.button("🧹 清空所有对话"):
        st.session_state.messages = [{"role": "system", "content": "你是一个极其专业的助手。请详尽、有逻辑地回答问题，不要偷懒。"}]
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "你是一个极其专业的助手。请详尽、有逻辑地回答问题，不要偷懒。"}]

# 显示历史对话
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            # 如果历史记录是列表（带附件的），提取文字显示
            if isinstance(m["content"], list):
                text_msg = next((i["text"] for i in m["content"] if i["type"] == "text"), "附件内容")
                st.markdown(text_msg)
            else:
                st.markdown(m["content"])

# --- 4. 核心对话逻辑（打字机效果实现） ---
if prompt := st.chat_input("在此输入您的问题..."):
    # 构造发送给 AI 的内容
    user_payload = [{"type": "text", "text": prompt + " (请详细回复，字数多一点)"}]
    
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        if uploaded_file.type.startswith("image"):
            img_b64 = base64.b64encode(file_bytes).decode('utf-8')
            user_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
        elif uploaded_file.type == "application/pdf":
            pdf_b64 = base64.b64encode(file_bytes).decode('utf-8')
            # 兼容大部分中转商的 PDF 传输格式
            user_payload.append({"type": "image_url", "image_url": {"url": f"data:application/pdf;base64,{pdf_b64}"}})
        elif uploaded_file.type == "text/plain":
            user_payload[0]["text"] += f"\n\n文档内容如下：\n{file_bytes.decode('utf-8')}"
    
    # 记录用户消息
    st.session_state.messages.append({"role": "user", "content": user_payload})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 生成回复（流式显示）
    with st.chat_message("assistant"):
        client = openai.OpenAI(api_key=NEW_API_KEY, base_url=BASE_URL)
        # 创建一个空容器，用于放实时蹦出来的字
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 发起流式请求
            response = client.chat.completions.create(
                model=selected_model,
                messages=st.session_state.messages,
                stream=True,
                max_tokens=4000,
                temperature=0.7
            )
            
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_response += delta
                        # 重点：每收到一个字就刷新一次界面，后面加个光标 ▌ 更有感觉
                        message_placeholder.markdown(full_response + "▌")
            
            # 回复完成后，去掉光标，完整显示
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"出错啦: {str(e)}")
