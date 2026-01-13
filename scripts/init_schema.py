from conf.database import CassandraConnection
from loguru import logger

def create_keyspace(session):
    """Créer le keyspace"""
    query = """
    CREATE KEYSPACE IF NOT EXISTS library_system
    WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': 3
    }
    """
    session.execute(query)
    logger.success("✅ Keyspace créé")

def create_tables(session):
    """Créer toutes les tables"""
    session.set_keyspace('library_system')

    # Lire le fichier schema.cql
    with open('schema/schema.cql', 'r') as f:
        cql_commands = f.read()

    # Exécuter chaque commande
    for command in cql_commands.split(';'):
        command = command.strip()
        if command:
            try:
                session.execute(command)
                logger.success(f"✅ Table créée")
            except Exception as e:
                logger.warning(f"⚠️  {e}")

if __name__ == "__main__":
    db = CassandraConnection(keyspace='system')
    session = db.connect()

    create_keyspace(session)
    create_tables(session)

    logger.success("🎉 Schéma initialisé!")
    db.close()