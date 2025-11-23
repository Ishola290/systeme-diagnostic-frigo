#!/usr/bin/env python3
"""
Script de vérification de la configuration
Vérifie que tout est bien configuré pour démarrer l'application
"""

import os
import sys
import subprocess
from pathlib import Path

class SetupChecker:
    def __init__(self):
        self.workspace_root = Path(__file__).parent
        self.chat_dir = self.workspace_root / "chat"
        self.issues = []
        self.warnings = []
        self.success = []

    def print_header(self):
        print("\n" + "="*60)
        print("🔍 VÉRIFICATION DE LA CONFIGURATION")
        print("="*60 + "\n")

    def check_python(self):
        """Vérifier Python"""
        try:
            version = subprocess.check_output(
                ["python", "--version"],
                stderr=subprocess.STDOUT,
                text=True
            ).strip()
            self.success.append(f"✓ Python: {version}")
            return True
        except:
            self.issues.append("✗ Python n'est pas installé ou pas accessible")
            return False

    def check_pip(self):
        """Vérifier pip"""
        try:
            subprocess.check_output(
                ["pip", "--version"],
                stderr=subprocess.STDOUT,
                text=True
            )
            self.success.append("✓ pip est installé")
            return True
        except:
            self.issues.append("✗ pip n'est pas installé")
            return False

    def check_files(self):
        """Vérifier les fichiers essentiels"""
        files_to_check = {
            "app.py": self.workspace_root / "app.py",
            "requirements.txt": self.workspace_root / "requirements.txt",
            "chat/app_web.py": self.chat_dir / "app_web.py",
            "chat/requirements.txt": self.chat_dir / "requirements.txt",
        }

        for name, path in files_to_check.items():
            if path.exists():
                self.success.append(f"✓ Fichier trouvé: {name}")
            else:
                self.issues.append(f"✗ Fichier manquant: {name}")

    def check_env_files(self):
        """Vérifier les fichiers .env"""
        env_root = self.workspace_root / ".env"
        env_chat = self.chat_dir / ".env"
        env_example_root = self.workspace_root / ".env.example"
        env_example_chat = self.chat_dir / ".env.example"

        if env_root.exists():
            self.success.append("✓ .env (racine) exists")
        elif env_example_root.exists():
            self.warnings.append("⚠ .env (racine) absent - utilise .env.example")
        else:
            self.warnings.append("⚠ .env.example (racine) absent")

        if env_chat.exists():
            self.success.append("✓ chat/.env exists")
        elif env_example_chat.exists():
            self.warnings.append("⚠ chat/.env absent - utilise .env.example")
        else:
            self.warnings.append("⚠ chat/.env.example absent")

    def check_database(self):
        """Vérifier les bases de données"""
        db_files = {
            "chat/instance/chat.db": self.chat_dir / "instance" / "chat.db",
        }

        for name, path in db_files.items():
            if path.exists():
                self.success.append(f"✓ Base de données trouvée: {name}")
            else:
                self.warnings.append(f"⚠ Base de données absente: {name} (sera créée à l'init)")

    def check_ports(self):
        """Vérifier les ports disponibles"""
        import socket
        ports = {"5000": 5000, "5001": 5001}

        for name, port in ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()

            if result != 0:
                self.success.append(f"✓ Port {port} disponible")
            else:
                self.warnings.append(f"⚠ Port {port} déjà utilisé")

    def check_packages(self):
        """Vérifier les packages Python importants"""
        packages = [
            "flask",
            "flask_cors",
            "flask_socketio",
            "requests",
            "python_dotenv",
        ]

        for package in packages:
            try:
                __import__(package)
                self.success.append(f"✓ Package trouvé: {package}")
            except ImportError:
                self.warnings.append(f"⚠ Package absent: {package} (sera installé)")

    def print_results(self):
        """Afficher les résultats"""
        print("\n📋 RÉSULTATS:\n")

        if self.success:
            print("✅ SUCCÈS:")
            for item in self.success:
                print(f"   {item}")

        if self.warnings:
            print("\n⚠️  AVERTISSEMENTS:")
            for item in self.warnings:
                print(f"   {item}")

        if self.issues:
            print("\n❌ PROBLÈMES:")
            for item in self.issues:
                print(f"   {item}")

    def print_next_steps(self):
        """Afficher les prochaines étapes"""
        print("\n📝 PROCHAINES ÉTAPES:\n")

        if not (self.workspace_root / ".env").exists():
            print("1. ⚙️  Configure .env (racine):")
            print("   cp .env.example .env")
            print("   # Édite avec tes clés API\n")

        if not (self.chat_dir / ".env").exists():
            print("2. ⚙️  Configure chat/.env:")
            print("   cp chat/.env.example chat/.env")
            print("   # Édite avec ta configuration\n")

        if not (self.chat_dir / "instance" / "chat.db").exists():
            print("3. 🗄️  Initialise la base de données:")
            print("   python chat/init_db.py\n")

        print("4. 📦 Installe les dépendances:")
        print("   pip install -r requirements.txt")
        print("   cd chat && pip install -r requirements.txt\n")

        print("5. 🚀 Démarre l'application:")
        print("   # Option 1: Script PowerShell")
        print("   powershell -ExecutionPolicy Bypass -File start.ps1\n")
        print("   # Option 2: Script batch")
        print("   start.bat\n")
        print("   # Option 3: Manuel (2 terminals)")
        print("   Terminal 1: python app.py")
        print("   Terminal 2: cd chat && python app_web.py\n")

    def print_urls(self):
        """Afficher les URLs"""
        print("🌐 URLS D'ACCÈS:\n")
        print("   • App Principale: http://localhost:5000")
        print("   • Chat Web: http://localhost:5001")
        print("   • Login par défaut: admin@example.com / admin123\n")

    def run(self):
        """Exécuter toutes les vérifications"""
        self.print_header()

        self.check_python()
        self.check_pip()
        self.check_files()
        self.check_env_files()
        self.check_database()
        self.check_ports()
        self.check_packages()

        self.print_results()

        if self.issues:
            print("\n" + "="*60)
            print("⚠️  Des problèmes ont été détectés")
            print("="*60)
            return False

        self.print_next_steps()
        self.print_urls()

        print("="*60)
        print("✅ Configuration vérifiée avec succès!")
        print("="*60 + "\n")
        return True


if __name__ == "__main__":
    checker = SetupChecker()
    success = checker.run()
    sys.exit(0 if success else 1)
