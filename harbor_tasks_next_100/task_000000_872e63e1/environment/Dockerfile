FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    wget \
    unzip \
    python3 \
    python3-pip \
    zip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

RUN mkdir -p /opt/android-sdk/cmdline-tools && \
    cd /opt/android-sdk/cmdline-tools && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O cmdline-tools.zip && \
    unzip -q cmdline-tools.zip && \
    rm cmdline-tools.zip && \
    mv cmdline-tools latest

ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/build-tools/33.0.0

RUN yes | sdkmanager --licenses > /dev/null 2>&1 || true && \
    sdkmanager "build-tools;33.0.0" "platform-tools"

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/pipeline/config && \
    mkdir -p /home/user/pipeline/keys && \
    mkdir -p /home/user/pipeline/builds

RUN keytool -genkeypair \
    -alias release-key \
    -keyalg RSA \
    -keysize 2048 \
    -sigalg SHA256withRSA \
    -validity 10000 \
    -keystore /home/user/pipeline/keys/release.jks \
    -storepass android123 \
    -keypass android123 \
    -dname "CN=Release Key, OU=Development, O=MyCompany, L=City, ST=State, C=US"

RUN cat > /home/user/pipeline/config/signing.yaml << 'EOF'
keystore_path: /home/user/pipeline/keys/release.jks
key_alias: release-key
keystore_pass: android123
key_pass: android123
signature_algorithm: SHA1withRSA
EOF

RUN cat > /home/user/pipeline/config/verify.conf << 'EOF'
VERIFY_MIN_SDK=24
EOF

RUN mkdir -p /tmp/apk_build/META-INF && \
    echo "Manifest-Version: 1.0" > /tmp/apk_build/META-INF/MANIFEST.MF && \
    echo "Created-By: 11.0 (Ubuntu)" >> /tmp/apk_build/META-INF/MANIFEST.MF && \
    echo "" >> /tmp/apk_build/META-INF/MANIFEST.MF

RUN cat > /tmp/apk_build/AndroidManifest.xml << 'XMLEOF'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.testapp"
    android:versionCode="1"
    android:versionName="1.0">
    <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="33"/>
    <application android:label="TestApp">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
XMLEOF

RUN mkdir -p /tmp/apk_build/res/layout && \
    mkdir -p /tmp/apk_build/res/values

RUN cat > /tmp/apk_build/res/values/strings.xml << 'XMLEOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TestApp</string>
</resources>
XMLEOF

RUN cat > /tmp/apk_build/res/layout/activity_main.xml << 'XMLEOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">
    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Hello World"/>
</LinearLayout>
XMLEOF

RUN dd if=/dev/urandom of=/tmp/apk_build/classes.dex bs=1024 count=30 2>/dev/null && \
    dd if=/dev/urandom of=/tmp/apk_build/resources.arsc bs=1024 count=10 2>/dev/null

RUN cd /tmp/apk_build && \
    zip -r /home/user/pipeline/builds/app-release-unsigned.apk . && \
    rm -rf /tmp/apk_build

RUN cat > /home/user/pipeline/sign_apk.sh << 'SCRIPTEOF'
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/signing.yaml"
VERIFY_CONF="$SCRIPT_DIR/config/verify.conf"
INPUT_APK="$SCRIPT_DIR/builds/app-release-unsigned.apk"
OUTPUT_APK="$SCRIPT_DIR/builds/app-release-signed.apk"

# Source verify config
if [ -f "$VERIFY_CONF" ]; then
    source "$VERIFY_CONF"
fi

# Parse YAML config (simple parser)
parse_yaml() {
    local key=$1
    grep "^${key}:" "$CONFIG_FILE" | sed "s/^${key}:[[:space:]]*//"
}

KEYSTORE_PATH=$(parse_yaml "keystore_path")
KEY_ALIAS=$(parse_yaml "key_alias")
KEYSTORE_PASS=$(parse_yaml "keystore_pass")
KEY_PASS=$(parse_yaml "key_pass")
SIG_ALGORITHM=$(parse_yaml "signature_algorithm")

echo "=== Android APK Signing Pipeline ==="
echo "Keystore: $KEYSTORE_PATH"
echo "Alias: $KEY_ALIAS"
echo "Signature Algorithm: $SIG_ALGORITHM"
echo ""

# Verify keystore exists
if [ ! -f "$KEYSTORE_PATH" ]; then
    echo "ERROR: Keystore not found at $KEYSTORE_PATH"
    exit 1
fi

# Verify input APK exists
if [ ! -f "$INPUT_APK" ]; then
    echo "ERROR: Input APK not found at $INPUT_APK"
    exit 1
fi

# Verify alias exists in keystore
echo "Verifying keystore alias..."
if ! keytool -list -keystore "$KEYSTORE_PATH" -storepass "$KEYSTORE_PASS" | grep -q "$KEY_ALIAS"; then
    echo "ERROR: Alias '$KEY_ALIAS' not found in keystore"
    exit 1
fi

# Remove old signed APK if exists
rm -f "$OUTPUT_APK"

# Sign the APK using apksigner with specified algorithm
echo "Signing APK..."
apksigner sign \
    --ks "$KEYSTORE_PATH" \
    --ks-key-alias "$KEY_ALIAS" \
    --ks-pass "pass:$KEYSTORE_PASS" \
    --key-pass "pass:$KEY_PASS" \
    --v1-signing-enabled true \
    --v2-signing-enabled true \
    --v1-signer-name "CERT" \
    --out "$OUTPUT_APK" \
    --sig-algorithm "$SIG_ALGORITHM" \
    "$INPUT_APK"

echo "Signing complete."

# Verify the signed APK
echo ""
echo "Verifying signed APK..."

# Check min SDK warning
if [ -n "$VERIFY_MIN_SDK" ]; then
    echo "Note: Verify min SDK set to $VERIFY_MIN_SDK"
fi

# This is where the failure happens - certificate chain validation
if ! apksigner verify --print-certs "$OUTPUT_APK"; then
    echo "ERROR: Certificate chain validation failed!"
    echo "The signed APK failed verification."
    rm -f "$OUTPUT_APK"
    exit 1
fi

echo ""
echo "=== APK signed successfully ==="
echo "Output: $OUTPUT_APK"
exit 0
SCRIPTEOF

RUN chmod +x /home/user/pipeline/sign_apk.sh

RUN chmod -R 0777 /home/user/pipeline

RUN sha256sum /home/user/pipeline/keys/release.jks > /home/user/pipeline/keys/.keystore_checksum

WORKDIR /home/user

CMD ["/bin/bash"]
