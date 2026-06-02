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
        background-color: #0e1117;
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
    if st.button("🗑️ Limpar Histórico de Mensagens"):
        if os.path.exists(ARQUIVO_HISTORICO):
            os.remove(ARQUIVO_HISTORICO)
        st.session_state.messages = []
        st.rerun()

# Reconstrói mensagens antigas na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["content"].startswith("http"):
            st.image(message["content"], use_container_width=True)
        elif message["content"].startswith("data:image") or len(message["content"]) > 1000:
            st.warning("🖼️ [Imagem Enviada para Análise]")
        else:
            st.write(message["content"])

# --- ÁREA DE UPLOAD DE FOTOS ---
st.markdown("### 📸 Análise Multimodal")
foto_enviada = st.file_uploader("Arraste ou envie uma foto para o Codex analisar junto com seu texto:", type=["jpg", "jpeg", "png"])

# 3. CONTROLE CENTRAL DE COMANDOS (TEXTO E IMAGEM)
if prompt := st.chat_input("Digite aqui... Ex: 'Crie a imagem de um dragão' ou tire dúvidas"):
    texto_usuario = prompt.lower().strip()
    
    # 🎨 GERADOR GRÁFICO (ROTA CORRIGIDA DA POLLINATIONS.AI)
    if texto_usuario.startswith("crie a imagem de") or texto_usuario.startswith("desenhe"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("O Codex está desenhando sua arte... 🎨"):
                prompt_limpo = texto_usuario.replace("crie a imagem de", "").replace("desenhe", "").strip()
                # Codifica o texto para formato de URL seguro
                prompt_url = requests.utils.quote(prompt_limpo)
                
                # CORREÇÃO DA URL: Adicionado o endpoint '/p/' necessário para renderizar a imagem
                link_imagem = f"https://pollinations.ai{prompt_url}?width=1024&height=1024&nologo=true"
                
                # Mostra a imagem na tela
                st.image(link_imagem, caption=f"Arte Gerada: {prompt_limpo}", use_container_width=True)
                
                st.session_state.messages.append({"role": "assistant", "content": link_imagem})
                with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
                    f.write(f"user|||{prompt}\n")
                    f.write(f"assistant|||{link_imagem}\n")
                st.stop()

    # 💬 CHAT E ANÁLISE DE FOTO COM A GROQ (LLAMA 3.2 VISION)
    if not api_key:
        st.info("Por favor, adicione sua Groq API Key na barra lateral.")
        st.stop()
        
    client = Groq(api_key=api_key)
    conteudo_mensagem = [{"type": "text", "text": prompt}]

    # Renderiza o input do usuário na tela antes do processamento
    with st.chat_message("user"):
        st.write(prompt)
        if foto_enviada:
            bytes_foto = foto_enviada.read()
            st.image(bytes_foto, width=250)
            imagem_base64 = base64.b64encode(bytes_foto).decode("utf-8")
            conteudo_mensagem.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{imagem_base64}"}
            })

    # Adiciona a pergunta ao histórico de sessão do Streamlit
    st.session_state.messages.append({"role": "user", "content": prompt})
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"user|||{prompt}\n")

    with st.chat_message("assistant"):
        with st.spinner("Codex processando... 🧠"):
            historico_ia = []
            # Monta o histórico de chat textual clássico para a IA
            for m in st.session_state.messages[:-1]:
                if not m["content"].startswith("http") and not m["content"].startswith("data:image"):
                    historico_ia.append({"role": m["role"], "content": m["content"]})
            
            historico_ia.append({"role": "user", "content": conteudo_mensagem})

            # CORREÇÃO DO MODELO: Alterado para 'llama-3.2-11b-vision-preview' para aceitar imagens de verdade
            modelo_usado = "llama-3.2-11b-vision-preview" if foto_enviada else "llama-3.1-8b-instant"

            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "Você é o Codex. Responda de forma prestativa, simpática e use gírias leves."}] + historico_ia,
                model=modelo_usado,
                temperature=0.3,
                max_tokens=2048
            )
            resposta = chat_completion.choices[0].message.content
            st.write(resposta)
        
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"assistant|||{resposta}\n")
