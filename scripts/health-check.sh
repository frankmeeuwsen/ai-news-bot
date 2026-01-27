#!/bin/bash
#
# Server Health Check Dashboard
#
# Post-deployment verificatie script dat server status checkt.
# Gebruikt voor troubleshooting deployment issues en quick diagnostics.
#
# Usage:
#   # Lokaal (op server):
#   ./scripts/health-check.sh
#
#   # Remote (vanaf development machine):
#   ssh dtd 'cd ~/apps/ai-news-bot && ./scripts/health-check.sh'
#
# Exit codes:
#   0 = Healthy - All checks passed
#   1 = Unhealthy - Issues detected
#   2 = Warning - Minor issues found
#

set +e  # Don't exit on error - we want to collect all diagnostics

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
HEALTHY=0
WARNINGS=0
ERRORS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
}

print_ok() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((HEALTHY++))
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

print_header "SERVER HEALTH CHECK DASHBOARD"
echo "Checking AI News Bot server health..."
echo -e "${BLUE}Timestamp:${NC} $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo -e "${BLUE}Hostname:${NC} $(hostname)"

# ============================================================================
# CHECK 1: Git Status
# ============================================================================
print_section "Git Repository Status"

# Current commit hash
CURRENT_COMMIT=$(git log -1 --format="%h - %s" 2>/dev/null)
if [ $? -eq 0 ]; then
    print_ok "Git repository accessible"
    print_info "Current commit: $CURRENT_COMMIT"

    # Check for uncommitted changes
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        print_ok "Working tree clean"
    else
        print_warn "Working tree has uncommitted changes"
        MODIFIED=$(git status --porcelain 2>/dev/null | head -5)
        echo "$MODIFIED" | while IFS= read -r line; do
            print_info "$line"
        done
    fi

    # Check if we're ahead/behind remote
    git fetch origin main --quiet 2>/dev/null
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse origin/main 2>/dev/null)

    if [ "$LOCAL" = "$REMOTE" ]; then
        print_ok "In sync with origin/main"
    elif [ -z "$REMOTE" ]; then
        print_warn "Cannot check remote (network issue or not set up)"
    else
        print_warn "Out of sync with origin/main"
        print_info "Local: $LOCAL"
        print_info "Remote: $REMOTE"
    fi
else
    print_error "Cannot access git repository"
fi

# ============================================================================
# CHECK 2: Python Environment & Dependencies
# ============================================================================
print_section "Python Environment"

# Check if venv exists
if [ -d "venv" ]; then
    print_ok "Virtual environment exists"

    # Check Python version
    PYTHON_VERSION=$(./venv/bin/python --version 2>&1)
    print_info "$PYTHON_VERSION"

    # Check if critical packages are installed
    CRITICAL_PACKAGES=(
        "openai"
        "pyyaml"
        "feedparser"
        "sqlalchemy"
    )

    MISSING_PACKAGES=()
    for package in "${CRITICAL_PACKAGES[@]}"; do
        if ./venv/bin/python -c "import $package" 2>/dev/null; then
            # Silent success
            :
        else
            MISSING_PACKAGES+=("$package")
        fi
    done

    if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
        print_ok "All critical packages installed"
    else
        print_error "Missing packages: ${MISSING_PACKAGES[*]}"
        print_info "Run: pip install -r requirements.txt"
    fi

    # Check for outdated requirements
    if [ -f "requirements.txt" ]; then
        # Count differences (simple check)
        INSTALLED_COUNT=$(./venv/bin/pip list --format=freeze 2>/dev/null | wc -l)
        REQUIRED_COUNT=$(cat requirements.txt | grep -v "^#" | grep -v "^$" | wc -l)

        if [ "$INSTALLED_COUNT" -ge "$REQUIRED_COUNT" ]; then
            print_ok "Dependencies appear up to date ($INSTALLED_COUNT installed)"
        else
            print_warn "May need to update dependencies"
            print_info "Installed: $INSTALLED_COUNT, Required: $REQUIRED_COUNT"
        fi
    fi
