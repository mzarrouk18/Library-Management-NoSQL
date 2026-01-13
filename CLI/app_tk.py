import tkinter as tk
from tkinter import messagebox, ttk
from uuid import UUID

# Imports de tes modules
from conf.database import CassandraConnection
from Gestion_des_livres.books import find_book_by_isbn, list_books_by_category, list_books_by_author
from Gestion_des_livres.users import create_user
from Gestion_des_livres.borrows import borrow_book

class LibraryAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Library Manager Pro - Cassandra")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f2f5")

        try:
            self.db = CassandraConnection(keyspace='library_system')
            self.session = self.db.connect()
        except Exception as e:
            messagebox.showerror("Erreur", f"Connexion Cassandra échouée : {e}")
            root.destroy()

        # --- STYLE ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # --- PANNEAU DE NAVIGATION (ONGLETS) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglets
        self.tab_search = ttk.Frame(self.notebook)
        self.tab_loans = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_search, text="🔍 RECHERCHE LIVRES")
        self.notebook.add(self.tab_loans, text="📖 EMPRUNTS & RETOURS")

        self.setup_search_tab()
        self.setup_loans_tab()

    def setup_search_tab(self):
        """Interface dédiée à la recherche de livres"""
        frame_top = tk.Frame(self.tab_search, padx=20, pady=20)
        frame_top.pack(fill="x")

        tk.Label(frame_top, text="Rechercher par :", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        
        self.search_mode = tk.StringVar(value="ISBN")
        combo = ttk.Combobox(frame_top, textvariable=self.search_mode, values=["ISBN", "Auteur", "Catégorie"], state="readonly")
        combo.grid(row=0, column=1, padx=10)

        self.ent_query = tk.Entry(frame_top, width=30, font=("Helvetica", 11))
        self.ent_query.grid(row=0, column=2, padx=10)

        btn_search = tk.Button(frame_top, text="Lancer la recherche", bg="#2196F3", fg="white", command=self.action_rechercher_livres)
        btn_search.grid(row=0, column=3, padx=5)

        # Tableau des résultats
        self.tree = ttk.Treeview(self.tab_search, columns=("ISBN", "Titre", "Auteur", "Genre"), show='headings')
        self.tree.heading("ISBN", text="ISBN")
        self.tree.heading("Titre", text="Titre")
        self.tree.heading("Auteur", text="Auteur")
        self.tree.heading("Genre", text="Catégorie")
        self.tree.column("ISBN", width=120)
        self.tree.column("Titre", width=250)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def setup_loans_tab(self):
        """Interface pour les emprunts (ton code précédent intégré)"""
        f = tk.Frame(self.tab_loans, padx=20, pady=20)
        f.pack(fill="both")
        
        tk.Label(f, text="Enregistrer un Emprunt", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        tk.Label(f, text="UUID Étudiant :").pack()
        self.ent_loan_uid = tk.Entry(f, width=40)
        self.ent_loan_uid.pack(pady=5)
        
        tk.Label(f, text="ISBN Livre :").pack()
        self.ent_loan_isbn = tk.Entry(f, width=40)
        self.ent_loan_isbn.pack(pady=5)
        
        tk.Button(f, text="Valider l'Emprunt", bg="#4CAF50", fg="white", command=self.action_emprunt_gui).pack(pady=20)

    # --- LOGIQUE DE RECHERCHE ---

    def action_rechercher_livres(self):
        query = self.ent_query.get().strip()
        mode = self.search_mode.get()
        
        # Nettoyer le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not query:
            return

        results = []
        if mode == "ISBN":
            book = find_book_by_isbn(self.session, query) #
            if book: results = [book]
        elif mode == "Auteur":
            results = list_books_by_author(self.session, query) #
        elif mode == "Catégorie":
            results = list_books_by_category(self.session, query) #

        if results:
            for b in results:
                # On adapte selon si c'est un Row Cassandra ou un objet
                self.tree.insert("", "end", values=(b.isbn, b.title, b.author, getattr(b, 'category', mode)))
        else:
            messagebox.showinfo("Info", "Aucun résultat trouvé.")

    def action_emprunt_gui(self):
        uid = self.ent_loan_uid.get().strip()
        isbn = self.ent_loan_isbn.get().strip()
        try:
            book = find_book_by_isbn(self.session, isbn)
            if book:
                borrow_book(self.session, UUID(uid), isbn, book.title) #
                messagebox.showinfo("Succès", f"Emprunt de '{book.title}' enregistré.")
            else:
                messagebox.showerror("Erreur", "Livre introuvable.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryAppGUI(root)
    root.mainloop()