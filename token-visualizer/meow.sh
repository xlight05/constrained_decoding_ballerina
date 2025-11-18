#!/bin/bash
#
# Claude Code v2.0.76 LSP Fix
# ============================
# Fixes: https://github.com/anthropics/claude-code/issues/13952
#
# The bug: In b52() (LSP server manager factory), the initialize method G()
# is empty: "async function G(){return}" - it does nothing!
#
# Root cause: The function that should load LSP servers from plugins and
# register them simply returns without doing any work.
#
# What this fix does:
#   1. Calls v52() to load LSP configs from enabled plugins
#   2. Creates server instances with T52(serverName, config)
#   3. Registers servers in Map A (server registry)
#   4. Maps file extensions -> server names in Map Q
#
# Usage: ./apply-claude-code-2.0.76-lsp-fix.sh [--check|--restore]
#   --check   : Only check if patch is needed/applied
#   --restore : Restore from most recent backup
#
# Requirements: perl (standard on macOS/Linux)
#
# Note: This patch will be overwritten when Claude Code updates.
#       Re-run this script after updates if LSP stops working.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}!${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Find Claude Code cli.js location
find_cli_path() {
    local locations=(
        # Native install (default)
        "$HOME/.claude/local/node_modules/@anthropic-ai/claude-code/cli.js"
        # npm global install (common locations)
        "/usr/local/lib/node_modules/@anthropic-ai/claude-code/cli.js"
        "/usr/lib/node_modules/@anthropic-ai/claude-code/cli.js"
        # npm prefix-based global install
        "$(npm root -g 2>/dev/null)/@anthropic-ai/claude-code/cli.js"
    )

    for path in "${locations[@]}"; do
        if [ -f "$path" ]; then
            echo "$path"
            return 0
        fi
    done

    return 1
}

CLI_PATH=$(find_cli_path)

if [ -z "$CLI_PATH" ]; then
    print_error "Claude Code cli.js not found"
    echo ""
    echo "Searched locations:"
    echo "  - \$HOME/.claude/local/node_modules/@anthropic-ai/claude-code/cli.js"
    echo "  - /usr/local/lib/node_modules/@anthropic-ai/claude-code/cli.js"
    echo "  - /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js"
    echo "  - \$(npm root -g)/@anthropic-ai/claude-code/cli.js"
    exit 1
fi

# Check for restore flag
if [ "$1" = "--restore" ]; then
    LATEST_BACKUP=$(ls -t "${CLI_PATH}.backup-"* 2>/dev/null | head -1)
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "No backup found for $CLI_PATH"
        exit 1
    fi
    echo "Restoring from: $LATEST_BACKUP"
    cp "$LATEST_BACKUP" "$CLI_PATH"
    print_status "Restored successfully"
    exit 0
fi

# Get Claude Code version
VERSION=$(grep -o '"version":"[^"]*"' "$CLI_PATH" | head -1 | cut -d'"' -f4 2>/dev/null || echo "unknown")
echo "Claude Code version: $VERSION"
echo "CLI path: $CLI_PATH"
echo ""

# Check if already patched
if grep -q 'async function G(){let{servers:F}=await v52()' "$CLI_PATH"; then
    print_status "Already patched!"
    if [ "$1" = "--check" ]; then
        exit 0
    fi
    echo ""
    echo "To restore original: $0 --restore"
    exit 0
fi

# Check if the buggy pattern exists
if ! grep -q 'async function G(){return}async function Z()' "$CLI_PATH"; then
    print_error "Expected pattern not found"
    echo ""
    echo "This patch is for Claude Code v2.0.76"
    echo "Your version ($VERSION) may have different function names."
    echo ""
    echo "The patch looks for:"
    echo '  async function G(){return}async function Z()'
    echo ""
    echo "You can search for the pattern manually:"
    echo "  grep -o 'async function [A-Z](){return}' \"\$CLI_PATH\""
    exit 1
fi

if [ "$1" = "--check" ]; then
    print_warning "Patch needed - run without --check to apply"
    exit 1
fi

# Create backup
BACKUP_PATH="${CLI_PATH}.backup-$(date +%Y%m%d-%H%M%S)"
cp "$CLI_PATH" "$BACKUP_PATH"
echo "Backup: $BACKUP_PATH"
echo ""

echo "Applying fix..."

# The fix: Replace empty G() with proper initialization
#
# Before: async function G(){return}
# After:  async function G(){
#           let{servers:F}=await v52();           // Load LSP configs from plugins
#           for(let[E,z]of Object.entries(F)){    // For each server config
#             let $=T52(E,z);                     // Create server instance
#             A.set(E,$);                         // Register in server map
#             for(let[L,N]of Object.entries(z.extensionToLanguage)){
#               let M=Q.get(L)||[];               // Get existing mappings
#               M.push(E);                        // Add this server
#               Q.set(L,M)                        // Update extension map
#             }
#           }
#         }

perl -i -pe 's/async function G\(\)\{return\}async function Z\(\)/async function G(){let{servers:F}=await v52();for(let[E,z]of Object.entries(F)){let \$=T52(E,z);A.set(E,\$);for(let[L,N]of Object.entries(z.extensionToLanguage)){let M=Q.get(L)||[];M.push(E);Q.set(L,M)}}}async function Z()/g' "$CLI_PATH"

# Verify the fix was applied
if grep -q 'async function G(){let{servers:F}=await v52()' "$CLI_PATH"; then
    echo ""
    print_status "Fix applied successfully!"
    print_warning "Restart Claude Code for changes to take effect"
    echo ""
    echo "To restore original: $0 --restore"
else
    print_error "Fix verification failed. Restoring backup..."
    cp "$BACKUP_PATH" "$CLI_PATH"
    exit 1
fi
