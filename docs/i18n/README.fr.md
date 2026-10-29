# Lanshu OpenAI Media API

**Génération d’images et transcription vocale pour les agents, avec suivi de l’utilisation.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Runtime](https://img.shields.io/badge/runtime-standard_library-475569?style=flat-square)](../../README.md#requirements)
[![Documentation](https://img.shields.io/badge/docs-7_languages-0F766E?style=flat-square)](../../README.md#documentation)
[![License](https://img.shields.io/badge/license-MIT-16A34A?style=flat-square)](../../LICENSE)
[![岚叔 X](https://img.shields.io/badge/%E5%B2%9A%E5%8F%94-X-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/LufzzLiz)

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md)

Une petite interface Python et un skill distribuable pour les API OpenAI de génération d’images, de transcription de fichiers et de consultation des coûts. Chaque appel réussi conserve les fichiers produits, l’identifiant de requête et l’utilisation. Le README anglais constitue la documentation principale.

## Fonctionnalités

- Générer des images avec Sunburst ou Flare en choisissant taille, qualité, quantité et format.
- Transcrire des fichiers audio ou vidéo avec GPT-Transcribe, des indications de langue et des mots-clés métier.
- Consulter les coûts par projet, clé API et modèle avec une clé d’administration.
- Récupérer les résultats d’exécution en JSON pour les agents et les scripts.

## Modèles sélectionnés

| Usage | Modèle | Choix |
| --- | --- | --- |
| Priorité à la qualité d’image | `gpt-image-2.5-sunburst` | Image par défaut |
| Priorité à la rapidité | `gpt-image-2.5-flare` | Brouillons rapides |
| Transcription de fichiers audio et vidéo | `gpt-transcribe` | ASR par défaut |

Documentation des modèles vérifiée le 2026-10-29. Un modèle explicitement demandé est conservé, sans substitution automatique.

## Prérequis

Python 3.9 ou ultérieur ; seules les bibliothèques standard sont requises à l’exécution. curl, ffprobe et zsh sont facultatifs. curl est privilégié pour HTTP, ffprobe relève la durée d’autres formats audio et zsh peut charger les variables déjà exportées dans ~/.zshrc.

## Démarrage rapide

Exécutez les commandes depuis le répertoire du projet. Configurez votre clé API ordinaire dans l’environnement local existant avant un appel facturé.

### Générer une image

```bash
python3 scripts/openai_media.py image \
  --prompt "Un chat roux sur un rebord de fenêtre ensoleillé, photographie naturelle, sans texte" \
  --out output/cat.png
```

Valeurs par défaut : une image PNG de 1024×1024 en qualité medium. Pour un brouillon rapide, ajoutez --model gpt-image-2.5-flare --quality low ; pour davantage de détails, utilisez --quality high. Les options --prompt-file, --size, --n et --output-format sont aussi disponibles. --dry-run affiche uniquement la requête prévue. Un fichier de sortie ou de métadonnées existant bloque l’appel avant facturation.

### Transcrire un enregistrement

```bash
python3 scripts/openai_media.py transcribe \
  --input /absolute/path/recording.wav \
  --languages fr \
  --keyword OpenAI \
  --out output/transcript.txt
```

Répétez --languages pour plusieurs langues attendues. --prompt fournit le contexte et --keyword des termes pertinents. empty_transcript: true signale un texte vide. Cette interface traite les fichiers ; elle ne propose ni microphone en direct, ni séparation des locuteurs, ni horodatage mot à mot.

### Consulter les coûts

```bash
python3 scripts/openai_media.py costs \
  --date 2026-10-29 --timezone UTC \
  --project-id YOUR_PROJECT_ID \
  --key-name YOUR_KEY_NAME \
  --model gpt-image-2.5-sunburst \
  --out output/costs.json
```

Remplacez la date et les identifiants par les valeurs réelles. Si le nom de clé est ambigu, utilisez --api-key-id. Cette commande emploie une clé d’administration.

### Installer la commande

Le script source fonctionne sans installation. Pour disposer d’une commande dédiée, installez le projet dans un environnement virtuel.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
lanshu-openai-media-api models
```

## Identifiants

| Variable | Utilisation |
| --- | --- |
| `OPENAI_API_KEY` | Génération d’images et transcription |
| `OPENAI_ADMIN_KEY` | Coûts et résolution des noms de clés |
| `OPENAI_ADMIN_API_KEY` | Alias compatible de la clé d’administration |

Un --env-file explicite remplace la variable correspondante. Sinon, le processus utilise son environnement, puis les exports de ~/.zshrc si nécessaire. --no-shell-env désactive ce repli. Le fichier d’identifiants est analysé comme des affectations littérales, sans exécuter son contenu. La sortie de démarrage du shell est ignorée et la clé passe par un tube mémoire privé.

Les clés restent dans votre environnement local ou fichier d’identifiants existant. Elles sont exclues du dépôt, des journaux et des archives. La clé d’administration sert à consulter les coûts.

## Utilisation par d’autres agents

La racine contient SKILL.md, les métadonnées de l’agent et les scripts. La commande ci-dessous produit un dossier de skill autonome, une archive ZIP et un manifeste de sommes de contrôle. Placez le dossier dans le répertoire de skills de votre agent ; Codex utilise généralement ~/.codex/skills/. Le nom d’invocation est $lanshu-openai-media-api. --force remplace une précédente compilation.

```bash
python3 tools/build_skill.py --output-dir dist
```

## Sorties et limites de facturation

Les appels média enregistrent le fichier demandé et un fichier .metadata.json associé. Celui-ci conserve les paramètres, le statut HTTP, le request ID, l’usage, la durée, les chemins et les métadonnées de réponse, sans clé ni image encodée en base64.

usage décrit la consommation. Le champ amount de l’API Costs représente des totaux journaliers UTC. Les filtres par projet, clé et modèle ne donnent pas un reçu par request ID. Une date locale peut chevaucher plusieurs intervalles UTC : consultez returned_daily_buckets et date_window_exact. L’absence de lignes ne prouve pas la gratuité.

Les requêtes POST ne sont pas relancées automatiquement et le modèle n’est pas remplacé. Une erreur réseau GET est réessayée au maximum une fois. Après une interruption, examinez les fichiers et les métadonnées avant de poursuivre.

## Développement et vérifications

Les tests de protocole utilisent un serveur HTTP local et des données synthétiques, sans clé réelle. La CI cible Python 3.9, 3.11 et 3.13. Le CLI a aussi été vérifié avec une image Sunburst et 30 secondes de parole chinoise ; cela ne constitue pas une évaluation de précision dans chaque langue documentée.

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -B tools/check_docs.py
python3 -B tools/build_skill.py --output-dir dist
```

Consultez les [notes API](../../references/api-notes.md) pour les paramètres, les tarifs datés et les sources officielles. Faites évoluer ensemble le guide anglais, les traductions et le skill.

## Licence

[MIT](../../LICENSE) · Copyright © 2026 Lanshu.
