"""
Service IA Local - Point central de traitement
Architecture modulaire: Support multi-modèles (phi-2, mistral, ollama, gpt2)
Sélection automatique selon GPU/CPU disponible
Prêt pour réentraînement avec données domaine frigo
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import requests

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IAConfig:
    """Configuration du service IA - Support multi-modèles"""
    
    # ========== MODÈLES DISPONIBLES ==========
    # Format: 'nom_court': {'hf_id': 'huggingface_id', 'local_folder': 'dossier_local', 'production': bool}
    MODEL_OPTIONS = {
        'phi2': {
            'hf_id': 'microsoft/phi-2',
            'local_folder': 'phi-2',
            'production': True,
            'description': 'Phi-2: Petit, rapide, bon (2.7B params)'
        },
        'mistral': {
            'hf_id': 'mistralai/Mistral-7B-Instruct-v0.1',
            'local_folder': 'mistral-7b',
            'production': True,
            'description': 'Mistral-7B: Équilibré (7B params)'
        },
        'neural': {
            'hf_id': 'Intel/neural-chat-7b-v3-1',
            'local_folder': 'neural-chat-7b',
            'production': True,
            'description': 'Neural-Chat: Optimisé pour chat'
        },
        'gpt2': {
            'hf_id': 'openai/gpt2',
            'local_folder': 'gpt2',
            'production': False,  # Fallback/dev seulement
            'description': 'GPT-2: Ultra-léger (125M params)'
        },
        'ollama': {
            'hf_id': None,  # Utilise ollama API
            'local_folder': None,
            'production': True,
            'description': 'Ollama: Local inference engine'
        }
    }
    
    # Sélection automatique selon ressources
    MODEL_SELECTION_STRATEGY = {
        'has_gpu_high_memory': 'mistral',    # GPU avec beaucoup VRAM
        'has_gpu_low_memory': 'phi2',        # GPU limité
        'cpu_only': 'phi2',                  # CPU seulement (phi2 optimisé CPU)
        'ollama_available': 'ollama',        # Si ollama est disponible
        'fallback': 'gpt2'                   # Dernier recours
    }
    
    # Paramètres LLM - Optimisés pour production
    MAX_TOKENS = 120
    TEMPERATURE = 0.6
    TOP_P = 0.90
    
    # Contexte persistant
    CONTEXT_SIZE = 5
    
    # Bases de données
    DB_PATH = Path(__file__).parent / "data"
    CACHE_PATH = Path(__file__).parent / "cache"
    MODELS_PATH = Path(__file__).parent.parent / "models"
    
    def __init__(self):
        self.DB_PATH.mkdir(exist_ok=True)
        self.CACHE_PATH.mkdir(exist_ok=True)
        self.MODELS_PATH.mkdir(exist_ok=True)

class IAService:
    """Service IA principal - Architecture modulaire multi-modèles"""
    
    def __init__(self, model_name=None):
        self.config = IAConfig()
        self.model = None
        self.tokenizer = None
        self.text_generator = None
        self.conversation_history = {}  # {user_id: [messages]}
        self.knowledge_base = {}
        self.model_info = {}
        
        # Sélection intelligente si pas spécifié
        if model_name is None:
            model_name = self._auto_select_model()
        
        self.model_name = model_name
        logger.info(f"🤖 Initialisation service IA")
        logger.info(f"📋 Modèle demandé: {model_name}")
        
        self._load_model()
        self._load_knowledge_base()
    
    def _auto_select_model(self):
        """Sélection automatique selon ressources disponibles"""
        logger.info("🔍 Détection des ressources disponibles...")
        
        # Vérifier ollama
        try:
            requests.get('http://localhost:11434/api/tags', timeout=2)
            logger.info("✅ Ollama détecté - utilisation recommandée")
            return 'ollama'
        except:
            pass
        
        # Vérifier GPU
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info(f"✅ GPU disponible: {gpu_memory:.1f}GB")
            if gpu_memory > 10:
                logger.info("📊 GPU haute mémoire -> Mistral-7B")
                return 'mistral'
            else:
                logger.info("📊 GPU mémoire limitée -> Phi-2")
                return 'phi2'
        
        # CPU seulement
        logger.info("📊 CPU seulement -> Phi-2 (optimisé CPU)")
        return 'phi2'
    
    def _load_model(self):
        """Charger le modèle LLM - Support multi-modèles avec fallback"""
        try:
            # Supporter anciens noms (mapping backward compatibility)
            model_name = self._normalize_model_name(self.model_name)
            
            if model_name not in self.config.MODEL_OPTIONS:
                logger.error(f"❌ Modèle inconnu: {model_name}")
                logger.info(f"Modèles disponibles: {list(self.config.MODEL_OPTIONS.keys())}")
                return False
            
            model_cfg = self.config.MODEL_OPTIONS[model_name]
            logger.info(f"📋 Configuration: {model_cfg['description']}")
            
            # Cas spécial: Ollama
            if model_name == 'ollama':
                return self._load_ollama_model()
            
            # Cas standard: HuggingFace
            return self._load_huggingface_model(model_name, model_cfg)
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            logger.warning("⚠️ Utilisation du mode fallback (réponses intelligentes)")
            self.model = None
            return False
    
    def _normalize_model_name(self, name):
        """Normaliser les noms de modèles (backward compat)"""
        mapping = {'phi': 'phi2', 'gpt': 'gpt2'}
        return mapping.get(name, name)
    
    def _load_huggingface_model(self, model_name, model_cfg):
        """Charger un modèle HuggingFace"""
        hf_id = model_cfg['hf_id']
        local_folder = model_cfg['local_folder']
        
        # 1. Vérifier modèle local d'abord
        local_path = self.config.MODELS_PATH / local_folder if local_folder else None
        use_local = local_path and local_path.exists()
        
        if use_local:
            logger.info(f"📁 Modèle local trouvé: {local_path}")
            model_id = str(local_path)
        else:
            # 2. Vérifier env var
            env_path = os.environ.get('HF_LOCAL_MODEL_PATH')
            if env_path:
                env_model_path = Path(env_path)
                if env_model_path.exists():
                    logger.info(f"📁 Modèle depuis HF_LOCAL_MODEL_PATH: {env_model_path}")
                    model_id = str(env_model_path)
                    use_local = True
                else:
                    logger.warning(f"⚠️ HF_LOCAL_MODEL_PATH introuvable: {env_path}")
            else:
                model_id = hf_id
        
        # 3. Vérifier connectivité si téléchargement
        if not use_local:
            try:
                requests.get('https://huggingface.co', timeout=3)
                logger.info("✅ Connectivité HuggingFace OK")
            except:
                logger.error("❌ Pas d'accès à huggingface.co")
                if model_name == 'phi2' or model_name == 'gpt2':
                    logger.info("💡 Fallback sur réponses intelligentes")
                    return False
        
        # 4. Charger le modèle
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"🖥️ Device: {device.upper()}")
            
            logger.info(f"⏳ Chargement tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                trust_remote_code=True,
                local_files_only=use_local
            )
            
            logger.info(f"⏳ Chargement modèle {model_name}...")
            load_kwargs = {
                'trust_remote_code': True,
                'device_map': 'auto' if torch.cuda.is_available() else None,
            }
            
            if use_local:
                load_kwargs['local_files_only'] = True
            
            if torch.cuda.is_available():
                load_kwargs['torch_dtype'] = torch.float16
            
            self.model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
            self.model.eval()
            
            # Créer le pipeline
            self.text_generator = pipeline(
                'text-generation',
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info(f"✅ Modèle {model_name} chargé avec succès")
            self.model_info = {'name': model_name, 'device': device}
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement HuggingFace: {e}")
            return False
    
    def _load_ollama_model(self):
        """Charger via Ollama API"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    logger.info(f"✅ Ollama disponible avec {len(models)} modèle(s)")
                    logger.info(f"📋 Modèles: {[m['name'] for m in models]}")
                    self.text_generator = None  # Sera utilisé différemment
                    self.model_info = {'name': 'ollama', 'api': 'localhost:11434'}
                    return True
                else:
                    logger.error("❌ Aucun modèle dans Ollama")
                    return False
            else:
                logger.error(f"❌ Ollama API erreur: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Impossible atteindre Ollama: {e}")
            return False

            # Par défaut, charger depuis models/{model_name} (chemin relatif au dossier gpt/)
            # Sinon, chercher dans HF_LOCAL_MODEL_PATH / LOCAL_MODEL_DIR
            # Priorité: env var > dossier local models/ > téléchargement HF
            use_local = False
            
            # 1. Vérifier si variable d'environnement est définie
            local_model_path = os.environ.get('HF_LOCAL_MODEL_PATH') or os.environ.get('LOCAL_MODEL_DIR')
            if local_model_path:
                local_path = Path(local_model_path)
                if local_path.exists():
                    logger.info(f"📁 Chargement modèle depuis env HF_LOCAL_MODEL_PATH: {local_path}")
                    model_id = str(local_path)
                    use_local = True
                else:
                    logger.warning(f"⚠️ Chemin env HF_LOCAL_MODEL_PATH non trouvé: {local_model_path}")
            
            # 2. Si pas d'env var ou chemin invalide, essayer models/{model_name} (chemin relatif)
            if not use_local:
                # Mapping entre noms modèles courts et dossiers
                model_folder_mapping = {
                    'phi': 'phi-2',
                    'mistral': 'mistral-7b',
                    'llama': 'llama-2-7b',
                    'neural': 'neural-chat-7b'
                }
                folder_name = model_folder_mapping.get(self.model_name, self.model_name)
                # Chemin relatif: depuis gpt/ vers ../models/{folder_name}
                default_local = Path(__file__).parent.parent / "models" / folder_name
                if default_local.exists():
                    logger.info(f"📁 Chargement modèle depuis chemin par défaut: {default_local}")
                    model_id = str(default_local)
                    use_local = True
                else:
                    logger.warning(f"⚠️ Dossier modèle par défaut non trouvé: {default_local} - tentative téléchargement HF")

            # Vérifier rapidement la connectivité vers huggingface pour éviter longues tentatives
            hf_online = True
            if not use_local:
                try:
                    requests.get('https://huggingface.co', timeout=3)
                except Exception:
                    hf_online = False
                    logger.warning("⚠️ Impossible de contacter huggingface.co (vérifiez la connexion réseau / DNS / proxy).\n"+
                                   "Si vous souhaitez charger un modèle depuis un dossier local, définissez HF_LOCAL_MODEL_PATH.")
            
            # Déterminer le device (GPU ou CPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"🖥 Device: {device.upper()}")
            
            # Si pas en ligne et pas de modèle local, on stoppe pour éviter de longues retries
            if not use_local and not hf_online:
                raise RuntimeError("Pas d'accès réseau à huggingface.co et aucun modèle local fourni")

            # Charger le tokenizer
            logger.info(f"⏳ Chargement du tokenizer pour {model_id}...")
            tokenizer_kwargs = {
                'trust_remote_code': True,
            }
            if use_local:
                tokenizer_kwargs['local_files_only'] = True
            else:
                # param dtype seulement si GPU
                tokenizer_kwargs['torch_dtype'] = torch.float16 if torch.cuda.is_available() else torch.float32

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                **tokenizer_kwargs
            )
            
            # Charger le modèle
            logger.info(f"⏳ Chargement du modèle {model_id}...")
            
            # Options de chargement selon les ressources disponibles
            load_kwargs = {
                'trust_remote_code': True,
                'device_map': 'auto' if torch.cuda.is_available() else None,
            }
            
            # Utiliser quantization pour économiser la mémoire si GPU disponible
            if torch.cuda.is_available():
                load_kwargs['torch_dtype'] = torch.float16
                try:
                    from transformers import BitsAndBytesConfig
                    load_kwargs['quantization_config'] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16
                    )
                except:
                    pass  # Fallback sans quantization
            
            if use_local:
                load_kwargs['local_files_only'] = True

            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                **load_kwargs
            )
            
            # Mettre le modèle en mode eval
            self.model.eval()
            
            # Créer le pipeline de génération
            self.text_generator = pipeline(
                'text-generation',
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info(f"✅ Modèle {self.model_name} chargé avec succès sur {device}")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            # Conseils actionnables
            logger.warning("⚠ Utilisation du mode simulation (sans vrai modèle)")
            logger.info("Conseils: 1) Vérifiez votre connexion Internet / DNS; 2) Si vous êtes derrière un proxy, exportez HTTP_PROXY/HTTPS_PROXY;\n"+
                        "3) Pour de meilleures performances de téléchargement, installez 'hf_xet': `pip install huggingface_hub[hf_xet]`;\n"+
                        "4) Pour éviter les téléchargements, pré-téléchargez le modèle et définissez HF_LOCAL_MODEL_PATH vers le dossier du modèle.")

            # Tentative rapide: si pas d'accès HF et aucun modèle local fourni,
            # essayer de charger un modèle local léger 'gpt2' s'il est présent dans le cache
            try:
                fallback_id = 'gpt2'
                logger.info(f"🔁 Tentative de chargement fallback local: {fallback_id}")
                # Charger tokenizer et modèle uniquement à partir des fichiers locaux
                tk = AutoTokenizer.from_pretrained(fallback_id, local_files_only=True)
                mdl = AutoModelForCausalLM.from_pretrained(fallback_id, local_files_only=True)
                mdl.eval()
                self.tokenizer = tk
                self.model = mdl
                self.text_generator = pipeline('text-generation', model=self.model, tokenizer=self.tokenizer, device=-1)
                logger.info(f"✅ Modèle de fallback '{fallback_id}' chargé depuis le cache local")
                return
            except Exception:
                logger.info("ℹ️ Aucun modèle de fallback local disponible, maintien du mode simulation")

            self.model = None
            self.text_generator = None
    
    def _load_knowledge_base(self):
        """Charger la base de connaissances"""
        try:
            kb_file = self.config.DB_PATH / "knowledge_base.json"
            if kb_file.exists():
                with open(kb_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"✅ Base de connaissances chargée: {len(self.knowledge_base)} entrées")
            else:
                logger.info("ℹ Pas de base de connaissances existante")
        except Exception as e:
            logger.error(f"❌ Erreur chargement KB: {e}")
    
    def process_chat_message(self, message, user_id=None):
        """
        Traiter un message du chat
        
        Args:
            message (str): Message de l'utilisateur
            user_id (str): ID de l'utilisateur
            
        Returns:
            dict: Réponse du service IA
        """
        try:
            logger.info(f"💬 Message reçu: {message[:50]}...")
            
            # 1. Analyser le message
            intent = self._analyze_intent(message)
            
            # 2. Récupérer le contexte
            context = self._get_context(message, user_id)
            
            # 3. Générer la réponse
            response = self._generate_response(message, context, intent)
            
            # 4. Sauvegarder dans l'historique
            self._save_to_history(user_id, message, response)
            
            return {
                'success': True,
                'response': response,
                'intent': intent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': 'Erreur lors du traitement du message'
            }
    
    def process_alert(self, alert_data):
        """
        Traiter une alerte de app.py
        
        Args:
            alert_data (dict): Données d'alerte
            
        Returns:
            dict: Alerte traitée et enrichie
        """
        try:
            logger.info(f"🚨 Alerte reçue: {alert_data.get('title', 'N/A')}")
            
            # 1. Analyser l'alerte
            severity = self._analyze_alert_severity(alert_data)
            
            # 2. Chercher des solutions
            solutions = self._find_solutions(alert_data)
            
            # 3. Enrichir l'alerte
            enriched_alert = {
                **alert_data,
                'processed': True,
                'severity_score': severity,
                'suggested_solutions': solutions,
                'processed_at': datetime.now().isoformat()
            }
            
            return enriched_alert
        except Exception as e:
            logger.error(f"❌ Erreur traitement alerte: {e}")
            return alert_data  # Retourner l'alerte originale en cas d'erreur
    
    def _analyze_intent(self, message):
        """Analyser l'intention du message"""
        message_lower = message.lower()
        
        intents = {
            'diagnostic': ['diagnostic', 'diagnose', 'problem', 'issue'],
            'solution': ['fix', 'repair', 'solution', 'how to'],
            'alert': ['alert', 'error', 'warning', 'critical'],
            'info': ['what', 'why', 'how', 'explain'],
            'learn': ['learn', 'train', 'remember'],
        }
        
        for intent, keywords in intents.items():
            if any(kw in message_lower for kw in keywords):
                return intent
        
        return 'general'
    
    def _get_context(self, message, user_id):
        """Récupérer le contexte pertinent"""
        user_history = self.conversation_history.get(str(user_id), [])
        context = {
            'message': message,
            'user_id': user_id,
            'history': user_history[-self.config.CONTEXT_SIZE:],
            'knowledge': self._search_knowledge_base(message)
        }
        return context
    
    def _search_knowledge_base(self, query):
        """Chercher dans la base de connaissances"""
        # Sera implémenté avec recherche sémantique
        results = []
        for key, value in self.knowledge_base.items():
            if any(word in query.lower() for word in key.split()):
                results.append(value)
        return results[:3]  # Top 3 résultats
    
    def _generate_response(self, message, context, intent):
        """Générer une réponse avec le modèle LLM - MODE ULTRA-RAPIDE CPU"""
        try:
            if self.text_generator is None:
                logger.warning("⚠ Modèle non disponible, réponse de fallback")
                return self._generate_fallback_response(message, intent)
            
            # Sur CPU, mode ultra-rapide: réponses très courtes (40 tokens max)
            logger.info("🧠 Génération rapide CPU...")
            
            # Prompt structuré pour éviter le bruit
            prompt = self._build_prompt(message, context, intent)
            
            # Paramètres ultra-optimisés pour CPU + qualité + rapidité
            generation_params = {
                'max_new_tokens': 40,  # Ultra-court: 40 tokens
                'temperature': 0.3,    # Plus déterministe (moins aléatoire)
                'top_p': 0.85,
                'do_sample': False,    # Greedy decoding (plus rapide, plus cohérent)
                'pad_token_id': self.tokenizer.eos_token_id if self.tokenizer else 50256,
            }
            
            try:
                outputs = self.text_generator(
                    prompt,
                    **generation_params
                )
            except Exception as e:
                logger.warning(f"⚠ Génération échouée ({e}), fallback")
                return self._generate_fallback_response(message, intent)
            
            if not outputs or len(outputs) == 0:
                return self._generate_fallback_response(message, intent)
                
            full_text = outputs[0].get('generated_text', '')
            response = full_text[len(prompt):].strip()
            
            # Nettoyer et limiter
            response = response.replace('\n', ' ')[:150]
            response = response.strip()
            
            if not response or len(response) < 3:
                return self._generate_fallback_response(message, intent)
            
            logger.info(f"✅ Réponse: {response[:70]}...")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            return self._generate_fallback_response(message, intent)
    
    def _generate_fallback_response(self, message, intent):
        """Générer une réponse de fallback intelligente - PRIORITÉ sur gpt2 aléatoire"""
        message_lower = message.lower()
        
        # Réponses intelligentes basées sur les mots-clés
        if any(word in message_lower for word in ['panne', 'problème', 'erreur', 'error', 'problem', 'fail']):
            return "🔴 Diagnostic d'alerte détecté.\n\nEtapes recommandées:\n1. Vérifier l'alimentation\n2. Contrôler la température\n3. Inspecter les connexions\n4. Consulter les logs détaillés"
        
        elif any(word in message_lower for word in ['température', 'temperature', 'temp', 'chaud', 'froid', 'heat', 'cold']):
            return "🌡️ Problème de température identifié.\n\nActions:\n1. Vérifier le thermostat\n2. Nettoyer les filtres à air\n3. Vérifier la circulation d'air\n4. Contrôler le compresseur"
        
        elif any(word in message_lower for word in ['électrique', 'electrical', 'puissance', 'power', 'courant', 'current']):
            return "⚡ Problème d'alimentation détecté.\n\nVérifications:\n1. Contrôler le fusible/disjoncteur\n2. Mesurer la tension (230V)\n3. Vérifier le câblage\n4. Tester l'interrupteur"
        
        elif any(word in message_lower for word in ['bruit', 'noise', 'son', 'sound', 'vibration']):
            return "🔊 Anomalie sonore détectée.\n\nCauses possibles:\n1. Compresseur usé\n2. Ventilateur défaillant\n3. Vibrations mécaniques\n4. Accumulation de givre"
        
        elif any(word in message_lower for word in ['fuite', 'leak', 'eau', 'water', 'condensation']):
            return "💧 Problème d'humidité détecté.\n\nSolutions:\n1. Nettoyer l'évacuation\n2. Vérifier les joints\n3. Vérifier l'évaporateur\n4. Contrôler le drainage"
        
        elif any(word in message_lower for word in ['diagnostique', 'diagnostic', 'analyse', 'analyze', 'test']):
            return "🔍 Diagnostic en cours.\n\nParamètres vérifiés:\n- Température interne/externe\n- Pression du circuit\n- Consommation électrique\n- Cycles de compresseur\n- État des alarmes"
        
        elif intent == 'solution':
            return "🔧 Dépannage recommandé:\n1. Arrêter et redémarrer\n2. Vérifier tous les raccordements\n3. Nettoyer les surfaces\n4. Tester en mode diagnostic\n5. Consulter la documentation"
        
        elif intent == 'alert':
            return "🚨 Alerte système détectée et enregistrée.\n\nLe diagnostic procède à l'analyse des anomalies. Veuillez consulter le tableau de bord pour les détails."
        
        else:
            # Fallback générique
            return f"💬 Traitement de votre demande relative aux systèmes frigorifiques.\n\nPour plus d'informations spécifiques, veuillez:\n1. Décrire le symptôme observé\n2. Indiquer la température actuelle\n3. Signaler toute anomalie"
    
    def _build_prompt(self, message, context, intent):
        """Construire le prompt pour le modèle - COURT et STRUCTURÉ"""
        # Prompt court mais structuré pour éviter du bruit
        prompt = f"""Vous etes un expert en diagnostic frigorifique. Repondez brievement.

Question: {message}

Reponse courte et technique:"""
        return prompt
    
    def _analyze_alert_severity(self, alert_data):
        """Analyser la sévérité d'une alerte"""
        severity_map = {
            'info': 1,
            'warning': 2,
            'error': 3,
            'critical': 4
        }
        base_severity = severity_map.get(alert_data.get('severity', 'info'), 1)
        
        # Ajuster selon les données
        if 'temperature' in str(alert_data).lower():
            base_severity *= 1.2
        
        return min(base_severity, 4)
    
    def _find_solutions(self, alert_data):
        """Trouver des solutions pour une alerte"""
        solutions = []
        alert_str = str(alert_data).lower()
        
        # Solutions pré-définies
        solution_map = {
            'temperature': [
                'Vérifier le thermostat',
                'Nettoyer les filtres',
                'Vérifier la circulation d\'air'
            ],
            'pressure': [
                'Vérifier le compresseur',
                'Vérifier les connexions',
                'Mesurer la pression'
            ],
            'noise': [
                'Vérifier les vibrations',
                'Vérifier le compresseur',
                'Vérifier le ventilateur'
            ]
        }
        
        for key, sols in solution_map.items():
            if key in alert_str:
                solutions.extend(sols)
        
        return solutions[:3]  # Top 3 solutions
    
    def _save_to_history(self, user_id, message, response):
        uid = str(user_id) if user_id else 'anonymous'
        if uid not in self.conversation_history:
            self.conversation_history[uid] = []
        self.conversation_history[uid].append({
            'message': message,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        # Garder seulement les 20 derniers messages par utilisateur
        if len(self.conversation_history[uid]) > 20:
            self.conversation_history[uid] = self.conversation_history[uid][-20:]
        
       
    def add_to_knowledge_base(self, topic, content):
        """Ajouter une entrée à la base de connaissances"""
        self.knowledge_base[topic] = content
        
        # Sauvegarder
        kb_file = self.config.DB_PATH / "knowledge_base.json"
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Entrée ajoutée à la KB: {topic}")
    
    def get_stats(self):
        """Obtenir les statistiques du service"""
        return {
            'model': self.model_name,
            'messages_processed': sum(len(v) for v in self.conversation_history.values()),
            'knowledge_base_size': len(self.knowledge_base),
            'uptime': datetime.now().isoformat()
        }


# Singleton global
_ia_service = None

def get_ia_service(model='phi'):
    """Obtenir l'instance du service IA (singleton)"""
    global _ia_service
    if _ia_service is None:
        _ia_service = IAService(model)
    return _ia_service
