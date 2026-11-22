# Fork „Kingsteam“ von ha-secvest

Dieses Repo ist eine Abzweigung (Fork) der Integration [thomasdanz/ha-secvest](https://github.com/thomasdanz/ha-secvest) (MIT-Lizenz) für die ABUS Secvest.

## Warum ein Fork
Im Original gilt ein Code in Home Assistant immer **für Aktivieren und Deaktivieren gemeinsam**. Eine Automation („Haus verlassen“) soll die Anlage aber **ohne Code scharf** schalten können, während **Unscharf** nur mit Code geht.

## Was anders ist (nur das)
- Neue Einstellung **„Aktivieren ohne Code“** unter Optionen → Codes (erscheint, sobald mindestens ein Code angelegt ist). Standard: aus.
- Ist sie an: Scharf und intern scharf gehen ohne Code (`code_arm_required: false`). Unscharf braucht weiterhin einen Code. Wird beim Aktivieren trotzdem ein Code eingegeben, wird er geprüft (falscher Code → abgelehnt, nichts wird gesendet).
- Tests: `tests/test_arm_without_code.py`.
- Version `1.1.2+ks.1` (Originalversion + eigene Zählung), Links in `manifest.json` zeigen auf dieses Repo.

Alles andere ist unverändert, auch die Schutzregeln des Originals (eine Verbindung, mindestens 24 s Abstand, Stopp nach falschem Passwort, Zertifikat fest).

## Getestet
- Automatische Tests mit der simulierten Zentrale des Originals (736 Tests, ruff, mypy).
- **Noch nicht mit der echten Anlage** (Secvest Touch FUAA50100, Firmware 3.01.21). Das Original ist mit FUAA50500 / 3.01.31 getestet.

## Neue Versionen des Originals übernehmen
```bash
git fetch upstream main --no-tags
git checkout -b update-<version> main
git merge upstream/main        # Konflikte meist nur in manifest.json, pyproject.toml, CHANGELOG.md, stored_entries.json
uv sync && uv run pytest && uv run ruff check . && uv run mypy custom_components tests scripts
```
Danach Version auf `<neue Version>+ks.1` setzen, CHANGELOG ergänzen, Tests grün → nach `main`.

## Regeln
- Keine Daten des Hauses im Repo (Adressen, Codes, Seriennummern, Zonen- oder Raumnamen, Zugangsdaten).
- Nie gegen die echte Zentrale entwickeln oder testen.
- Die Tests des Originals nie abschwächen oder überspringen.
