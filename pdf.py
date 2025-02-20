import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import os
import base64
import requests
import pandas as pd
import re

# Configuração da API da OpenAI
OPENAI_API_KEY = "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"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Inicializa o DataFrame na sessão com edição ativada
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Página", "Texto Extraído"])

# Função para converter PDF em imagens
def pdf_to_images(pdf_bytes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_path = os.path.join(output_dir, f"page_{page_num + 1}.jpg")
        img.save(img_path, "JPEG")
        images.append(img_path)
    return images

# Função para codificar a imagem em base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Função para extrair texto da imagem usando a OpenAI
def extract_text_from_image(image_base64, prompt):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4o", #gpt-4o
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ],
        "max_tokens": 100,
    }
    response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        extracted_text = response.json()["choices"][0]["message"]["content"]
        extracted_text = re.sub(r"[^0-9A-Za-z@./,\s-]", "", extracted_text).strip()
        return extracted_text
    else:
        st.error(f"Erro na API da OpenAI: {response.status_code} - {response.text}")
        return None

# Interface da barra lateral

with st.sidebar:
    #image = Image.open(r"C:\Users\20829\Pictures\Screenshots\bemol.png")
    #st.image(image, caption="Imagem carregada", use_container_width=True)
    uploaded_file = st.sidebar.file_uploader("Faça o upload de um PDF", type="pdf")

    if uploaded_file is not None:
        output_dir = "output_images"
        pdf_bytes = uploaded_file.read()
        images = pdf_to_images(pdf_bytes, output_dir)
        st.sidebar.write(f"📄 {len(images)} páginas processadas.")

        if "page_index" not in st.session_state:
            st.session_state.page_index = 0

        def next_page():
            if st.session_state.page_index + 1 < len(images):
                st.session_state.page_index += 1

        def previous_page():
            if st.session_state.page_index - 1 >= 0:
                st.session_state.page_index -= 1

        # Navegação
        st.sidebar.button("⏪ Página anterior", on_click=previous_page, disabled=(st.session_state.page_index == 0))
        st.sidebar.button("⏩ Próxima página", on_click=next_page, disabled=(st.session_state.page_index == len(images) - 1))

        # Entrada do prompt para extração
        prompt = st.sidebar.text_input("🔍 O que deseja extrair?")
        
# Corpo principal
st.title(f"📄 Página {st.session_state.page_index + 1} de {len(images)}")
st.image(images[st.session_state.page_index], use_column_width=True)

if prompt:
    image_base64 = encode_image_to_base64(images[st.session_state.page_index])
    extracted_text = extract_text_from_image(image_base64, prompt)
    if extracted_text:
        st.subheader("Texto Extraído")
        st.write(f"```{extracted_text}```")
        if st.sidebar.button("💾 Salvar Texto"):
            new_row = pd.DataFrame(
                [[st.session_state.page_index + 1, extracted_text]],
                columns=["Página", "Texto Extraído"]
                )
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)

    if not st.session_state.data.empty:
        st.sidebar.subheader("📊 Dados Extraídos")
        st.session_state.data = st.sidebar.data_editor(st.session_state.data, key="editable_dataframe")
        csv = st.session_state.data.to_csv(index=False).encode("utf-8")
        st.sidebar.download_button("📥 Baixar CSV", csv, "dados_extraidos.csv", "text/csv")

#Quais são as variações em cm dos Rios?
