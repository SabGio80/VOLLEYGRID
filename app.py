import io
import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from database import Database
from streamlit_drawable_canvas import st_canvas

# Import ReportLab per l'esportazione PDF
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Gestionale Pallavolo Web", layout="wide")

db = Database()
db.inizializza_db()

# --- GESTIONE LOGIN E RUOLI ---
def verifica_login(username, password):
    if hasattr(db, 'verifica_utente'):
        return db.verifica_utente(username, password)
    
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
tabs = ["Gestione Squadre", "Rosa Atleti", "Programmazione Allenamenti", "Reportistica"]

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

# ==========================================
# --- TAB 1: GESTIONE SQUADRE ---
# ==========================================
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

# ==========================================
# --- TAB 2: ROSA ATLETI ---
# ==========================================
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
                                st.success("Salvato!")
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

# ==========================================
# --- TAB 3: PROGRAMMAZIONE ALLENAMENTI & LAVAGNA TATTICA ---
# ==========================================
elif st.session_state.active_tab == "Programmazione Allenamenti":
    st.title("📋 Programmazione Allenamenti & Lavagna Tattica")
    
    if not squadra_id:
        st.info("Seleziona una squadra in alto per definire il programma delle sedute.")
    else:
        # Recupero atleti per la gestione presenze
        atleti_squadra = db.ottieni_atleti_per_squadra(squadra_id)
        lista_atleti_nomi = [f"{a[0]} - {a[1]} {a[2]}" for a in atleti_squadra] if atleti_squadra else []

        # Inizializzazione archivio esercizi con schemi
        if "archivio_esercizi" not in st.session_state:
            st.session_state.archivio_esercizi = []

        # Inizializzazione sedute
        if "progr_sedute" not in st.session_state:
            st.session_state.progr_sedute = [
                {
                    "Seduta": "SEDUTA 1", 
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Ora Inizio": "18:00",
                    "Ora Fine": "20:00",
                    "Luogo": "Palazzetto dello Sport",
                    "Focus Tecnica": "TECNICA MURO", 
                    "Focus Tattica": "FASE PALLA SCONTATA",
                    "Presenti": lista_atleti_nomi.copy(),
                    "Esercizi": [
                        {"Fase": "WARMUP", "Esercizio": "Attivazione dinamica", "Tempo (min)": 15, "Note": "Palla da allenamento"},
                        {"Fase": "TECNICA", "Esercizio": "Spostamento muro + difesa", "Tempo (min)": 40, "Note": "3 gruppi da 4"}
                    ]
                }
            ]

        # Sotto-schede: Programmazione Sedute vs Creazione Esercizi/Schemi
        tab_sedute, tab_creatore = st.tabs(["📅 Gestione Sedute & Presenze", "✏️ Creatore Esercizi & Campo Tattico"])

        # -------------------------------------------------------------------
        # SUB-TAB 1: GESTIONE SEDUTE, ORA, LUOGO E PRESENZE
        # -------------------------------------------------------------------
        with tab_sedute:
            col_p1, col_p2 = st.columns([1, 2])

            with col_p1:
                st.subheader("➕ Aggiungi Nuova Seduta")
                n_seduta = st.text_input("Nome Seduta", value=f"SEDUTA {len(st.session_state.progr_sedute) + 1}")
                d_seduta = st.date_input("Data Seduta").strftime("%d/%m/%Y")
                
                c_ora1, c_ora2 = st.columns(2)
                with c_ora1:
                    ora_in = st.time_input("Ora Inizio", value=datetime.strptime("18:00", "%H:%M").time()).strftime("%H:%M")
                with c_ora2:
                    ora_fi = st.time_input("Ora Fine", value=datetime.strptime("20:00", "%H:%M").time()).strftime("%H:%M")
                
                luogo_sed = st.text_input("Luogo / Palestra", value="Palazzetto dello Sport")
                f_tecnica = st.text_input("Focus Tecnico Main", value="TECNICA MURO")
                f_tattica = st.text_input("Focus Tattico / Sistema", value="FASE PALLA SCONTATA")
                
                presenti_default = st.multiselect("Atleti Convocati/Presenti", options=lista_atleti_nomi, default=lista_atleti_nomi)

                if st.button("Aggiungi Seduta", type="primary", disabled=not is_admin):
                    st.session_state.progr_sedute.append({
                        "Seduta": n_seduta,
                        "Data": d_seduta,
                        "Ora Inizio": ora_in,
                        "Ora Fine": ora_fi,
                        "Luogo": luogo_sed,
                        "Focus Tecnica": f_tecnica,
                        "Focus Tattica": f_tattica,
                        "Presenti": presenti_default,
                        "Esercizi": [
                            {"Fase": "WARMUP", "Esercizio": "Attivazione", "Tempo (min)": 15, "Note": ""},
                            {"Fase": "TECNICA", "Esercizio": "", "Tempo (min)": 30, "Note": ""}
                        ]
                    })
                    st.success("Seduta aggiunta con successo!")
                    st.rerun()

            col_list_sedute = col_p2
            with col_list_sedute:
                st.subheader("📅 Schede Sedute Programmate")
                
                for idx, seduta in enumerate(st.session_state.progr_sedute):
                    titolo_exp = f"📌 {seduta['Seduta']} - {seduta['Data']} ({seduta.get('Ora Inizio','--')} - {seduta.get('Ora Fine','--')}) | {seduta.get('Luogo','')}"
                    
                    with st.expander(titolo_exp, expanded=(idx == 0)):
                        # Logistica
                        c_l1, c_l2, c_l3 = st.columns(3)
                        with c_l1:
                            seduta['Luogo'] = st.text_input("Luogo", value=seduta.get('Luogo', ''), key=f"luogo_{idx}", disabled=not is_admin)
                        with c_l2:
                            seduta['Ora Inizio'] = st.text_input("Ora Inizio", value=seduta.get('Ora Inizio', '18:00'), key=f"oin_{idx}", disabled=not is_admin)
                        with c_l3:
                            seduta['Ora Fine'] = st.text_input("Ora Fine", value=seduta.get('Ora Fine', '20:00'), key=f"ofi_{idx}", disabled=not is_admin)

                        # Focus
                        c_s1, c_s2 = st.columns(2)
                        with c_s1:
                            seduta['Focus Tecnica'] = st.text_input("Focus Tecnico", value=seduta['Focus Tecnica'], key=f"ft_{idx}", disabled=not is_admin)
                        with c_s2:
                            seduta['Focus Tattica'] = st.text_input("Focus Tattico", value=seduta['Focus Tattica'], key=f"ftat_{idx}", disabled=not is_admin)

                        # Presenze Atleti
                        st.write("👥 **Atleti Presenti:**")
                        seduta['Presenti'] = st.multiselect(
                            "Seleziona Atleti Presenti",
                            options=lista_atleti_nomi,
                            default=seduta.get('Presenti', []),
                            key=f"pres_{idx}",
                            disabled=not is_admin
                        )

                        # Inserimento rapido da Archivio Esercizi Creati
                        if st.session_state.archivio_esercizi:
                            st.write("📥 **Importa Esercizio da Archivio Tattico:**")
                            c_ex_sel, c_ex_btn = st.columns([3, 1])
                            with c_ex_sel:
                                ex_scelto_idx = st.selectbox(
                                    "Seleziona esercizio salvato", 
                                    options=range(len(st.session_state.archivio_esercizi)),
                                    format_func=lambda i: st.session_state.archivio_esercizi[i]['nome'],
                                    key=f"sel_arch_{idx}"
                                )
                            with c_ex_btn:
                                st.write("")
                                st.write("")
                                if st.button("Importa", key=f"btn_imp_{idx}", disabled=not is_admin):
                                    obj_ex = st.session_state.archivio_esercizi[ex_scelto_idx]
                                    seduta["Esercizi"].append({
                                        "Fase": obj_ex["fase"],
                                        "Esercizio": obj_ex["nome"],
                                        "Tempo (min)": obj_ex["durata"],
                                        "Note": obj_ex["descrizione"]
                                    })
                                    st.success("Esercizio inserito!")
                                    st.rerun()

                        # Tabella Esercizi Seduta
                        st.write("**Dettaglio Esercizi & Fasi:**")
                        df_ex = pd.DataFrame(seduta["Esercizi"])
                        
                        edited_ex = st.data_editor(
                            df_ex,
                            num_rows="dynamic",
                            use_container_width=True,
                            key=f"editor_seduta_{idx}",
                            disabled=not is_admin
                        )
                        seduta["Esercizi"] = edited_ex.to_dict(orient="records")
                        
                        if is_admin and st.button(f"🗑️ Elimina {seduta['Seduta']}", key=f"del_sed_{idx}"):
                            st.session_state.progr_sedute.pop(idx)
                            st.rerun()

