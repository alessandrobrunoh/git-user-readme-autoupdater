# 🤖 GitHub Profile README Auto-Updater

Genera automaticamente un bellissimo README per il tuo profilo GitHub con statistiche in tempo reale!

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Caratteristiche

- 📊 **Statistiche Complete** - Repos, linguaggi, linee di codice
- 🏆 **Top 5 Repositories** - I tuoi progetti più stellati
- 💻 **Top 5 Linguaggi** - I linguaggi che usi di più con grafici
- 🎨 **Design Accattivante** - Markdown ben strutturato
- ⚙️ **Altamente Configurabile** - Includi/escludi repos e linguaggi
- 🤖 **Automazione** - Integrazione con GitHub Actions

## 🚀 Quick Start

```bash
# 1. Clona il repository
git clone https://github.com/yourusername/git-user-readme-autoupdater.git
cd git-user-readme-autoupdater

# 2. Installa le dipendenze
pip install -r requirements.txt

# 3. Configura il token GitHub
export GIT_TOKEN="your_github_token_here"

# 4. Personalizza la configurazione
cp config.example.yaml config.yaml
nano config.yaml

# 5. Genera il README
python generate_readme.py
```

## 📋 Requisiti

- Python 3.7 o superiore
- GitHub Personal Access Token con permessi `repo` e `read:user`

## ⚙️ Configurazione

Personalizza il file `config.yaml`:

```yaml
profile:
  name: "Il Tuo Nome"
  description: |
    Sviluppatore appassionato che ama costruire cose incredibili

repositories:
  include:
    - "torvalds/linux"  # Repos a cui hai contribuito
  exclude:
    - "username/test"   # Repos da nascondere

languages:
  exclude:
    - "HTML"  # Linguaggi da escludere
    - "CSS"
```

## 🤖 Automazione

Il progetto include un workflow GitHub Actions che aggiorna automaticamente il tuo profilo ogni giorno!

1. Aggiungi `GIT_TOKEN` ai secrets del repository
2. Il workflow si attiverà automaticamente
3. Il tuo README sarà sempre aggiornato

## 📚 Documentazione Completa

Per istruzioni dettagliate, consulta [DOCUMENTATION.md](DOCUMENTATION.md)

## 📊 Esempio di Output

Il README generato include:

- ✅ Statistiche generali (repos, linee di codice, stars)
- ✅ Top 5 repositories con dettagli
- ✅ Top 5 linguaggi con grafici a barre
- ✅ Tabella distribuzione linguaggi
- ✅ Lista completa repositories
- ✅ Timestamp ultimo aggiornamento

## 🛠️ Utilizzo Avanzato

```bash
# Con config personalizzato
python generate_readme.py my-config.yaml

# Con output personalizzato
python generate_readme.py config.yaml PROFILE.md
```

## 🤝 Contributi

I contributi sono benvenuti! Sentiti libero di:

- 🐛 Segnalare bug
- 💡 Proporre nuove funzionalità
- 🔧 Inviare pull request

## 📄 Licenza

MIT License - Vedi [LICENSE](LICENSE) per dettagli

## 🌟 Supporta il Progetto

Se trovi utile questo progetto, lascia una ⭐!

---

**Made with ❤️ by developers, for developers**
