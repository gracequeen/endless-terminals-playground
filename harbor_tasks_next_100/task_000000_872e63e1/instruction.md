Android signing pipeline at /home/user/pipeline broke overnight — the `sign_apk.sh` script is rejecting builds with "certificate chain validation failed" but the keystore hasn't changed in months. QA says APKs built locally sign fine, it's just the CI path that's choking.

Weird part is I can see the keystore file right there at the expected path and `keytool -list` shows the alias exists. So it's not a missing file situation. Feels like maybe something changed in how we're invoking jarsigner or apksigner? Or maybe a config got stale somewhere. There's a signing config yaml that controls some of this at /home/user/pipeline/config/signing.yaml.

Need this unblocked — the script should successfully sign /home/user/pipeline/builds/app-release-unsigned.apk and drop the signed output at /home/user/pipeline/builds/app-release-signed.apk.
