# 📚 Système de Gestion de Bibliothèque (Cassandra & Tkinter)

Ce projet est une application complète de gestion de bibliothèque capable de gérer plus de 150 000 entrées grâce à la puissance de **Apache Cassandra**.

## 🚀 Fonctionnalités
- **Performance NoSQL** : Recherche instantanée parmi 100k livres et 50k étudiants.
- **Interface Graphique** : GUI intuitive développée avec Tkinter.
- **Gestion des Flux** : Emprunts et retours gérés avec des Batch Statements pour la cohérence des données.
- **Statistiques** : Utilisation des compteurs Cassandra pour le suivi global.

## 🛠️ Installation
1. Cloner le projet : `git clone https://github.com/mzarrouk18/Système_de_Gestion_de_Bibliothèque_Numérique.git`
2. Installer les dépendances : `pip install -r requirements.txt`
3. Lancer Cassandra (Docker recommandé).
4. Générer les données : `python scripts/generate_data.py`
5. Lancer l'app : `python CLI/app_tk.py`