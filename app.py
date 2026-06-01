import streamlit as st
from groq import Groq
import os
import base64
import requests
import time

# 1. CONFIGURAÇÃO DA PÁGINA E TÍTULO
st.set_page_config(page_title="IA Codex", page_icon="🤖")

# --- VISUAL: PLANO DE FUNDO E CORES CUSTOMIZADAS ---
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
    
    /* Caixas de mensagem customizadas em Azul Neon Escuro */
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
st.info("Bem vindo ao Codex, uma IA de sistema avançado para conversas e pesquias inteligentes do dia a dia 💡")
st.markdown("""Nota: A Codex estava apresentando comportamentos "rebeldes" que foram corrigidos com a atualizaçao para a versao LLAMA 4 e 1.6.0. Se encontrar algo estranho, por favor reporte clicando no botão de feedback! 🚀""")

# 🎵 PLAYER DE MÚSICA DE FUNDO
st.audio("https://soundhelix.com")

# Notas de Atualização
with st.expander("📢 Notas da Atualização mais recente - Versão V1.6.0", expanded=False):
    st.markdown("""
    *   **bugs fixed:** o Codex foi criado a poucos dias, portanto pode apresentar falhas por estar na versao de teste.
    *   **New Feature:** Novas funço~es e aprimoramentos disponiveis para explorar. clique em "buscar atualizações"🚀
    *   **New AI:** O Codex agora é alimentado por llama 4. um dos sistemas de IAs mais avançados.
    """)

# 2. SISTEMA DE MEMÓRIA (CARREGAR HISTÓRICO SALVO)
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

# Carrega a API Key salva
chave_salva = ""
if os.path.exists(ARQUIVO_CONFIG):
    with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
        chave_salva = f.read().strip()

# BARRA LATERAL (MENU DO APP)
with st.sidebar:
    st.subheader("⚙️ Configurações do Codex")
    api_key = st.text_input("Insira sua Groq API Key", value=chave_salva, type="password")
    
    if api_key != chave_salva:
        with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
            f.write(api_key)
        st.success("Chave de API salva! 🔑")
        st.rerun()

    st.markdown("---")
    
    # RECURSO NOVO: Seletor de Personalidade Dinâmico para o Llama 4
    st.subheader("🧠 Modo de Operação")
    modo_selecionado = st.selectbox(
        "Escolha a especialidade do Codex:",
        ["Simpática e Descontraída", "Programador Expert", "Professor Didático", "Mestre de RPG"]
    )
    
    # Define as instruções do sistema com base na escolha
    if modo_selecionado == "Simpática e Descontraída":
        prompt_sistema = "Você é uma IA chamada Codex. Você é simpática, descontraída e usa gírias leves."
    elif modo_selecionado == "Programador Expert":
        prompt_sistema = "Você é o Codex no modo Programador Expert. Responda com códigos limpos em Python/HTML, seja direto e focado em engenharia de software."
    elif modo_selecionado == "Professor Didático":
        prompt_sistema = "Você é o Codex no modo Professor. Explique conceitos difíceis de forma simples, paciente, pedagógica e cheia de exemplos práticos."
    else:
        prompt_sistema = "Você é o Codex, um narrador e mestre de RPG criativo. Crie cenários imersivos, misteriosos e interaja como um mestre de jogo."

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

# Mostra as mensagens antigas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Se a mensagem for um link de imagem gerada, exibe como imagem
        if message["content"].startswith("http") and "pollinations.ai" in message["content"]:
            st.image(message["content"], caption="Imagem gerada pelo Codex")
        else:
            st.write(message["content"])

# CAMPO DE ENVIAR IMAGEM (VISÃO)
foto_enviada = st.file_uploader("📸 Envie uma foto para o Codex analisar (Opcional)", type=["jpg", "jpeg", "png"])

def converter_imagem(upload_file):
    return base64.b64encode(upload_file.read()).decode("utf-8")

# 3. CAMPO DE ENVIO DE TEXTO (CHAT)
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    
    # --- RECURSO NOVO: SISTEMA DE GERAÇÃO DE IMAGENS ---
    texto_usuario = prompt.lower()
    if texto_usuario.startswith("crie a imagem de") or texto_usuario.startswith("desenhe"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Desenhando sua imagem... 🎨"):
                # Limpa o texto para mandar apenas a descrição para a API de imagem
                descricao = prompt.replace("crie a imagem de", "").replace("desenhe", "").strip()
                # Cria a URL da imagem gratuita usando a Pollinations AI
                link_imagem = f"https://pollinations.ai{requests.utils.quote(descricao)}?width=1024&height=1024&enhanced=true"
                
                # Exibe o desenho na tela
                st.image(link_imagem, caption=f"Resultado: {descricao}")
                
                # Salva o link no histórico para não perder
                st.session_state.messages.append({"role": "assistant", "content": link_imagem})
                with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
                    f.write(f"user|||{prompt}\n")
                    f.write(f"assistant|||{link_imagem}\n")
                st.stop() # Para a execução aqui para não acionar o Llama 4 de texto
                
    # --- FLUXO NORMAL DO CHAT (TEXTO E FOTO COM LLAMA 4) ---
    if not api_key:
        st.info("Insira sua API KEY. Você pode obter uma gratuitamente em https://groq.com")
        st.stop()
        
    client = Groq(api_key=api_key)

    conteudo_mensagem = [{"type": "text", "text": prompt}]
    texto_salvar = prompt

    if foto_enviada:
        imagem_base64 = converter_imagem(foto_enviada)
        conteudo_mensagem.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{imagem_base64}"}
        })
        texto_salvar = f"[Enviou uma Foto] - {prompt}"
        st.image(foto_enviada, caption="Imagem enviada", width=250)

    st.session_state.messages.append({"role": "user", "content": texto_salvar})
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"user|||{texto_salvar}\n")
        
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Codex está pesquisando... 🧠"):
            time.sleep(1)  # Simula um pequeno delay para melhor UX
            
            historico_ia = []
            for m in st.session_state.messages[:-1]:
                # Ignora links de imagens antigas na memória de texto para não bugar a API
                if not (m["content"].startswith("http") and "pollinations.ai" in m["content"]):
                    historico_ia.append({"role": m["role"], "content": m["content"]})
            
            historico_ia.append({"role": "user", "content": conteudo_mensagem})

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": f"{prompt_sistema} FILTRO DE REALIDADE: Nunca invente dados falsos. Se não souber algo em tempo real, avise."}
                ] + historico_ia,
                model="llama-4-scout",
                temperature=0.3,
                max_tokens=2048
            )
            resposta = chat_completion.choices[0].message.content
            st.write(resposta)
        
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"assistant|||{resposta}\n")