# -------------------------------------------------------------------
        # SUB-TAB 2: CREATORE ESERCIZI & CAMPO DA PALLAVOLO (VERSIONE STABILE)
        # -------------------------------------------------------------------
        with tab_creatore:
            st.subheader("✏️ Lavagna Tattica & Disegno Schemi")
            st.caption("Campo fisso di sfondo e oggetti orientabili (Pedine, Frecce, Palloni).")

            from PIL import Image, ImageDraw
            import streamlit_drawable_canvas as sdc

            # 1. Generatore Immagine di Sfondo del Campo (TOTALMENTE FISSO)
            @st.cache_data
            def get_volleyball_field_image():
                img = Image.new("RGB", (600, 400), color="#D2691E")
                draw = ImageDraw.Draw(img)
                # Bordo perimetrale
                draw.rectangle([30, 30, 570, 370], outline="white", width=4)
                # Linea centrale / Rete
                draw.line([(300, 30), (300, 370)], fill="white", width=4)
                # Linee d'attacco 3 metri
                draw.line([(210, 30), (210, 370)], fill="white", width=2)
                draw.line([(390, 30), (390, 370)], fill="white", width=2)
                return img

            bg_image = get_volleyball_field_image()

            # Gestione Stato Oggetti Canvas
            if "canvas_objects" not in st.session_state:
                st.session_state.canvas_objects = []

            # Se l'utente interagisce col canvas, aggiorniamo la lista oggetti
            def salva_stato_corrente():
                if "last_canvas_data" in st.session_state and st.session_state.last_canvas_data:
                    if "objects" in st.session_state.last_canvas_data:
                        st.session_state.canvas_objects = st.session_state.last_canvas_data["objects"]

            # 2. Pulsantiera Inserimento Oggetti Pronti (Pedine, Frecce, Pallone)
            st.write("📌 **Inserisci Elementi sul Campo:**")
            col_p1, col_p2, col_p3, col_p4, col_p5, col_p6, col_p7, col_p8 = st.columns(8)

            def aggiungi_gruppo_canvas(obj_json):
                salva_stato_corrente()
                st.session_state.canvas_objects.append(obj_json)
                st.rerun()

            def aggiungi_pedina(ruolo, colore_sfondo):
                semicircle_path = "M 0 25 L 50 25 A 25 25 0 0 0 0 25 Z"
                pedina = {
                    "type": "group", "left": 275, "top": 185, "width": 50, "height": 30,
                    "objects": [
                        {"type": "path", "path": semicircle_path, "fill": colore_sfondo, "stroke": "#FFFFFF", "strokeWidth": 2, "left": -25, "top": -15},
                        {"type": "textbox", "text": ruolo, "fontSize": 16, "fontWeight": "bold", "fill": "#FFFFFF", "textAlign": "center", "left": -7, "top": -8, "width": 20}
                    ],
                    "hasControls": True, "selectable": True
                }
                aggiungi_gruppo_canvas(pedina)

            def aggiungi_freccia_oggetto(colore="#FFFF00"):
                # Freccia pronta (asta + punta) che l'utente può ruotare/ridimensionare a piacere
                freccia = {
                    "type": "group", "left": 250, "top": 180, "width": 100, "height": 30,
                    "objects": [
                        {"type": "line", "x1": -50, "y1": 0, "x2": 35, "y2": 0, "stroke": colore, "strokeWidth": 5},
                        {"type": "polygon", "points": [{"x": 35, "y": -10}, {"x": 50, "y": 0}, {"x": 35, "y": 10}], "fill": colore}
                    ],
                    "hasControls": True, "selectable": True
                }
                aggiungi_gruppo_canvas(freccia)

            def aggiungi_pallone():
                palla = {
                    "type": "circle", "left": 285, "top": 185, "radius": 12,
                    "fill": "#FFD700", "stroke": "#000000", "strokeWidth": 2,
                    "hasControls": True, "selectable": True
                }
                aggiungi_gruppo_canvas(palla)

            if col_p1.button("➕ **A**"): aggiungi_pedina("A", "#1E90FF")
            if col_p2.button("➕ **O**"): aggiungi_pedina("O", "#FF4500")
            if col_p3.button("➕ **S**"): aggiungi_pedina("S", "#2E8B57")
            if col_p4.button("➕ **C**"): aggiungi_pedina("C", "#8A2BE2")
            if col_p5.button("➕ **L**"): aggiungi_pedina("L", "#FFA500")
            if col_p6.button("➕ **T**"): aggiungi_pedina("T", "#333333")
            if col_p7.button("➡️ **Freccia**"): aggiungi_freccia_oggetto()
            if col_p8.button("🏐 **Palla**"): aggiungi_pallone()

            # 3. Controlli Disegno Manuale e Opzioni Canvas
            col_tools, col_space = st.columns([3, 1])
            with col_tools:
                strumenti_map = {
                    "Sposta / Ruota / Ridimensiona": "transform",
                    "Disegno Libero (Mano libera)": "freedraw",
                    "Linea Retta": "line",
                    "Cerchio / Zona": "circle",
                    "Rettangolo / Zona": "rect"
                }
                c_t1, c_t2, c_t3, c_t4 = st.columns(4)
                with c_t1:
                    strumento_scelto = st.selectbox("Modalità:", list(strumenti_map.keys()), key="draw_mode_label")
                    drawing_mode = strumenti_map[strumento_scelto]
                with c_t2:
                    stroke_color = st.color_picker("Colore:", "#FFFF00", key="stroke_clr")
                with c_t3:
                    stroke_width = st.slider("Spessore:", 1, 10, 3, key="stroke_w")
                with c_t4:
                    if st.button("🔄 **Pulisci Tutto**", type="secondary"):
                        st.session_state.canvas_objects = []
                        st.session_state.last_canvas_data = None
                        st.rerun()

            col_canv, col_info_ex = st.columns([3, 2])

            with col_canv:
                initial_json = {"objects": st.session_state.canvas_objects}

                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0.2)",
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    background_image=bg_image,
                    height=400,
                    width=600,
                    drawing_mode=drawing_mode,
                    initial_drawing=initial_json,
                    key="volleyball_board_v10"
                )

                if canvas_result and canvas_result.json_data:
                    st.session_state.last_canvas_data = canvas_result.json_data

            with col_info_ex:
                st.subheader("💾 Salva in Archivio Esercizi")
                ex_nome = st.text_input("Nome Esercizio", key="ex_nome_input", disabled=not is_admin)
                ex_fase = st.selectbox("Fase di Gioco", ["WARMUP", "TECNICA", "SISTEMA", "SITUAZIONALE", "DEFENSE/MURO", "GLOBAL"], key="ex_fase_input", disabled=not is_admin)
                ex_durata = st.number_input("Durata Stimata (min)", min_value=5, max_value=120, value=20, step=5, key="ex_durata_input", disabled=not is_admin)
                ex_desc = st.text_area("Descrizione / Regole / Obiettivi", key="ex_desc_input", disabled=not is_admin)

                if st.button("💾 Salva Schema & Esercizio", type="primary", disabled=not is_admin):
                    if ex_nome:
                        st.session_state.archivio_esercizi.append({
                            "nome": ex_nome,
                            "fase": ex_fase,
                            "durata": ex_durata,
                            "descrizione": ex_desc,
                            "canvas_data": canvas_result.json_data if canvas_result else None
                        })
                        st.success(f"Esercizio '{ex_nome}' registrato nell'archivio!")
                    else:
                        st.warning("Inserisci il nome dell'esercizio.")

