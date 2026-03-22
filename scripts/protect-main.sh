#!/bin/sh
set -eu

repo="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
branch="${2:-main}"

cat <<EOF
Applying branch protection to ${repo}:${branch}
- required check: fmt, clippy, test, build
- required check: merge-readiness/e0da
- strict updates: false
- enforce admins: true
EOF

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/${repo}/branches/${branch}/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": false,
    "contexts": [
      "fmt, clippy, test, build",
      "merge-readiness/e0da"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF
