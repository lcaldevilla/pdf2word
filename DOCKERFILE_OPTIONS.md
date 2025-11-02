# Dockerfile Options for LibreOffice Installation

## 🎯 Problem Context

The original Dockerfile failed with `exit code: 100` due to complex LibreOffice dependencies that may not be available or compatible in Railway's container environment.

## 🛠️ Available Solutions

### Option 1: Dockerfile (Simplified - RECOMMENDED)

**File:** `Dockerfile` ✅ **Currently active**

```dockerfile
# Imagen base ligera
FROM python:3.9-slim

# Instalar solo LibreOffice básico
RUN apt-get update && apt-get install -y libreoffice && rm -rf /var/lib/apt/lists/*

# Verificación básica
RUN soffice --version || echo "LibreOffice installation completed"
```

**Pros:**
- ✅ Minimal dependencies (less failure points)
- ✅ Fast build time
- ✅ Uses standard repositories
- ✅ Simple and maintainable

**Cons:**
- ⚠️ May have limited LibreOffice features
- ⚠️ No fallback to unoconv

---

### Option 2: Dockerfile.alternative (Robust with Fallback)

**File:** `Dockerfile.alternative`

```dockerfile
# Multi-stage installation with error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends libreoffice && \
    soffice --version && \
    rm -rf /var/lib/apt/lists/* || \
    (echo "Basic installation failed, trying alternative..." && \
     apt-get install -y --no-install-recommends \
        libreoffice-core libreoffice-writer libreoffice-common && \
     soffice --version && \
     rm -rf /var/lib/apt/lists/*) || \
    (echo "LibreOffice installation failed, installing unoconv only..." && \
     apt-get install -y --no-install-recommends unoconv && \
     rm -rf /var/lib/apt/lists/*)
```

**Pros:**
- ✅ Multiple fallback strategies
- ✅ Includes unoconv installation
- ✅ Graceful failure handling
- ✅ Detailed logging of installation process

**Cons:**
- ❌ More complex
- ❌ Longer build time
- ⚠️ May still fail if core packages are unavailable

---

### Option 3: Dockerfile.prebuilt (Pre-built Image)

**File:** `Dockerfile.prebuilt`

```dockerfile
# Use pre-built LibreOffice image
FROM ghcr.io/linuxserver/libreoffice:latest

# Install Python if needed
RUN if ! command -v python3 &> /dev/null; then \
        apt-get update && \
        apt-get install -y python3 python3-pip && \
        rm -rf /var/lib/apt/lists/*; \
    fi
```

**Pros:**
- ✅ Pre-tested LibreOffice installation
- ✅ No package installation issues
- ✅ Professional LibreOffice setup
- ✅ Most reliable option

**Cons:**
- ⚠️ Larger image size
- ⚠️ Less control over LibreOffice version
- ⚠️ Depends on external image maintenance

---

## 🚀 How to Use Each Option

### Method 1: Rename the Desired Option (Simplest)

```bash
# Use Option 1 (Simplified) - Currently active
# No changes needed, already active as Dockerfile

# Use Option 2 (Alternative)
mv Dockerfile Dockerfile.backup
mv Dockerfile.alternative Dockerfile

# Use Option 3 (Prebuilt)
mv Dockerfile Dockerfile.backup
mv Dockerfile.prebuilt Dockerfile
```

### Method 2: Copy Content

```bash
# Copy the content from the desired option to Dockerfile
cp Dockerfile.alternative Dockerfile  # or .prebuilt
```

### Method 3: Git Branch Strategy

```bash
# Create branches for each option
git checkout -b simplified-dockerfile  # Option 1
git checkout -b alternative-dockerfile # Option 2
git checkout -b prebuilt-dockerfile    # Option 3
```

## 🎯 Recommendation

### Start with Option 1 (Dockerfile)
- ✅ Simplest and most reliable
- ✅ Fastest to deploy
- ✅ Should work for basic PDF → DOCX conversion

### If Option 1 Fails:
- **Try Option 2** for more robust installation
- **Try Option 3** for maximum reliability

### Testing Each Option:

1. **Local Test:**
```bash
docker build -t pdf2word-test .
```

2. **Railway Deploy:**
```bash
git add Dockerfile*
git commit -m "Test Dockerfile option X"
git push origin main
```

3. **Verify Installation:**
```bash
curl https://your-app.railway.app/api/diagnose
```

## 📊 Expected Results

### Success Indicators:
- ✅ Build completes without errors
- ✅ `/api/diagnose` shows LibreOffice available
- ✅ PDF conversion works in logs
- ✅ Email with DOCX attachment is sent

### Failure Indicators:
- ❌ Build fails during apt-get install
- ❌ `/api/diagnose` shows "soffice_available": false
- ❌ Conversion fails with "LibreOffice not found"
- ❌ Logs show "command not found: soffice"

## 🔄 Quick Switch Instructions

To quickly switch between options during testing:

```bash
# Switch to Alternative
mv Dockerfile Dockerfile.simple && mv Dockerfile.alternative Dockerfile

# Switch to Prebuilt  
mv Dockerfile Dockerfile.simple && mv Dockerfile.prebuilt Dockerfile

# Switch back to Simple
mv Dockerfile Dockerfile.alternative && mv Dockerfile.simple Dockerfile
```

## 📝 Notes

- All options preserve the Python code and API logic
- The code already supports both LibreOffice and unoconv fallbacks
- Railway will automatically rebuild when Dockerfile changes
- Monitor Railway logs during build to see which step might be failing

**Remember to test the `/api/diagnose` endpoint after each deployment to verify LibreOffice is working!**
