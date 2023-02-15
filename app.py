import streamlit as st
import pandas as pd
import datetime
import json
import firebase_admin
from firebase_admin import credentials, firestore

key_dict = json.loads(st.secrets['textkey'])

@st.cache_resource
def initialize_app():
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db

marmitas = pd.read_csv("marmitas.csv", sep=";")
db = initialize_app()

st.title("Marmitas 🥕")

tab_menu, tab_order, tab_lot = st.tabs(["Menu", "Pedido", "Lote"])

tab_menu.write("Aqui você pode ver os sabores disponíveis:")
tab_menu.dataframe(marmitas)

with tab_order.form("order"):
    name = st.text_input("Digite seu nome:")
    # multiplica os sabores disponíveis por 5
    options = marmitas["sabores"].tolist() * 5
    choices = st.multiselect("Escolha os sabores:", options, max_selections=5)
    date = st.date_input("Escolha a data:", min_value=datetime.date.today())


    confirm_btn = st.form_submit_button("Confirmar pedido")
    
with tab_lot.form("lot"):
    date = st.date_input("Escolha a data do lote:")
    lot_btn = st.form_submit_button("Confirmar data")
    # Add filter by name
    name_filter = tab_lot.text_input("Filtrar por nome:")
    filter_btn = tab_lot.button("Filtrar")

def send_order():
    st.success("Pedido enviado com sucesso!")
    st.markdown("**Se você quiser fazer outro pedido, recarregue a página.**")
    
    db.collection(date.strftime('%d-%m-%Y')).document(name).set({
        "pedido": choices
    })


if confirm_btn:
    tab_order.info(f"""Seu pedido é: \n
    Nome: {name} \n
    Sabores: {', '.join(choices)} \n
    Data: {date} \n
    """)
    tab_order.button("Enviar pedido", on_click=send_order)

if lot_btn:
    tab_lot.info(f"Data do lote: {date}")
    tab_lot.write("Pedidos do lote:")
    # Get data from firestore
    docs = db.collection(date.strftime('%d-%m-%Y')).stream()
    # Create a dataframe from the data
    df = []
    for doc in docs:
        for doc_item in doc.to_dict().get("pedido"):
            df.append(doc_item)
    df = pd.DataFrame({"Quantidade":df})
    df = df["Quantidade"].value_counts(sort=True)
    df = df.to_frame()
    # Show the dataframe
    tab_lot.dataframe(df)

    

if filter_btn:
    tab_lot.info(f"Data do lote: {date}")
    tab_lot.info(f"Pedido dx: {name_filter}")
    tab_lot.write("Pedidos do lote:")
    docs = db.collection(date.strftime('%d-%m-%Y')).stream()
    df = []
    for doc in docs:
        # tab_lot.write(doc.id)
        if name_filter in doc.id:
            for doc_item in doc.to_dict().get("pedido"):
                df.append(doc_item)
    df = pd.DataFrame({"Quantidade":df})
    df = df["Quantidade"].value_counts(sort=True)
    df = df.to_frame()
    tab_lot.dataframe(df)
