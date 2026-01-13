from conf.database import CassandraConnection

def truncate_tables():
    db = CassandraConnection(keyspace='library_system')
    session = db.connect()
    tables = [
        "book_by_isbn", "book_by_category", "book_by_author",
        "users_by_id", "borrows_by_user", "borrows_by_book",
        "non_returned_book", "reservations"
    ]
    print("🧹 Nettoyage de la base de données...")
    for table in tables:
        session.execute(f"TRUNCATE {table}")
    # Note: On ne truncate pas global_stats car c'est une table de compteurs
    print("✅ Base prête pour le chargement de masse.")
    db.close()

if __name__ == "__main__":
    truncate_tables()