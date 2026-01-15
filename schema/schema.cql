-- Trouver un livre par ISBN
CREATE TABLE IF NOT EXISTS book_by_isbn ( 
	isbn text PRIMARY KEY,
	title text,
	author text,
	category text,
	published_year int
	);

-- Lister tous les livres d'une catégorie
CREATE TABLE IF NOT EXISTS book_by_category ( 
	category text,
	title text,
	author text,
	isbn text,
	PRIMARY KEY (category, title, isbn)
	);

-- Trouver tous les livres d'un auteur
CREATE TABLE IF NOT EXISTS book_by_author(
	author text,
	title text,
	isbn text,
	PRIMARY KEY (author,title,isbn)
	);
	
-- Voir le profil d'un utilisateur
CREATE TABLE IF NOT EXISTS users_by_id(
	user_id uuid PRIMARY KEY,
	nom text,
	email text,
	join_date date
	);
	
-- Historique des emprunts d'un utilisateur
CREATE TABLE IF NOT EXISTS borrows_by_user(
	user_id uuid,
	loan_date timestamp,
	isbn text,
	book_title text,
	return_date timestamp,
	PRIMARY KEY (user_id, loan_date)
) WITH CLUSTERING ORDER BY (loan_date DESC);

-- Qui a emprunté un livre spécifique
CREATE TABLE IF NOT EXISTS borrows_by_book(
	isbn text,
	title text,
	loan_date timestamp,
	user_id uuid,
	PRIMARY KEY (isbn,loan_date)
);

-- Livres actuellement empruntés (non retournés)
CREATE TABLE IF NOT EXISTS non_returned_book(
	isbn text PRIMARY KEY,
	title text,
	loan_date timestamp,
	user_id uuid
);

-- Réservations en attente pour un livre
CREATE TABLE IF NOT EXISTS reservations(
	isbn text,
	reservation_date timestamp,
	user_id uuid,
	status text,
	PRIMARY KEY (isbn, reservation_date)
	);

-- Statistiques globales (Compteurs)
CREATE TABLE IF NOT EXISTS global_stats (
    stat_name text PRIMARY KEY,
    stat_value counter
);


