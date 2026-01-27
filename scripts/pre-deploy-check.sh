#!/bin/bash
#
# Pre-Deployment Validation Script
#
# Voorkomt deployment chaos door systematische checks VOORDAT je naar server pusht.
# Geïnspireerd op de 2026-01-04 deployment retrospective.
#
# Usage:
#   ./scripts/pre-deploy-check.sh
#
# Exit codes:
#   0 = GO - Safe to deploy
#   1 = NO-GO - Issues found, fix before deploying
#

set +e  # Don't exit on error - we handle errors ourselves

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
WARNINGS=0
ERRORS=0
CHECKS_PASSED=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_check() {
    echo -e "\n${BLUE}▶${NC} $1"
}

print_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

print_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_error() {
    echo -e "  ${RED}✗${NC} $1"
    ((ERRORS++))
}

print_info() {
    echo -e "    ${BLUE}→${NC} $1"
}

# Change to project root
cd "$(dirname "$0")/.."

print_header "PRE-DEPLOYMENT VALIDATION"
echo "Checking if it's safe to push to production..."

# ============================================================================
# CHECK 1: Git Status Audit
# ============================================================================
print_check "Check 1: Git Status Audit"

# Check for uncommitted changes
UNCOMMITTED=$(git status --porcelain)

if [ -z "$UNCOMMITTED" ]; then
    print_pass "No uncommitted changes - working tree clean"
else
    # Check for uncommitted changes in critical paths
    CRITICAL_PATHS=(
        "src/database/models.py"
        "src/database/"
        "src/news/generator.py"
        "src/news/fetcher.py"
        "main.py"
        "requirements.txt"
        "config.yaml"
    )

    CRITICAL_UNCOMMITTED=0
    for path in "${CRITICAL_PATHS[@]}"; do
        if echo "$UNCOMMITTED" | grep -q "$path"; then
            print_error "Uncommitted changes in critical file: $path"
            print_info "Run: git status --short"
            ((CRITICAL_UNCOMMITTED++))
        fi
    done

    if [ $CRITICAL_UNCOMMITTED -eq 0 ]; then
        print_warn "Uncommitted changes in non-critical files"
        echo "$UNCOMMITTED" | while read line; do
            print_info "$line"
        done
    fi
fi

# ============================================================================
# CHECK 2: Database Model Changes Check
# ============================================================================
print_check "Check 2: Database Model Changes"

# Check if models.py has uncommitted changes
if git diff --name-only | grep -q "src/database/models.py"; then
    print_error "models.py has uncommitted changes!"
    print_info "If you commit models.py, ensure ALL users of changed models are also committed"
    print_info "Run: git grep -l 'from.*models import' to find model users"
