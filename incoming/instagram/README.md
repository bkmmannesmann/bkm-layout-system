# Eingang Instagram

Fertige Karussells, die als HTML aus Claude Design kommen und **nicht** über den Content-Plan
laufen. Ein ZIP wird beim Bau hierher entpackt:

```bash
python3 scripts/build_instagram.py ~/Downloads/<projekt>.zip --slug <name>
```

Der Regelweg für Posts ist `content/instagram/<post>/content.json`, siehe `docs/INSTAGRAM.md`.
Neue Designvorlagen gehören nach `templates/instagram/referenz/`, nicht hierher.
