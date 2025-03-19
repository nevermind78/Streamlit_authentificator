import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
import bcrypt
from PIL import Image
import requests
from dotenv import load_dotenv  # Pour charger les variables d'environnement
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration de la base de données MySQL à partir des variables d'environnement
db_config = {
    'host': os.getenv("DB_HOST"),  # Charger DB_HOST depuis .env
    'user': os.getenv("DB_USER"),  # Charger DB_USER depuis .env
    'password': os.getenv("DB_PASSWORD"),  # Charger DB_PASSWORD depuis .env
    'database': os.getenv("DB_NAME")  # Charger DB_NAME depuis .env
}
# Fonction pour se connecter à la base de données
def connect_to_db():
    return mysql.connector.connect(**db_config)

# Fonction pour hacher un mot de passe
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Fonction pour vérifier un mot de passe
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Fonction pour vérifier si un utilisateur existe déjà
def user_exists(username, email):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

# Fonction pour ajouter un nouvel utilisateur
def add_user(username, email, password):
    conn = connect_to_db()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
    conn.commit()
    cursor.close()
    conn.close()

# Fonction pour vérifier les informations de connexion
def verify_user(username_or_email, password):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s OR email =%s", (username_or_email,username_or_email))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        hashed_password = result[0]
        return verify_password(password, hashed_password)
    return False

# Interface d'inscription
def register_user():
    st.subheader("Créer un compte")
    username = st.text_input("Nom d'utilisateur")
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    confirm_password = st.text_input("Confirmer le mot de passe", type="password")

    if st.button("S'inscrire"):
        if password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        elif user_exists(username, email):
            st.error("Un utilisateur avec ce nom d'utilisateur ou cet email existe déjà.")
        else:
            add_user(username, email, password)
            st.success("Inscription réussie ! Vous pouvez maintenant vous connecter.")

# Interface de connexion
def login_user():
    st.subheader("Se connecter")
    username_or_email = st.text_input("Nom d'utilisateur ou email")
    password = st.text_input("Mot de passe", type="password")
    #st.markdown("[Mot de passe oublié ?](#)")  # Lien vers la récupération du mot de passe

    if st.button("Se connecter"):
        if verify_user(username_or_email, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username_or_email
            st.success("Connexion réussie !")
            st.rerun()  # Redémarrer l'application pour afficher l'interface principale
        else:
            st.error("Nom d'utilisateur/email ou mot de passe incorrect.")

# Interface principale de l'application
def main_app():
    # Afficher un message dans le sidebar pour indiquer que l'utilisateur est connecté
    st.sidebar.markdown(f"**Vous êtes connecté en tant que :** {st.session_state['username']}")
    # Bouton de déconnexion
    if st.sidebar.button("Déconnexion"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)
        st.rerun()  # Redémarrer l'application pour afficher l'interface de connexion

    # Titre de l'application
    st.title("Modèle de Classification Fashion MNIST")

    # Classes Fashion MNIST
    fmnist_classes = [
        "T-shirt/top",  # Classe 0
        "Trouser",      # Classe 1
        "Pullover",     # Classe 2
        "Dress",        # Classe 3
        "Coat",         # Classe 4
        "Sandal",       # Classe 5
        "Shirt",        # Classe 6
        "Sneaker",      # Classe 7
        "Bag",          # Classe 8
        "Ankle boot"    # Classe 9
    ]

    # URL de l'API Flask (remplacez par l'URL de votre API si nécessaire)
    API_URL = "https://ml-project-api.onrender.com/predict"

    # Téléchargement de l'image
    uploaded_file = st.file_uploader("Téléchargez une image (28x28 pixels)", type=["png", "jpg", "jpeg"])

    # Afficher l'image téléchargée une seule fois
    if uploaded_file is not None:
        # Réinitialiser le pointeur du fichier pour éviter l'erreur PIL
        uploaded_file.seek(0)
        
        # Ouvrir l'image
        image = Image.open(uploaded_file).convert('L')  # Convertir en niveaux de gris
        
        # Afficher l'image avec une taille réduite
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:  # Utilise la colonne du milieu pour centrer l'image
            st.image(image, caption="Image téléchargée", width=150)

    # Sélection du modèle
    model_name = st.selectbox(
        "Sélectionnez un modèle",
        ["Logistic Regression", "Linear SVC", "KNN"]
    )

    # Bouton pour lancer la prédiction
    if st.button("Prédire"):
        if uploaded_file is not None:
            # Réinitialiser le pointeur du fichier
            uploaded_file.seek(0)
            
            # Envoyer la requête à l'API Flask
            files = {"file": uploaded_file}
            data = {"model": model_name}
            response = requests.post(API_URL, files=files, data=data)

            # Afficher le résultat
            if response.status_code == 200:
                result = response.json()
                prediction = result.get("prediction")  # Correction : "prediction" -> "prediction"
                
                # Afficher la prédiction
                class_name = fmnist_classes[prediction]  # Convertir le numéro en nom de classe
                st.success(f"**Prédiction :** {class_name} (Classe {prediction})")
            else:
                st.error(f"Erreur lors de la prédiction : {response.text}")
        else:
            st.warning("Veuillez télécharger une image avant de lancer la prédiction.")

# Gestion de l'état de connexion
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Affichage de l'interface d'inscription ou de connexion
if not st.session_state['logged_in']:
    # Centrer les éléments au milieu de la page
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:  # Utiliser la colonne du milieu pour centrer les éléments
        st.title("Authentification")

        # Menu horizontal avec streamlit_option_menu
        selected = option_menu(
            menu_title=None,  # Pas de titre
            options=["Sign In", "Sign Up"],  # Options du menu
            icons=["box-arrow-in-right", "person-plus"],  # Icônes pour les options
            menu_icon="cast",  # Icône du menu
            default_index=0,  # Option par défaut
            orientation="horizontal",  # Menu horizontal
        )

        if selected == "Sign In":
            login_user()
        elif selected == "Sign Up":
            register_user()
else:
    main_app()  # Afficher l'interface principale si l'utilisateur est connecté