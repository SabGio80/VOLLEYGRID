import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import io

# PDF Generation (ReportLab)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import database as db

# -----------------------------------------------------------------------------
# CONFIGURAZIONE PAGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestionale Pallavolo",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializzazione Database
db.init_db()

# -----------------------------------------------------------------------------
# AUTENTICAZIONE E RUOLI (Session State)
# -----------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

def login():
    st.sidebar.title("🔐 Login")
    user = st.sidebar.text_input("Username")
    pwd = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Accedi"):
        role = db.verifica_credenziali(user, pwd)
        if role:
            st.session_state["logged_in"] = True
            st.session_state["username"] = user
            st.session_state["role"] = role
            st.rerun()
        else:
            st.sidebar.error("Username o password errati")

def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.rerun()

if not st.session_state["logged_in"]:
    st.title("🏐 Gestionale Squadre di Pallavolo")
    st.info("Effettua il login dal menu a sinistra per accedere alle funzionalità.")
    login()
    st.stop()

# Sidebar Info Utente
st.sidebar.write(f"Utente: **{st.session_state['username']}** ({st.session_state['role']})")
st.sidebar.button("Logout", on_click=logout)

is_admin = (st.session_state["role"] == "Admin")

# -----------------------------------------------------------------------------
# METODI DI SUPPORTO GENERAZIONE PDF
# -----------------------------------------------------------------------------
def genera_pdf_presenze(squadra_nome, df_presenze, atleti):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=15,
        textColor=colors.HexColor('#1E3A8A')
    )
    
    elements.append(Paragraph(f"Registro Presenze - Squadra: {squadra_nome}", title_style))
    elements.append(Spacer(1, 10))

    if not df_presenze.empty:
        # Costruzione Dati Tabella
        headers = ["Atleta", "Ruolo"] + [d.strftime("%d/%m") if isinstance(d, (date, datetime)) else str(d) for d in df_presenze.columns]
        table_data = [headers]

        for atl in atleti:
            atl_id = atl[0]
            nome_atl = f"{atl[1]} {atl[2]}"
            ruolo_atl = atl[3] or ""
            
            row = [nome_atl, ruolo_atl]
            for col in df_presenze.columns:
                val = df_presenze.loc[atl_id, col] if atl_id in df_presenze.index else ""
                row.append(str(val) if pd.notna(val) else "")
            table_data.append(row)

        # Dimensionamento Colonne
        col_widths = [120, 60] + [25] * len(df_presenze.columns)

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,1), (0,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F3F4F6')])
        ]))
        elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# -----------------------------------------------------------------------------
# INTERFACCIA PRINCIPALE (TAB)
# -----------------------------------------------------------------------------
st.title("🏐 Gestionale Pallavolo")

tab1, tab2, tab3 = st.tabs([
    "📋 Gestione Squadre & Allenamenti", 
    "🏃‍♂️ Gestione Anagrafica Atleti", 
    "📊 Registro Presenze & Report PDF"
])

