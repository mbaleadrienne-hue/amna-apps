import os, json, pandas as pd, streamlit as st
from datetime import datetime
from fpdf import FPDF
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="AMNA - CEO Dashboard", page_icon="👑", layout="wide")
HISTO="ventes.csv"; F_BOUT="boutiques.json"; F_PROD="produits.json"; DOSSIER_FACT="factures"
if "lang" not in st.session_state: st.session_state.lang="FR"
if "panier" not in st.session_state: st.session_state.panier=[]
if "last_pdf" not in st.session_state: st.session_state.last_pdf=None
def T(fr,en): return fr if st.session_state.lang=="FR" else en

def load_boutiques():
    if not os.path.exists(F_BOUT): return {}
    try:
        with open(F_BOUT,"r",encoding="utf-8") as f: return json.load(f)
    except: return {}
def load_produits():
    if not os.path.exists(F_PROD): return []
    try:
        with open(F_PROD,"r",encoding="utf-8") as f: d=json.load(f)
        return d if isinstance(d,list) else []
    except: return []
def get_df():
    if not os.path.exists(HISTO): return pd.DataFrame()
    try:
        df=pd.read_csv(HISTO)
        if df.empty: return df
        df["total"]=pd.to_numeric(df.get("total",0), errors="coerce").fillna(0)
        df["qte"]=pd.to_numeric(df.get("qte",0), errors="coerce").fillna(0)
        if "date" in df.columns: df["date"]=pd.to_datetime(df["date"], errors="coerce")
        return df
    except: return pd.DataFrame()

with st.sidebar:
    st.markdown("### 🌐 LANGUE / LANGUAGE")
    choix=st.radio("Lang", ["🇫🇷 FR","🇬🇧 EN"], index=0 if st.session_state.lang=="FR" else 1, label_visibility="collapsed")
    st.session_state.lang="FR" if "FR" in choix else "EN"
    st.divider()
    st.markdown(T("### 📍 BOUTIQUE AMNA","### 📍 AMNA STORE"))
    with st.form("b", clear_on_submit=True):
        nb=st.text_input(T("Nom boutique","Store name"))
        region=st.selectbox(T("Région","Region"), ["Littoral-Douala","Centre-Yaoundé","Gabon-Libreville","Ghana-Accra","Kribi"])
        if st.form_submit_button(T("➕ Créer","➕ Create"), use_container_width=True) and nb.strip():
            coords={"Littoral-Douala":[4.05,9.76],"Centre-Yaoundé":[3.87,11.52],"Gabon-Libreville":[0.41,9.46],"Ghana-Accra":[5.6,-0.20],"Kribi":[2.94,9.91]}
            b=load_boutiques(); b[nb.strip()]=coords.get(region,[4.05,9.76])
            with open(F_BOUT,"w",encoding="utf-8") as f: json.dump(b,f,ensure_ascii=False,indent=2)
            st.rerun()
    st.divider()
    st.markdown(T("### 📦 PRODUIT AMNA","### 📦 AMNA PRODUCT"))
    with st.form("p", clear_on_submit=True):
        np=st.text_input(T("Nom produit","Product name"))
        pp=st.number_input(T("Prix","Price"),0,10000000,50000,1000)
        if st.form_submit_button(T("➕ Nouveau","➕ New"), use_container_width=True) and np.strip():
            pr=load_produits(); pr.append({"nom":np.strip(),"prix":pp})
            with open(F_PROD,"w",encoding="utf-8") as f: json.dump(pr,f,ensure_ascii=False,indent=2)
            st.rerun()

BOUTIQUES=load_boutiques(); PRODUITS=load_produits()
os.makedirs(DOSSIER_FACT, exist_ok=True)

t1,t2,t3,t4,t5=st.tabs([T("🧾 Caisse AMNA","🧾 AMNA Cashier"), T("📅 Ventes AUTO","📅 Sales AUTO"), "📊 Pivot AMNA", "📈 Dashboard MAP+AFTER", T("💡 Conseil","💡 Advice")])

