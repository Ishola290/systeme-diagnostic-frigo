def _analyze_with_gemini(self, prompt):
    """Analyser avec Gemini uniquement"""
    try:
        result = self.gemini_service.generer_analyse_sync(prompt)
        if result.get('success'):
            return {
                'success': True,
                'response': result.get('analyse', ''),
                'model_used': 'gemini',
                'processing_time': result.get('processing_time', 0)
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Erreur Gemini'),
                'model_used': 'gemini'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erreur Gemini: {str(e)}',
            'model_used': 'gemini'
        }

def _analyze_with_gpt4(self, prompt):
    """Analyser avec GPT-4 uniquement"""
    try:
        result = self.gpt4_service.generer_analyse_sync(prompt)
        if result.get('success'):
            return {
                'success': True,
                'response': result.get('analyse', ''),
                'model_used': 'gpt-4',
                'processing_time': result.get('processing_time', 0)
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Erreur GPT-4'),
                'model_used': 'gpt-4'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erreur GPT-4: {str(e)}',
            'model_used': 'gpt-4'
        }

def _analyze_with_primary_fallback(self, prompt):
    """Analyser avec modèle principal, fallback sur le second"""
    primary = self.config.PRIMARY_MODEL
    
    # Essayer le modèle principal d'abord
    if primary == 'gemini':
        result = self._analyze_with_gemini(prompt)
        if result.get('success'):
            return result
        logger.warning(f"⚠️ Échec modèle principal (Gemini), fallback sur GPT-4")
        return self._analyze_with_gpt4(prompt)
    else:  # primary == 'gpt4'
        result = self._analyze_with_gpt4(prompt)
        if result.get('success'):
            return result
        logger.warning(f"⚠️ Échec modèle principal (GPT-4), fallback sur Gemini")
        return self._analyze_with_gemini(prompt)

def _analyze_with_comparison(self, prompt):
    """Analyser avec les deux modèles et comparer"""
    gemini_result = self._analyze_with_gemini(prompt)
    gpt4_result = self._analyze_with_gpt4(prompt)
    
    # Si les deux échouent
    if not gemini_result.get('success') and not gpt4_result.get('success'):
        return {
            'success': False,
            'error': 'Les deux modèles ont échoué',
            'model_used': 'none'
        }
    
    # Si un seul réussit
    if gemini_result.get('success') and not gpt4_result.get('success'):
        return gemini_result
    if gpt4_result.get('success') and not gemini_result.get('success'):
        return gpt4_result
    
    # Si les deux réussissent, choisir le plus rapide
    gemini_time = gemini_result.get('processing_time', 999)
    gpt4_time = gpt4_result.get('processing_time', 999)
    
    if gemini_time < gpt4_time:
        logger.info(f"🏆 Gemini plus rapide ({gemini_time:.2f}s vs {gpt4_time:.2f}s)")
        return gemini_result
    else:
        logger.info(f"🏆 GPT-4 plus rapide ({gpt4_time:.2f}s vs {gemini_time:.2f}s)")
        return gpt4_result
