import streamlit as st
from groq import Groq
import os
import base64
import requests
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="IA Codex", page_icon="🤖")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: url("https://unsplash.com");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    [data-testid="stHeader"], [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
    }
    .stChatMessage {
        background-color: rgba(20, 30, 50, 0.6) !important;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        backdrop-filter: blur(6px);
        border: 1px solid rgba(0, 150, 255, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("IA Codex 🤖")
st.info("Bem-vindo ao Codex, uma IA perfeita para ajudar com tarefas e criar imagens no dia a dia. 💡")

st.audio("https://soundhelix.com")

# 2. SISTEMA DE MEMÓRIA
ARQUIVO_HISTORICO = "historico.txt"
ARQUIVO_CONFIG = "config.txt"

if "messages" not in st.session_state:
    st.session_state.messages = []
    if os.path.exists(ARQUIVO_HISTORICO):
        with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
            for linha in f:
                if "|||" in linha:
                    role, content = linha.strip().split("|||", 1)
                    st.session_state.messages.append({"role": role, "content": content})

chave_salva = ""
if os.path.exists(ARQUIVO_CONFIG):
    with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
        chave_salva = f.read().strip()

with st.sidebar:
    st.subheader("⚙️ Configurações")
    api_key = st.text_input("Insira sua Groq API Key", value=chave_salva, type="password")
    if api_key != chave_salva:
        with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
            f.write(api_key)
        st.rerun()
    st.markdown("---")
    if st.button("❄️ Modo Inverno"):
        st.snow()
    if st.button("🔄 Procurar Atualizações"):
        st.rerun()
    if st.button("🗑️ Limpar Histórico de Mensagens"):
        if os.path.exists(ARQUIVO_HISTORICO):
            os.remove(ARQUIVO_HISTORICO)
        st.session_state.messages = []
        st.rerun()

# Mostra mensagens antigas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["content"].startswith("http") and "pollinations.ai" in message["content"]:
            try:
                res = requests.get(message["content"], timeout=10)
                st.image(res.content, use_container_width=True)
            except:
                st.write("⚠️ Erro ao carregar imagem antiga.")
        else:
            st.write(message["content"])

foto_enviada = st.file_uploader("📸 Envie uma foto para analisar (Opcional)", type=["jpg", "jpeg", "png"])

# 3. CAMPO DE ENVIO (CHAT E GERADOR)
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    texto_usuario = prompt.lower().strip()
    
    # GERADOR DE IMAGENS TOTALMENTE SEPARADO E SEGURO
    if texto_usuario.startswith("crie a imagem de") or texto_usuario.startswith("desenhe"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Desenhando sua imagem... 🎨"):
                time.sleep(1)
                # Remove o comando de forma limpa
                prompt_limpo = texto_usuario.replace("crie a imagem de", "").replace("desenhe", "").strip()
                # Troca os espaços por %20 para a URL funcionar
                prompt_url = prompt_limpo.replace(" ", "%20")
                
                # URL CORRIGIDA: Forçando a barra /p/ de forma estática e segura
                link_imagem = f"https://pollinations.ai{prompt_url}?width=1024&height=1024&nologo=true"
                
                try:
                    conteudo_foto = requests.get(link_imagem, timeout=15).content
                    st.image(conteudo_foto, caption=f"Resultado: {prompt_limpo}", use_container_width=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": link_imagem})
                    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
                        f.write(f"user|||{prompt}\n")
                        f.write(f"assistant|||{link_imagem}\n")
                except:
                    st.error("Erro de conexão com o servidor de desenhos. Tente novamente.")
                st.stop()

    # CHAT NORMAL DE TEXTO DA GROQ
    if not api_key:
        st.info("Insira sua API KEY.")
        st.stop()
        
    client = Groq(api_key=api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"user|||{prompt}\n")
        
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Codex está pensando... 🧠"):
            historico_ia = []
            for m in st.session_state.messages[:-1]:
                if not (m["content"].startswith("http") and "pollinations.ai" in m["content"]):
                    historico_ia.append({"role": m["role"], "content": m["content"]})
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "Você é a IA Codex, simpática e descontraída."}] + historico_ia,
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=2048
            )
            resposta = chat_completion.choices[0].message.content
            st.write(resposta)
        
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"assistant|||{resposta}\n")
