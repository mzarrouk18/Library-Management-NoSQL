from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from loguru import logger

class CassandraConnection:
    """Gestionnaire de connexion Cassandra"""

    def __init__(self, hosts=['127.0.0.1'], port=9042, keyspace='system'):
        self.hosts = hosts
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None

    def connect(self):
        """Établir la connexion"""
        try:
            self.cluster = Cluster(
                contact_points=self.hosts,
                port=self.port
            )
            self.session = self.cluster.connect()
            logger.success(f"✅ Connecté à Cassandra: {self.hosts}")

            # Utiliser le keyspace
            self.session.set_keyspace(self.keyspace)
            logger.success(f"✅ Keyspace actif: {self.keyspace}")

            return self.session

        except Exception as e:
            logger.error(f"❌ Erreur connexion: {e}")
            raise

    def close(self):
        """Fermer la connexion"""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("🔌 Connexion fermée")

# Test de connexion
if __name__ == "__main__":
    db = CassandraConnection()
    session = db.connect()

    # Test query
    rows = session.execute("SELECT release_version FROM system.local")
    for row in rows:
        logger.info(f"Cassandra version: {row.release_version}")

    db.close()