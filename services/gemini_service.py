"""
Service Google Gemini - Analyse intelligente des pannes
"""

import google.generativeai as genai
import logging
from typing import Dict, List, Optional
import json
import re

logger = logging.getLogger(__name__)


class GeminiService:
    """Service pour l'analyse IA avec Google Gemini"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash", temperature: float = 0.3):
        """
        Initialise le service Gemini
        
        Args:
            api_key: Clé API Google Generative AI
            model_name: Nom du modèle Gemini à utiliser
            temperature: Température pour la génération (0-1)
        """
        logger.info(f"🔍 Initialisation Gemini - API Key présente: {bool(api_key and api_key.strip())}")
        
        if not api_key or not api_key.strip():
            logger.warning("❌ GEMINI_API_KEY non configurée ou vide - Mode dégradé")
            self.api_key = None
            self.model = None
            return
            
        genai.configure(api_key=api_key)
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Gemini configuré - Modèle: {model_name}")
    
    def generer_analyse_sync(self, prompt: str) -> Dict:
        """
        Génère une analyse détaillée d'une panne (version synchrone)
        
        Args:
            prompt: Prompt contenant les données de diagnostic
            
        Returns:
            Dict contenant l'analyse Gemini
        """
        if not self.model:
            logger.warning("Gemini non disponible - Retour fallback")
            return self._generer_fallback_analyse()
        
        try:
            logger.info("Appel Gemini pour analyse panne")
            logger.debug(f"Modèle utilisé: {self.model}")
            logger.debug(f"Premier 100 caractères du prompt: {prompt[:100]}...")
            
            logger.info("🚀 AVANT generate_content() - Vérification model")
            logger.info(f"   - self.model existe: {self.model is not None}")
            logger.info(f"   - Type self.model: {type(self.model)}")
            logger.info(f"   - Méthode generate_content: {hasattr(self.model, 'generate_content')}")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=1024,
                )
            )
            
            logger.info("✅ generate_content() RÉUSSI - Traitement réponse...")
            logger.info(f"🔍 Vérification réponse Gemini:")
            logger.info(f"   - finish_reason: {response.finish_reason if hasattr(response, 'finish_reason') else 'N/A'}")
            logger.info(f"   - prompt_feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
            logger.info(f"   - candidates count: {len(response.candidates) if hasattr(response, 'candidates') else 0}")
            if hasattr(response, 'candidates') and response.candidates:
                logger.info(f"   - candidate[0].finish_reason: {response.candidates[0].finish_reason if hasattr(response.candidates[0], 'finish_reason') else 'N/A'}")
                logger.info(f"   - candidate[0].content.parts length: {len(response.candidates[0].content.parts) if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts') else 'N/A'}")
            logger.debug(f"Réponse Gemini reçue - Type: {type(response)}, Attributs: {dir(response)[:5]}")
            
            # Extraire le texte de la réponse Gemini
            texte_analyse = ""
            try:
                # Essayer l'accesseur rapide d'abord
                texte_analyse = response.text
                logger.debug(f"✅ Texte extrait via response.text: {len(texte_analyse)} caractères")
            except Exception as e:
                logger.warning(f"⚠️ Impossible d'accéder à response.text: {e}")
                # Si ça échoue, accéder directement aux candidates
                if hasattr(response, 'candidates') and response.candidates:
                    content = response.candidates[0].content
                    if hasattr(content, 'parts') and content.parts:
                        texte_analyse = content.parts[0].text
                        logger.debug(f"✅ Texte extrait via candidates: {len(texte_analyse)} caractères")
            
            if not texte_analyse:
                logger.warning("❌ Aucun texte extrait de la réponse Gemini")
                # Ne JAMAIS faire str(response) - utiliser _extract_response_text
                texte_analyse = self._extract_response_text(response)
                if not texte_analyse:
                    # Si toujours rien, utiliser fallback
                    logger.warning("❌ _extract_response_text retourné vide - Utilisation fallback")
                    return self._generer_fallback_analyse()
            
            logger.info(f"✅ Analyse Gemini générée ({len(texte_analyse)} caractères)")
            
            # Parser la réponse
            analyse = self._parser_analyse(texte_analyse)
            
            return {
                'succes': True,
                'analyse': texte_analyse,
                'recommandations': analyse.get('recommandations', []),
                'urgence': analyse.get('urgence', 'normal'),
                'actions_rapides': analyse.get('actions_rapides', []),
                'durabilite_estimee': analyse.get('durabilite', 'Inconnue')
            }
            
        except Exception as e:
            logger.error(f"❌ ERREUR GEMINI - Type: {type(e).__name__}, Message complet: {str(e)}", exc_info=True)
            logger.warning(f"Gemini indisponible ({str(e)[:60]}), utilisation fallback")
            return self._generer_fallback_analyse()
    
    def generer_notification_retraining_sync(self, apprentissage_data: Dict) -> str:
        """
        Génère une notification pour un réentraînement (version synchrone)
        
        Args:
            apprentissage_data: Données d'apprentissage
            
        Returns:
            Message formaté pour Telegram (GARANTIE STRING)
        """
        try:
            if not self.model:
                return self._extract_text_safe(self._notification_fallback_retraining(apprentissage_data))
            
            prompt = f"""
            Génère un message court et professionnel pour notifier qu'un réentraînement du modèle a été déclenché.
            
            Données:
            - Nombre de diagnostics depuis dernier entraînement: {apprentissage_data.get('compteur_total', 0)}
            - Nouvelles pannes identifiées: {len(apprentissage_data.get('nouvelles_pannes', []))}
            - Panne la plus fréquente: {apprentissage_data.get('panne_plus_frequente', 'Non déterminée')}
            
            Format: Message court, clair, avec emojis. Max 200 caractères.
            """
            
            response = self.model.generate_content(prompt)
            
            # Extraire le texte avec la nouvelle méthode sûre
            texte = self._extract_response_text(response)
            
            if texte:
                return texte
            else:
                return self._extract_text_safe(self._notification_fallback_retraining(apprentissage_data))
            
        except Exception as e:
            logger.error(f"Erreur notification retraining: {e}")
            return self._extract_text_safe(self._notification_fallback_retraining(apprentissage_data))
    
    def generer_notification_nouvelle_panne_sync(self, nouvelle_panne: Dict) -> str:
        """
        Génère une notification pour une nouvelle panne détectée (version synchrone)
        
        Args:
            nouvelle_panne: Information sur la nouvelle panne
            
        Returns:
            Message formaté pour Telegram (GARANTIE STRING)
        """
        try:
            if not self.model:
                return self._extract_text_safe(self._notification_fallback_nouvelle_panne(nouvelle_panne))
            
            prompt = f"""
            Génère un message d'alerte court pour une NOUVELLE panne détectée dans un système frigorifique.
            
            Type de panne: {nouvelle_panne.get('type', 'Inconnue')}
            Confiance: {nouvelle_panne.get('confiance', 0)*100:.1f}%
            Capteurs affectés: {', '.join(nouvelle_panne.get('capteurs_affectes', []))}
            
            Format: Alerte, clair, urgence appropriée. Max 250 caractères. Inclure emojis.
            """
            
            response = self.model.generate_content(prompt)
            
            # Extraire le texte avec la nouvelle méthode sûre
            texte = self._extract_response_text(response)
            
            if texte:
                return texte
            else:
                return self._extract_text_safe(self._notification_fallback_nouvelle_panne(nouvelle_panne))
            
        except Exception as e:
            logger.error(f"Erreur notification nouvelle panne: {e}")
            return self._extract_text_safe(self._notification_fallback_nouvelle_panne(nouvelle_panne))
    
    def generer_diagnostic_detaille_sync(self, donnees_diagnostic: Dict) -> Dict:
        """
        Génère un diagnostic complet et détaillé (version synchrone)
        
        Args:
            donnees_diagnostic: Toutes les données du diagnostic
            
        Returns:
            Diagnostic complet structuré
        """
        if not self.model:
            return self._diagnostic_fallback(donnees_diagnostic)
        
        try:
            prompt = self._construire_prompt_diagnostic(donnees_diagnostic)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=2048,
                )
            )
            
            # Extraire le texte de manière robuste
            try:
                texte = response.text
            except:
                if hasattr(response, 'candidates') and response.candidates:
                    texte = response.candidates[0].content.parts[0].text
                else:
                    # Ne JAMAIS faire str(response) directement
                    texte_extracted = self._extract_response_text(response)
                    if texte_extracted:
                        texte = texte_extracted
                    else:
                        return self._diagnostic_fallback(donnees_diagnostic)
            
            diagnostic = self._parser_diagnostic_complet(texte)
            logger.info("Diagnostic détaillé généré")
            
            return diagnostic
            
        except Exception as e:
            logger.error(f"Erreur diagnostic détaillé: {e}")
            return self._diagnostic_fallback(donnees_diagnostic)
    
    def _parser_analyse(self, texte: str) -> Dict:
        """
        Parse l'analyse Gemini pour extraire informations clés
        
        Args:
            texte: Texte de l'analyse
            
        Returns:
            Dict structuré
        """
        urgence = "normal"
        if "urgence haute" in texte.lower() or "critique" in texte.lower():
            urgence = "haute"
        elif "urgence moyenne" in texte.lower():
            urgence = "moyenne"
        
        recommandations = []
        if "recommandation" in texte.lower():
            lignes = texte.split('\n')
            for ligne in lignes:
                if '-' in ligne and len(ligne) > 10:
                    recommandations.append(ligne.strip('- '))
        
        return {
            'urgence': urgence,
            'recommandations': recommandations[:5],  # Limiter à 5
            'actions_rapides': self._extraire_actions_rapides(texte)
        }
    
    def _extraire_actions_rapides(self, texte: str) -> List[str]:
        """Extrait les actions rapides du texte"""
        actions = []
        keywords = ['vérifier', 'contrôler', 'nettoyer', 'remplacer', 'arrêter', 'redémarrer']
        
        for keyword in keywords:
            if keyword in texte.lower():
                actions.append(keyword.capitalize())
        
        return actions[:3]
    
    def _construire_prompt_diagnostic(self, donnees: Dict) -> str:
        """Construit un prompt complet pour diagnostic détaillé"""
        return f"""
        Fournis une analyse détaillée d'un système frigorifique basée sur les données suivantes:
        
        Données capteurs:
        {json.dumps(donnees.get('donnees_capteurs', {}), indent=2)}
        
        Prédiction IA:
        {json.dumps(donnees.get('prediction_ia', {}), indent=2)}
        
        Format de réponse attendu:
        1. DIAGNOSTIC: Résumé du problème identifié
        2. CAUSES POSSIBLES: Liste des causes potentielles
        3. RECOMMANDATIONS: Actions recommandées
        4. URGENCE: Niveau d'urgence (Critique/Haute/Moyenne/Basse)
        5. DURABILITÉ ESTIMÉE: Temps estimé avant défaillance
        
        Sois professionnel, technique mais compréhensible.
        """
    
    def _parser_diagnostic_complet(self, texte: str) -> Dict:
        """Parse un diagnostic complet"""
        return {
            'succes': True,
            'diagnostic': texte,
            'urgence': self._extraire_urgence(texte),
            'type_panne': self._extraire_type_panne(texte)
        }
    
    def _extraire_urgence(self, texte: str) -> str:
        """Extrait le niveau d'urgence"""
        if "critique" in texte.lower():
            return "critique"
        elif "haute" in texte.lower():
            return "haute"
        elif "moyenne" in texte.lower():
            return "moyenne"
        return "basse"
    
    def _extraire_type_panne(self, texte: str) -> str:
        """Extrait le type de panne"""
        types_pannes = [
            'compresseur',
            'conduit',
            'évaporateur',
            'détendeur',
            'capteur',
            'électrique',
            'mécanique',
            'fuite'
        ]
        
        for panne in types_pannes:
            if panne in texte.lower():
                return panne.capitalize()
        
        return "Indéterminée"
    
    def _extract_response_text(self, response) -> str:
        """
        Extrait le texte d'une réponse Gemini de manière sûre
        GARANTIT QUE LE RÉSULTAT EST UNE STRING, JAMAIS UN OBJET RESPONSE
        
        Args:
            response: Objet response de Gemini
            
        Returns:
            String ou string vide
        """
        try:
            # Première tentative: utiliser response.text
            if hasattr(response, 'text'):
                try:
                    text = response.text
                    if isinstance(text, str) and text.strip():
                        logger.info(f"✅ response.text extrait avec succès: {text[:100]}")
                        return text
                except Exception as e:
                    logger.info(f"⚠️ response.text échoué ({type(e).__name__}): {str(e)[:100]}")
        except:
            pass
        
        try:
            # Deuxième tentative: accéder aux candidates
            logger.info(f"🔍 Tentative candidates: hasattr candidates={hasattr(response, 'candidates')}")
            if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                logger.info(f"✅ candidates trouvé, length={len(response.candidates)}")
                candidate = response.candidates[0]
                logger.info(f"✅ candidate[0] trouvé, has content={hasattr(candidate, 'content')}")
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    logger.info(f"✅ content.parts trouvé, length={len(candidate.content.parts)}")
                    if candidate.content.parts and len(candidate.content.parts) > 0:
                        part = candidate.content.parts[0]
                        logger.info(f"✅ part[0] trouvé, type={type(part).__name__}")
                        if hasattr(part, 'text'):
                            text = part.text
                            logger.info(f"✅ part.text extrait: {text[:100]}")
                            if isinstance(text, str) and text.strip():
                                return text
        except Exception as e:
            logger.warning(f"⚠️ Erreur candidates extraction: {type(e).__name__}: {str(e)[:100]}")
        
        # Si on arrive ici, retourner une string vide
        logger.warning(f"❌ Impossible d'extraire texte - Retour string vide")
        return ""
    
    def _extract_text_safe(self, obj) -> str:
        """
        Extrait le texte de n'importe quel objet de manière sûre
        GARANTIT TOUJOURS QUE LE RÉSULTAT EST UNE STRING
        
        Args:
            obj: Objet quelconque
            
        Returns:
            String (jamais None, jamais un objet Response)
        """
        # Si c'est déjà une string, la retourner
        if isinstance(obj, str):
            return obj.strip()
        
        # Si c'est un dict, essayer d'extraire 'text', 'message', 'analyse'
        if isinstance(obj, dict):
            for key in ['text', 'message', 'analyse', 'content']:
                if key in obj and isinstance(obj[key], str):
                    return obj[key].strip()
            # Si aucune clé ne marche, convertir le dict en string JSON
            return str(obj)
        
        # Si c'est un objet Response Gemini
        if 'GenerateContentResponse' in str(type(obj)):
            extracted = self._extract_response_text(obj)
            if extracted:
                return extracted
            return ""
        
        # Fallback: convertir en string mais nettoyer si c'est un objet
        text = str(obj) if obj else ""
        
        # Si la conversion retourne une représentation d'objet, retourner vide
        if '<' in text and 'object at 0x' in text:
            return ""
        
        return text.strip() if text else ""
    
    def _generer_fallback_analyse(self) -> Dict:
        """Analyse fallback si Gemini non disponible"""
        return {
            'succes': False,
            'analyse': "Service Gemini indisponible. Analyse par défaut appliquée.",
            'recommandations': [
                "Vérifier la pression du système",
                "Inspecter les connexions électriques",
                "Contrôler l'évaporateur"
            ],
            'urgence': 'normal',
            'actions_rapides': ['Vérifier', 'Inspécter'],
            'durabilite_estimee': 'Inconnue'
        }
    
    def _notification_fallback_retraining(self, data: Dict) -> str:
        """Notification fallback pour retraining"""
        return f"""
        🔄 RÉENTRAÎNEMENT MODÈLE DÉCLENCHÉ
        
        📊 Stats:
        - Diagnostics traités: {data.get('compteur_total', 0)}
        - Nouvelles pannes: {len(data.get('nouvelles_pannes', []))}
        - Modèle mis à jour ✅
        """
    
    def _notification_fallback_nouvelle_panne(self, panne: Dict) -> str:
        """Notification fallback pour nouvelle panne"""
        return f"""
        🆕 NOUVELLE PANNE IDENTIFIÉE
        
        Type: {panne.get('type', 'Inconnue')}
        Confiance: {panne.get('confiance', 0)*100:.0f}%
        En apprentissage...
        """
    
    def _diagnostic_fallback(self, donnees: Dict) -> Dict:
        """Diagnostic fallback"""
        return {
            'succes': False,
            'diagnostic': "Service indisponible",
            'urgence': 'normal',
            'type_panne': 'Indéterminée'
        }
