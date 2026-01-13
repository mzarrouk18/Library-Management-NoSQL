import click
from uuid import UUID
from tabulate import tabulate
from conf.database import CassandraConnection
from Gestion_des_livres.books import find_book_by_isbn, list_books_by_category, list_books_by_author
from Gestion_des_livres.users import create_user
from Gestion_des_livres.borrows import borrow_book, add_reservation, return_book_logic

# Initialisation de la connexion via ton module conf
db = CassandraConnection(keyspace='library_system')
session = db.connect()

@click.group()
def cli():
    """📚 SYSTÈME DE GESTION DE BIBLIOTHÈQUE UNIVERSITAIRE"""
    pass

# ========== MODULE LIVRES (Module 4) ==========

@cli.group()
def books():
    """Recherche et gestion du catalogue"""
    pass

@books.command()
@click.option('--isbn', prompt='ISBN', help='ISBN du livre')
def search(isbn):
    """Trouver un livre par son ISBN"""
    book = find_book_by_isbn(session, isbn)
    if book:
        data = [
            ["Titre", book.title],
            ["Auteur", book.author],
            ["Catégorie", book.category],
            ["Année", book.published_year]
        ]
        click.echo("\n" + tabulate(data, headers=["Champ", "Valeur"], tablefmt="fancy_grid"))
    else:
        click.echo(click.style("❌ Aucun livre trouvé pour cet ISBN.", fg='red'))

@books.command()
@click.option('--author', prompt='Nom de l\'auteur')
def author(author):
    """Lister tous les livres d'un auteur"""
    results = list_books_by_author(session, author)
    data = [[b.isbn, b.title] for b in results]
    if data:
        click.echo("\n" + tabulate(data, headers=["ISBN", "Titre"], tablefmt="psql"))
    else:
        click.echo(click.style("❌ Aucun livre trouvé pour cet auteur.", fg='yellow'))

# ========== MODULE UTILISATEURS (Module 5) ==========

@cli.group()
def students():
    """Gestion des profils étudiants"""
    pass

@students.command()
@click.option('--nom', prompt='Nom complet')
@click.option('--email', prompt='Email universitaire')
def add(nom, email):
    """Inscrire un nouvel étudiant"""
    user_id = create_user(session, nom, email)
    click.echo(click.style(f"✅ Inscription réussie ! ID : {user_id}", fg='green', bold=True))

# ========== MODULE EMPRUNTS (Module 6) ==========

@cli.group()
def loans():
    """Gestion des emprunts et réservations"""
    pass

@loans.command()
@click.option('--uid', prompt='ID Étudiant (UUID)')
@click.option('--isbn', prompt='ISBN du livre')
def start(uid, isbn):
    """Enregistrer un nouvel emprunt"""
    # On vérifie si le livre existe pour avoir le titre
    book = find_book_by_isbn(session, isbn)
    if book:
        borrow_book(session, UUID(uid), isbn, book.title)
        click.echo(click.style(f"📖 Emprunt de '{book.title}' validé.", fg='green'))
    else:
        click.echo(click.style("❌ Livre introuvable.", fg='red'))
        
        
@loans.command()
@click.option('--user-id', prompt='ID Utilisateur (UUID)', help='UUID de l\'étudiant')
@click.option('--isbn', prompt='ISBN du livre', help='ISBN du livre retourné')
def back(user_id, isbn):
    """Enregistrer le retour d'un livre"""

    try:
        # Conversion du texte en UUID pour Cassandra
        uid = UUID(user_id)
        
        if return_book_logic(session, uid, isbn):
            click.echo(click.style(f"✅ Succès : Le livre {isbn} a été rendu.", fg='green', bold=True))
            
            # Petit bonus : on vérifie les stats
            # On pourrait décrémenter un compteur 'active_loans' ici si tu en as un !
        else:
            click.echo(click.style("❌ Erreur lors de la mise à jour de la base.", fg='red'))
            
    except ValueError:
        click.echo(click.style("❌ Format UUID invalide.", fg='red'))
        
        

@loans.command()
@click.option('--isbn', prompt='ISBN')
@click.option('--uid', prompt='ID Étudiant')
def reserve(isbn, uid):
    """Placer une réservation"""
    add_reservation(session, isbn, UUID(uid))
    click.echo(click.style("⏳ Réservation mise en attente.", fg='blue'))

if __name__ == '__main__':
    try:
        cli()
    finally:
        db.close() # Fermeture propre