# =============================================================================
# TAB 1: GESTIONE SQUADRE & ALLENAMENTI
# =============================================================================
with tab1:
    st.header("Gestione Squadre e Sessioni Allenamento")
    
    col_sq, col_all = st.columns([1, 2])
    
    with col_sq:
        st.subheader("Squadre")
        squadre = db.ottieni_squadre()
        
        if is_admin:
            with st.expander("➕ Nuova Squadra"):
                nuova_sq = st.text_input("Nome Nuova Squadra")
                if st.button("Salva Squadra"):
                    if nuova_sq.strip():
                        db.aggiungi_squadra(nuova_sq.strip())
                        st.success(f"Squadra '{nuova_sq}' creata!")
                        st.rerun()
                    else:
                        st.warning("Inserisci un nome valido.")
                        
        squadra_selezionata = st.selectbox("Seleziona Squadra:", squadre, format_func=lambda x: x[1] if x else "Nessuna")
        
    with col_all:
        if squadra_selezionata:
            sq_id, sq_nome = squadra_selezionata[0], squadra_selezionata[1]
            st.subheader(f"Allenamenti: {sq_nome}")
            
            if is_admin:
                with st.expander("📅 Pianifica / Aggiungi Allenamento"):
                    data_all = st.date_input("Data Allenamento", value=date.today())
                    ora_in = st.time_input("Ora Inizio")
                    ora_fi = st.time_input("Ora Fine")
                    desc = st.text_input("Descrizione / Note (opzionale)")
                    
                    if st.button("Crea Allenamento"):
                        db.crea_allenamento(sq_id, data_all.strftime("%Y-%m-%d"), ora_in.strftime("%H:%M"), ora_fi.strftime("%H:%M"), desc)
                        st.success("Allenamento creato con successo!")
                        st.rerun()
            
            allenamenti = db.ottieni_allenamenti_squadra(sq_id)
            if allenamenti:
                df_all = pd.DataFrame(allenamenti, columns=["ID", "Data", "Ora Inizio", "Ora Fine", "Note"])
                st.dataframe(df_all[["Data", "Ora Inizio", "Ora Fine", "Note"]], use_container_width=True)
            else:
                st.info("Nessun allenamento programmato per questa squadra.")

# =============================================================================
# TAB 2: GESTIONE ANAGRAFICA ATLETI
# =============================================================================
with tab2:
    st.header("Anagrafica & Schede Atleti")
    
    if squadra_selezionata:
        sq_id, sq_nome = squadra_selezionata[0], squadra_selezionata[1]
        
        if is_admin:
            with st.expander("➕ Aggiungi Nuovo Atleta"):
                with st.form("form_nuovo_atleta"):
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        nome = st.text_input("Nome *")
                        cognome = st.text_input("Cognome *")
                        ruolo = st.selectbox("Ruolo", ["Alzatore", "Schiacciatore", "Centrale", "Opposto", "Libero"])
                        num_maglia = st.number_input("Numero Maglia", min_value=0, max_value=99, step=1)
                    with col_a2:
                        d_nascita = st.text_input("Data Nascita (GG/MM/AAAA)")
                        l_nascita = st.text_input("Luogo Nascita")
                        cod_fisc = st.text_input("Codice Fiscale")
                        
                    submitted = st.form_submit_button("Registra Atleta")
                    if submitted:
                        if nome and cognome:
                            db.aggiungi_atleta(sq_id, nome, cognome, ruolo, num_maglia, d_nascita, l_nascita, cod_fisc)
                            st.success(f"Atleta {nome} {cognome} registrato!")
                            st.rerun()
                        else:
                            st.error("Nome e Cognome sono obbligatori.")
                            
        st.subheader(f"Atleti Tesserati - {sq_nome}")
        atleti = db.ottieni_atleti_squadra(sq_id)
        
        if atleti:
            df_atleti = pd.DataFrame(atleti, columns=["ID", "Nome", "Cognome", "Ruolo", "N° Maglia"])
            
            # Selezione Atleta per Gestione/Dettagli
            atleta_id_scelto = st.selectbox(
                "Seleziona Atleta per visualizzare o modificare la scheda:",
                df_atleti["ID"].tolist(),
                format_func=lambda x: f"{df_atleti.loc[df_atleti['ID']==x, 'Nome'].values[0]} {df_atleti.loc[df_atleti['ID']==x, 'Cognome'].values[0]} (#{df_atleti.loc[df_atleti['ID']==x, 'N° Maglia'].values[0]})"
            )
            
            if atleta_id_scelto:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    with st.expander("📝 Dati Anagrafici"):
                        curr = db.ottieni_dati_atleta_completi(atleta_id_scelto)
                        if curr:
                            dn = st.text_input("Data Nascita (GG/MM/AAAA)", value=curr[5] or "", key=f"dn_{atleta_id_scelto}", disabled=not is_admin)
                            ln = st.text_input("Luogo Nascita", value=curr[6] or "", key=f"ln_{atleta_id_scelto}", disabled=not is_admin)
                            cf = st.text_input("Codice Fiscale", value=curr[7] or "", key=f"cf_{atleta_id_scelto}", disabled=not is_admin)
                            email = st.text_input("Email", value=curr[14] if len(curr) > 14 and curr[14] else "", key=f"email_{atleta_id_scelto}", disabled=not is_admin)
                            tel = st.text_input("Telefono / Cellulare", value=curr[13] if len(curr) > 13 and curr[13] else "", key=f"tel_{atleta_id_scelto}", disabled=not is_admin)
                            ind = st.text_input("Indirizzo", value=curr[8] or "", key=f"ind_{atleta_id_scelto}", disabled=not is_admin)
                            cit = st.text_input("Città", value=curr[9] or "", key=f"cit_{atleta_id_scelto}", disabled=not is_admin)
                            cap = st.text_input("CAP", value=curr[10] or "", key=f"cap_{atleta_id_scelto}", disabled=not is_admin)
                            naz = st.text_input("Nazionalità", value=curr[11] or "", key=f"naz_{atleta_id_scelto}", disabled=not is_admin)
                            vis = st.text_input("Scadenza Visita (GG/MM/AAAA)", value=curr[12] or "", key=f"vis_{atleta_id_scelto}", disabled=not is_admin)
                            
                            if st.button("Aggiorna Anagrafica", disabled=not is_admin):
                                db.aggiorna_anagrafica_atleta(atleta_id_scelto, dn, ln, cf, ind, cit, cap, naz, vis, tel, email)
                                st.success("Anagrafica aggiornata!")
                                st.rerun()

                with col_btn2:
                    if is_admin:
                        st.subheader("Azioni Pericolose")
                        if st.button("🗑️ Elimina Atleta", type="primary"):
                            db.elimina_atleta(atleta_id_scelto)
                            st.success("Atleta eliminato.")
                            st.rerun()
            
            st.divider()
            st.dataframe(df_atleti, use_container_width=True)
        else:
            st.info("Nessun atleta registrato in questa squadra.")

