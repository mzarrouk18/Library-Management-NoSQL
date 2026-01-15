from cassandra.query import BatchStatement
from datetime import datetime
from click import UUID
from uuid import UUID

def borrow_book(session, user_id, isbn, title):
    try:
        batch = BatchStatement()
        loan_date = datetime.now()

        # 1. Historique utilisateur
        batch.add("INSERT INTO borrows_by_user (user_id, loan_date, isbn, book_title) VALUES (%s, %s, %s, %s)", 
                  (user_id, loan_date, isbn, title))
        # 2. Historique livre
        batch.add("INSERT INTO borrows_by_book (isbn, loan_date, user_id, title) VALUES (%s, %s, %s, %s)", 
                  (isbn, loan_date, user_id, title))
        # 3. Liste des livres sortis (suivi)
        batch.add("INSERT INTO non_returned_book (isbn, title, loan_date, user_id) VALUES (%s, %s, %s, %s)", 
                  (isbn, title, loan_date, user_id))

        session.execute(batch)
        
        # --- AJOUT : Mise à jour du compteur ---
        increment_total_books(session) 
        
        print(f"📖 Emprunt enregistré pour '{title}'")
        return True  # <--- INDISPENSABLE pour que le CLI affiche "Succès"
    except Exception as e:
        print(f"❌ Erreur borrow_book: {e}")
        return False
    
def add_reservation(session, isbn, user_id):
    query = "INSERT INTO reservations (isbn, reservation_date, user_id, status) VALUES (%s, %s, %s, %s)"
    session.execute(query, (isbn, datetime.now(), user_id, 'en_attente'))

def increment_total_books(session):
    # Les compteurs s'utilisent avec UPDATE en Cassandra
    query = "UPDATE global_stats SET stat_value = stat_value + 1 WHERE stat_name = 'total_loans'"
    session.execute(query)
    

def return_book_logic(session, user_id, isbn, loan_date):
    """
    Logique de retour sans ALLOW FILTERING.
    Nécessite la clé primaire complète : user_id + loan_date.
    """
    try:
        # 1. Conversion des types
        uid_conv = UUID(user_id) if isinstance(user_id, str) else user_id
        return_date = datetime.now()

        # 2. Mise à jour de l'historique utilisateur (UPDATE au lieu de DELETE)
        # On utilise la clé primaire (user_id, loan_date) pour cibler la ligne exacte
        update_user_query = """
            UPDATE borrows_by_user 
            SET return_date = %s 
            WHERE user_id = %s AND loan_date = %s
        """
        session.execute(update_user_query, (return_date, uid_conv, loan_date))

        # 3. Suppression des suivis actifs (car le livre est rendu)
        # Suppression par partition key (isbn)
        session.execute("DELETE FROM non_returned_book WHERE isbn = %s", (isbn,))
        

        return True

    except Exception as e:
        print(f"❌ Erreur lors du retour (sans filtrage) : {e}")
        return False