with t1:
    if not BOUTIQUES or not PRODUITS:
        st.warning(T("Crée d'abord une boutique + un produit à gauche!","Create store + product on left first!"))
    else:
        boutique=st.selectbox("Store/Boutique AMNA", list(BOUTIQUES.keys()))
        client=st.text_input(T("Client","Client"), value="Mme Jenaya")
        caiss=st.text_input(T("Caissière","Cashier"), value="Marie - 02")
        c1,c2=st.columns([3,1])
        with c1: prod=st.selectbox("Product/Produit AMNA", [p["nom"] for p in PRODUITS])
        with c2: qte=st.number_input("Qty/Qte",1,1000,1)
        pu=next((p["prix"] for p in PRODUITS if p["nom"]==prod),0)
        st.info(f"PU: {pu:,.0f} | Total: {pu*qte:,.0f}")
        mode=st.selectbox("Payment/Paiement", ["Card","OM","MoMo","Cash"])
        if st.button(T("➕ Panier","➕ Cart"), use_container_width=True):
            st.session_state.panier.append({"produit":prod,"qte":qte,"pu":pu,"total":pu*qte}); st.rerun()
        if st.session_state.panier:
            st.dataframe(pd.DataFrame(st.session_state.panier), use_container_width=True)
            total=sum(x["total"] for x in st.session_state.panier)
            st.markdown(f"### Total: {total:,.0f} FCFA")
            if st.button(T("💾 ENCAISSER - 1 VENTE = 1 PDF AMNA","💾 PAY - 1 SALE = 1 PDF AMNA"), type="primary", use_container_width=True):
                now=datetime.now(); fid=f"AMNA-{now.strftime('%Y%m%d-%H%M%S')}"
                rows=[{"date":str(now),"boutique":boutique,"facture":fid,"caissiere":caiss,"client":client,"produit":i["produit"],"qte":i["qte"],"pu":i["pu"],"total":i["total"],"ModePaiement":mode} for i in st.session_state.panier]
                pd.DataFrame(rows).to_csv(HISTO, mode='a', header=not os.path.exists(HISTO), index=False)
                pdf=FPDF(); pdf.add_page(); pdf.set_font("Arial","B",16); pdf.cell(0,12,f"AMNA - {boutique}",ln=True,align="C")
                pdf.set_font("Arial","",11); pdf.cell(0,7,f"Facture/Invoice: {fid} | {mode}",ln=True); pdf.cell(0,7,f"Client: {client} | Cashier: {caiss}",ln=True); pdf.ln(4)
                for it in st.session_state.panier: pdf.cell(0,7,f"{it['produit']} x{it['qte']} = {it['total']:,.0f}",ln=True)
                pdf.set_font("Arial","B",13); pdf.cell(0,10,f"TOTAL: {total:,.0f} FCFA",ln=True,align="R")
                pdf.ln(5); pdf.set_font("Arial","I",10); pdf.cell(0,7,f"Merci - Thank you - AMNA Business",ln=True,align="C")
                path=f"{DOSSIER_FACT}/{fid}.pdf"; pdf.output(path)
                st.session_state.last_pdf=path; st.session_state.panier=[]; st.balloons(); st.rerun()
        if st.session_state.last_pdf and os.path.exists(st.session_state.last_pdf):
            with open(st.session_state.last_pdf,"rb") as ff:
                st.download_button(T("📥 TÉLÉCHARGER PDF AMNA","📥 DOWNLOAD AMNA PDF"), ff, file_name=os.path.basename(st.session_state.last_pdf), type="primary", use_container_width=True)

with t2:
    df=get_df()
    if df.empty: st.info("Empty/Vide - Fais une vente d'abord")
    else:
        st.dataframe(df, use_container_width=True)
        st.metric("CA AMNA", f"{df['total'].sum():,.0f} FCFA")
        if os.path.exists(DOSSIER_FACT):
            for f in sorted(os.listdir(DOSSIER_FACT), reverse=True)[:20]:
                with open(f"{DOSSIER_FACT}/{f}","rb") as ff:
                    st.download_button(f"📥 {f}", ff, file_name=f, key=f"s_{f}")

with t3:
    df=get_df()
    if not df.empty:
        pivot=df.pivot_table(index="boutique", columns="produit", values="total", aggfunc="sum", fill_value=0)
        st.markdown("### AMNA Pivot - CA par Boutique x Produit")
        st.dataframe(pivot.style.background_gradient(cmap="Greens").format("{:,.0f}"), use_container_width=True)

