import streamlit as st
from groq import Groq

st.title("IA Codex 🤖")

with st.expander("📢 Notas da Atualização - Versão V1.0.0", expanded=True):
    st.markdown("""
    *   **New AI:** Migrado com sucesso para o modelo moderno *Llama 3.1*.
    *   **Bugs Fixed:** Corrigido o erro vermelho de conexão da API.
    *   **Bugs Fixed:** Ajustado o erro de digitação nas variáveis.
    *   **Nova Personalidade:** Modo Codex Simpática ativado! 🌟
    """)


with st.sidebar:
    api_key = st.text_input("Insira sua Groq API Key", type="password")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    if not api_key:
        st.info("burrice tu tem que colocar sua API Key para usar o chat")
        st.stop()
        
    client = Groq(api_key=api_key)

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        chat_completion = client.chat.completions.create(
                    messages=[
                {"role": "system", "content": "Você é uma IA chamada Codex que é simpatica, e ajuda os outros. usa girias tmb e fala de forma descontraida,ela nao interage com rp e tem um humor doido"}
            ] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],

                
    
            model="llama-3.1-8b-instant",

        )
        resposta = chat_completion.choices[0].message.content
        st.write(resposta)
        
    st.session_state.messages.append({"role": "assistant", "content": resposta})
