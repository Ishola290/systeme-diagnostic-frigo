"""
Script création admin - DESACTIVE car USE_DB=false
"""
import os

if os.getenv("USE_DB", "false").lower() != "true":
    print("⚠️ USE_DB=false -> Création admin ignorée")
    exit(0)

print("✅ Création admin ignorée - authentification désactivée")
