from supabase import create_client, Client

SUPABASE_URL = "https://ydsbzhlwxojgwiqlnlcq.supabase.co"
SUPABASE_KEY = "sb_publishable_EBe_zY3gcaChaRydWfs1Hw_PRCuUyFR"

class Database:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def inizializza_db(self):
        """Metodo mantenuto per compatibilità con app.py"""
        pass

    # --- STAGIONI ---
    def aggiungi_stagione(self, nome):
        try:
            self.supabase.table("stagioni").insert({"nome": nome}).execute()
            return True
        except Exception:
            return False

    def ottieni_stagioni(self):
        res = self.supabase.table("stagioni").select("id, nome").order("nome", desc=True).execute()
        return [(item["id"], item["nome"]) for item in res.data]

    # --- SQUADRE ---
    def aggiungi_squadra(self, nome, categoria, stagione_id):
        self.supabase.table("squadre").insert({
            "nome": nome, "categoria": categoria, "stagione_id": stagione_id
        }).execute()

    def modifica_squadra(self, squadra_id, nome, categoria):
        self.supabase.table("squadre").update({"nome": nome, "categoria": categoria}).eq("id", squadra_id).execute()

    def elimina_squadra(self, squadra_id):
        self.supabase.table("squadre").delete().eq("id", squadra_id).execute()

    def ottieni_squadre_per_stagione(self, stagione_id):
        res = self.supabase.table("squadre").select("id, nome, categoria").eq("stagione_id", stagione_id).execute()
        return [(item["id"], item["nome"], item["categoria"]) for item in res.data]

    # --- ATLETI ---
    def aggiungi_atleta(self, nome, cognome, ruolo, numero, squadra_id, foto_base64=None):
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

    def modifica_atleta(self, atleta_id, nome, cognome, ruolo, numero, foto_base64=None):
        payload = {
            "nome": nome,
            "cognome": cognome,
            "ruolo": ruolo,
            "numero_maglia": numero
        }
        if foto_base64:
            payload["foto"] = foto_base64
            
        self.supabase.table("atleti").update(payload).eq("id", atleta_id).execute()

    def aggiorna_atleta(self, atleta_id, nome, cognome, ruolo, numero, foto_base64=None):
        self.modifica_atleta(atleta_id, nome, cognome, ruolo, numero, foto_base64)

    def aggiorna_anagrafica_atleta(self, atleta_id, dn, ln, cf, ind, cit, cap, naz, vis):
        self.supabase.table("atleti").update({
            "data_nascita": dn, "luogo_nascita": ln, "codice_fiscale": cf,
            "indirizzo": ind, "citta": cit, "cap": cap, "nazionalita": naz, "scadenza_visita": vis
        }).eq("id", atleta_id).execute()

    def elimina_atleta(self, atleta_id):
        self.supabase.table("atleti").delete().eq("id", atleta_id).execute()

    def ottieni_atleti_per_squadra(self, squadra_id):
        res = self.supabase.table("atleti").select("numero_maglia, cognome, nome, ruolo, id, foto").eq("squadra_id", squadra_id).order("numero_maglia").execute()
        return [(i["numero_maglia"], i["cognome"], i["nome"], i["ruolo"], i["id"], i.get("foto")) for i in res.data]

    def ottieni_dati_atleta_completi(self, atleta_id):
        res = self.supabase.table("atleti").select("*").eq("id", atleta_id).execute()
        if res.data:
            i = res.data[0]
            return (
                i["id"], i["nome"], i["cognome"], i["ruolo"], i["numero_maglia"], 
                i.get("data_nascita"), i.get("luogo_nascita"), i.get("codice_fiscale"), 
                i.get("indirizzo"), i.get("citta"), i.get("cap"), i.get("nazionalita"), 
                i.get("scadenza_visita"), i.get("foto")
            )
        return None

    # --- ANTROPOMETRIA ---
    def aggiungi_antropometria(self, atleta_id, data, altezza, peso, r1, v1, j1, r2, v2, j2):
        self.supabase.table("antropometria").insert({
            "atleta_id": atleta_id, "data_rilevazione": data, "altezza": altezza, "peso": peso,
            "reach1": r1, "vertec1": v1, "jump1": j1, "reach2": r2, "vertec2": v2, "jump2": j2
        }).execute()

    def elimina_antropometria(self, ant_id):
        self.supabase.table("antropometria").delete().eq("id", ant_id).execute()

    def ottieni_antropometria_atleta(self, atleta_id):
        res = self.supabase.table("antropometria").select("id, data_rilevazione, altezza, peso, reach1, vertec1, jump1, reach2, vertec2, jump2").eq("atleta_id", atleta_id).order("id", desc=True).execute()
        return [(i["id"], i["data_rilevazione"], i["altezza"], i["peso"], i["reach1"], i["vertec1"], i["jump1"], i["reach2"], i["vertec2"], i["jump2"]) for i in res.data]
def ottieni_tutti_atleti_completi(self):
        """Recupera tutti gli atleti con i dati anagrafici e la squadra associata."""
        cursor = self.conn.cursor()
        query = """
            SELECT 
                a.id, a.nome, a.cognome, a.ruolo, a.numero,
                s.nome AS squadra, s.categoria,
                a.data_nascita, a.luogo_nascita, a.codice_fiscale,
                a.indirizzo, a.citta, a.cap, a.nazionalita, a.scadenza_visita
            FROM atleti a
            LEFT JOIN squadre s ON a.squadra_id = s.id
            ORDER BY s.nome, a.cognome, a.nome
        """
        cursor.execute(query)
        return cursor.fetchall()

    def ottieni_tutte_antropometrie_complete(self):
        """Recupera lo storico di tutte le misurazioni antropometriche e salti con il nome dell'atleta."""
        cursor = self.conn.cursor()
        query = """
            SELECT 
                ant.id, a.cognome, a.nome, s.nome AS squadra,
                ant.data_rilevazione, ant.altezza, ant.peso,
                ant.reach1, ant.vertec1, ant.jump1,
                ant.reach2, ant.vertec2, ant.jump2
            FROM antropometria ant
            JOIN atleti a ON ant.atleta_id = a.id
            LEFT JOIN squadre s ON a.squadra_id = s.id
            ORDER BY ant.data_rilevazione DESC, a.cognome
        """
        cursor.execute(query)
        return cursor.fetchall()