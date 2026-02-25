# 🔧 RÉFÉRENCE DES 12 PANNES DU SYSTÈME

Le simulateur gère maintenant **12 types de pannes** spécifiques au système frigorifique.

---

## 📊 TABLEAU RÉCAPITULATIF

| # | Panne | Variables affectées | Signature | Sévérité |
|---|-------|-------------------|-----------|----------|
| 1 | **surchauffe_compresseur** | Température, Courant, Vibration | Température +15°C, Courant +35A, Vibrations +150% | 🔴 CRITIQUE |
| 2 | **fuite_fluide** | Pression_BP, Température, Courant | Pression -40%, Température +8°C, Courant +20A | 🔴 CRITIQUE |
| 3 | **givrage_evaporateur** | Température, Humidité, Débit_air | Température -25°C, Humidité +50%, Débit -40% | 🟠 HAUTE |
| 4 | **panne_electrique** | Tension, Courant | Tension ±50V, Courant +60A | 🔴 CRITIQUE |
| 5 | **obstruction_conduit** | Débit_air, Pression_BP | Débit -70%, Pression -30% | 🟠 HAUTE |
| 6 | **défaillance_ventilateur** | Débit_air, Humidité | Débit -80%, Humidité +40% | 🟠 HAUTE |
| 7 | **capteur_defectueux** | Température, Courant | Température aberrante (±50°C), Courant aberrant | 🟡 MOYEN |
| 8 | **pression_anormale_HP** | Pression_HP, Courant | Pression +80%, Courant +40A | 🔴 CRITIQUE |
| 9 | **pression_anormale_BP** | Pression_BP, Température | Pression -50%, Température +10°C | 🟠 HAUTE |
| 10 | **défaut_dégivrage** | Température, Débit_air | Température -26°C, Débit -60% | 🟠 HAUTE |
| 11 | **défaillance_thermostat** | Température, Courant | Température aberrante (±30 ou +20°C), Courant +30A | 🟡 MOYEN |
| 12 | **défaillance_compresseur** | Courant, Vibration | Courant +70A, Vibrations +200% | 🔴 CRITIQUE |

---

## 🔍 DÉTAIL DE CHAQUE PANNE

### 1️⃣ SURCHAUFFE COMPRESSEUR 🔴
**Description:** Le compresseur surchauffe - trop de chaleur, vibrations, courant élevé

**Variables affectées:**
- `Température`: +15°C (très chaud)
- `Courant`: +35A (consommation excessive)
- `Vibration`: +150% (vibrations importantes)

**Causes possibles:**
- Gaz frigorigène insuffisant
- Compresseur usé
- Ventilateur ne refroidit pas

**Action corrective:** Arrêter immédiatement et laisser refroidir

---

### 2️⃣ FUITE DE FLUIDE 🔴
**Description:** Perte de fluide frigorigène - pressions et température anormales

**Variables affectées:**
- `Pression_BP`: -40% (très basse)
- `Température`: +8°C (trop chaud)
- `Courant`: +20A (compresseur travaille plus)

**Causes possibles:**
- Connexion desserrée
- Tuyau percé
- Joint défaillant

**Action corrective:** Ajouter du fluide / réparer la fuite

---

### 3️⃣ GIVRAGE ÉVAPORATEUR 🟠
**Description:** Accumulation de givre à l'évaporateur - trop de froid, peu de débit

