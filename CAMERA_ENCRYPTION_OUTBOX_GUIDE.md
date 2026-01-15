# 🎥 Camera-Side Encryption & OUTBOX Guide  
### Capture • Encrypt • Queue • Ship (Safely)

## 🔗 This guide pairs with

- **CAMERA_ENCRYPTION_OUTBOX_GUIDE.md** or **CAMERA_ENCRYPTION_OUTBOX_GUIDE_GNUPG.md** — camera-side encryption & OUTBOX
- **SECURE_CAMERA_RECEIVER_SYNC.md** — SSH transport & automation
- **RECEIVER_VERIFICATION_INGEST_GUIDE.md** — receiver-side verification & ingest

These guides form a single, coherent pipeline and are intended to be used together.


---

## 🧠 Purpose

This document defines the **camera-side responsibilities** in the secure capture pipeline.

The camera node is the **only place where plaintext exists**.  
Its job is to:
- Capture video reliably
- Encrypt immediately after finalization
- Queue encrypted artifacts
- Never export plaintext

This guide completes the **Camera → Transport → Receiver** trilogy.

---

## 🎯 Camera Goals

🟢 Plaintext never leaves the node  
🟢 Encryption is automatic and deterministic  
🟢 OUTBOX behaves like a safe queue  
🟢 Failures do not cause data loss  
🟢 Artifacts are verifiable downstream  

---

## 🧱 Trust Boundary (Critical)

```
┌─────────────────────────────┐
│ CAMERA NODE (TRUSTED)       │
│ ├─ Plaintext allowed        │
│ ├─ LUKS at rest             │
│ └─ Encryption authority     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ OUTBOX (UNTRUSTED ZONE)     │
│ ├─ Encrypted only           │
│ ├─ Safe to copy/ship        │
│ └─ No secrets inside        │
└─────────────────────────────┘
```

Once data enters **OUTBOX**, it must be assumed hostile environments await.

---

## 📁 Canonical Directory Layout

```
/media/user/disk/
├── videos/        # plaintext clips (local only)
├── outbox/        # encrypted artifacts (export only)
├── logs/          # camera + detection logs
└── tmp/           # transient working files
```

❌ OUTBOX must never contain plaintext  
❌ videos/ must never be synced  

---

## 🔐 Encryption Strategy

### Recommended Tool: `age`

Why `age`:
- Modern, simple, scriptable
- Public-key encryption
- Minimal metadata leakage

### Key Rules

- Camera stores **recipient public key only**
- Private key never touches the camera
- Loss of camera ≠ loss of archive

---

## 🔑 Key Setup (Once)

On receiver (or secure admin machine):
```bash
age-keygen -o camera_receiver.key
```

Copy **public key only** to camera:
```bash
age-keygen -y camera_receiver.key > camera_receiver.pub
```

Place on camera:
```
/etc/camkeys/receiver.pub
```

Permissions:
```bash
chmod 444 /etc/camkeys/receiver.pub
```

---

## 🎬 Clip Finalization Flow

1. Camera records clip to `videos/`
2. Clip is closed and stable
3. Encryption job triggers
4. Encrypted file written to `outbox/`
5. Hash + manifest updated
6. Plaintext handled per retention policy

---

## 🔁 Encrypt + Queue (Canonical Example)

```bash
age -r $(cat /etc/camkeys/receiver.pub)   -o /media/user/disk/outbox/clip_20260115_1200.mp4.age   /media/user/disk/videos/clip_20260115_1200.mp4
```

Generate hash:
```bash
sha256sum /media/user/disk/outbox/clip_*.age   > /media/user/disk/outbox/clip_20260115_1200.mp4.age.sha256
```

---

## 📜 Manifest Design (Strongly Recommended)

Example `manifest.json` entry:
```json
{
  "clip": "clip_20260115_1200.mp4.age",
  "sha256": "abc123...",
  "timestamp": "2026-01-15T12:00:00Z",
  "camera_id": "cam1",
  "software": "AI_CAM_VIDSec v1.0"
}
```

Manifests:
- Aid forensic reconstruction
- Prevent silent truncation
- Enable downstream validation

---

## 🧹 Plaintext Retention Policy

Choose **one**:

### Option A — Short Retention (recommended)
- Keep plaintext for N hours
- Auto-delete after verification

### Option B — No Retention
- Delete plaintext immediately after encryption
- Maximum secrecy, minimal recovery window

### Option C — Manual Review Window
- Retain until operator confirmation
- Requires discipline

🚨 Plaintext deletion should be deliberate and logged.

---

## 🧪 Validation Before Shipping

Before OUTBOX sync:
```bash
ls -lh outbox/
sha256sum -c *.sha256
```

Only verified files should leave the node.

---

## 🧰 Automation Options

### Option 1 — Post-clip hook
- Encryption script called after recording completes

### Option 2 — systemd path unit
- Watches `videos/` for new files

### Option 3 — Periodic job
- Encrypts any unprocessed clips

**Rule:** automation must be idempotent.

---

## 📴 Offline Safety

OUTBOX is safe to:
- Copy to USB
- Store on staging disks
- Transmit over hostile networks

Because:
- No secrets inside
- No plaintext
- Integrity verifiable

---

## ❌ Camera Anti-Patterns

🚫 Encrypting during recording  
🚫 Storing private keys on camera  
🚫 Syncing `videos/` directory  
🚫 Overwriting encrypted files  
🚫 Mixing logs with OUTBOX data  

---

## 🧠 Operational Philosophy

> **The camera is the root of trust.**

- If encryption fails, stop exporting
- If verification fails, stop syncing
- Silence is acceptable
- Silent corruption is not

---

## ✅ Camera Checklist

- [ ] LUKS enabled
- [ ] Public key only stored
- [ ] OUTBOX encrypted-only
- [ ] Hashes generated
- [ ] Manifests maintained
- [ ] Plaintext retention defined

---

**End of document**


## 📁 Standard Directory Layout (Project-Wide)

Unless explicitly stated otherwise, all guides use the following layout for **encrypted ingest data**:

```
<BASE_PATH>/
├── encrypted/     # encrypted artifacts (.gpg / .age)
├── hashes/        # integrity hashes (.sha256)
├── manifests/     # JSON manifests
└── quarantine/    # failed or unverified files
```

Notes:
- Plaintext is **never** stored here
- Only `encrypted/` is transported between systems
- `quarantine/` is for investigation only and is never synced
