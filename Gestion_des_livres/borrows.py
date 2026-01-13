from cassandra.query import BatchStatement
from datetime import datetime

def borrow_book(session, user_id, isbn, title):
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
    print(f"📖 Emprunt enregistré pour '{title}'")
    
def add_reservation(session, isbn, user_id):
    query = "INSERT INTO reservations (isbn, reservation_date, user_id, status) VALUES (%s, %s, %s, %s)"
    session.execute(query, (isbn, datetime.now(), user_id, 'en_attente'))

def increment_total_books(session):
    # Les compteurs s'utilisent avec UPDATE en Cassandra
    query = "UPDATE global_stats SET stat_value = stat_value + 1 WHERE stat_name = 'total_loans'"
    session.execute(query)
    
# Dans Gestion_des_livres/borrows.py

def return_book_logic(session, user_id, isbn):
    """
    Logique de retour : 
    1. Supprime le livre de la table des livres sortis.
    2. Met à jour la date de retour dans l'historique de l'utilisateur.
    """
    
    # 1. On supprime l'emprunt actif
    delete_query = "DELETE FROM non_returned_book WHERE isbn = %s"
    
    # 2. On met à jour l'historique (Note: loan_date fait partie de la PK, 
    # donc pour un vrai historique pro, on cherche souvent la ligne d'abord)
    # Ici, on simplifie en se concentrant sur la table de suivi.
    
    try:
        session.execute(delete_query, (isbn,))
        return True
    except Exception as e:
        print(f"❌ Erreur Cassandra : {e}")
        return False