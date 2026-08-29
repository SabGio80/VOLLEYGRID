import io
import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from database import Database

# Import ReportLab per l'esportazione PDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Gestionale Pallavolo Web", layout="wide")

db = Database()
db.inizializza_db()

# --- GESTIONE LOGIN E RUOLI ---
def verifica_login(username, password):
    if hasattr(db, 'verifica_utente'):
        return db.verifica_utente(username, password)
    
    # Credenziali di test / fallback
    if username == "allenatore" and password == "admin123":
        return "admin"
    elif username == "ospite" and password == "view123":
        return "viewer"
    return None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

# SCHERMATA DI LOGIN
if not st.session_state.logged_in:
    st.title("🔐 Accesso Gestionale Pallavolo")
    col_u, col_p = st.columns(2)
    with col_u:
        user_input = st.text_input("Username")
    with col_p:
        pass_input = st.text_input("Password", type="password")
    
    if st.button("Accedi", type="primary"):
        ruolo = verifica_login(user_input, pass_input)
        if ruolo:
            st.session_state.logged_in = True
            st.session_state.user_role = ruolo
            st.success(f"Benvenuto! Ruolo: {ruolo.upper()}")
            st.rerun()
        else:
            st.error("Credenziali errate.")
    st.stop()

# Flag di controllo permessi Admin vs Viewer
is_admin = (st.session_state.user_role == "admin")

# --- BARRA LATERALE E HEADER ---
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("🏐 Gestionale Pallavolo Web")
with col_head2:
    st.write(f"👤 Utente: **{st.session_state.user_role.upper()}**")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.rerun()

# --- FUNZIONI UTILI ---
def file_to_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        mime_type = uploaded_file.type
        b64_str = base64.b64encode(bytes_data).decode("utf-8")
        return f"data:{mime_type};base64,{b64_str}"
    return None

