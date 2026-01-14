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
@click.option('--fname', prompt='Prénom', help='Prénom de l\'étudiant')
@click.option('--lname', prompt='Nom', help='Nom de l\'étudiant')
@click.option('--email', prompt='Email', help='Email de l\'étudiant')
def add(fname, lname, email):
    """Inscrire un nouvel étudiant (comme dans l'onglet GESTION UTILISATEURS)"""
    try:
        # On passe fname et lname séparément comme dans app_tk.py
        user_id = create_user(session, fname, lname, email)
        click.echo(click.style(f"✅ Utilisateur créé ! ID : {user_id}", fg='green', bold=True))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))

@students.command()
def list():
    """Afficher tous les étudiants enregistrés"""
    try:
        users = list_all_users(session)
        data = [[u.user_id, u.nom, u.email, u.join_date] for u in users]
        click.echo("\n" + tabulate(data, headers=["ID", "Nom", "Email", "Date Adhésion"], tablefmt="psql"))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))

# ========== MODULE EMPRUNTS & RETOURS (Version sans ALLOW FILTERING) ==========

@cli.group()
def loans():
    """Emprunts et Retours"""
    pass

@loans.command()
@click.option('--uid', prompt='UUID Étudiant')
def check(uid):
    """Lister les emprunts en cours d'un étudiant (Action charger emprunts GUI)"""
    try:
        query = "SELECT isbn, loan_date, book_title FROM borrows_by_user WHERE user_id = %s"
        rows = session.execute(query, [UUID(uid)])
        data = [[row.isbn, row.book_title, row.loan_date] for row in rows]
        
        if data:
            click.echo("\n" + tabulate(data, headers=["ISBN", "Titre", "Date Emprunt"], tablefmt="fancy_grid"))
        else:
            click.echo(click.style("ℹ️ Aucun emprunt en cours pour cet étudiant.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))

@loans.command()
@click.option('--uid', prompt='UUID Étudiant')
@click.option('--isbn', prompt='ISBN Livre')
# On ajoute la date en option pour éviter le filtrage Cassandra
@click.option('--date', prompt='Date Emprunt (YYYY-MM-DD HH:MM:SS)', help='Date exacte de l\'emprunt')
def back(uid, isbn, date):
    """Marquer comme Rendu (Action Retour GUI utilisant la Clé de Clustering)"""
    try:
        # Conversion de la date string en objet datetime pour Cassandra
        loan_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        
        # Appel de la logique avec le triplet complet : UID, ISBN, DATE
        if return_book_logic(session, UUID(uid), isbn, loan_date):
            click.echo(click.style(f"✅ Succès : Le livre {isbn} a été rendu.", fg='green', bold=True))
        else:
            click.echo(click.style("❌ Échec du retour.", fg='red'))
    except ValueError:
        click.echo(click.style("❌ Format de date invalide. Utilisez YYYY-MM-DD HH:MM:SS", fg='red'))
    except Exception as e:
        click.echo(click.style(f"❌ Erreur : {e}", fg='red'))

if __name__ == '__main__':
    try:
        cli()
    finally:
        db.close()