else
    print_error "Virtual environment not found"
    print_info "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# ============================================================================
# CHECK 3: Database Status
# ============================================================================
print_section "Database Status"

if [ -f "data/newsbot.db" ]; then
    print_ok "Database file exists"

    # Check database size
    DB_SIZE=$(du -h data/newsbot.db | cut -f1)
    print_info "Database size: $DB_SIZE"

    # Check database accessibility and get record counts
    if [ -x "./venv/bin/python" ]; then
        # Try to query database
        DB_STATS=$(./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.database import get_session
    from src.database.models import NewsItem, NewsletterRun, RSSHealth

    session = get_session()
    news_count = session.query(NewsItem).count()
    run_count = session.query(NewsletterRun).count()
    rss_count = session.query(RSSHealth).count()

    print(f'{news_count}|{run_count}|{rss_count}')
    session.close()
except Exception as e:
    print(f'ERROR|{e}')
" 2>&1)

        if [[ "$DB_STATS" == ERROR* ]]; then
            print_error "Database query failed"
            print_info "${DB_STATS#ERROR|}"
        else
            IFS='|' read -r NEWS_COUNT RUN_COUNT RSS_COUNT <<< "$DB_STATS"
            print_ok "Database accessible"
            print_info "News items: $NEWS_COUNT"
            print_info "Newsletter runs: $RUN_COUNT"
            print_info "RSS health records: $RSS_COUNT"

            # Sanity checks
            if [ "$NEWS_COUNT" -eq 0 ]; then
                print_warn "No news items in database (fresh install?)"
            fi

            if [ "$RUN_COUNT" -eq 0 ]; then
                print_warn "No newsletter runs recorded yet"
            fi
        fi
    else
        print_warn "Cannot query database (Python not available)"
    fi
else
    print_error "Database file not found at data/newsbot.db"
    print_info "Run: python main.py (will create database on first run)"
fi

# ============================================================================
# CHECK 4: Configuration Files
# ============================================================================
print_section "Configuration Files"

CONFIG_FILES=(
    "config.yaml:Config file"
    "sources.yaml:RSS sources"
    ".env:Environment variables"
)

for entry in "${CONFIG_FILES[@]}"; do
    IFS=':' read -r file desc <<< "$entry"

    if [ -f "$file" ]; then
        print_ok "$desc exists ($file)"
    else
        if [ "$file" = ".env" ]; then
            # .env might be at ~/.env-newsbot on server
            if [ -f "$HOME/.env-newsbot" ]; then
                print_ok "$desc exists (~/.env-newsbot)"
            else
                print_warn "$desc not found ($file or ~/.env-newsbot)"
            fi
        else
            print_error "$desc not found ($file)"
        fi
    fi
done

# Check for required environment variables
if [ -f ".env" ]; then
    source .env
elif [ -f "$HOME/.env-newsbot" ]; then
    source "$HOME/.env-newsbot"
fi

REQUIRED_VARS=(
    "OPENROUTER_API_KEY"
    "GMAIL_ADDRESS"
    "GMAIL_APP_PASSWORD"
)

ENV_VARS_OK=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -n "${!var}" ]; then
        ((ENV_VARS_OK++))
    fi
done