def genera_pdf_report(df, titolo="Report Gestionale Pallavolo"):
    """Genera un file PDF formattato in formato orizzontale a partire da un DataFrame."""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
    )
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray,
        spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph(titolo, title_style))
    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Generato il: {data_ora}", subtitle_style))
    
    headers = [Paragraph(str(col), header_style) for col in df.columns]
    data_table = [headers]
    
    for row in df.itertuples(index=False):
        row_data = []
        for val in row:
            text = "" if pd.isna(val) else str(val)
            row_data.append(Paragraph(text, cell_style))
        data_table.append(row_data)
        
    t = Table(data_table, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

# --- INIZIALIZZAZIONE SESSION STATE ---
if "mostra_form_stagione" not in st.session_state:
    st.session_state.mostra_form_stagione = False

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Gestione Squadre"

if "nav_tab" not in st.session_state:
    st.session_state.nav_tab = st.session_state.active_tab

if "squadra_da_selezionare" not in st.session_state:
    st.session_state.squadra_da_selezionare = None

if "input_nome_sq" not in st.session_state:
    st.session_state.input_nome_sq = ""

if "input_cat_sq" not in st.session_state:
    st.session_state.input_cat_sq = ""

if "modo_nuovo_atleta" not in st.session_state:
    st.session_state.modo_nuovo_atleta = False

if "grid_sq_key" not in st.session_state:
    st.session_state.grid_sq_key = 0

# --- SELEZIONE STAGIONE E SQUADRA ---
stagioni = db.ottieni_stagioni()
stagioni_dict = {s[1]: s[0] for s in stagioni}

col_top1, col_top2, col_top3 = st.columns([2, 2, 2])

with col_top1:
    stagione_scelta = st.selectbox("Stagione:", options=list(stagioni_dict.keys()) if stagioni_dict else ["Nessuna"])
    stagione_id = stagioni_dict.get(stagione_scelta)

with col_top2:
    if not st.session_state.mostra_form_stagione:
        st.write("") 
        if st.button("+ Aggiungi Stagione", disabled=not is_admin):
            st.session_state.mostra_form_stagione = True
            st.rerun()
    else:
        nuova_stagione = st.text_input("Nuova Stagione (es. 2025/2026):", disabled=not is_admin)
        col_btn_s1, col_btn_s2 = st.columns(2)
        with col_btn_s1:
            if st.button("Salva", type="primary", disabled=not is_admin):
                if nuova_stagione:
                    esito = db.aggiungi_stagione(nuova_stagione)
                    if esito:
                        st.success("Stagione aggiunta!")
                        st.session_state.mostra_form_stagione = False
                        st.rerun()
                    else:
                        st.error("Stagione già esistente o errore.")
                else:
                    st.warning("Inserisci il nome.")
        with col_btn_s2:
            if st.button("Annulla"):
                st.session_state.mostra_form_stagione = False
                st.rerun()

squadre_dict = {}
if stagione_id:
    squadre = db.ottieni_squadre_per_stagione(stagione_id)
    squadre_dict = {f"{s[1]} ({s[2]})": s[0] for s in squadre}

with col_top3:
    options_sq = list(squadre_dict.keys()) if squadre_dict else ["Nessuna"]
    
    if st.session_state.squadra_da_selezionare in options_sq:
        st.session_state.squadra_scelta_key = st.session_state.squadra_da_selezionare
        st.session_state.squadra_da_selezionare = None
        
    squadra_scelta = st.selectbox(
        "Squadra Attiva:", 
        options=options_sq,
        key="squadra_scelta_key"
    )
    squadra_id = squadre_dict.get(squadra_scelta)

st.divider()

# --- TABS PRINCIPALI ---
tabs = ["Gestione Squadre", "Rosa Atleti", "Reportistica"]

if "target_tab" in st.session_state:
    st.session_state.nav_tab = st.session_state.target_tab
    st.session_state.active_tab = st.session_state.target_tab
    del st.session_state.target_tab

def on_tab_change():
    if "nav_tab" in st.session_state:
        st.session_state.active_tab = st.session_state.nav_tab

selected_tab = st.radio(
    "Navigazione", 
    tabs, 
    key="nav_tab",
    on_change=on_tab_change,
    horizontal=True, 
    label_visibility="collapsed"
)

# --- TAB SQUADRE ---
if st.session_state.active_tab == "Gestione Squadre":
    col_sq1, col_sq2 = st.columns([1, 2])
    
    with col_sq1:
        st.subheader("Aggiungi Squadra")
        nome_sq = st.text_input("Nome Squadra", value=st.session_state.input_nome_sq, disabled=not is_admin)
        cat_sq = st.text_input("Categoria", value=st.session_state.input_cat_sq, disabled=not is_admin)
        
        if st.button("Salva Squadra", disabled=not is_admin):
            if nome_sq and stagione_id:
                db.aggiungi_squadra(nome_sq, cat_sq, stagione_id)
                st.success("Squadra creata!")
                st.session_state.input_nome_sq = ""
                st.session_state.input_cat_sq = ""
                st.rerun()
            else:
                st.warning("Assicurati di inserire il nome della squadra e di aver selezionato una stagione.")
                
    with col_sq2:
        st.subheader("Squadre della Stagione")
        if stagione_id:
            sq_list = db.ottieni_squadre_per_stagione(stagione_id)
            if sq_list:
                st.caption("💡 Clicca sull'intestazione di una colonna per ordinare. Clicca su una riga per selezionare la squadra ed andare alla sua rosa.")
                
                df_squadre = pd.DataFrame(sq_list, columns=["ID Database", "Nome Squadra", "Categoria"])
                
                event_sq = st.dataframe(
                    df_squadre[["ID Database", "Nome Squadra", "Categoria"]],
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key=f"df_squadre_{st.session_state.grid_sq_key}"
                )

                if event_sq and event_sq.selection and event_sq.selection.rows:
                    selected_idx = event_sq.selection.rows[0]
                    sq_row = df_squadre.iloc[selected_idx]
                    sq_label_full = f"{sq_row['Nome Squadra']} ({sq_row['Categoria']})"
                    
                    st.session_state.squadra_da_selezionare = sq_label_full
                    st.session_state.target_tab = "Rosa Atleti"
                    st.session_state.grid_sq_key += 1
                    st.rerun()
            else:
                st.info("Nessuna squadra inserita per questa stagione.")

# --- TAB ATLETI ---
elif st.session_state.active_tab == "Rosa Atleti":
    if not squadra_id:
        st.info("Seleziona una squadra in alto per procedere.")
    else:
        col_form, col_list = st.columns([1, 2])
        atleti = db.ottieni_atleti_per_squadra(squadra_id)
        
        lista_ruoli = ["Alzatore", "Opposto", "Schiacciatore", "Centrale", "Libero", "Universale"]

        if atleti:
            df_atleti = pd.DataFrame(atleti, columns=["N° Maglia", "Cognome", "Nome", "Ruolo", "ID Database", "Foto"])
            
            if "target_atleta_id" in st.session_state:
                st.session_state.select_atleta_attivo = st.session_state.target_atleta_id
                del st.session_state.target_atleta_id

            if "select_atleta_attivo" not in st.session_state or st.session_state.select_atleta_attivo not in df_atleti["ID Database"].values:
                st.session_state.select_atleta_attivo = int(df_atleti["ID Database"].iloc[0])

            with col_list:
                st.subheader("Rosa della Squadra")
                
                opzioni_atleti = {a[4]: f"N°{a[0]} - {a[1]} {a[2]} ({a[3]})" for a in atleti}
                
                atleta_id_scelto = st.selectbox(
                    "Atleta Attivo Selezionato:",
                    options=list(opzioni_atleti.keys()),
                    format_func=lambda x: opzioni_atleti[x],
                    key="select_atleta_attivo",
                    on_change=lambda: st.session_state.update({"modo_nuovo_atleta": False})
                )
                
                atleta_attuale = next((a for a in atleti if a[4] == atleta_id_scelto), None)

                st.caption("💡 Clicca sull'intestazione di una colonna per ordinare. Clicca su una riga per selezionare l'atleta.")

                event = st.dataframe(
                    df_atleti[["N° Maglia", "Cognome", "Nome", "Ruolo"]],
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )

                if event and event.selection and event.selection.rows:
                    selected_index = event.selection.rows[0]
                    selected_id = int(df_atleti.iloc[selected_index]["ID Database"])
                    if selected_id != st.session_state.select_atleta_attivo:
                        st.session_state.target_atleta_id = selected_id
                        st.session_state.modo_nuovo_atleta = False
                        st.rerun()

            with col_form:
                st.subheader("Nuovo / Modifica Atleta")
                
                if atleta_attuale and not st.session_state.modo_nuovo_atleta:
                    st.info(f"Atleta Attivo: **{atleta_attuale[2]} {atleta_attuale[1]}**")
                    
                    foto_db = atleta_attuale[5]
                    if foto_db:
                        st.image(foto_db, width=150, caption="Foto Atleta")

                    val_numero = int(atleta_attuale[0]) if atleta_attuale[0] else 1
                    val_cognome = atleta_attuale[1] or ""
                    val_nome = atleta_attuale[2] or ""
                    val_ruolo = atleta_attuale[3] if atleta_attuale[3] in lista_ruoli else "Alzatore"
                    
                    nome = st.text_input("Nome", value=val_nome, key=f"mod_nome_{atleta_id_scelto}", disabled=not is_admin)
                    cognome = st.text_input("Cognome", value=val_cognome, key=f"mod_cognome_{atleta_id_scelto}", disabled=not is_admin)
                    ruolo = st.selectbox("Ruolo", lista_ruoli, index=lista_ruoli.index(val_ruolo), key=f"mod_ruolo_{atleta_id_scelto}", disabled=not is_admin)
                    numero = st.number_input("N° Maglia", min_value=1, max_value=99, step=1, value=val_numero, key=f"mod_numero_{atleta_id_scelto}", disabled=not is_admin)
                    
                    foto_file = st.file_uploader("Aggiorna/Carica Foto", type=["jpg", "jpeg", "png"], key=f"mod_foto_{atleta_id_scelto}", disabled=not is_admin)
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("Aggiorna Atleta", type="primary", disabled=not is_admin):
                            if nome and cognome:
                                foto_b64 = file_to_base64(foto_file) if foto_file else None
                                db.modifica_atleta(atleta_id_scelto, nome, cognome, ruolo, numero, foto_base64=foto_b64)
                                st.success("Atleta aggiornato!")
                                st.rerun()
                            else:
                                st.warning("Inserisci nome e cognome.")
                    with col_b2:
                        if st.button("+ Nuovo Atleta", disabled=not is_admin):
                            st.session_state.modo_nuovo_atleta = True
                            st.rerun()
                else:
                    st.success("Modalità: **Inserimento Nuovo Atleta**")
                    nome = st.text_input("Nome", key="new_nome", disabled=not is_admin)
                    cognome = st.text_input("Cognome", key="new_cognome", disabled=not is_admin)
                    ruolo = st.selectbox("Ruolo", lista_ruoli, key="new_ruolo", disabled=not is_admin)
                    numero = st.number_input("N° Maglia", min_value=1, max_value=99, step=1, key="new_numero", disabled=not is_admin)
                    foto_file = st.file_uploader("Carica Foto", type=["jpg", "jpeg", "png"], key="new_foto", disabled=not is_admin)
                    
                    col_nb1, col_nb2 = st.columns(2)
                    with col_nb1:
                        if st.button("Aggiungi Atleta", type="primary", disabled=not is_admin):
                            if nome and cognome:
                                foto_b64 = file_to_base64(foto_file) if foto_file else None
                                db.aggiungi_atleta(nome, cognome, ruolo, numero, squadra_id, foto_base64=foto_b64)
                                st.session_state.modo_nuovo_atleta = False
                                st.success("Atleta salvato!")
                                st.rerun()
                            else:
                                st.warning("Inserisci nome e cognome.")
                    with col_nb2:
                        if atleti:
                            if st.button("Annulla"):
                                st.session_state.modo_nuovo_atleta = False
                                st.rerun()

            with col_list:
                if atleta_id_scelto:
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        with st.expander("📝 Dati Anagrafici"):
                            curr = db.ottieni_dati_atleta_completi(atleta_id_scelto)
                            if curr:
                                dn = st.text_input("Data Nascita (GG/MM/AAAA)", value=curr[5] or "", key=f"dn_{atleta_id_scelto}", disabled=not is_admin)
                                ln = st.text_input("Luogo Nascita", value=curr[6] or "", key=f"ln_{atleta_id_scelto}", disabled=not is_admin)
                                cf = st.text_input("Codice Fiscale", value=curr[7] or "", key=f"cf_{atleta_id_scelto}", disabled=not is_admin)
                                ind = st.text_input("Indirizzo", value=curr[8] or "", key=f"ind_{atleta_id_scelto}", disabled=not is_admin)
                                cit = st.text_input("Città", value=curr[9] or "", key=f"cit_{atleta_id_scelto}", disabled=not is_admin)
                                cap = st.text_input("CAP", value=curr[10] or "", key=f"cap_{atleta_id_scelto}", disabled=not is_admin)
                                naz = st.text_input("Nazionalità", value=curr[11] or "", key=f"naz_{atleta_id_scelto}", disabled=not is_admin)
                                vis = st.text_input("Scadenza Visita (GG/MM/AAAA)", value=curr[12] or "", key=f"vis_{atleta_id_scelto}", disabled=not is_admin)
                                
                                if st.button("Aggiorna Anagrafica", disabled=not is_admin):
                                    db.aggiorna_anagrafica_atleta(atleta_id_scelto, dn, ln, cf, ind, cit, cap, naz, vis)
                                    st.success("Anagrafica aggiornata!")
                                    st.rerun()

                    with col_btn2:
                        with st.expander("📊 Dati Antropometrici"):
                            st.write("**Registra Nuova Rilevazione**")
                            data_ril = st.date_input("Data Rilevazione", key=f"dt_ril_{atleta_id_scelto}", disabled=not is_admin).strftime("%d/%m/%Y")
                            
                            col_a1, col_a2 = st.columns(2)
                            with col_a1:
                                alt = st.number_input("Altezza (cm)", value=0.0, step=0.5, key=f"alt_{atleta_id_scelto}", disabled=not is_admin)
                            with col_a2:
                                peso = st.number_input("Peso (kg)", value=0.0, step=0.5, key=f"peso_{atleta_id_scelto}", disabled=not is_admin)
                            
                            st.markdown("---")
                            
                            st.write("**Test Salto Attacco**")
                            c_r1, c_v1, c_j1 = st.columns(3)
                            with c_r1:
                                r1 = st.number_input("Reach 1 (cm)", value=0.0, step=1.0, key=f"r1_{atleta_id_scelto}", disabled=not is_admin)
                            with c_v1:
                                v1 = st.number_input("Vertec 1 (cm)", value=0.0, step=1.0, key=f"v1_{atleta_id_scelto}", disabled=not is_admin)
                            
                            j1 = v1 - r1 if (v1 > 0 and r1 > 0) else 0.0
                            with c_j1:
                                st.number_input("Jump 1 (cm)", value=float(j1), disabled=True, key=f"j1_{atleta_id_scelto}")

                            st.write("**Test Salto Muro**")
                            c_r2, c_v2, c_j2 = st.columns(3)
                            with c_r2:
                                r2 = st.number_input("Reach 2 (cm)", value=0.0, step=1.0, key=f"r2_{atleta_id_scelto}", disabled=not is_admin)
                            with c_v2:
                                v2 = st.number_input("Vertec 2 (cm)", value=0.0, step=1.0, key=f"v2_{atleta_id_scelto}", disabled=not is_admin)
                            
                            j2 = v2 - r2 if (v2 > 0 and r2 > 0) else 0.0
                            with c_j2:
                                st.number_input("Jump 2 (cm)", value=float(j2), disabled=True, key=f"j2_{atleta_id_scelto}")

                            st.markdown("---")
                            
                            diff_jump = j1 - j2
                            st.number_input("Differenziale (Jump 1 - Jump 2)", value=float(diff_jump), disabled=True, key=f"diff_{atleta_id_scelto}")

                            if st.button("Salva Rilevazione", type="primary", disabled=not is_admin):
                                db.aggiungi_antropometria(
                                    atleta_id_scelto, data_ril, alt, peso, 
                                    r1, v1, j1, r2, v2, j2
                                )
                                st.success("Misurazione registrata con successo!")
                                st.rerun()
                            
                            st.divider()
                            st.write("**Storico Rilevazioni**")
                            ant_data = db.ottieni_antropometria_atleta(atleta_id_scelto)
                            if ant_data:
                                df_ant = pd.DataFrame(
                                    ant_data, 
                                    columns=["ID", "Data", "Altezza (cm)", "Peso (kg)", "Reach 1", "Vertec 1", "Jump 1", "Reach 2", "Vertec 2", "Jump 2"]
                                )
                                df_ant["Diff."] = df_ant["Jump 1"] - df_ant["Jump 2"]
                                
                                st.dataframe(
                                    df_ant[["Data", "Altezza (cm)", "Peso (kg)", "Reach 1", "Vertec 1", "Jump 1", "Reach 2", "Vertec 2", "Jump 2", "Diff."]], 
                                    use_container_width=True
                                )

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("❌ Elimina Atleta", type="primary", disabled=not is_admin):
                        db.elimina_atleta(atleta_id_scelto)
                        st.session_state.pop("select_atleta_attivo", None)
                        st.success("Atleta eliminato.")
                        st.rerun()
        else:
            st.info("Nessun atleta presente in questa squadra.")

st.title("📊 Generatore di Report Personalizzati")
st.write("Seleziona esattamente i singoli campi che desideri includere nel tuo report personalizzato ed esportali in Excel o PDF.")

# 1. Recupero dati da Supabase
dati_atleti = db.ottieni_tutti_atleti_completi()
dati_antropometria = db.ottieni_tutte_antropometrie_complete()

if dati_atleti:
    # Creazione dei dataframe base
    cols_atl = ["ID", "Nome", "Cognome", "Ruolo", "Numero", "Squadra", "Categoria", 
                "Data Nascita", "Luogo Nascita", "Codice Fiscale", "Indirizzo", "Città", "CAP", "Nazionalità", "Scadenza Visita"]
    df_atl = pd.DataFrame(dati_atleti, columns=cols_atl)

    if dati_antropometria:
        cols_ant = ["ID_Ant", "Cognome", "Nome", "Squadra", "Data Rilevazione", "Altezza", "Peso", 
                    "Reach Attacco", "Vertec Attacco", "Jump Attacco", 
                    "Reach Muro", "Vertec Muro", "Jump Muro"]
        df_ant = pd.DataFrame(dati_antropometria, columns=cols_ant)
        
        # Calcolo dei Differenziali
        df_ant["Diff. Attacco"] = pd.to_numeric(df_ant["Jump Attacco"], errors='coerce') - pd.to_numeric(df_ant["Reach Attacco"], errors='coerce')
        df_ant["Diff. Muro"] = pd.to_numeric(df_ant["Jump Muro"], errors='coerce') - pd.to_numeric(df_ant["Reach Muro"], errors='coerce')
        
        # Unione dati anagrafici e antropometrici
        df_merged = pd.merge(df_atl, df_ant, on=["Cognome", "Nome", "Squadra"], how="left")
    else:
        df_merged = df_atl

    st.markdown("---")
    
    # 2. Selezione granulare dei campi tramite Checkbox divise per colonne
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 🏐 Squadra & Ruolo")
        inc_squadra = st.checkbox("Squadra", value=True)
        inc_categoria = st.checkbox("Categoria", value=True)
        inc_ruolo = st.checkbox("Ruolo", value=True)
        inc_numero = st.checkbox("Numero Maglia", value=True)

    with col2:
        st.markdown("### 👤 Dati Anagrafici")
        inc_dn = st.checkbox("Data di Nascita", value=False)
        inc_ln = st.checkbox("Luogo di Nascita", value=False)
        inc_cf = st.checkbox("Codice Fiscale", value=False)
        inc_naz = st.checkbox("Nazionalità", value=False)
        inc_visita = st.checkbox("Scadenza Visita Medica", value=True)

    with col3:
        st.markdown("### 🏠 Contatti")
        inc_ind = st.checkbox("Indirizzo", value=False)
        inc_cit = st.checkbox("Città", value=False)
        inc_cap = st.checkbox("CAP", value=False)

    with col4:
        st.markdown("### 📏 Antropometria & Salti")
        inc_data_ant = st.checkbox("Data Rilevazione", value=False)
        inc_alt = st.checkbox("Altezza (cm)", value=True)
        inc_peso = st.checkbox("Peso (kg)", value=True)
        inc_r_att = st.checkbox("Reach Attacco", value=False)
        inc_v_att = st.checkbox("Vertec Attacco", value=False)
        inc_j_att = st.checkbox("Jump Attacco", value=True)
        inc_d_att = st.checkbox("Diff. Attacco (Elevazione)", value=True)
        inc_r_mur = st.checkbox("Reach Muro", value=False)
        inc_v_mur = st.checkbox("Vertec Muro", value=False)
        inc_j_mur = st.checkbox("Jump Muro", value=True)
        inc_d_mur = st.checkbox("Diff. Muro (Elevazione)", value=True)

    # 3. Costruzione dinamica della lista colonne
    colonne_selezionate = ["Cognome", "Nome"]

    # Squadra & Ruolo
    if inc_squadra: colonne_selezionate.append("Squadra")
    if inc_categoria: colonne_selezionate.append("Categoria")
    if inc_ruolo: colonne_selezionate.append("Ruolo")
    if inc_numero: colonne_selezionate.append("Numero")

    # Anagrafica
    if inc_dn: colonne_selezionate.append("Data Nascita")
    if inc_ln: colonne_selezionate.append("Luogo Nascita")
    if inc_cf: colonne_selezionate.append("Codice Fiscale")
    if inc_naz: colonne_selezionate.append("Nazionalità")
    if inc_visita: colonne_selezionate.append("Scadenza Visita")

    # Contatti
    if inc_ind: colonne_selezionate.append("Indirizzo")
    if inc_cit: colonne_selezionate.append("Città")
    if inc_cap: colonne_selezionate.append("CAP")

    # Antropometria & Salti
    if dati_antropometria:
        if inc_data_ant: colonne_selezionate.append("Data Rilevazione")
        if inc_alt: colonne_selezionate.append("Altezza")
        if inc_peso: colonne_selezionate.append("Peso")
        if inc_r_att: colonne_selezionate.append("Reach Attacco")
        if inc_v_att: colonne_selezionate.append("Vertec Attacco")
        if inc_j_att: colonne_selezionate.append("Jump Attacco")
        if inc_d_att: colonne_selezionate.append("Diff. Attacco")
        if inc_r_mur: colonne_selezionate.append("Reach Muro")
        if inc_v_mur: colonne_selezionate.append("Vertec Muro")
        if inc_j_mur: colonne_selezionate.append("Jump Muro")
        if inc_d_mur: colonne_selezionate.append("Diff. Muro")

    # 4. Filtraggio dati ed Anteprima
    df_report = df_merged[colonne_selezionate].fillna("-")

    st.markdown("---")
    st.subheader(f"📋 Anteprima Report ({len(df_report)} atleti)")
    st.dataframe(df_report, use_container_width=True)

    # 5. Pulsanti di Esportazione (Excel + PDF)
    col_exp1, col_exp2 = st.columns(2)

    # --- ESPORTAZIONE EXCEL ---
    with col_exp1:
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df_report.to_excel(writer, index=False, sheet_name='Report Personalizzato')
        excel_data = output_excel.getvalue()

        st.download_button(
            label="📥 Scarica Report Excel (.xlsx)",
            data=excel_data,
            file_name="report_personalizzato_pallavolo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # --- ESPORTAZIONE PDF (tramite WeasyPrint) ---
    with col_exp2:
        from weasyprint import HTML

        # Costruzione HTML per la tabella PDF
        html_headers = "".join([f"<th>{col}</th>" for col in df_report.columns])
        html_rows = ""
        for _, row in df_report.iterrows():
            html_rows += "<tr>" + "".join([f"<td>{val}</td>" for val in row]) + "</tr>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4 landscape;
                    margin: 12mm;
                    background-color: #ffffff;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 9pt;
                    color: #333333;
                    margin: 0;
                    padding: 0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #1e3a8a;
                    padding-bottom: 8px;
                }}
                h1 {{
                    color: #1e3a8a;
                    font-size: 16pt;
                    margin: 0 0 5px 0;
                }}
                .meta {{
                    font-size: 8pt;
                    color: #666666;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                th {{
                    background-color: #1e3a8a;
                    color: #ffffff;
                    font-weight: bold;
                    padding: 6px 8px;
                    text-align: left;
                    font-size: 8.5pt;
                    border: 1px solid #1e3a8a;
                }}
                td {{
                    padding: 5px 8px;
                    border: 1px solid #e2e8f0;
                    font-size: 8pt;
                }}
                tr:nth-child(even) {{
                    background-color: #f8fafc;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Report Personalizzato Pallavolo</h1>
                <div class="meta">Data generazione: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Totale atleti: {len(df_report)}</div>
            </div>
            <table>
                <thead>
                    <tr>{html_headers}</tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html_content).write_pdf()

        st.download_button(
            label="📄 Scarica Report PDF (.pdf)",
            data=pdf_bytes,
            file_name="report_personalizzato_pallavolo.pdf",
            mime="application/pdf",
            use_container_width=True
        )

else:
    st.info("Nessun atleta presente nel database per generare il report.")