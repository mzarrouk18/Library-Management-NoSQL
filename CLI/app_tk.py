import tkinter as tk
from tkinter import messagebox, ttk
from uuid import UUID

from streamlit import success

# Imports de tes modules
from conf.database import CassandraConnection
from Gestion_des_livres.books import find_book_by_isbn, list_books_by_category, list_books_by_author
from Gestion_des_livres.users import create_user
from Gestion_des_livres.borrows import borrow_book, return_book_logic

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
        self.tab_users = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_search, text="🔍 RECHERCHE LIVRES")
        self.notebook.add(self.tab_loans, text="📖 EMPRUNTS & RETOURS")
        self.notebook.add(self.tab_users, text="👥 GESTION UTILISATEURS")

        self.setup_search_tab()
        self.setup_loans_tab()
        self.setup_users_tab() 

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
        """Interface pour les emprunts et retours avec tableau de sélection"""
        f = tk.Frame(self.tab_loans, padx=20, pady=20)
        f.pack(fill="both", expand=True)
        
        # --- SECTION EMPRUNT (HAUT) ---
        tk.Label(f, text="Enregistrer un Emprunt", font=("Helvetica", 12, "bold")).pack()
        
        row_emprunt = tk.Frame(f)
        row_emprunt.pack(pady=10)
        
        tk.Label(row_emprunt, text="ID Étudiant:").grid(row=0, column=0)
        self.ent_loan_uid = tk.Entry(row_emprunt, width=30)
        self.ent_loan_uid.grid(row=0, column=1, padx=5)
        
        tk.Label(row_emprunt, text="ISBN:").grid(row=0, column=2)
        self.ent_loan_isbn = tk.Entry(row_emprunt, width=20)
        self.ent_loan_isbn.grid(row=0, column=3, padx=5)
        
        tk.Button(f, text="Valider l'Emprunt", bg="#4CAF50", fg="white", 
                  command=self.action_emprunt_gui).pack(pady=5)

        # --- SECTION RETOUR (BAS) ---
        # Utilise ttk.Separator au lieu de tk.Separator
        ttk.Separator(f, orient='horizontal').pack(fill='x', pady=20)
        tk.Label(f, text="Livres en cours d'emprunt", font=("Helvetica", 12, "bold"), fg="#C62828").pack()
        
        # Bouton pour charger les emprunts de l'utilisateur saisi
        tk.Button(f, text="Afficher les emprunts de l'étudiant", command=self.action_charger_emprunts_etudiant).pack(pady=5)

        # Création du fameux 'tree_loans' qui manquait
        self.tree_loans = ttk.Treeview(f, columns=("UserID", "ISBN", "Date", "Titre"), show='headings', height=8)
        self.tree_loans.heading("UserID", text="ID Étudiant")
        self.tree_loans.heading("ISBN", text="ISBN")
        self.tree_loans.heading("Date", text="Date Emprunt")
        self.tree_loans.heading("Titre", text="Titre du Livre")
        
        # On peut cacher l'UserID si on veut, mais on en a besoin pour la logique
        self.tree_loans.column("UserID", width=100) 
        self.tree_loans.column("Date", width=150)
        self.tree_loans.pack(fill="both", expand=True, pady=10)

        tk.Button(f, text="Marquer la sélection comme RENDU", bg="#f44336", fg="white", 
                  command=self.action_retour_gui).pack(pady=10)
        
        
    def action_charger_emprunts_etudiant(self):
        uid = self.ent_loan_uid.get().strip()
        if not uid:
            messagebox.showwarning("Attention", "Saisissez l'ID de l'étudiant.")
            return
        # On vide le tableau visuel
        for item in self.tree_loans.get_children():
            self.tree_loans.delete(item)

        try:
            # On récupère TOUS les emprunts de l'utilisateur (très rapide via Partition Key)
            # On ajoute return_date dans le SELECT pour pouvoir le tester en Python
            query = "SELECT user_id, isbn, loan_date, book_title, return_date FROM borrows_by_user WHERE user_id = %s"
            rows = self.session.execute(query, [UUID(uid)])
            
            for row in rows:
                # FILTRAGE EN PYTHON :
                # On n'affiche dans le tableau QUE si le livre n'est pas encore rendu
                if row.return_date is None:
                    self.tree_loans.insert("", "end", values=(
                        row.user_id, 
                        row.isbn, 
                        row.loan_date, 
                        row.book_title
                    ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")
        
        
        
    def setup_users_tab(self):
        """Interface pour créer et lister les utilisateurs"""
        # --- Formulaire de création (Haut) ---
        frame_form = tk.LabelFrame(self.tab_users, text=" Ajouter un nouvel étudiant ", padx=10, pady=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_form, text="Prénom:").grid(row=0, column=0)
        self.ent_fname = tk.Entry(frame_form)
        self.ent_fname.grid(row=0, column=1, padx=5)

        tk.Label(frame_form, text="Nom:").grid(row=0, column=2)
        self.ent_lname = tk.Entry(frame_form)
        self.ent_lname.grid(row=0, column=3, padx=5)

        tk.Label(frame_form, text="Email:").grid(row=0, column=4)
        self.ent_email = tk.Entry(frame_form)
        self.ent_email.grid(row=0, column=5, padx=5)

        btn_add = tk.Button(frame_form, text="Créer l'utilisateur", bg="#4CAF50", fg="white", command=self.action_creer_utilisateur)
        btn_add.grid(row=0, column=6, padx=10)

        # --- Liste des utilisateurs (Bas) ---
        tk.Label(self.tab_users, text="Liste des étudiants enregistrés", font=("Helvetica", 10, "bold")).pack(pady=10)
        
        btn_refresh = tk.Button(self.tab_users, text="Rafraîchir la liste", command=self.action_lister_utilisateurs)
        btn_refresh.pack(pady=5)

        self.tree_users = ttk.Treeview(self.tab_users, columns=("ID", "Prenom", "Email", "Date"), show='headings')
        self.tree_users.heading("ID", text="UUID (ID)")
        self.tree_users.heading("Prenom", text="Prénom")
        self.tree_users.heading("Email", text="Email")
        self.tree_users.heading("Date", text="Date")
        self.tree_users.pack(fill="both", expand=True, padx=10, pady=10)

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
                borrow_book(self.session,UUID(uid), isbn, book.title) 
                messagebox.showinfo("Succès", f"Emprunt de '{book.title}' enregistré.")
            else:
                messagebox.showerror("Erreur", "Livre introuvable.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            
    def action_creer_utilisateur(self):
        fname = self.ent_fname.get().strip()
        lname = self.ent_lname.get().strip()
        nom = f"{fname} {lname}"
        email = self.ent_email.get().strip()

        if not fname or not lname or not email:
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs.")
            return

        try:
            # Appel de ta fonction existante dans Gestion_des_livres/users.py
            new_id = create_user(self.session,nom, email)
            messagebox.showinfo("Succès", f"Utilisateur créé !\nID : {new_id}")
            # Nettoyer les champs
            self.ent_fname.delete(0, tk.END); self.ent_lname.delete(0, tk.END); self.ent_email.delete(0, tk.END)
            self.action_lister_utilisateurs() # Actualiser la liste
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def action_lister_utilisateurs(self):
        # Nettoyer le tableau
        for item in self.tree_users.get_children():
            self.tree_users.delete(item)

        try:
            from Gestion_des_livres.users import list_all_users # Import local ou en haut du fichier
            users = list_all_users(self.session)
            # Convertir en liste pour pouvoir trier
            users_list = list(users)
            # Trier la liste par join_date de manière décroissante
            sorted_users = sorted(users_list, key=lambda x: x.join_date, reverse=True)
            for u in sorted_users:
                self.tree_users.insert("", "end", values=(u.user_id, u.nom, u.email, u.join_date))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les utilisateurs : {e}")
            
            
    def action_retour_gui(self):
        selected = self.tree_loans.selection()
        if not selected:
            messagebox.showwarning("Sélection", "Veuillez cliquer sur un emprunt dans le tableau.")
            return

        # On récupère les valeurs de la ligne cliquée
        values = self.tree_loans.item(selected, 'values')
        u_id = values[0]
        isbn = values[1]
        l_date = values[2] # On a enfin la loan_date sans ALLOW FILTERING !

        if return_book_logic(self.session, u_id, isbn, l_date):
            messagebox.showinfo("Succès", "Livre rendu !")
            self.action_charger_emprunts_etudiant() # Rafraîchir la liste
        else:
            messagebox.showerror("Erreur", "Le retour a échoué.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryAppGUI(root)
    root.mainloop()