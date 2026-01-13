from conf.database import CassandraConnection
from Gestion_des_livres.books import add_book
from Gestion_des_livres.users import *
from Gestion_des_livres.borrows import *
from cassandra.query import BatchStatement
import uuid
from datetime import datetime, date



def test_integration_totale():
    db = CassandraConnection(keyspace='library_system')
    session = db.connect()
    if not session: return

    try:
        # 1. Utilisation du module Books
        # Cette fonction interne s'occupe déjà d'écrire dans les 3 tables (ISBN, Auteur, Catégorie)
        add_book(session, "978-2070415793", "L'Etranger", "Albert Camus", "Roman", 1942)
        print("✅ Module Books : OK")

        # 2. Utilisation du module Users
        user_id = create_user(session, "Zarro", "zarro@email.com")
        print("✅ Module Users : OK")

        # 3. Utilisation du module Borrows
        # Cette fonction gère les 3 tables de flux (historique user, historique livre, non rendus)
        borrow_book(session, user_id, "978-2070415793", "L'Etranger")
        print("✅ Module Borrows : OK")

        # 4. Réservation 
        add_reservation(session, "978-2070415793", user_id)
        print("✅ Réservation : OK")

    except Exception as e:
        print(f"❌ ERREUR : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_integration_totale()