if [ $ENV_VARS_OK -eq ${#REQUIRED_VARS[@]} ]; then
    print_ok "All required environment variables set"
else
    print_warn "$ENV_VARS_OK/${#REQUIRED_VARS[@]} required environment variables set"
fi

# ============================================================================
# CHECK 5: Systemd Service Status (if running on server)
# ============================================================================
print_section "Systemd Service Status"

if command -v systemctl &> /dev/null; then
    # Check if service exists
    if systemctl list-unit-files | grep -q "ai-news-bot.service"; then
        print_ok "Service file exists"

        # Check service status
        SERVICE_STATUS=$(systemctl is-active ai-news-bot.service 2>/dev/null)
        TIMER_STATUS=$(systemctl is-active ai-news-bot.timer 2>/dev/null)

        if [ "$TIMER_STATUS" = "active" ]; then
            print_ok "Timer is active"

            # Get next run time
            NEXT_RUN=$(systemctl list-timers ai-news-bot.timer --no-pager 2>/dev/null | grep "ai-news-bot.timer" | awk '{print $1, $2, $3}')
            if [ -n "$NEXT_RUN" ]; then
                print_info "Next run: $NEXT_RUN"
            fi
        else
            print_warn "Timer is not active ($TIMER_STATUS)"
            print_info "Run: sudo systemctl start ai-news-bot.timer"
        fi

        # Check last service result
        LAST_RESULT=$(systemctl show ai-news-bot.service -p Result --value 2>/dev/null)
        LAST_EXIT=$(systemctl show ai-news-bot.service -p ExecMainStatus --value 2>/dev/null)

        if [ "$LAST_RESULT" = "success" ]; then
            print_ok "Last run: success (exit code: $LAST_EXIT)"
        elif [ -z "$LAST_RESULT" ]; then
            print_info "No previous runs recorded"
        else
            print_error "Last run: $LAST_RESULT (exit code: $LAST_EXIT)"
        fi

    else
        print_warn "Systemd service not configured"
        print_info "This might be a development environment"
    fi
else
    print_info "Systemd not available (not running on server?)"
fi

# ============================================================================
# CHECK 6: Log Files
# ============================================================================
print_section "Log Files"

if [ -d "logs" ]; then
    print_ok "Logs directory exists"

    # Check for recent logs
    LOG_FILES=$(find logs -type f -name "*.log" 2>/dev/null | sort)

    if [ -n "$LOG_FILES" ]; then
        LOG_COUNT=$(echo "$LOG_FILES" | wc -l)
        print_ok "Found $LOG_COUNT log file(s)"

        # Show most recent log info
        RECENT_LOG=$(echo "$LOG_FILES" | tail -1)
        LOG_SIZE=$(du -h "$RECENT_LOG" 2>/dev/null | cut -f1)
        LOG_LINES=$(wc -l < "$RECENT_LOG" 2>/dev/null)

        print_info "Most recent: $RECENT_LOG ($LOG_SIZE, $LOG_LINES lines)"

        # Check for recent errors
        if [ -f "$RECENT_LOG" ]; then
            ERROR_COUNT=$(grep -i "error\|exception\|failed" "$RECENT_LOG" 2>/dev/null | wc -l)
            if [ "$ERROR_COUNT" -gt 0 ]; then
                print_warn "Found $ERROR_COUNT error/exception lines in recent log"
            else
                print_ok "No errors in recent log"
            fi
        fi
    else
        print_warn "No log files found"
    fi
else
    print_warn "Logs directory not found"
fi

# ============================================================================
# CHECK 7: Disk Space
# ============================================================================
print_section "Disk Space"

DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -lt 80 ]; then
    print_ok "Disk usage: ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -lt 90 ]; then
    print_warn "Disk usage: ${DISK_USAGE}% (getting full)"
else
    print_error "Disk usage: ${DISK_USAGE}% (critically full)"
fi

DISK_AVAIL=$(df -h . | tail -1 | awk '{print $4}')
print_info "Available: $DISK_AVAIL"

# ============================================================================
# SUMMARY
# ============================================================================
print_header "HEALTH CHECK SUMMARY"

echo -e "\n${BLUE}Results:${NC}"
echo -e "  ${GREEN}✓${NC} Healthy:  $HEALTHY"
echo -e "  ${YELLOW}⚠${NC} Warnings: $WARNINGS"
echo -e "  ${RED}✗${NC} Errors:   $ERRORS"

# Determine overall health
if [ $ERRORS -gt 0 ]; then
    echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}🔴 UNHEALTHY - Critical issues detected${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\nAction required: Review and fix errors above"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🟡 WARNING - Minor issues detected${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\nReview warnings above - service should be operational"
    exit 2
else
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🟢 HEALTHY - All checks passed${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\nServer is healthy and ready for operation"
    exit 0
fi
