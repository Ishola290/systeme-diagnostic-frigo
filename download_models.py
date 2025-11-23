#!/usr/bin/env python3
"""
Télécharger et sauvegarder tous les modèles IA localement
Prépare les modèles pour déploiement et réentraînement futur

Usage:
    python download_models.py                    # Télécharger tous
    python download_models.py --model phi2       # Télécharger un seul
    python download_models.py --model mistral
    python download_models.py --model neural
    python download_models.py --model gpt2
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration des modèles
MODELS = {
    'phi2': {
        'hf_id': 'microsoft/phi-2',
        'size': '5GB',
        'description': 'Phi-2: Petit, rapide, performant (2.7B params)'
    },
    'mistral': {
        'hf_id': 'mistralai/Mistral-7B-Instruct-v0.1',
        'size': '13GB',
        'description': 'Mistral-7B: Équilibré, haute qualité (7B params)'
    },
    'neural': {
        'hf_id': 'Intel/neural-chat-7b-v3-1',
        'size': '13GB',
        'description': 'Neural-Chat: Optimisé pour chat (7B params)'
    },
    'gpt2': {
        'hf_id': 'openai/gpt2',
        'size': '500MB',
        'description': 'GPT-2: Fallback ultra-léger (125M params)'
    }
}

# Dossier de destination
MODELS_DIR = Path(__file__).parent / 'models'

def download_model(model_name):
    """Télécharger et sauvegarder un modèle"""
    
    if model_name not in MODELS:
        logger.error(f"❌ Modèle inconnu: {model_name}")
        logger.info(f"Modèles disponibles: {list(MODELS.keys())}")
        return False
    
    model_config = MODELS[model_name]
    hf_id = model_config['hf_id']
    size = model_config['size']
    desc = model_config['description']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📥 Téléchargement {model_name.upper()}")
    logger.info(f"{'='*70}")
    logger.info(f"📋 {desc}")
    logger.info(f"📊 Taille estimée: {size}")
    logger.info(f"🔗 Source: {hf_id}")
    
    # Créer le dossier de destination
    model_dir = MODELS_DIR / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Destination: {model_dir}")
    
    try:
        # Vérifier si modèle existe déjà
        if (model_dir / 'config.json').exists():
            logger.info(f"✅ Modèle {model_name} existe déjà")
            return True
        
        # Télécharger tokenizer
        logger.info(f"⏳ Étape 1/3: Téléchargement tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            hf_id,
            trust_remote_code=True
        )
        logger.info(f"✅ Tokenizer téléchargé")
        
        # Télécharger modèle
        logger.info(f"⏳ Étape 2/3: Téléchargement modèle (peut prendre plusieurs minutes)...")
        model = AutoModelForCausalLM.from_pretrained(
            hf_id,
            trust_remote_code=True,
            torch_dtype='auto',
            device_map='auto'
        )
        logger.info(f"✅ Modèle téléchargé")
        
        # Sauvegarder localement
        logger.info(f"⏳ Étape 3/3: Sauvegarde locale...")
        tokenizer.save_pretrained(str(model_dir))
        model.save_pretrained(str(model_dir))
        logger.info(f"✅ Modèle sauvegardé dans {model_dir}")
        
        # Vérifier la sauvegarde
        files = list(model_dir.glob('*'))
        logger.info(f"✅ Fichiers sauvegardés: {len(files)} fichier(s)")
        for f in files[:5]:
            logger.info(f"   - {f.name}")
        
        logger.info(f"🎉 {model_name.upper()} prêt!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement {model_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Télécharger les modèles IA localement'
    )
    parser.add_argument(
        '--model',
        help=f'Modèle spécifique à télécharger. Disponibles: {", ".join(MODELS.keys())}',
        default=None
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Télécharger tous les modèles'
    )
    
    args = parser.parse_args()
    
    logger.info(f"🤖 Gestionnaire Téléchargement Modèles IA")
    logger.info(f"📁 Dossier: {MODELS_DIR}")
    logger.info(f"")
    
    # Afficher les modèles disponibles
    logger.info("📋 Modèles disponibles:")
    for name, config in MODELS.items():
        logger.info(f"   - {name:10} ({config['size']:6}): {config['description']}")
    logger.info("")
    
    # Déterminer quels modèles télécharger
    if args.all:
        models_to_download = list(MODELS.keys())
    elif args.model:
        models_to_download = [args.model]
    else:
        # Par défaut: phi2 + gpt2 (production + fallback)
        models_to_download = ['phi2', 'gpt2']
        logger.info("💡 Mode par défaut: phi2 + gpt2")
        logger.info("   Utilisez --all pour télécharger tous les modèles")
        logger.info("   Utilisez --model <name> pour un modèle spécifique")
    
    logger.info(f"\n📥 À télécharger: {', '.join(models_to_download)}")
    
    # Télécharger les modèles
    results = {}
    for model_name in models_to_download:
        results[model_name] = download_model(model_name)
    
    # Résumé
    logger.info(f"\n{'='*70}")
    logger.info(f"📊 RÉSUMÉ")
    logger.info(f"{'='*70}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for model_name, success in results.items():
        status = "✅" if success else "❌"
        logger.info(f"{status} {model_name:10} - {MODELS[model_name]['size']:6}")
    
    logger.info(f"\n✅ Succès: {success_count}/{total_count}")
    
    if success_count == total_count:
        logger.info(f"\n🎉 Tous les modèles sont prêts!")
        logger.info(f"📦 Vous pouvez maintenant pousser vers GitHub avec Git LFS")
        logger.info(f"🚀 Et déployer sur Render")
        return 0
    else:
        logger.error(f"\n❌ Certains modèles ont échoué")
        return 1

if __name__ == '__main__':
    sys.exit(main())
