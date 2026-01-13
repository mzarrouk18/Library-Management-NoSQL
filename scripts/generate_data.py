# scripts/generate_data.py
from faker import Faker
from random import randint, choice
from loguru import logger
from conf.database import CassandraConnection
from Gestion_des_livres.books import add_book
from Gestion_des_livres.users import create_user

fake = Faker('fr_FR')

def generate_books(session, count=100):
    """Générer des livres aléatoires via ton module books.py"""
    categories = ['Science Fiction', 'Fantasy', 'Thriller', 'Romance',
                  'Histoire', 'Science', 'Biographie', 'Philosophie']

    logger.info(f"🎲 Génération de {count} livres...")

    for i in range(count):
        isbn = f"978-{randint(0,9)}-{randint(100000,999999)}-{randint(10,99)}-{randint(0,9)}"
        title = fake.sentence(nb_words=4)[:-1]
        author = fake.name()
        category = choice(categories)
        year = randint(1950, 2024)

        # Appel de TA fonction qui gère le Batch sur les 3 tables
        add_book(session, isbn, title, author, category, year)

        if (i + 1) % 10 == 0:
            logger.info(f"  ✅ {i+1}/{count} livres créés")

    logger.success(f"✅ {count} livres générés!")

def generate_users(session, count=50):
    """Générer des utilisateurs aléatoires via ton module users.py"""
    logger.info(f"👥 Génération de {count} utilisateurs...")

    for i in range(count):
        nom = fake.name()
        email = fake.email()

        # Appel de TA fonction create_user
        create_user(session, nom, email)

        if (i + 1) % 10 == 0:
            logger.info(f"  ✅ {i+1}/{count} utilisateurs créés")

    logger.success(f"✅ {count} utilisateurs générés!")

if __name__ == "__main__":
    # Connexion via ton module conf
    db = CassandraConnection(keyspace="library_system")
    session = db.connect()
    if not session:
        logger.error("Impossible de se connecter à Cassandra.")

    try:
        # Générer des données pour ton projet universitaire (50k / 100k)
        # Tu peux changer count=100 par count=100000 ici
        generate_books(session, count=10000)
        generate_users(session, count=5000)

        logger.success("🎉 Base de données peuplée avec succès !")
    except Exception as e:
        logger.error(f"Erreur durant la génération : {e}")
    finally:
        db.close()