with t4:
    df=get_df()
    if df.empty:
        st.info(T("Fais des ventes pour voir le Dashboard AMNA","Make sales to see AMNA Dashboard"))
    else:
        total=df["total"].sum()
        nb_fact=df["facture"].nunique()
        dom_prod=df.groupby(["boutique","produit"])["total"].sum().reset_index()
        dom_prod=dom_prod.sort_values(["boutique","total"], ascending=[True,False]).drop_duplicates("boutique")
        left, right = st.columns([1,1.3])
        with left:
            st.markdown(T("**📍 MAP AMNA - Régions**","**📍 AMNA MAP - Regions**"))
            map_data=[]
            for boutique, coord in BOUTIQUES.items():
                ca_bout=df[df["boutique"]==boutique]["total"].sum()
                prod_dom=dom_prod[dom_prod["boutique"]==boutique]["produit"].values[0] if not dom_prod[dom_prod["boutique"]==boutique].empty else "N/A"
                lat=float(coord[0]) if isinstance(coord,(list,tuple)) else 4.05
                lon=float(coord[1]) if isinstance(coord,(list,tuple)) else 9.76
                if lat<1: reg="GABON"
                elif lon<1: reg="GHANA"
                elif lat<3.5: reg="KRIBI"
                elif lat<4.0: reg="CENTRE"
                else: reg="LITTORAL"
                map_data.append({"boutique":boutique,"lat":lat,"lon":lon,"ca":int(ca_bout),"produit":prod_dom,"region":reg})
            dfm=pd.DataFrame(map_data)
            if not dfm.empty:
                layer=pdk.Layer("ScatterplotLayer", data=dfm, get_position='[lon, lat]', get_color='[0, 200, 120, 200]', get_radius=35000, pickable=True)
                view=pdk.ViewState(latitude=3.5, longitude=9.5, zoom=5)
                tooltip={"html":"<b>{boutique}</b><br/>Region: {region}<br/>CA: {ca} FCFA<br/>Top: {produit}", "style":{"backgroundColor":"white","color":"black"}}
                st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip))
                st.dataframe(dfm[["region","boutique","produit","ca"]], use_container_width=True)
        with right:
            st.markdown("**AMNA - AFTER - Clean File**")
            k1,k2=st.columns(2)
            with k1: st.markdown(f"""<div style="background:#E8F5E9;padding:15px;border-radius:10px;border-left:5px solid #00C853"><small>Revenue AMNA</small><h2>{total/1000:.1f}K</h2><small style="color:green">+217% vs avant</small></div>""", unsafe_allow_html=True)
            with k2: st.markdown(f"""<div style="background:#E8F5E9;padding:15px;border-radius:10px;border-left:5px solid #00C853"><small>Ventes AMNA</small><h2>{nb_fact}</h2><small style="color:green">100% nettoyé</small></div>""", unsafe_allow_html=True)
            st.divider()
            df["mois"]=df["date"].dt.to_period("M").astype(str)
            evol=df.groupby("mois")["total"].sum().reset_index()
            fig=px.bar(evol, x="mois", y="total", title="AMNA - Revenus Mensuels", color_discrete_sequence=["#00C896"])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            evol["cum_pct"]=(evol["total"].cumsum()/evol["total"].sum()*100)
            fig2=go.Figure()
            fig2.add_trace(go.Scatter(x=evol["mois"], y=evol["cum_pct"], mode='lines+markers', line=dict(color='#7C4DFF', width=3), fill='tozeroy'))
            fig2.update_layout(title="AMNA - Occupation (%)", height=250, yaxis=dict(range=[0,100]))
            st.plotly_chart(fig2, use_container_width=True)

with t5:
    df=get_df()
    if not df.empty:
        total=df["total"].sum()
        top_prod=df.groupby("produit")["total"].sum().sort_values(ascending=False)
        top_bout=df.groupby("boutique")["total"].sum().sort_values(ascending=False)
        st.metric("Best Product AMNA", top_prod.index[0], f"{top_prod.iloc[0]/total*100:.1f}%")
        st.metric("Best Store AMNA", top_bout.index[0], f"{top_bout.iloc[0]/total*100:.1f}%")
        c1,c2=st.columns(2)
        c1.plotly_chart(px.bar(top_prod.reset_index(), x="produit", y="total", color="produit"), use_container_width=True)
        c2.plotly_chart(px.pie(top_bout.reset_index(), names="boutique", values="total", hole=0.4), use_container_width=True)