**Variables affectées:**
- `Température`: -25°C (très froid)
- `Humidité`: +50% (trop d'humidité)
- `Débit_air`: -40% (circulation réduite)

**Causes possibles:**
- Cycle de dégivrage défaillant
- Filtre encrassé
- Hygrométrie élevée

**Action corrective:** Activer le dégivrage / nettoyer les filtres

---

### 4️⃣ PANNE ÉLECTRIQUE 🔴
**Description:** Problème électrique - tension instable, courant anormal

**Variables affectées:**
- `Tension`: +50V ou -50V (très instable)
- `Courant`: +60A (très élevé)

**Causes possibles:**
- Court-circuit
- Surcharge électrique
- Problème d'alimentation

**Action corrective:** Vérifier alimentation / appeler électricien

---

### 5️⃣ OBSTRUCTION CONDUIT 🟠
**Description:** Tuyau bloqué - débit d'air presque nul, pression basse haute

**Variables affectées:**
- `Débit_air`: -70% (presque bloqué)
- `Pression_BP`: -30% (trop basse)

**Causes possibles:**
- Encrassement du conduit
- Corps étranger
- Filtre très sale

**Action corrective:** Nettoyer / déboucher les conduits

---

### 6️⃣ DÉFAILLANCE VENTILATEUR 🟠
**Description:** Le ventilateur ne fonctionne pas / tourne lentement

**Variables affectées:**
- `Débit_air`: -80% (très peu d'air)
- `Humidité`: +40% (remonte)

**Causes possibles:**
- Ventilateur cassé
- Moteur défaillant
- Poulie/courroie usée

**Action corrective:** Remplacer ou réparer le ventilateur

---

### 7️⃣ CAPTEUR DÉFECTUEUX 🟡
**Description:** Un capteur envoie des valeurs erronées

**Variables affectées:**
- `Température`: Aberrante (±50°C - valeur totalement fausse)
- `Courant`: Aberrant (±80A - valeur impossible)

**Causes possibles:**
- Câble cassé
- Capteur usé
- Mauvais branchement

**Action corrective:** Vérifier les câbles / remplacer le capteur

---

### 8️⃣ PRESSION ANORMALE HP 🔴
**Description:** Pression haute élevée - système surchargé

**Variables affectées:**
- `Pression_HP`: +80% (très haute)
- `Courant`: +40A (compresseur travaille beaucoup)

**Causes possibles:**
- Condenseur encrassé
- Gaz trop chargé
- Ventilateur HP ne fonctionne pas

**Action corrective:** Nettoyer condenseur / vidanger si surcharge

---

### 9️⃣ PRESSION ANORMALE BP 🟠
**Description:** Pression basse très basse - manque de réfrigérant

**Variables affectées:**
- `Pression_BP`: -50% (très basse)
- `Température`: +10°C (trop chaud)

**Causes possibles:**
- Fuite de fluide
- Expandeur bloqué
- Filtre sec obstrué

**Action corrective:** Localiser et réparer fuite / ajouter fluide

---

### 🔟 DÉFAUT DÉGIVRAGE 🟠
**Description:** Système de dégivrage ne fonctionne pas - givre s'accumule

**Variables affectées:**
- `Température`: -26°C (trop froid)
- `Débit_air`: -60% (débit réduit par givre)

**Causes possibles:**
- Électrovanne dégivrage cassée
- Thermostat dégivrage défaillant
- Temporisateur bloqué

**Action corrective:** Vérifier électrovanne / remplacer thermostat

---

### 1️⃣1️⃣ DÉFAILLANCE THERMOSTAT 🟡
**Description:** Le thermostat ne régule pas bien la température

**Variables affectées:**
- `Température`: Aberrante (entre -30°C et +20°C - fluctue beaucoup)
- `Courant`: +30A (compresseur s'arrête/démarre)

**Causes possibles:**
- Sonde de température cassée
- Thermostat mal calibré
- Bulbe givré

**Action corrective:** Calibrer / remplacer thermostat

---

### 1️⃣2️⃣ DÉFAILLANCE COMPRESSEUR 🔴
**Description:** Le compresseur fonctionne mal - courant très élevé, vibrations excessives

**Variables affectées:**
- `Courant`: +70A (courant dangereux)
- `Vibration`: +200% (vibrations excessives et dangereuses)

**Causes possibles:**
- Compresseur usé/endommagé
- Roulements bloqués
- Piston coincé

**Action corrective:** Arrêter immédiatement / remplacer compresseur

---

## 📈 DISTRIBUTION PAR SÉVÉRITÉ

### 🔴 CRITIQUES (5) - Intervention IMMÉDIATE
- ✓ Surchauffe compresseur
- ✓ Fuite de fluide
- ✓ Panne électrique
- ✓ Pression HP anormale
- ✓ Défaillance compresseur

### 🟠 HAUTE (5) - Intervention URGENTE
- ✓ Givrage évaporateur
- ✓ Obstruction conduit
- ✓ Défaillance ventilateur
- ✓ Pression BP anormale
- ✓ Défaut dégivrage

### 🟡 MOYEN (2) - À SURVEILLER
- ✓ Capteur défectueux
- ✓ Défaillance thermostat

---

## 🎯 VARIABLES DU SYSTÈME

Le système utilise **8 variables** pour diagnostiquer ces pannes:

```
1. Température      (°C)       - Température dans la chambre
2. Pression_BP      (bar)      - Pression basse (évaporateur)
3. Pression_HP      (bar)      - Pression haute (condenseur)
4. Courant          (A)        - Consommation électrique
5. Tension          (V)        - Tension d'alimentation
6. Vibration        (% ou mm/s) - Vibrations du compresseur
7. Humidité         (%)        - Humidité relative
8. Débit_air        (m³/h)    - Débit d'air du ventilateur
```

---

## 🚀 UTILISATION DU SIMULATEUR

```bash
# Lancer avec pannes aléatoires (30% de chance)
python simulateur.py

# Lancer avec plus de pannes (50% de chance)
python simulateur.py --prob 0.5

# Lancer avec intervalles plus courts (15s)
python simulateur.py --interval 15

# Combiner options
python simulateur.py --prob 0.7 --interval 20 --duree-panne 180
```

---

## 📋 CHECKLIST DE DIAGNOSTIC

Pour chaque panne détectée, le système :

1. ✅ Identifie la panne par ses signatures
2. ✅ Calcule un score de confiance (0-100%)
3. ✅ Envoie une alerte avec description
4. ✅ Archive dans base d'apprentissage
5. ✅ Suggère action corrective

---

**Mise à jour:** Système adapté le 18/11/2025 - 12 pannes, 8 variables