# ==========================================
# --- TAB 4: REPORTISTICA & ESPORTAZIONE PDF ---
# ==========================================
elif st.session_state.active_tab == "Reportistica":
    st.title("📊 Reportistica & Esportazione Documenti PDF")

    if not squadra_id:
        st.info("Seleziona una squadra in alto per poter generare i report.")
    else:
        st.markdown("Genera e scarica i report PDF ufficiali della rosa completa o delle sedute di allenamento programmate.")

        tab_rep_atleti, tab_rep_allenamento = st.tabs(["📄 Report Rosa Atleti", "📄 Report Sedute Allenamento"])

        # -------------------------------------------------------------------
        # REPORT 1: ROSA ATLETI (PDF)
        # -------------------------------------------------------------------
        with tab_rep_atleti:
            st.subheader("Stampa Scheda Rosa Squadra")
            
            atleti_rep = db.ottieni_atleti_per_squadra(squadra_id)
            if atleti_rep:
                df_rep_atleti = pd.DataFrame(atleti_rep, columns=["N° Maglia", "Cognome", "Nome", "Ruolo", "ID Database", "Foto"])
                st.dataframe(df_rep_atleti[["N° Maglia", "Cognome", "Nome", "Ruolo"]], use_container_width=True, hide_index=True)

                if st.button("🖨️ Genera Report PDF Rosa", type="primary"):
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                    elements = []

                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(name="TitleStyle", fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=1, spaceAfter=20)
                    header_style = ParagraphStyle(name="HeaderStyle", fontName="Helvetica-Bold", fontSize=12, leading=14)
                    cell_style = ParagraphStyle(name="CellStyle", fontName="Helvetica", fontSize=10, leading=12)

                    elements.append(Paragraph(f"ROSA SQUADRA: {squadra_scelta}", title_style))
                    elements.append(Paragraph(f"Stagione Agonistica: {stagione_scelta}", styles["SubTitle"]))
                    elements.append(Spacer(1, 15))

                    data_table = [["N°", "Cognome", "Nome", "Ruolo"]]
                    for a in atleti_rep:
                        data_table.append([
                            Paragraph(str(a[0]), cell_style),
                            Paragraph(str(a[1]), cell_style),
                            Paragraph(str(a[2]), cell_style),
                            Paragraph(str(a[3]), cell_style)
                        ])

                    table = Table(data_table, colWidths=[40, 160, 160, 140])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F3F4F6")),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                    ]))

                    elements.append(table)
                    doc.build(elements)
                    buffer.seek(0)

                    st.download_button(
                        label="⬇️ Scarica PDF Rosa Squadra",
                        data=buffer,
                        file_name=f"Rosa_{squadra_scelta.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("Nessun atleta registrato in questa squadra.")

        # -------------------------------------------------------------------
        # REPORT 2: SEDUTA ALLENAMENTO (PDF)
        # -------------------------------------------------------------------
        with tab_rep_allenamento:
            st.subheader("Stampa Schede Allenamento")

            if "progr_sedute" in st.session_state and st.session_state.progr_sedute:
                idx_sed = st.selectbox(
                    "Seleziona Seduta da esportare in PDF:", 
                    options=range(len(st.session_state.progr_sedute)),
                    format_func=lambda i: f"{st.session_state.progr_sedute[i]['Seduta']} ({st.session_state.progr_sedute[i]['Data']})"
                )

                seduta_target = st.session_state.progr_sedute[idx_sed]

                if st.button("🖨️ Genera Scheda Seduta PDF", type="primary"):
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                    elements = []

                    styles = getSampleStyleSheet()
                    t_style = ParagraphStyle(name="TStyle", fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=10)
                    sub_style = ParagraphStyle(name="SubStyle", fontName="Helvetica-Bold", fontSize=12, leading=15, spaceAfter=5)
                    body_style = ParagraphStyle(name="BStyle", fontName="Helvetica", fontSize=10, leading=13)

                    elements.append(Paragraph(f"SCHEDA ALLENAMENTO: {seduta_target['Seduta']}", t_style))
                    elements.append(Paragraph(f"<b>Data:</b> {seduta_target['Data']} | <b>Ora:</b> {seduta_target.get('Ora Inizio','--')} - {seduta_target.get('Ora Fine','--')}", body_style))
                    elements.append(Paragraph(f"<b>Palestra:</b> {seduta_target.get('Luogo','')}", body_style))
                    elements.append(Spacer(1, 10))

                    elements.append(Paragraph(f"<b>Focus Tecnico:</b> {seduta_target.get('Focus Tecnica','')}", body_style))
                    elements.append(Paragraph(f"<b>Focus Tattico:</b> {seduta_target.get('Focus Tattica','')}", body_style))
                    elements.append(Spacer(1, 10))

                    # Sezione Presenze
                    pres_str = ", ".join(seduta_target.get('Presenti', [])) if seduta_target.get('Presenti') else "Nessuno specificato"
                    elements.append(Paragraph(f"<b>Atleti Convocati/Presenti:</b> {pres_str}", body_style))
                    elements.append(Spacer(1, 15))

                    # Tabella Esercizi
                    elements.append(Paragraph("Dettaglio Fasi ed Esercizi", sub_style))
                    ex_data = [["Fase", "Esercizio", "Min", "Note"]]
                    for item in seduta_target.get("Esercizi", []):
                        ex_data.append([
                            Paragraph(str(item.get("Fase", "")), body_style),
                            Paragraph(str(item.get("Esercizio", "")), body_style),
                            Paragraph(str(item.get("Tempo (min)", "")), body_style),
                            Paragraph(str(item.get("Note", "")), body_style)
                        ])

                    table_ex = Table(ex_data, colWidths=[80, 180, 40, 200])
                    table_ex.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0D9488")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                    ]))

                    elements.append(table_ex)
                    doc.build(elements)
                    buffer.seek(0)

                    st.download_button(
                        label="⬇️ Scarica Scheda Seduta (PDF)",
                        data=buffer,
                        file_name=f"Seduta_{seduta_target['Seduta'].replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.info("Nessuna seduta attualmente in programmazione.")