# 🛡️ Receiver-Side Verification & Ingest Guide  
### Encrypted Camera Data • Integrity • Trust Minimization

## 🔗 This guide pairs with

- **CAMERA_ENCRYPTION_OUTBOX_GUIDE.md** or **CAMERA_ENCRYPTION_OUTBOX_GUIDE_GNUPG.md** — camera-side encryption & OUTBOX
- **SECURE_CAMERA_RECEIVER_SYNC.md** — SSH transport & automation
- **RECEIVER_VERIFICATION_INGEST_GUIDE.md** — receiver-side verification & ingest

These guides form a single, coherent pipeline and are intended to be used together.


---

## 🧠 Purpose

This document defines the **receiver-side responsibilities** for securely ingesting encrypted camera data.

**Assumption:**  
> The receiver is *not trusted* with plaintext by default.

The receiver’s job is to:
- Accept encrypted artifacts
- Verify integrity and origin
- Store safely
- Decrypt **only when explicitly required**

---

## 🎯 Receiver Goals

🟢 Never accept plaintext by accident  
🟢 Detect corruption or tampering early  
🟢 Keep ingestion simple and auditable  
🟢 Separate storage from decryption  
🟢 Remain safe even if compromised  

---

## 🔐 Threat Model (Receiver)

| Threat | Mitigation |
|------|-----------|
| Network tampering | Hash verification |
| Partial transfers | Atomic rsync + hashes |
| Disk corruption | Hash re-checks |
| Receiver compromise | Encryption-at-rest |
| Operator error | Clear directory separation |

---

## 📁 Canonical Directory Layout

```
/srv/cam_ingest/
└── cam1/
    ├── encrypted/     # encrypted files (.gpg / .age / .enc)
    ├── hashes/        # .sha256 files
    ├── manifests/     # JSON manifests
    └── quarantine/    # failed verification
```

> Adjust layout as needed, but **never mix plaintext with encrypted storage**.

---

## 📦 Expected Incoming Files

Each clip should arrive as a **set**:

```
clip_YYYYMMDD_HHMM.mp4.gpg  (or .age)
clip_YYYYMMDD_HHMM.mp4.gpg  (or .age).sha256
manifest.json
```

Optional:
```
manifest.sig
```

---

## 🔎 Step 1 — Verify Transfer Completeness

Before verification:
```bash
ls -lh /srv/cam_ingest/cam1/
```

Confirm:
- File sizes are non-zero
- Matching `.sha256` exists for each encrypted file

---

## 🔎 Step 2 — Integrity Verification (Mandatory)

From inside the ingest directory:

```bash
sha256sum -c *.sha256
```

Expected output:
```
clip_xxx.mp4.age: OK
```

### Failure handling
If **any file fails**:
```bash
mv clip_xxx* quarantine/
```

🚨 Never attempt decryption on failed files.

---

## 🔏 Step 3 — Manifest Validation

Open the manifest:
```bash
jq . manifest.json
```

Verify:
- Timestamps are sane
- Filenames match actual files
- Hash values match `.sha256` files
- No unexpected paths or filenames

If signatures are used:
```bash
minisign -Vm manifest.json -P <CAMERA_PUBLIC_KEY>
```

---

## 🧊 Step 4 — Long-Term Storage Rules

✅ Store encrypted files only  
❌ Do not auto-decrypt  
❌ Do not rename without updating manifest  

Recommended:
- Read-only permissions after ingest
- Separate filesystem or disk if possible
- Periodic hash re-checks (monthly)

---

## 🔓 Step 5 — Controlled Decryption (When Required)

Decryption should be:
- Manual
- Logged
- Temporary

Example (age):
```bash
age -d -i camera_private.key clip_xxx.mp4.age > clip_xxx.mp4
```

After use:
```bash
shred -u clip_xxx.mp4
```

🟡 Decrypted files should never be re-ingested or backed up automatically.

---

## 🧪 Periodic Integrity Audit (Recommended)

Monthly or quarterly:
```bash
sha256sum -c *.sha256
```

Log results:
```bash
sha256sum -c *.sha256 >> integrity_audit.log
```

---

## ❌ Receiver Anti-Patterns

🚫 Auto-decrypt on arrival  
🚫 Trusting filenames alone  
🚫 Skipping hash checks  
🚫 Mixing encrypted and plaintext data  
🚫 Granting shell access to ingest users  

---

## 🧠 Operational Philosophy

> **The receiver is a vault, not a workstation.**

- It should ingest quietly
- Verify aggressively
- Reveal nothing by default
- Fail safely and visibly

---

## ✅ Receiver Checklist

- [ ] Ingest user locked down  
- [ ] Encrypted-only storage  
- [ ] Hash verification enforced  
- [ ] Quarantine directory present  
- [ ] Decryption is manual & logged  

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
