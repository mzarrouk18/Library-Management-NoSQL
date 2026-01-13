import os
import sys
from uuid import UUID
from tabulate import tabulate
from colorama import Fore, Style, init
from conf.database import CassandraConnection
from Gestion_des_livres.books import find_book_by_isbn, list_books_by_category
from Gestion_des_livres.users import create_user
from Gestion_des_livres.borrows import borrow_book, return_book_logic

# Initialisation des couleurs pour le terminal
init(autoreset=True)

class LibraryApp:
    def __init__(self):
        self.db = CassandraConnection(keyspace='library_system')
        self.session = self.db.connect()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def menu_principal(self):
        while True:
            self.clear_screen()
            print(Fore.CYAN + "================================================")
            print(Fore.CYAN + "📚 SYSTÈME DE GESTION BIBLIOTHÈQUE UNIVERSITAIRE")
            print(Fore.CYAN + "================================================")
            print("1. 🔍 Rechercher un livre (ISBN)")
            print("2. 🎓 Inscrire un nouvel étudiant")
            print("3. 📖 Enregistrer un EMPRUNT")
            print("4. ↩️  Enregistrer un RETOUR")
            print("5. 📊 Voir les statistiques globales")
            print("q. Quitter")
            print("-" * 48)
            
            choix = input("👉 Choisissez une option : ").lower()

            if choix == '1': self.rechercher_livre()
            elif choix == '2': self.inscrire_etudiant()
            elif choix == '3': self.faire_emprunt()
            elif choix == '4': self.faire_retour()
            elif choix == '5': self.voir_stats()
            elif choix == 'q': 
                self.db.close()
                print("Au revoir !")
                break
            else:
                input(Fore.RED + "Option invalide. Appuyez sur Entrée...")

    def rechercher_livre(self):
        isbn = input("\nEntrez l'ISBN du livre : ")
        book = find_book_by_isbn(self.session, isbn)
        if book:
            data = [[book.isbn, book.title, book.author, book.category]]
            print("\n" + tabulate(data, headers=["ISBN", "Titre", "Auteur", "Genre"], tablefmt="fancy_grid"))
        else:
            print(Fore.RED + "❌ Livre introuvable.")
        input("\nAppuyez sur Entrée pour revenir au menu...")

    def inscrire_etudiant(self):
        nom = input("\nNom de l'étudiant : ")
        email = input("Email : ")
        uid = create_user(self.session, nom, email)
        print(Fore.GREEN + f"\n✅ Étudiant créé ! Notez bien son ID : {uid}")
        input("\nAppuyez sur Entrée...")

    def faire_emprunt(self):
        uid = input("\nID Étudiant (UUID) : ")
        isbn = input("ISBN du livre : ")
        book = find_book_by_isbn(self.session, isbn)
        if book:
            try:
                borrow_book(self.session, UUID(uid), isbn, book.title)
                print(Fore.GREEN + f"\n✅ Succès : '{book.title}' est maintenant emprunté.")
            except Exception as e:
                print(Fore.RED + f"❌ Erreur : {e}")
        else:
            print(Fore.RED + "❌ ISBN inconnu.")
        input("\nAppuyez sur Entrée...")

    def faire_retour(self):
        isbn = input("\nISBN du livre à rendre : ")
        # On utilise ta logique de suppression dans non_returned_book
        self.session.execute("DELETE FROM non_returned_book WHERE isbn = %s", (isbn,))
        print(Fore.BLUE + f"\n✅ Retour enregistré. Le livre {isbn} est disponible.")
        input("\nAppuyez sur Entrée...")

    def voir_stats(self):
        res = self.session.execute("SELECT * FROM global_stats").all()
        if res:
            data = [[r.stat_name, r.stat_value] for r in res]
            print("\n" + tabulate(data, headers=["Indicateur", "Valeur"], tablefmt="grid"))
        else:
            print(Fore.YELLOW + "\n📊 Aucune statistique disponible pour le moment.")
        input("\nAppuyez sur Entrée...")

if __name__ == "__main__":
    app = LibraryApp()
    app.menu_principal()