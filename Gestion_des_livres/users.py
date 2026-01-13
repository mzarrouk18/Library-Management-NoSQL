# modules/users.py
import uuid
from datetime import date

def create_user(session, nom, email):
    user_id = uuid.uuid4()
    join_date = date.today()
    query = "INSERT INTO users_by_id (user_id, nom, email, join_date) VALUES (%s, %s, %s, %s)"
    session.execute(query, (user_id, nom, email, join_date))
    print(f"👤 Utilisateur créé : {nom} (ID: {user_id})")
    return user_id

