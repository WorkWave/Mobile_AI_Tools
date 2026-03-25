---
description: "Fetch the last 10 Firebase App Distribution builds for a project and OS. Usage: /getFirebaseBuilds [project] [android|ios]"
---

Parameters (parse from the command arguments):
- `project`: one of PestPac, RealGreen, WinTeam, RouteManager
- `os`: android or ios

Steps:

1. Load `$OUTPUT_DIR/<project>/config.json` to get `firebaseAppId.<os>` and `firebaseProject`
2. Load the Firebase key path for this project from session memory (set by `setup-firebase` skill). If not set → ask: "Please provide the path to your Firebase service account keys folder."
3. Call the Firebase App Distribution REST API directly (the Firebase CLI `appdistribution:releases:list` command is not available in this version):
```bash
python3 scripts/get_firebase_builds.py \
  --project <project> \
  --os <os> \
  --key <keyFilePath> \
  --config-dir <OUTPUT_DIR>
```
The script uses `google.oauth2.service_account` to obtain a Bearer token from the service account JSON and calls:
`GET https://firebaseappdistribution.googleapis.com/v1/projects/{project_id}/apps/{app_id}/releases?pageSize=10`

4. Parse and display:
```
Firebase Builds — <Project> (<OS>)
════════════════════════════════════
 [1]  v2.4.1 (build 241)   2026-03-18  "Fixed login crash on Android 14"
 [2]  v2.4.0 (build 240)   2026-03-15  "New scheduling module"
 ...
[10]  v2.3.5 (build 235)   2026-02-28  ""
[11]  Enter custom build ID or download URL
```

5. Ask: "Which build do you want to use? (1-11)"
   - If 1-10 → store the selected release in session memory and return `{ buildNumber, downloadUrl, version }`
   - If 11 → ask "Enter the custom Firebase release ID or direct download URL:" → store that

Rules:
- If `firebaseAppId` is empty in config.json → ask the user: "Firebase App ID for <project>/<os> is not set. Please provide it:" and persist it to config.json
- If Firebase CLI is not authenticated → run `firebase login --service-account <keyFile>` first
- If the project has no releases → say "No builds found for <project> on <os>. Upload a build to Firebase App Distribution first."
