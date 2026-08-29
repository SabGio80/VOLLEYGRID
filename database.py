import os
from supabase import create_client, Client

# Caricamento delle credenziali da variabili d'ambiente o valori di fallback
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ydsbzhlwxojgwiqlnlcq.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_EBe_zY3gcaChaRydWfs1Hw_PRCuUyFR")

class Database:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def inizializza_db(self):
        """Metodo mantenuto per compatibilità con l'applicazione."""
        pass

    # --- STAGIONI ---
    def aggiungi_stagione(self, nome: str) -> bool:
        try:
            self.supabase.table("stagioni").insert({"nome": nome}).execute()
            return True
        except Exception as e:
            print(f"Errore aggiunta stagione: {e}")
            return False

    def ottieni_stagioni(self) -> list:
        try:
            res = self.supabase.table("stagioni").select("id, nome").order("nome", desc=True).execute()
            return [(item["id"], item["nome"]) for item in res.data]
        except Exception as e:
            print(f"Errore recupero stagioni: {e}")
            return []

    # --- SQUADRE ---
    def aggiungi_squadra(self, nome: str, categoria: str, stagione_id: int) -> bool:
        try:
            self.supabase.table("squadre").insert({
                "nome": nome, "categoria": categoria, "stagione_id": stagione_id
            }).execute()
            return True
        except Exception as e:
            print(f"Errore aggiunta squadra: {e}")
            return False

    def modifica_squadra(self, squadra_id: int, nome: str, categoria: str) -> bool:
        try:
            self.supabase.table("squadre").update({"nome": nome, "categoria": categoria}).eq("id", squadra_id).execute()
            return True
        except Exception as e:
            print(f"Errore modifica squadra: {e}")
            return False

    def elimina_squadra(self, squadra_id: int) -> bool:
        try:
            self.supabase.table("squadre").delete().eq("id", squadra_id).execute()
            return True
        except Exception as e:
            print(f"Errore eliminazione squadra: {e}")
            return False

    def ottieni_squadre_per_stagione(self, stagione_id: int) -> list:
        try:
            res = self.supabase.table("squadre").select("id, nome, categoria").eq("stagione_id", stagione_id).execute()
            return [(item["id"], item["nome"], item["categoria"]) for item in res.data]
        except Exception as e:
            print(f"Errore recupero squadre: {e}")
            return []

    # --- ATLETI ---
    def aggiungi_atleta(self, nome: str, cognome: str, ruolo: str, numero: int, squadra_id: int, foto_base64: str = None) -> bool:
        try:
            payload = {
                "nome": nome,
                "cognome": cognome,
                "ruolo": ruolo, 
                "numero_maglia": numero,
                "squadra_id": squadra_id
            }
            if foto_base64:
                payload["foto"] = foto_base64
                
            self.supabase.table("atleti").insert(payload).execute()
            return True
        except Exception as e:
            print(f"Errore aggiunta atleta: {e}")
            return False

    def modifica_atleta(self, atleta_id: int, nome: str, cognome: str, ruolo: str, numero: int, foto_base64: str = None) -> bool:
        try:
            payload = {
                "nome": nome,
                "cognome": cognome,
                "ruolo": ruolo,
                "numero_maglia": numero
            }
            if foto_base64:
                payload["foto"] = foto_base64
                
            self.supabase.table("atleti").update(payload).eq("id", atleta_id).execute()
            return True
        except Exception as e:
            print(f"Errore modifica atleta: {e}")
            return False

    def aggiorna_atleta(self, atleta_id: int, nome: str, cognome: str, ruolo: str, numero: int, foto_base64: str = None) -> bool:
        return self.modifica_atleta(atleta_id, nome, cognome, ruolo, numero, foto_base64)

    def aggiorna_anagrafica_atleta(self, atleta_id: int, dn, ln, cf, ind, cit, cap, naz, vis, tel=None, email=None) -> bool:
        try:
            self.supabase.table("atleti").update({
                "data_nascita": dn, 
                "luogo_nascita": ln, 
                "codice_fiscale": cf,
                "indirizzo": ind, 
                "citta": cit, 
                "cap": cap, 
                "nazionalita": naz, 
                "scadenza_visita": vis,
                "telefono": tel,
                "email": email
            }).eq("id", atleta_id).execute()
            return True
        except Exception as e:
            print(f"Errore aggiornamento anagrafica: {e}")
            return False

    def elimina_atleta(self, atleta_id: int) -> bool:
        try:
            self.supabase.table("atleti").delete().eq("id", atleta_id).execute()
            return True
        except Exception as e:
            print(f"Errore eliminazione atleta: {e}")
            return False

    def ottieni_atleti_per_squadra(self, squadra_id: int) -> list:
        try:
            res = self.supabase.table("atleti").select("numero_maglia, cognome, nome, ruolo, id, foto").eq("squadra_id", squadra_id).order("numero_maglia").execute()
            return [(i["numero_maglia"], i["cognome"], i["nome"], i["ruolo"], i["id"], i.get("foto")) for i in res.data]
        except Exception as e:
            print(f"Errore recupero atleti squadra: {e}")
            return []

    def ottieni_dati_atleta_completi(self, atleta_id: int):
        try:
            res = self.supabase.table("atleti").select("*").eq("id", atleta_id).execute()
            if res.data:
                i = res.data[0]
                return (
                    i["id"], i["nome"], i["cognome"], i["ruolo"], i["numero_maglia"], 
                    i.get("data_nascita"), i.get("luogo_nascita"), i.get("codice_fiscale"), 
                    i.get("indirizzo"), i.get("citta"), i.get("cap"), i.get("nazionalita"), 
                    i.get("scadenza_visita"), i.get("foto"), i.get("email"), i.get("telefono")
                )
            return None
        except Exception as e:
            print(f"Errore recupero dati completi atleta: {e}")
            return None

    # --- ANTROPOMETRIA ---
    def aggiungi_antropometria(self, atleta_id: int, data, altezza, peso, r1, v1, j1, r2, v2, j2) -> bool:
        try:
            self.supabase.table("antropometria").insert({
                "atleta_id": atleta_id, "data_rilevazione": data, "altezza": altezza, "peso": peso,
                "reach1": r1, "vertec1": v1, "jump1": j1, "reach2": r2, "vertec2": v2, "jump2": j2
            }).execute()
            return True
        except Exception as e:
            print(f"Errore inserimento antropometria: {e}")
            return False

    def elimina_antropometria(self, ant_id: int) -> bool:
        try:
            self.supabase.table("antropometria").delete().eq("id", ant_id).execute()
            return True
        except Exception as e:
            print(f"Errore eliminazione antropometria: {e}")
            return False

    def ottieni_antropometria_atleta(self, atleta_id: int) -> list:
        try:
            res = self.supabase.table("antropometria").select(
                "id, data_rilevazione, altezza, peso, reach1, vertec1, jump1, reach2, vertec2, jump2"
            ).eq("atleta_id", atleta_id).order("id", desc=True).execute()
            return [(i["id"], i["data_rilevazione"], i["altezza"], i["peso"], i["reach1"], i["vertec1"], i["jump1"], i["reach2"], i["vertec2"], i["jump2"]) for i in res.data]
        except Exception as e:
            print(f"Errore recupero antropometria: {e}")
            return []

    # --- EXPORT / REPORTS ---
    def ottieni_tutti_atleti_completi(self) -> list:
        try:
            res = self.supabase.table("atleti").select(
                "id, nome, cognome, ruolo, numero_maglia, data_nascita, luogo_nascita, codice_fiscale, indirizzo, citta, cap, nazionalita, scadenza_visita, email, telefono, squadre(nome, categoria)"
            ).execute()
            
            risultati = []
            for i in res.data:
                squadra_info = i.get("squadre") or {}
                sq_nome = squadra_info.get("nome", "")
                sq_cat = squadra_info.get("categoria", "")
                risultati.append((
                    i["id"], i["nome"], i["cognome"], i["ruolo"], i.get("numero_maglia"),
                    sq_nome, sq_cat,
                    i.get("data_nascita"), i.get("luogo_nascita"), i.get("codice_fiscale"),
                    i.get("indirizzo"), i.get("citta"), i.get("cap"), i.get("nazionalita"), 
                    i.get("scadenza_visita"), i.get("email"), i.get("telefono")
                ))
            return risultati
        except Exception as e:
            print(f"Errore recupero report tutti gli atleti: {e}")
            return []

    def ottieni_tutte_antropometrie_complete(self) -> list:
        try:
            res = self.supabase.table("antropometria").select(
                "id, data_rilevazione, altezza, peso, reach1, vertec1, jump1, reach2, vertec2, jump2, atleti(nome, cognome, squadre(nome))"
            ).execute()
            
            risultati = []
            for i in res.data:
                atleta_info = i.get("atleti") or {}
                cognome = atleta_info.get("cognome", "")
                nome = atleta_info.get("nome", "")
                squadra_info = atleta_info.get("squadre") or {}
                sq_nome = squadra_info.get("nome", "")
                
                risultati.append((
                    i["id"], cognome, nome, sq_nome,
                    i.get("data_rilevazione"), i.get("altezza"), i.get("peso"),
                    i.get("reach1"), i.get("vertec1"), i.get("jump1"),
                    i.get("reach2"), i.get("vertec2"), i.get("jump2")
                ))
            return risultati
        except Exception as e:
            print(f"Errore recupero report tutte le antropometrie: {e}")
            return []