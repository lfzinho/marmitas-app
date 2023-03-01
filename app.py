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

st.title("🥕 Marmitas")

tab_menu, tab_feed, tab_order, tab_lot = st.tabs(["🥦 Menu", "✨ Feed", "📝 Pedido", "⚙️ Lote"])

tab_menu.write("Aqui você pode ver os sabores disponíveis:")
tab_menu.dataframe(marmitas)

with tab_order.expander("❔ Instruções"):
    st.markdown("""1. Digite seu nome no campo de texto.
2. Escolha os sabores que deseja.
3. Escolha a data que deseja receber a marmita.
4. Clique em "Confirmar pedido".
5. Confirme o pedido.
6. Recarregue a página para fazer outro pedido.""")
with tab_order.form("order"):

    name = st.text_input("Digite seu nome:")
    # multiplica os sabores disponíveis por 5
    options = marmitas["sabores"].tolist() * 5
    choices = st.multiselect("Escolha os sabores:", options, max_selections=5)
    date = st.date_input("Escolha a data:", min_value=datetime.date.today())


    confirm_btn = st.form_submit_button("Confirmar pedido")
    
with tab_lot.form("lot"):
    date_lot = st.date_input("Escolha a data do lote:")
    name_filter = st.text_input("Filtrar por nome:")
    lot_btn = st.form_submit_button("Filtrar lote")

with tab_feed:
    docs = db.collection("feed").order_by("time", direction=firestore.Query.DESCENDING).limit(30).get()
    if not docs:
        st.markdown('<div style="text-align: center;">Nenhum pedido ainda. 😿</div>', unsafe_allow_html=True)
    else:
        posts = []
        for doc in docs:
            doc = doc.to_dict()
            original_doc = db.collection(doc["collection"]).document(doc["person"]).get()
            doc_dict = original_doc.to_dict()
            if doc_dict is None: # if the original post was deleted
                continue
            doc_dict["person"] = doc["person"]
            doc_dict["date"] = doc["collection"]
            doc_dict["time"] = doc["time"] - datetime.timedelta(hours=3)
            doc_dict["likes"] = doc["likes"]
            posts.append(doc_dict)
        
        for post in posts:
            with st.expander(post["person"], expanded=True):
                pedido_format = ', \n\n'.join(post["pedido"])
                st.markdown(pedido_format)
                st.caption(f"***Data: {post['date']}***")
                st.session_state[post["person"]+post["date"]+"_state"] = post["likes"]
                col1, col2 = st.columns([1, 10])

                # like button
                if col1.button("👍", key=post["person"]+post["date"]):
                    st.session_state[post["person"]+post["date"]+"_state"] += 1
                    db.collection("feed").document(post["person"]+post["date"]).update({"likes": post["likes"] + 1})
                    st.balloons()
                
                # number of likes
                n_curtidas = st.session_state[post['person']+post['date']+ '_state']
                col2.write(f" {n_curtidas} {'curtida' if n_curtidas <= 1 else 'curtidas'}")
                st.caption(f"*{post['time'].strftime('%d/%m/%Y, %H:%M:%S')}*")

def send_order():
    st.success("Pedido enviado com sucesso!")
    st.markdown("**Se você quiser fazer outro pedido, recarregue a página.**")
    
    db.collection(date.strftime('%d-%m-%Y')).document(name).set({
        "pedido": choices
    })
    # sends to feed
    db.collection("feed").document(name+date.strftime('%d-%m-%Y')).set({
        "collection":date.strftime('%d-%m-%Y'),
        "person":name,
        "time": firebase_admin.firestore.SERVER_TIMESTAMP,
        "likes": 1,
    })

if confirm_btn:
    choices_format = ', \n\n'.join(choices)
    tab_order.info(f"""Seu pedido é: \n
Nome: {name} \n
Sabores: \n\n {choices_format} \n
Data: {date} \n
""")
    tab_order.button("Enviar pedido", on_click=send_order)

if lot_btn:
    # Get data from firestore
    if name_filter == "": # if no name is given, show all
        tab_lot.info(f"Data do lote: {date_lot}")
        docs = db.collection(date_lot.strftime('%d-%m-%Y')).stream()
    else: # if a name is given, show only that name
        tab_lot.info(f"Data do lote: {date_lot} \n\nPedido de: {name_filter}")
        docs = [db.collection(date_lot.strftime('%d-%m-%Y')).document(name_filter).get()]

    tab_lot.write("Pedidos do lote:")
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
    # Show total
    tab_lot.write(f"Total: {df['Quantidade'].sum()}")
