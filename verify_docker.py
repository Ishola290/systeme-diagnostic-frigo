#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration Docker
"""

import subprocess
import sys
import os
from pathlib import Path

class DockerChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success = []

    def run_command(self, cmd, shell=False):
        """Exécuter une commande et retourner le résultat"""
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def check_docker(self):
        """Vérifier Docker"""
        success, stdout, stderr = self.run_command(["docker", "--version"])
        if success:
            self.success.append(f"✓ Docker: {stdout.strip()}")
            return True
        else:
            self.issues.append("✗ Docker n'est pas installé")
            return False

    def check_docker_compose(self):
        """Vérifier docker-compose"""
        success, stdout, stderr = self.run_command(["docker-compose", "--version"])
        if success:
            self.success.append(f"✓ Docker Compose: {stdout.strip()}")
            return True
        else:
            self.issues.append("✗ Docker Compose n'est pas installé")
            return False

    def check_files(self):
        """Vérifier les fichiers essentiels"""
        root = Path(__file__).parent
        
        files = {
            "docker-compose.yml": root / "docker-compose.yml",
            "Dockerfile (principal)": root / "Dockerfile",
            "Dockerfile (chat)": root / "chat" / "Dockerfile",
            ".env.docker": root / ".env.docker",
        }

        for name, path in files.items():
            if path.exists():
                self.success.append(f"✓ Fichier trouvé: {name}")
            else:
                self.warnings.append(f"⚠ Fichier absent: {name}")

    def check_docker_compose_syntax(self):
        """Vérifier la syntaxe du docker-compose.yml"""
        success, stdout, stderr = self.run_command(
            ["docker-compose", "config"],
            shell=False
        )
        if success:
            self.success.append("✓ docker-compose.yml syntaxe valide")
            return True
        else:
            self.issues.append(f"✗ Erreur syntaxe docker-compose.yml: {stderr}")
            return False

    def check_disk_space(self):
        """Vérifier l'espace disque"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)
            
            if free_gb > 5:
                self.success.append(f"✓ Espace disque: {free_gb:.1f} GB disponible")
                return True
            else:
                self.warnings.append(f"⚠ Espace disque faible: {free_gb:.1f} GB")
                return True
        except:
            return True

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

    def print_results(self):
        """Afficher les résultats"""
        print("\n" + "="*60)
        print("✅ RÉSULTATS VÉRIFICATION DOCKER")
        print("="*60 + "\n")

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

        root = Path(__file__).parent
        if not (root / ".env.docker").exists():
            print("1. Créer .env.docker:")
            print("   cp .env.docker.example .env.docker")
            print("   # Édite avec tes clés API\n")

        if not self.issues:
            print("2. Démarrer Docker:")
            print("   .\docker-run.ps1 (PowerShell)")
            print("   OU")
            print("   .\docker-start.bat (Batch)\n")

            print("3. Vérifier l'accès:")
            print("   Chat Web: http://localhost:5001")
            print("   App Principale: http://localhost:5000\n")

    def run(self):
        """Exécuter toutes les vérifications"""
        print("\n" + "="*60)
        print("🔍 VÉRIFICATION CONFIGURATION DOCKER")
        print("="*60 + "\n")

        self.check_docker()
        self.check_docker_compose()
        self.check_files()
        self.check_docker_compose_syntax()
        self.check_disk_space()
        self.check_ports()

        self.print_results()

        if not self.issues:
            self.print_next_steps()
            print("="*60)
            print("✅ Configuration Docker prête!")
            print("="*60 + "\n")
            return True
        else:
            print("\n" + "="*60)
            print("❌ Problèmes détectés - Corrige les avant de continuer")
            print("="*60 + "\n")
            return False


if __name__ == "__main__":
    checker = DockerChecker()
    success = checker.run()
    sys.exit(0 if success else 1)
