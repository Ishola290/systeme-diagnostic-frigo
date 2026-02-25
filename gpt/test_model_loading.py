#!/usr/bin/env python3
"""
Script de test pour vérifier le chargement du modèle LLM
Teste Phi-2 et les autres modèles disponibles
"""

import os
import sys
import logging
import torch

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_device():
    """Tester la disponibilité du GPU"""
    logger.info("🖥 Vérification des ressources...")
    logger.info(f"  GPU disponible: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"  GPU utilisé: {torch.cuda.get_device_name(0)}")
        logger.info(f"  VRAM disponible: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    logger.info(f"  CPU: {os.cpu_count()} cores")

def test_imports():
    """Tester l'import des dépendances"""
    logger.info("📦 Vérification des dépendances...")
    
    try:
        import torch
        logger.info("  ✅ torch")
    except ImportError as e:
        logger.error(f"  ❌ torch: {e}")
        return False
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        logger.info("  ✅ transformers")
    except ImportError as e:
        logger.error(f"  ❌ transformers: {e}")
        return False
    
    try:
        import flask
        logger.info("  ✅ flask")
    except ImportError as e:
        logger.error(f"  ❌ flask: {e}")
        return False
    
    return True

def test_phi2_loading():
    """Tester le chargement de Phi-2"""
    logger.info("\n🚀 Test de chargement du modèle Phi-2...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_id = "microsoft/phi-2"
        logger.info(f"  Modèle: {model_id}")
        logger.info(f"  Taille: 2.7B")
        logger.info("  ⏳ Chargement du tokenizer...")
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
        )
        logger.info("  ✅ Tokenizer chargé")
        
        logger.info("  ⏳ Chargement du modèle (peut prendre 1-2 minutes)...")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        logger.info("  ✅ Modèle chargé")
        
        # Test de génération simple
        logger.info("  ⏳ Test de génération...")
        model.eval()
        
        prompt = "Diagnostic frigorifique: Le compresseur ne démarre pas. "
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Générer avec les paramètres standard
        with torch.no_grad():
            outputs = model.generate(
                inputs['input_ids'],
                max_new_tokens=100,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"  ✅ Génération réussie")
        logger.info(f"  📝 Prompt: {prompt}")
        logger.info(f"  💬 Réponse: {response[len(prompt):].strip()[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ia_service():
    """Tester le service IA"""
    logger.info("\n🤖 Test du service IA...")
    
    try:
        from ia_service import IAService
        
        logger.info("  ⏳ Initialisation du service IA...")
        service = IAService(model_name='phi')
        
        logger.info("  ✅ Service IA initialisé")
        
        # Test de traitement de message
        logger.info("  ⏳ Test de traitement d'un message...")
        result = service.process_chat_message(
            "Le compresseur ne démarre pas, qu'est-ce que je dois faire?",
            user_id="test_user"
        )
        
        if result['success']:
            logger.info("  ✅ Message traité")
            logger.info(f"  Intent détecté: {result['intent']}")
            logger.info(f"  Réponse: {result['response'][:100]}...")
        else:
            logger.error(f"  ❌ Erreur: {result.get('error', 'Inconnu')}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    logger.info("=" * 60)
    logger.info("🧪 TEST DU SERVICE IA - MODÈLE PHI-2")
    logger.info("=" * 60)
    
    # Test 1: Ressources
    test_device()
    
    # Test 2: Dépendances
    if not test_imports():
        logger.error("\n❌ Dépendances manquantes. Installer avec:")
        logger.error("pip install -r requirements.txt")
        return 1
    
    # Test 3: Chargement du modèle
    if not test_phi2_loading():
        logger.warning("\n⚠ Le chargement du modèle a échoué")
        logger.warning("Vérifier la connexion internet et l'espace disque disponible")
    
    # Test 4: Service IA
    if not test_ia_service():
        logger.warning("\n⚠ Le test du service IA a échoué")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Tests complétés!")
    logger.info("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
