# GitHub Profile README Auto-Updater

Uno script Python che genera automaticamente un bellissimo README per il tuo profilo GitHub con statistiche in tempo reale.

## ✨ Caratteristiche

- 📊 **Statistiche Complete**: Visualizza repos, linguaggi, linee di codice
- 🏆 **Top 5 Repositories**: I tuoi progetti più stellati
- 💻 **Top 5 Linguaggi**: I linguaggi che usi di più
- 🎨 **Design Accattivante**: Markdown ben strutturato con grafici e tabelle
- ⚙️ **Configurabile**: Includi/escludi repos e linguaggi
- 🤖 **Automatizzabile**: Integrazione con GitHub Actions

## 📋 Requisiti

- Python 3.7+
- GitHub Personal Access Token con permessi `repo` e `read:user`

## 🚀 Installazione

### 1. Clone il repository

```bash
git clone https://github.com/yourusername/git-user-readme-autoupdater.git
cd git-user-readme-autoupdater
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Configura il token GitHub

Crea un Personal Access Token su GitHub:
1. Vai su Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Clicca "Generate new token (classic)"
3. Seleziona i permessi: `repo` e `read:user`
4. Copia il token generato

Esporta il token come variabile d'ambiente:

```bash
export GIT_TOKEN="your_github_token_here"
```

Oppure crea un file `.env`:

```bash
echo "export GIT_TOKEN='your_github_token_here'" >> ~/.bashrc
source ~/.bashrc
```

### 4. Configura il profilo

Copia il file di esempio e personalizzalo:

```bash
cp config.example.yaml config.yaml
nano config.yaml  # o usa il tuo editor preferito
```

## ⚙️ Configurazione

Il file `config.yaml` supporta le seguenti opzioni:

```yaml
# Informazioni del profilo
profile:
  name: "Il Tuo Nome"
  description: |
    Una breve descrizione di te
    Può essere su più righe

# Gestione repositories
repositories:
  # Aggiungi repos a cui hai contribuito
  include:
    - "username/repo-name"

  # Escludi repos che non vuoi mostrare
  exclude:
    - "username/test-repo"

# Gestione linguaggi
languages:
  # Escludi linguaggi dalle statistiche
  exclude:
    - "HTML"
    - "CSS"
```

### Opzioni disponibili

#### Profile
- **name**: Il nome da visualizzare nel README
- **description**: Descrizione che apparirà sotto il titolo

#### Repositories
- **include**: Lista di repos (formato `owner/repo`) da includere anche se non sono tuoi
- **exclude**: Lista di repos da escludere dalle statistiche

#### Languages
- **exclude**: Lista di linguaggi da escludere (utile per HTML, CSS, etc.)

## 🎯 Utilizzo

### Esecuzione base

```bash
python generate_readme.py
```

Questo comando:
1. Legge la configurazione da `config.yaml`
2. Si connette a GitHub usando `GIT_TOKEN`
3. Recupera tutte le tue repositories
4. Calcola le statistiche
5. Genera `README.md`

### Con file di configurazione personalizzato

```bash
python generate_readme.py my-config.yaml
```

### Con output personalizzato

```bash
python generate_readme.py config.yaml MY_PROFILE.md
```

## 🤖 Automazione con GitHub Actions

Per aggiornare automaticamente il tuo profilo, crea un workflow GitHub Actions.

### 1. Crea il file workflow

Crea `.github/workflows/update-readme.yml`:

```yaml
name: Update README

on:
  schedule:
    # Esegui ogni giorno alle 00:00 UTC
    - cron: '0 0 * * *'
  workflow_dispatch:  # Permette esecuzione manuale

jobs:
  update-readme:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate README
        env:
          GIT_TOKEN: ${{ secrets.GIT_TOKEN }}
        run: python generate_readme.py

      - name: Commit and push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add README.md
          git diff --quiet && git diff --staged --quiet || git commit -m "🤖 Auto-update README"
          git push
```

### 2. Aggiungi il secret su GitHub

1. Vai nelle Settings del tuo repository
2. Seleziona Secrets and variables → Actions
3. Clicca "New repository secret"
4. Nome: `GIT_TOKEN`
5. Valore: Il tuo Personal Access Token

### 3. Attiva il workflow

Il workflow partirà automaticamente ogni giorno, oppure puoi eseguirlo manualmente dalla tab Actions.

## 📊 Output Esempio

Lo script genera un README con:

```markdown
# Hi, Welcome to username's Profile! 👋

Descrizione del profilo...

## 📊 GitHub Statistics

### 📈 Overview
- Total Repositories: 25
- Total Lines of Code: 150,000
- Total Stars: 250
- Total Forks: 45

### 🏆 Top 5 Repositories
1. **awesome-project** - ⭐ 120 | 🔱 25
   - Un progetto fantastico
   - Language: Python | Lines: 25,000

### 💻 Top 5 Languages
1. **Python** - 45.2%
   ```
   ██████████████████████████████████████░░░░░░░░░░░░
   ```

### 📊 Language Distribution
| Language | Percentage | Usage |
|----------|------------|-------|
| Python   | 45.2%      | █████████ |

🤖 This profile was automatically updated on 2025-10-22 12:00:00
```

## 🛠️ Risoluzione Problemi

### Errore: GIT_TOKEN non trovato

Assicurati di aver esportato la variabile d'ambiente:

```bash
export GIT_TOKEN="your_token"
```

### Errore: Rate limit exceeded

L'API GitHub ha limiti di richieste. Con un token autenticato hai 5000 richieste/ora.

### Errore: 404 Not Found per repository inclusa

Verifica che:
1. Il nome della repo sia corretto (formato: `owner/repo`)
2. La repo sia pubblica o che il token abbia accesso
3. La repo esista effettivamente

## 📝 Formati supportati

Lo script supporta file di configurazione in:
- **YAML** (`.yaml`, `.yml`) - Raccomandato
- **JSON** (`.json`)
- **TOML** (`.toml`)

## 🤝 Contributi

I contributi sono benvenuti! Sentiti libero di aprire issue o pull request.

## 📄 Licenza

MIT License - Sentiti libero di usare questo progetto come preferisci.

## 🔗 Link Utili

- [GitHub Personal Access Tokens](https://github.com/settings/tokens)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub REST API](https://docs.github.com/en/rest)

---

Fatto con ❤️ per la community degli sviluppatori
