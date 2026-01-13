from cassandra.query import BatchStatement

def add_book(session, isbn, title, author, category, published_year):
    """
    Ajoute un livre dans les 3 tables de recherche en une seule fois.
    """
    # On utilise un BATCH pour s'assurer que les 3 tables sont synchronisées
    batch = BatchStatement()
    
    # 1. Insertion pour la recherche par ISBN
    query1 = "INSERT INTO book_by_isbn (isbn, title, author, category, published_year) VALUES (%s, %s, %s, %s, %s)"
    batch.add(query1, (isbn, title, author, category, published_year))
    
    # 2. Insertion pour la recherche par Catégorie
    query2 = "INSERT INTO book_by_category (category, title, author, isbn) VALUES (%s, %s, %s, %s)"
    batch.add(query2, (category, title, author, isbn))
    
    # 3. Insertion pour la recherche par Auteur
    query3 = "INSERT INTO book_by_author (author, title, isbn) VALUES (%s, %s, %s)"
    batch.add(query3, (author, title, isbn))
    
    try:
        session.execute(batch)
        print(f"✅ SUCCESS : '{title}' ajouté dans les 3 tables.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'ajout : {e}")
        
#Les fonctions de consultation     
def find_book_by_isbn(session, isbn):
    """Trouve un livre précis via son ISBN."""
    query = "SELECT * FROM book_by_isbn WHERE isbn = %s"
    return session.execute(query, (isbn,)).one()

def list_books_by_category(session, category):
    """Liste tous les livres d'un genre (ex: 'Roman')."""
    query = "SELECT * FROM book_by_category WHERE category = %s"
    return session.execute(query, (category,))

def list_books_by_author(session, author):
    """Liste tous les livres d'un auteur précis."""
    query = "SELECT * FROM book_by_author WHERE author = %s"
    return session.execute(query, (author,))



