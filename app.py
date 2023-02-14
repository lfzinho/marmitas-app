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

tab_menu, tab_order = st.tabs(["Menu", "Pedido"])

tab_menu.write("Aqui você pode ver os sabores disponíveis:")
tab_menu.dataframe(marmitas)

with tab_order.form("order"):
    name = st.text_input("Digite seu nome:")
    # multiplica os sabores disponíveis por 5
    options = marmitas["sabores"].tolist() * 5
    choices = st.multiselect("Escolha os sabores:", options, max_selections=5)
    date = st.date_input("Escolha a data:", min_value=datetime.date.today())


    confirm_btn = st.form_submit_button("Confirmar pedido")
    
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