# =============================================================================
# TAB 3: REGISTRO PRESENZE & REPORT PDF
# =============================================================================
with tab3:
    st.header("Registro Presenze & Export PDF")
    
    if squadra_selezionata:
        sq_id, sq_nome = squadra_selezionata[0], squadra_selezionata[1]
        
        allenamenti = db.ottieni_allenamenti_squadra(sq_id)
        atleti = db.ottieni_atleti_squadra(sq_id)
        
        if allenamenti and atleti:
            # Creazione Pivot/Matrice Presenze
            df_p = db.ottieni_matrice_presenze(sq_id)
            
            st.subheader(f"Tabella Presenze - {sq_nome}")
            st.dataframe(df_p, use_container_width=True)
            
            st.divider()
            st.subheader("📌 Inserimento / Modifica Presenza")
            
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                all_scelto = st.selectbox("Allenamento", allenamenti, format_func=lambda x: f"{x[1]} ({x[2]}-{x[3]})")
            with col_p2:
                atl_scelto = st.selectbox("Atleta", atleti, format_func=lambda x: f"{x[1]} {x[2]}")
            with col_p3:
                stato_presenza = st.selectbox("Stato", ["Presente", "Assente", "Giustificato", "Infortunato"])
                
            if st.button("Registra Presenza", disabled=not is_admin):
                db.registra_presenza(all_scelto[0], atl_scelto[0], stato_presenza)
                st.success("Presenza aggiornata!")
                st.rerun()
                
            st.divider()
            st.subheader("📄 Generazione e Download Report PDF")
            
            if st.button("🚀 Genera Report PDF Presenze"):
                pdf_bytes = genera_pdf_presenze(sq_nome, df_p, atleti)
                safe_title = f"Presenze_{sq_nome}".replace(" ", "_")
                
                st.download_button(
                    label="📄 Scarica Report PDF (.pdf)",
                    data=pdf_bytes,
                    file_name=f"{safe_title}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.warning("Servono sia almeno un allenamento che almeno un atleta registrato per accedere al registro presenze.")