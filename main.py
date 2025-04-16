import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
import json
from dotenv import load_dotenv
load_dotenv()

blobConnectionString = os.getenv('BLOB_CONNECTION_STRING')
blobContainerName = os.getenv('BLOB_CONTAINER_NAME')
blobAccountName = os.getenv('BLOB_ACCOUNT_NAME')

SQL_SERVER = os.getenv('SQL_SERVER')
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USER = os.getenv('SQL_USER')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

st.title("Cadastro de Produtos")


#product forms
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])

#save image to blob storage
def upload_blob(file):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
        container_client = blob_service_client.get_container_client(blobContainerName)
        blob_name = str(uuid.uuid4()) + file.name
        blob_client = container_client.get_blob_client(blob_name)
        # Fix: Call file.read() instead of passing file.read
        blob_client.upload_blob(file.read(), overwrite=True)
        image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
        return image_url
    except Exception as e:
        st.error(f"Erro ao fazer upload da imagem: {e}")
        return None 

def insert_product_to_sql(product_name, product_price, product_description, product_image):
    try:
        # Upload image first
        image_url = upload_blob(product_image)
        if image_url is None:
            return False
            
        # Then insert into database
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Produtos (nome, descricao, preco, imagem_url) 
            VALUES (%s, %s, %s, %s)
        """, (product_name, product_description, product_price, image_url))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto no banco de dados: {e}")
        return False

def list_products():
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, preco, descricao, imagem_url FROM Produtos")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return products
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []

def list_products_screen():
    products = list_products()
    for product in products:
        st.image(product[4], width=100)  # imagem_url
        st.write(f"**Nome:** {product[1]}")  # nome
        st.write(f"**Preço:** R$ {product[2]:.2f}")  # preco
        st.write(f"**Descrição:** {product[3]}")  # descricao
        st.write("---")  # Add a separator between products

if st.button('Salvar Produto'):
    if product_name and product_price and product_description and product_image:
        if insert_product_to_sql(product_name, product_price, product_description, product_image):
            st.success('Produto Salvo com sucesso!')
        else:
            st.error('Erro ao salvar produto')
    else:
        st.warning('Por favor, preencha todos os campos')

st.header('Produtos Cadastrados')

if st.button('Listar Produtos'):
    list_products_screen()
    return_message = 'Listando Produtos...'

