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
st.info("Bem-vindo ao Codex, uma IA perfeita para ajudar com tarefas, analisar fotos e criar imagens no dia a dia. 💡")

st.audio("https://soundhelix.com")

# 2. SISTEMA DE BANCO DE DADOS LOCAL
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
        st.success("Chave salva com sucesso!")
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

# Reconstrói mensagens antigas de forma segura
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["content"].startswith("data:image"):
            st.image(message["content"], use_container_width=True)
        else:
            st.write(message["content"])

# --- ÁREA DE UPLOAD DE FOTOS ---
st.markdown("### 📸 Análise Multimodal")
foto_enviada = st.file_uploader("Arraste ou envie uma foto para o Codex analisar junto com seu texto:", type=["jpg", "jpeg", "png"])

# 3. CONTROLE CENTRAL DE COMANDOS (TEXTO E IMAGEM)
if prompt := st.chat_input("Digite aqui... Ex: 'Crie a imagem de um dragão' ou tire dúvidas"):
    texto_usuario = prompt.lower().strip()
    
    # 🎨 RECURSO: GERADOR GRÁFICO VIA HUGGING FACE (ESTÁVEL E SEGURO)
    if texto_usuario.startswith("crie a imagem de") or texto_usuario.startswith("desenhe"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Conectando ao motor gráfico do Hugging Face... 🎨"):
                time.sleep(1)
                prompt_limpo = texto_usuario.replace("crie a imagem de", "").replace("desenhe", "").strip()
                prompt_url = requests.utils.quote(prompt_limpo)
                
                # NOVO LINK CORRIGIDO: Usando o servidor estável do Stable Diffusion via Hugging Face
                link_imagem = f"https://huggingface.co{prompt_url}"
                
                try:
                    # O Python baixa os dados da imagem do Hugging Face
                    resposta_web = requests.get(link_imagem, timeout=25)
                    if resposta_web.status_code == 200:
                        # Transforma em texto Base64 para não dar bloqueio no Streamlit
                        dados_base64 = base64.b64encode(resposta_web.content).decode("utf-8")
                        link_seguro_base64 = f"data:image/jpeg;base64,{dados_base64}"
                        
                        # Exibe na tela
                        st.image(link_seguro_base64, caption=f"Arte Gerada: {prompt_limpo}", use_container_width=True)
                        
                        st.session_state.messages.append({"role": "assistant", "content": link_seguro_base64})
                        with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
                            f.write(f"user|||{prompt}\n")
                            f.write(f"assistant|||{link_seguro_base64}\n")
                    else:
                        st.error("O servidor do Hugging Face está processando muitas requisições. Tente novamente em alguns segundos.")
                except:
                    st.error("Erro ao conectar com o motor gráfico do Hugging Face. Verifique sua conexão.")
                st.stop()

    # 💬 CHAT E ANÁLISE DE FOTO COM A GROQ (LLAMA ESTÁVEL)
    if not api_key:
        st.info("Por favor, adicione sua Groq API Key na barra lateral.")
        st.stop()
        
    client = Groq(api_key=api_key)
    
    conteudo_mensagem = [{"type": "text", "text": prompt}]
    texto_salvar = prompt

    if foto_enviada:
        bytes_foto = foto_enviada.read()
        imagem_base64 = base64.b64encode(bytes_foto).decode("utf-8")
        conteudo_mensagem.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{imagem_base64}"}
        })
        texto_salvar = f"data:image/jpeg;base64,{imagem_base64}"
        
        st.session_state.messages.append({"role": "user", "content": texto_salvar})
        with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
            f.write(f"user|||{texto_salvar}\n")

    if not foto_enviada:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
            f.write(f"user|||{prompt}\n")
            
    with st.chat_message("user"):
        st.write(prompt)
        if foto_enviada:
            st.image(bytes_foto, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Codex processando... 🧠"):
            historico_ia = []
            for m in st.session_state.messages[:-1]:
                if not m["content"].startswith("data:image"):
                    historico_ia.append({"role": m["role"], "content": m["content"]})
            
            historico_ia.append({"role": "user", "content": conteudo_mensagem})

            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "Você é o Codex. Responda de forma prestativa, simpática e use gírias leves."}] + historico_ia,
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=2048
            )
            resposta = chat_completion.choices[0].message.content
            st.write(resposta)
        
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"assistant|||{resposta}\n")
