---
name: setup-firebase
description: Scan a folder of Firebase service account JSON keys, auto-match them to WorkWave projects (PestPac, RealGreen, WinTeam, RouteManager), persist the mapping to firebase_keys.json, and pre-populate each project's config.json with Firebase data.
---

# Firebase Key Setup

## Step 0 — Check for saved Firebase keys config

Check if `firebase_keys.json` exists in `$OUTPUT_DIR/firebase_keys.json` (the output directory root, set in session from the wizard's Step 0).

**If `firebase_keys.json` EXISTS**, read it and show:
```
Firebase keys already configured:
═════════════════════════════════════════════════════════
✅  PestPac      → /path/to/pestpac.json      (pestpac-xxxxx)
✅  RealGreen    → /path/to/realgreen.json    (realgreen-e72e9)
✅  WinTeam      → /path/to/winteam.json      (winteam-xxxxx)
❌  RouteManager → NOT FOUND
═════════════════════════════════════════════════════════

  [1] Use these keys
  [2] Reconfigure (scan a different folder)
```
- If [1] → load the mapping into session memory, skip to **Step 5 — Pre-populate configs**
- If [2] → continue to Step 1

**If `firebase_keys.json` does NOT exist**, continue to Step 1.

---

## Step 1 — Ask for keys folder

```
Where are your Firebase service account key files?
Enter the absolute path to the folder containing your .json key files:
```

---

## Step 2 — Scan the folder

Read all `.json` files in the folder. For each file, read the `project_id` field.

---

## Step 3 — Match to known projects

Match by checking if `project_id` contains a known identifier:

| project_id contains | Matched Project |
|--------------------|-----------------|
| `pestpac` | PestPac |
| `realgreen` | RealGreen |
| `winteam` | WinTeam |
| `routemanager` or `route-manager` | RouteManager |

---

## Step 4 — Display match table

```
Firebase Key Mapping
═════════════════════════════════════════════════════════
✅  PestPac      → /path/to/pestpac.json      (pestpac-xxxxx)
✅  RealGreen    → /path/to/realgreen.json    (realgreen-e72e9)
✅  WinTeam      → /path/to/winteam.json      (winteam-xxxxx)
❌  RouteManager → NOT FOUND
═════════════════════════════════════════════════════════
```

For any unmatched project:
```
No Firebase key found for RouteManager.
Enter the path to the RouteManager service account JSON (or press Enter to skip):
```

---

## Step 5 — Persist mapping

### 5a — Save to firebase_keys.json

Write the mapping to `$OUTPUT_DIR/firebase_keys.json`:

```json
{
  "lastUpdated": "<ISO timestamp>",
  "keysFolder": "/absolute/path/to/keys/folder",
  "projects": {
    "PestPac": {
      "keyPath": "/absolute/path/to/pestpac.json",
      "projectId": "pestpac-xxxxx"
    },
    "RealGreen": {
      "keyPath": "/absolute/path/to/realgreen.json",
      "projectId": "realgreen-e72e9"
    },
    "WinTeam": {
      "keyPath": "/absolute/path/to/winteam.json",
      "projectId": "winteam-xxxxx"
    },
    "RouteManager": {
      "keyPath": "/absolute/path/to/routemanager.json",
      "projectId": "routemanager-xxxxx"
    }
  }
}
```

Omit any project that was skipped (no key found and user pressed Enter).

### 5b — Store in session memory

```json
{
  "firebaseKeys": {
    "PestPac":      "/absolute/path/to/pestpac.json",
    "RealGreen":    "/absolute/path/to/realgreen.json",
    "WinTeam":      "/absolute/path/to/winteam.json",
    "RouteManager": "/absolute/path/to/routemanager.json"
  }
}
```

### 5c — Verify Firebase CLI auth

For each matched key:
```bash
firebase projects:list --json --service-account <keyPath>
```
If auth fails → warn: "⚠️ Key for <Project> could not authenticate. Check that it is a valid service account JSON."

---

## Step 6 — Pre-populate project configs

For each matched project, extract data from the service account JSON:

**Fields to extract from each `.json` key file:**

| Service account field | Maps to config.json field |
|----------------------|---------------------------|
| `project_id` | `firebaseProject` |
| file path (absolute) | `firebaseServiceAccountPath` |
| `client_email` | (stored as `firebaseServiceAccountEmail`, for reference) |

**Known static defaults per project:**

| Field | PestPac | RealGreen | WinTeam | RouteManager |
|---|---|---|---|---|
| `repository` | WorkWave/PestPac-Mobile | WorkWave/Real-Green-Mobile | WorkWave/WinTeam-Mobile | WorkWave/RouteManager-Mobile |
| `defaultBranch` | dev | dev | dev | dev |
| `bundleId.android` | com.workwave.pestpac | com.workwave.realgreen | com.workwave.winteam | com.workwave.routemanager |
| `bundleId.ios` | com.workwave.pestpac | com.workwave.realgreen | com.workwave.winteam | com.workwave.routemanager |
| `authSchema.type` | sso | custom | sso | standard |
| `authSchema.fields` | [email, password] | [companyNumber, employeeId, password] | [email, password] | [email, password] |
| `stepTimeoutMs` | 10000 | 10000 | 10000 | 10000 |

### 6a — Fetch Firebase App IDs from the API

For each matched project, use the service account key to obtain an access token and query the Firebase Management API to retrieve the Android and iOS App IDs:

```bash
python3 - <<'EOF'
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import requests, json

key_path = "<keyPath>"
project_id = "<project_id>"

creds = service_account.Credentials.from_service_account_file(
    key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
creds.refresh(Request())
headers = {"Authorization": f"Bearer {creds.token}"}

base = f"https://firebase.googleapis.com/v1beta1/projects/{project_id}"
android = requests.get(f"{base}/androidApps", headers=headers).json().get("apps", [])
ios     = requests.get(f"{base}/iosApps",     headers=headers).json().get("apps", [])

print("android:", android[0]["appId"] if android else "")
print("ios:",     ios[0]["appId"]     if ios     else "")
EOF
```

If the API call fails or returns no apps → leave `firebaseAppId` empty and note it in the result.

### 6b — Write project config.json

For each matched project, check if `$OUTPUT_DIR/<project>/config.json` exists:

**If config.json does NOT exist → create it:**

Write `$OUTPUT_DIR/<project>/config.json` with all known fields pre-filled:

```json
{
  "name": "<ProjectName>",
  "repository": "<from table above>",
  "localRepoPath": "",
  "defaultBranch": "dev",
  "firebaseProject": "<project_id from key file>",
  "firebaseServiceAccountPath": "<absolute path to key file>",
  "firebaseServiceAccountEmail": "<client_email from key file>",
  "firebaseAppId": {
    "android": "<fetched from API, or empty>",
    "ios": "<fetched from API, or empty>"
  },
  "bundleId": {
    "android": "<from table above>",
    "ios": "<from table above>"
  },
  "authSchema": {
    "type": "<from table above>",
    "fields": ["<from table above>"]
  },
  "stepTimeoutMs": 10000
}
```

**If config.json EXISTS → merge only missing or empty fields:**

Read the existing config.json. Update **only if the field is missing or empty string**:
- `firebaseProject` ← `project_id` from key file
- `firebaseServiceAccountPath` ← absolute path to key file
- `firebaseServiceAccountEmail` ← `client_email` from key file
- `firebaseAppId.android` ← fetched from API
- `firebaseAppId.ios` ← fetched from API

Do **not** overwrite fields that already have a value. Write the merged result back to `config.json`.

### Show result:

```
Project configs updated:
  ✅ PestPac     → ~/WWMobileTestAgentAIResults/PestPac/config.json (created, App IDs fetched)
  ✅ RealGreen   → ~/WWMobileTestAgentAIResults/RealGreen/config.json (updated, App IDs fetched)
  ⚠️ WinTeam     → ~/WWMobileTestAgentAIResults/WinTeam/config.json (created, App IDs not available)
  ⚠️ RouteManager → skipped (no key available)
```
