"""
firebase_config.py
Inicialização singleton do Firebase Admin SDK + Firestore client.
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

_CRED_PATH = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")


def _init_firebase():
    """Inicializa o Firebase Admin SDK (executa apenas uma vez)."""
    if not firebase_admin._apps:
        # Tenta ler das variáveis de ambiente primeiro (para nuvem/Railway)
        firebase_env = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        
        if firebase_env:
            try:
                # Carrega a string JSON da variável de ambiente como dicionário
                cred_dict = json.loads(firebase_env)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError as e:
                raise ValueError("A variável de ambiente FIREBASE_SERVICE_ACCOUNT_JSON não contém um formato de JSON válido.") from e
        elif os.path.exists(_CRED_PATH):
            # Fallback para o arquivo local (para desenvolvimento)
            cred = credentials.Certificate(_CRED_PATH)
        else:
            raise FileNotFoundError(
                "Credenciais do Firebase ausentes.\n"
                "Configure a variável FIREBASE_SERVICE_ACCOUNT_JSON na plataforma\n"
                "ou adicione 'serviceAccountKey.json' localmente."
            )
            
        firebase_admin.initialize_app(cred)
    return firestore.client()


# Expõe o Firestore client como singleton
db = _init_firebase()
