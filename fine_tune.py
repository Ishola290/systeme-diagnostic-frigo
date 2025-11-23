#!/usr/bin/env python3
"""
Fine-tuning des modèles IA avec données domaine frigo
À exécuter sur le serveur Render après déploiement

Usage (Local):
    python fine_tune.py --model phi2 --data data/frigo_training.csv --epochs 3

Usage (Serveur Render):
    # Via SSH ou webhook
    python fine_tune.py --model phi2 --data /app/data/frigo_training.csv

Résultat:
    Modèle fine-tuné sauvegardé dans models/{model_name}-finetuned/
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

import torch
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    TextDataset,
    DataCollatorForLanguageModeling,
    EarlyStoppingCallback
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinetuneConfig:
    """Configuration du fine-tuning"""
    
    MODELS = {
        'phi2': 'microsoft/phi-2',
        'mistral': 'mistralai/Mistral-7B-Instruct-v0.1',
        'neural': 'Intel/neural-chat-7b-v3-1',
        'gpt2': 'openai/gpt2'
    }
    
    # Hyperparamètres
    LEARNING_RATE = 2e-5
    BATCH_SIZE = 4  # Réduit pour serveur (économiser VRAM)
    NUM_EPOCHS = 3
    MAX_SEQ_LENGTH = 512
    WARMUP_STEPS = 100
    WEIGHT_DECAY = 0.01
    
    # Paths
    MODELS_DIR = Path(__file__).parent / 'models'
    DATA_DIR = Path(__file__).parent / 'data'
    OUTPUT_DIR = Path(__file__).parent / 'models'

class DataProcessor:
    """Traiter les données d'entraînement"""
    
    @staticmethod
    def load_csv_data(csv_path, text_column='text'):
        """Charger données depuis CSV"""
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            
            if text_column not in df.columns:
                logger.error(f"❌ Colonne '{text_column}' non trouvée")
                logger.info(f"Colonnes disponibles: {df.columns.tolist()}")
                return None
            
            # Combiner les textes
            texts = df[text_column].astype(str).tolist()
            logger.info(f"✅ {len(texts)} exemples chargés depuis {csv_path}")
            
            return texts
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture CSV: {e}")
            return None
    
    @staticmethod
    def load_jsonl_data(jsonl_path, text_field='text'):
        """Charger données depuis JSONL (1 JSON par ligne)"""
        try:
            texts = []
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                        if text_field in data:
                            texts.append(str(data[text_field]))
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Ligne {line_num} invalide: {e}")
            
            logger.info(f"✅ {len(texts)} exemples chargés depuis {jsonl_path}")
            return texts
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture JSONL: {e}")
            return None
    
    @staticmethod
    def save_training_file(texts, output_path):
        """Sauvegarder les textes pour l'entraînement"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for text in texts:
                    f.write(text + '\n')
            logger.info(f"✅ Fichier d'entraînement créé: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde: {e}")
            return False

class ModelFinetuner:
    """Fine-tuner les modèles IA"""
    
    def __init__(self, model_name):
        self.config = FinetuneConfig()
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"🤖 Fine-tuner: {model_name}")
        logger.info(f"🖥️ Device: {self.device.upper()}")
        
        if self.device == "cuda":
            logger.info(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
    
    def load_model(self):
        """Charger le modèle"""
        try:
            hf_id = self.config.MODELS.get(self.model_name)
            if not hf_id:
                logger.error(f"❌ Modèle inconnu: {self.model_name}")
                return False
            
            # Essayer charger depuis local d'abord
            local_path = self.config.MODELS_DIR / self.model_name
            if local_path.exists():
                logger.info(f"📁 Modèle local trouvé: {local_path}")
                model_id = str(local_path)
                use_local = True
            else:
                logger.info(f"🌐 Modèle depuis HuggingFace: {hf_id}")
                model_id = hf_id
                use_local = False
            
            logger.info(f"⏳ Chargement tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                trust_remote_code=True,
                local_files_only=use_local
            )
            
            logger.info(f"⏳ Chargement modèle...")
            load_kwargs = {
                'trust_remote_code': True,
                'device_map': 'auto' if torch.cuda.is_available() else None,
            }
            
            if self.device == "cuda":
                load_kwargs['torch_dtype'] = torch.float16
            
            if use_local:
                load_kwargs['local_files_only'] = True
            
            self.model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
            
            logger.info(f"✅ Modèle chargé: {self.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            return False
    
    def prepare_dataset(self, train_file):
        """Préparer le dataset pour l'entraînement"""
        try:
            logger.info(f"📊 Préparation dataset: {train_file}")
            
            # Load dataset
            dataset = TextDataset(
                tokenizer=self.tokenizer,
                file_path=train_file,
                block_size=self.config.MAX_SEQ_LENGTH
            )
            
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
            
            logger.info(f"✅ Dataset prêt: {len(dataset)} exemples")
            return dataset, data_collator
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation dataset: {e}")
            return None, None
    
    def fine_tune(self, train_file, num_epochs=3, batch_size=4):
        """Lancer le fine-tuning"""
        try:
            # Préparer le dataset
            dataset, data_collator = self.prepare_dataset(train_file)
            if dataset is None:
                return False
            
            # Output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.config.OUTPUT_DIR / f"{self.model_name}-finetuned-{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📁 Output directory: {output_dir}")
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(output_dir),
                overwrite_output_dir=False,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=batch_size,
                save_steps=100,
                save_total_limit=2,
                logging_steps=10,
                learning_rate=self.config.LEARNING_RATE,
                weight_decay=self.config.WEIGHT_DECAY,
                warmup_steps=self.config.WARMUP_STEPS,
                gradient_accumulation_steps=2,
                fp16=self.device == "cuda",  # Mixed precision
                dataloader_pin_memory=True,
                dataloader_num_workers=0,  # Important pour serveur
            )
            
            logger.info(f"⏳ Démarrage du fine-tuning...")
            logger.info(f"   Epochs: {num_epochs}")
            logger.info(f"   Batch size: {batch_size}")
            logger.info(f"   Learning rate: {self.config.LEARNING_RATE}")
            
            # Trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=dataset,
                callbacks=[EarlyStoppingCallback(
                    early_stopping_patience=3,
                    early_stopping_threshold=0.001
                )]
            )
            
            # Train
            result = trainer.train()
            
            logger.info(f"✅ Fine-tuning complété!")
            logger.info(f"📊 Loss final: {result.training_loss:.4f}")
            
            # Sauvegarder
            logger.info(f"💾 Sauvegarde du modèle...")
            self.model.save_pretrained(str(output_dir))
            self.tokenizer.save_pretrained(str(output_dir))
            
            # Créer un lien symbolique vers la version "latest"
            latest_dir = self.config.OUTPUT_DIR / f"{self.model_name}-finetuned"
            if latest_dir.exists():
                import shutil
                shutil.rmtree(latest_dir)
            latest_dir.symlink_to(output_dir)
            
            logger.info(f"🎉 Modèle fine-tuné sauvegardé!")
            logger.info(f"📁 Chemin: {output_dir}")
            logger.info(f"🔗 Lien: {latest_dir} -> {output_dir}")
            
            # Sauvegarder les métadonnées
            metadata = {
                'model_name': self.model_name,
                'timestamp': timestamp,
                'num_epochs': num_epochs,
                'batch_size': batch_size,
                'final_loss': float(result.training_loss),
                'device': self.device,
                'data_file': str(train_file)
            }
            
            with open(output_dir / 'finetuning_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Métadonnées sauvegardées")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur fine-tuning: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(
        description='Fine-tuner les modèles IA avec données domaine'
    )
    parser.add_argument(
        '--model',
        required=True,
        choices=['phi2', 'mistral', 'neural', 'gpt2'],
        help='Modèle à fine-tuner'
    )
    parser.add_argument(
        '--data',
        required=True,
        help='Fichier d\'entraînement (CSV ou JSONL)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Nombre d\'epochs (default: 3)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Batch size (default: 4, réduire si OOM)'
    )
    parser.add_argument(
        '--text-column',
        default='text',
        help='Nom de la colonne texte (pour CSV)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"{'='*70}")
    logger.info(f"🤖 Fine-tuning IA - Domaine Frigorifique")
    logger.info(f"{'='*70}")
    
    # Vérifier le fichier de données
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"❌ Fichier non trouvé: {args.data}")
        return 1
    
    logger.info(f"📊 Données: {data_path}")
    logger.info(f"🤖 Modèle: {args.model}")
    logger.info(f"⏱️  Epochs: {args.epochs}")
    logger.info(f"📦 Batch size: {args.batch_size}")
    
    # Charger les données
    logger.info(f"\n⏳ Chargement des données...")
    
    if data_path.suffix == '.csv':
        texts = DataProcessor.load_csv_data(str(data_path), args.text_column)
    elif data_path.suffix == '.jsonl':
        texts = DataProcessor.load_jsonl_data(str(data_path))
    else:
        logger.error(f"❌ Format non supporté: {data_path.suffix}")
        logger.info("Formats supportés: .csv, .jsonl")
        return 1
    
    if not texts:
        logger.error(f"❌ Aucune donnée trouvée")
        return 1
    
    # Créer fichier d'entraînement
    train_file = data_path.parent / f"train_{args.model}.txt"
    if not DataProcessor.save_training_file(texts, train_file):
        return 1
    
    # Fine-tuner
    finetuner = ModelFinetuner(args.model)
    
    if not finetuner.load_model():
        return 1
    
    if not finetuner.fine_tune(train_file, args.epochs, args.batch_size):
        return 1
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🎉 SUCCÈS!")
    logger.info(f"{'='*70}")
    logger.info(f"Modèle fine-tuné: models/{args.model}-finetuned/")
    logger.info(f"Prêt pour production!")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
