import click
from uuid import UUID
from tabulate import tabulate
from datetime import datetime
from conf.database import CassandraConnection
from Gestion_des_livres.books import find_book_by_isbn
from Gestion_des_livres.users import create_user, list_all_users
from Gestion_des_livres.borrows import borrow_book, return_book_logic

# Initialisation de la connexion
try:
    db = CassandraConnection(keyspace='library_system')
    session = db.connect()
except Exception as e:
    print(f"Erreur de connexion : {e}")
    exit(1)

@click.group()
def cli():
    """📚 SYSTÈME DE GESTION DE BIBLIOTHÈQUE (CLI)"""
    pass

# ========== MODULE UTILISATEURS (Synchronisé avec GUI) ==========

@cli.group()
def students():
    """Gestion des étudiants"""
    pass

@students.command()
@click.option('--fname', prompt='Prénom')
@click.option('--lname', prompt='Nom')
@click.option('--email', prompt='Email')
def add(fname, lname, email):
    """Inscrire un nouvel étudiant (Identique à l'onglet GESTION UTILISATEURS)"""
    try:
        # On concatène pour correspondre à la logique de la GUI
        nom_complet = f"{fname} {lname}"
        user_id = create_user(session, nom_complet, email)
        click.echo(click.style(f"✅ Utilisateur créé ! ID : {user_id}", fg='green', bold=True))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))

@students.command()
def list_users():
    """Afficher les étudiants triés par date (Tri Python comme app_tk)"""
    try:
        users = list(list_all_users(session))
        # Tri applicatif pour contourner les limitations de Cassandra
        sorted_users = sorted(users, key=lambda x: x.join_date, reverse=True)
        
        data = [[u.user_id, u.nom, u.email, u.join_date] for u in sorted_users]
        click.echo("\n" + tabulate(data, headers=["ID", "Nom", "Email", "Date Adhésion"], tablefmt="psql"))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))

# ========== MODULE EMPRUNTS & RETOURS ==========

@cli.group()
def loans():
    """Emprunts et Retours"""
    pass

@loans.command()
@click.option('--uid', prompt='UUID Étudiant')
def check(uid):
    """Lister UNIQUEMENT les emprunts en cours (Filtrage Python)"""
    try:
        # On récupère return_date pour filtrer en local comme dans action_charger_emprunts_etudiant
        query = "SELECT isbn, loan_date, book_title, return_date FROM borrows_by_user WHERE user_id = %s"
        rows = session.execute(query, [UUID(uid)])
        
        # Filtrage : On ne garde que ceux qui n'ont pas de date de retour
        data = [[row.isbn, row.book_title, row.loan_date] for row in rows if row.return_date is None]
        
        if data:
            click.echo("\n" + tabulate(data, headers=["ISBN", "Titre", "Date Emprunt"], tablefmt="fancy_grid"))
        else:
            click.echo(click.style("ℹ️ Aucun emprunt en cours (tous les livres sont rendus).", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))
        
@loans.command()
@click.option('--uid', prompt='UUID Étudiant', help='ID unique de l\'étudiant')
@click.option('--isbn', prompt='ISBN Livre', help='ISBN du livre à emprunter')
def borrow(uid, isbn):
    """Enregistrer un nouvel emprunt avec récupération automatique du titre"""
    try:
        # 1. On cherche d'abord le livre pour obtenir son titre (comme dans la GUI)
        book = find_book_by_isbn(session, isbn)
        
        if not book:
            click.echo(click.style(f"❌ Erreur : Le livre avec l'ISBN {isbn} n'existe pas.", fg='red'))
            return

        # 2. On récupère le titre
        titre = book.title
        click.echo(f"📖 Livre trouvé : {titre}")

        # 3. On effectue l'emprunt avec le titre récupéré
        # Note : Vérifie si ta fonction borrow_book prend (session, uid, isbn, titre) 
        # ou si elle cherche le titre elle-même. 
        if borrow_book(session, UUID(uid), isbn,titre):
            click.echo(click.style(f"✅ Succès : '{titre}' a été emprunté par {uid}.", fg='green', bold=True))
        else:
            click.echo(click.style("❌ Échec : L'enregistrement a échoué dans Cassandra.", fg='red'))
            
    except Exception as e:
        click.echo(click.style(f"❌ Erreur technique : {e}", fg='red'))

@loans.command()
@click.option('--uid', prompt='UUID Étudiant')
@click.option('--isbn', prompt='ISBN Livre')
@click.option('--date', prompt='Date Emprunt (YYYY-MM-DD HH:MM:SS)')
def back(uid, isbn, date):
    """Marquer comme Rendu (Triplet complet pour éviter ALLOW FILTERING)"""
    try:
        loan_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        # Utilisation de la logique commune return_book_logic
        if return_book_logic(session, UUID(uid), isbn, loan_date):
            click.echo(click.style(f"✅ Succès : Le livre {isbn} a été marqué comme rendu.", fg='green', bold=True))
        else:
            click.echo(click.style("❌ Échec : Vérifiez les informations saisies.", fg='red'))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))

if __name__ == '__main__':
    try:
        cli()
    finally:
        db.close()