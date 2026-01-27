# Pre-Deployment Validation Script

## Overzicht

Het `pre-deploy-check.sh` script voorkomt deployment chaos door systematische validatie VOORDAT je naar productie pusht. Geïnspireerd op de 2026-01-04 deployment retrospective waar 5 commits nodig waren door uncommitted files en schema mismatches.

## Gebruik

```bash
# Voor elke git push naar main:
./scripts/pre-deploy-check.sh
```

Het script geeft exit codes:
- **0** = ✅ GO - Safe to deploy
- **1** = ⛔ NO-GO - Fix errors before deploying

## Checks

### 1. Git Status Audit
- Detecteert uncommitted changes in kritieke files
- Kritieke paden: `src/database/`, `main.py`, `requirements.txt`, `config.yaml`
- **Error** als kritieke files uncommitted zijn

### 2. Database Model Changes
- Checkt of `models.py` wijzigingen heeft
- Waarschuwt als model users (generator.py, fetcher.py) niet mee gecommit zijn
- Voorkomt: `'X' is an invalid keyword argument` runtime errors

### 3. Breaking Changes Scan
- Grep naar `nullable=False`, `NOT NULL`, `ForeignKey` in database models
- Waarschuwt als migratie script nodig kan zijn
- Voorkomt: `NOT NULL constraint failed` errors

### 4. Dependency Changes
- Detecteert wijzigingen in `requirements.txt`
- Laat zien welke dependencies added/removed zijn
- Reminder: `pip install -r requirements.txt` op server

### 5. Configuration Changes
- Checkt wijzigingen in `config.yaml`, `sources.yaml`
- Informeert over auto-deployment van config

### 6. Import Tests (Pre-Push Dry Run)
- Test kritieke imports in lokale venv
- Voorkomt import errors op server
- Test modules: models, generator, fetcher, obsidian

### 7. Atomic Commit Validation
- Detecteert anti-patronen (models.py staged maar generator.py niet)
- Waarschuwt bij potentieel niet-atomische commits
- Voorkomt incomplete deployments

## Output Voorbeelden

### ✅ Safe to Deploy

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results:
  ✓ Checks passed: 7
  ⚠ Warnings:      0
  ✗ Errors:        0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ GO - Safe to deploy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next steps:
  1. git push origin main
  2. Wait 15 seconds for Forgejo auto-deployment
  3. Verify: ssh dtd 'cd ~/apps/ai-news-bot && git log -1 --oneline'
```

### ⚠️ Proceed with Caution

```
Results:
  ✓ Checks passed: 5
  ⚠ Warnings:      2
  ✗ Errors:        0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  PROCEED WITH CAUTION - Review warnings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommended actions:
  1. Review all warnings above
  2. Ensure you have a rollback plan
  3. Monitor deployment closely
```

### ⛔ NO-GO - Errors Found

```
Results:
  ✓ Checks passed: 3
  ⚠ Warnings:      1
  ✗ Errors:        2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ NO-GO - Fix errors before deploying
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Workflow Integratie

### Optie 1: Manueel (Aanbevolen voor start)

```bash
# Maak wijzigingen
git add .
git commit -m "feat: nieuwe feature"

# Valideer VOOR push
./scripts/pre-deploy-check.sh

# Als GO:
git push origin main
```

### Optie 2: Git Pre-Push Hook (Automatisch)

Maak `.git/hooks/pre-push`:

```bash
#!/bin/bash
echo "Running pre-deployment validation..."
./scripts/pre-deploy-check.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "Pre-deployment validation failed!"
    echo "Fix errors before pushing, or use: git push --no-verify"
    exit 1
fi
```

Maak executable:
```bash
chmod +x .git/hooks/pre-push
```

Bypass (alleen in noodgevallen):
```bash
git push --no-verify
```

## Troubleshooting

### "Virtual environment not found"

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Import failed" errors

Check of alle dependencies geïnstalleerd zijn:
```bash
./venv/bin/pip list
./venv/bin/pip install -r requirements.txt
```

### False Positives voor Breaking Changes

Het script checked alleen `src/database/*.py` bestanden.
Als je false positives ziet, check de grep pattern in het script.

## Impact

**Voor de 2026-01-04 deployment:**
- ❌ 5 separate commits nodig
- ❌ 45 minuten debugging tijd
- ❌ 3 gefaalde deployments

**Met dit script:**
- ✅ Atomic commits forced
- ✅ Pre-push validatie
- ✅ One-shot deployments

## Zie Ook

- `CLAUDE.md` - Deployment retrospective (2026-01-04)
- `TODO.md` - Deployment checklist items
- `scripts/health-check.sh` - Post-deployment validation (TODO)
