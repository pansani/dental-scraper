#!/bin/bash

echo "Cleaning up zombie Playwright processes..."
echo "(This will NOT kill your regular Chrome browser)"
echo ""

pkill -f "playwright/driver/node" 2>/dev/null && echo "Killed Playwright driver processes" || echo "No Playwright driver processes found"

pkill -f "ms-playwright" 2>/dev/null && echo "Killed Playwright browser processes" || echo "No Playwright browser processes found"

pkill -f ".cache/ms-playwright" 2>/dev/null && echo "Killed cached Playwright processes" || echo "No cached Playwright processes found"

echo ""
echo "Remaining Playwright-related processes:"
ps aux | grep -E "playwright|ms-playwright" | grep -v grep || echo "None found"

echo ""
echo "Cleanup complete!"
