"""
Script d'initialisation - DESACTIVE car USE_DB=false
"""
import os

if os.getenv("USE_DB", "false").lower() != "true":
    print("⚠️ USE_DB=false -> Initialisation de la base ignorée")
    exit(0)

print("✅ Initialisation ignorée - authentification désactivée")