elif git diff --cached --name-only | grep -q "src/database/models.py"; then
    print_warn "models.py is staged for commit"

    # Check if other files that use models are also staged
    MODEL_USERS=$(git grep -l "from.*models import\|from src.database import" -- "*.py" | grep -v "models.py" | grep -v "__pycache__" || true)

    STAGED_FILES=$(git diff --cached --name-only)

    MISSING_USERS=()
    while IFS= read -r user_file; do
        # Check if this file is modified but not staged
        if git diff --name-only | grep -q "^$user_file$"; then
            MISSING_USERS+=("$user_file")
        fi
    done <<< "$MODEL_USERS"

    if [ ${#MISSING_USERS[@]} -gt 0 ]; then
        print_warn "Model users with uncommitted changes:"
        for user in "${MISSING_USERS[@]}"; do
            print_info "$user (modified but not staged)"
        done
    else
        print_pass "Model changes appear atomic (related files staged together)"
    fi
else
    print_pass "No database model changes detected"
fi

# ============================================================================
# CHECK 3: Breaking Changes Scan
# ============================================================================
print_check "Check 3: Breaking Changes Scan"

# Check staged diff for breaking changes (only in Python files)
BREAKING_PATTERNS=(
    "nullable=False"
    "Column.*NOT NULL"
    "ForeignKey"
)

BREAKING_FOUND=0
for pattern in "${BREAKING_PATTERNS[@]}"; do
    # Only check Python files in src/database/
    MATCHES=$(git diff --cached -- 'src/database/*.py' | grep -E "$pattern" || true)
    if [ -n "$MATCHES" ]; then
        print_warn "Found potential breaking change: $pattern"
        echo "$MATCHES" | while IFS= read -r line; do
            print_info "$line"
        done
        ((BREAKING_FOUND++))
    fi
done

if [ $BREAKING_FOUND -gt 0 ]; then
    print_warn "Breaking changes detected - ensure migration script exists"
    print_info "Check: Do new NOT NULL columns have default values?"
    print_info "Check: Is there a migration script in scripts/migrations/?"
else
    print_pass "No breaking schema changes detected"
fi

# ============================================================================
# CHECK 4: Dependency Changes
# ============================================================================
print_check "Check 4: Dependency Changes"

if git diff --cached --name-only | grep -q "requirements.txt"; then
    print_warn "requirements.txt has changes"
    print_info "After deployment, verify server runs: pip install -r requirements.txt"

    # Show what changed
    ADDED=$(git diff --cached requirements.txt | grep "^+" | grep -v "^+++" || true)
    REMOVED=$(git diff --cached requirements.txt | grep "^-" | grep -v "^---" || true)

    if [ -n "$ADDED" ]; then
        print_info "Added dependencies:"
        echo "$ADDED" | while IFS= read -r line; do
            print_info "  $line"
        done
    fi

    if [ -n "$REMOVED" ]; then
        print_info "Removed dependencies:"
        echo "$REMOVED" | while IFS= read -r line; do
            print_info "  $line"
        done
    fi
else
    print_pass "No dependency changes"
fi

# ============================================================================
# CHECK 5: Config Changes
# ============================================================================
print_check "Check 5: Configuration Changes"

CONFIG_FILES=("config.yaml" "sources.yaml")
CONFIG_CHANGED=0

for config in "${CONFIG_FILES[@]}"; do
    if git diff --cached --name-only | grep -q "$config"; then
        print_warn "$config has changes"
        ((CONFIG_CHANGED++))
    fi
done

if [ $CONFIG_CHANGED -eq 0 ]; then
    print_pass "No config file changes"
else
    print_info "Config changes will auto-deploy, no manual action needed"
fi

# ============================================================================
# CHECK 6: Pre-Push Dry Run (Import Tests)
# ============================================================================
print_check "Check 6: Import Tests (Pre-Push Dry Run)"

# Check if venv exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found at ./venv"
    print_info "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
else
    # Test critical imports
    IMPORT_TESTS=(
        "from src.database.models import AISummary, NewsItem"
        "from src.news.generator import NewsGenerator"
        "from src.news.fetcher import NewsFetcher"
        "from src.obsidian.uri_builder import build_obsidian_uri"
    )

    IMPORT_FAILURES=0
    for test in "${IMPORT_TESTS[@]}"; do
        if ./venv/bin/python -c "$test" 2>/dev/null; then
            # Silent success
            :
        else
            print_error "Import failed: $test"
            ((IMPORT_FAILURES++))
        fi
    done

    if [ $IMPORT_FAILURES -eq 0 ]; then
        print_pass "All critical imports successful"
    else
        print_error "$IMPORT_FAILURES import test(s) failed"
        print_info "Fix import errors before deploying"
    fi
fi

# ============================================================================
# CHECK 7: Atomic Commit Validation
# ============================================================================
print_check "Check 7: Atomic Commit Validation"

# Check if there are staged changes
STAGED=$(git diff --cached --name-only)

if [ -z "$STAGED" ]; then
    print_warn "No staged changes - nothing to deploy"
else
    # Check for common anti-patterns

    # Anti-pattern 1: models.py staged but generator.py modified (not staged)
    if echo "$STAGED" | grep -q "models.py" && git diff --name-only | grep -q "generator.py"; then
        print_error "Anti-pattern detected: models.py staged but generator.py not staged"
        print_info "These changes are likely related - commit them together"
    fi

    # Anti-pattern 2: Only main.py staged, but other files modified
    STAGED_COUNT=$(echo "$STAGED" | wc -l | xargs)
    MODIFIED_COUNT=$(git diff --name-only | wc -l | xargs)

    if [ "$STAGED_COUNT" -eq 1 ] && [ "$MODIFIED_COUNT" -gt 0 ] && echo "$STAGED" | grep -q "main.py"; then
        print_warn "Only main.py staged, but other files are modified"
        print_info "Are these changes related? Consider atomic commit."
    fi

    if [ $ERRORS -eq 0 ]; then
        print_pass "Staged changes appear atomic"
    fi
fi

# ============================================================================
# SUMMARY & VERDICT
# ============================================================================
print_header "VALIDATION SUMMARY"

echo -e "\n${BLUE}Results:${NC}"
echo -e "  ${GREEN}✓${NC} Checks passed: $CHECKS_PASSED"
echo -e "  ${YELLOW}⚠${NC} Warnings:      $WARNINGS"
echo -e "  ${RED}✗${NC} Errors:        $ERRORS"

if [ $ERRORS -gt 0 ]; then
    echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⛔ NO-GO - Fix errors before deploying${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  PROCEED WITH CAUTION - Review warnings${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\nRecommended actions:"
    echo -e "  1. Review all warnings above"
    echo -e "  2. Ensure you have a rollback plan"
    echo -e "  3. Monitor deployment closely"
    echo -e "\nIf you're confident, proceed with: ${BLUE}git push origin main${NC}"
    exit 0
else
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ GO - Safe to deploy${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\nNext steps:"
    echo -e "  1. ${BLUE}git push origin main${NC}"
    echo -e "  2. Wait 15 seconds for Forgejo auto-deployment"
    echo -e "  3. Verify: ${BLUE}ssh dtd 'cd ~/apps/ai-news-bot && git log -1 --oneline'${NC}"
    exit 0
fi
