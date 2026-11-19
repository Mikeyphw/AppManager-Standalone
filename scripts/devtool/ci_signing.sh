#!/usr/bin/env bash
# GitHub-hosted signing boundary. No logs contain keystores/passwords.
set -Eeuo pipefail
umask 077
: "${RUNNER_TEMP:?GitHub runner required}"
: "${GITHUB_ENV:?GitHub Actions environment required}"
: "${AM_SIGNING_VARIANT:?debug or release signing selection required}"
[[ "$AM_SIGNING_VARIANT" == debug || "$AM_SIGNING_VARIANT" == release ]] || {
  echo 'SIGNING_REFUSED unsupported variant' >&2; exit 2;
}
if [[ "$AM_SIGNING_VARIANT" == debug ]]; then
  key_b64="${AM_DEBUG_KEYSTORE_B64:-}"
  alias="${AM_DEBUG_KEY_ALIAS:-}"
  password="${AM_DEBUG_STORE_PASSWORD:-}"
  key_password="${AM_DEBUG_KEY_PASSWORD:-}"
  password_var=AM_DEBUG_STORE_PASSWORD
else
  key_b64="${AM_RELEASE_KEYSTORE_B64:-}"
  alias="${AM_RELEASE_KEY_ALIAS:-}"
  password="${AM_RELEASE_STORE_PASSWORD:-}"
  key_password="${AM_RELEASE_KEY_PASSWORD:-}"
  password_var=AM_RELEASE_STORE_PASSWORD
fi
[[ -n "$key_b64" && -n "$alias" && -n "$password" && -n "$key_password" ]] || {
  echo 'SIGNING_REFUSED incomplete protected GitHub Secrets' >&2; exit 2;
}
case "${1:-}" in
  prepare)
    command -v keytool >/dev/null
    command -v base64 >/dev/null
    # mktemp + private directory + cleanup of failed decoding, with no source tree writes.
    secret_dir="$(mktemp -d "$RUNNER_TEMP/appmanager-signing-XXXXXXXX")"
    keyfile="$secret_dir/ci-keystore.p12"
    if ! printf '%s' "$key_b64" | base64 --decode > "$keyfile"; then
      rm -rf -- "$secret_dir"
      echo 'SIGNING_REFUSED invalid keystore encoding' >&2; exit 2
    fi
    chmod 600 "$keyfile"
    [[ -s "$keyfile" ]] || { rm -rf -- "$secret_dir"; echo 'SIGNING_REFUSED empty keystore' >&2; exit 2; }
    if ! keytool -list -v -keystore "$keyfile" -alias "$alias" \
              -storepass:env "$password_var" > "$secret_dir/cert-info" 2>/dev/null; then
      rm -rf -- "$secret_dir"
      echo 'SIGNING_REFUSED keystore password, alias or format invalid' >&2; exit 2
    fi
    fingerprint="$(sed -n -E 's/^[[:space:]]*SHA256:[[:space:]]*([0-9A-Fa-f:]+).*/\1/p' "$secret_dir/cert-info" | head -n 1 | tr -d ':' | tr '[:upper:]' '[:lower:]')"
    rm -f -- "$secret_dir/cert-info"
    [[ "$fingerprint" =~ ^[0-9a-f]{64}$ ]] || {
      rm -rf -- "$secret_dir"; echo 'SIGNING_REFUSED certificate digest unavailable' >&2; exit 2;
    }
    printf 'AM_SIGNING_KEYSTORE=%s\nAM_SIGNING_CERT_SHA256=%s\n' "$keyfile" "$fingerprint" >> "$GITHUB_ENV"
    echo "SIGNING_READY variant=$AM_SIGNING_VARIANT fingerprint=$fingerprint"
    ;;
  verify)
    : "${AM_SIGNING_CERT_SHA256:?prepare must have succeeded}"
    : "${ANDROID_HOME:?Android SDK required for apksigner}"
    root="${2:?APK output directory required}"
    [[ -d "$root" ]] || { echo 'SIGNING_REFUSED no APK directory' >&2; exit 2; }
    apksigner="$ANDROID_HOME/build-tools/36.1.0/apksigner"
    [[ -x "$apksigner" ]] || { echo 'SIGNING_REFUSED apksigner 36.1.0 unavailable' >&2; exit 2; }
    count=0
    while IFS= read -r -d '' apk; do
      count=$((count+1))
      output="$($apksigner verify --verbose --print-certs "$apk")" || {
        echo "SIGNING_REFUSED unsigned/invalid APK $apk" >&2; exit 2;
      }
      apk_digest="$(printf '%s\n' "$output" | sed -n -E 's/^Signer #1 certificate SHA-256 digest:[[:space:]]*([0-9A-Fa-f:]+).*/\1/p' | head -n 1 | tr -d ':' | tr '[:upper:]' '[:lower:]')"
      [[ "$apk_digest" == "$AM_SIGNING_CERT_SHA256" ]] || {
        echo "SIGNING_REFUSED certificate mismatch for $apk" >&2; exit 2;
      }
      echo "SIGNED_APK_VERIFIED $apk $apk_digest"
    done < <(find "$root" -type f -name '*.apk' -print0)
    (( count > 0 )) || { echo 'SIGNING_REFUSED zero APKs' >&2; exit 2; }
    echo "SIGNING_ACCEPTED count=$count variant=$AM_SIGNING_VARIANT"
    ;;
  *) echo 'Usage: ci_signing.sh prepare|verify APK_DIRECTORY' >&2; exit 2 ;;
esac
