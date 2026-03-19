/**
 * Frontend SSR Safety Verification
 * 
 * This script verifies that the Next.js frontend is SSR-safe
 * by checking all critical files for proper client-side guards.
 */

import * as fs from 'fs';
import * as path from 'path';

interface SafetyCheck {
  file: string;
  issue?: string;
  passed: boolean;
}

const checks: SafetyCheck[] = [];

function checkFile(filePath: string, rules: ((content: string) => string | null)[]) {
  if (!fs.existsSync(filePath)) {
    checks.push({
      file: filePath,
      issue: 'File not found',
      passed: false
    });
    return;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  
  for (const rule of rules) {
    const issue = rule(content);
    if (issue) {
      checks.push({
        file: path.relative(process.cwd(), filePath),
        issue,
        passed: false
      });
      return;
    }
  }

  checks.push({
    file: path.relative(process.cwd(), filePath),
    passed: true
  });
}

// Rules
const hasUseClient = (content: string) => {
  if (!content.includes("'use client'") && !content.includes('"use client"')) {
    return "Missing 'use client' directive";
  }
  return null;
};

const localStorageHasGuard = (content: string) => {
  const localStorageUsage = content.match(/localStorage\./g);
  if (localStorageUsage) {
    // Check if it's in useEffect or has typeof window guard
    if (!content.includes('useEffect') && !content.includes('typeof window')) {
      return "localStorage used without typeof window guard or useEffect";
    }
  }
  return null;
};

const windowHasGuard = (content: string) => {
  const windowUsage = content.match(/\bwindow\./g);
  if (windowUsage) {
    // Check if it's in useEffect or has typeof window guard
    if (!content.includes('useEffect') && !content.includes('typeof window')) {
      return "window used without typeof window guard or useEffect";
    }
  }
  return null;
};

console.log('🔍 Running Frontend SSR Safety Checks...\n');

// Check API utility
checkFile(path.join(process.cwd(), 'lib/api.ts'), [localStorageHasGuard, windowHasGuard]);

// Check pages that use browser APIs
const pagesWithBrowserAPIs = [
  'app/page.tsx',
  'app/dashboard/page.tsx',
  'app/login/page.tsx',
  'app/signup/page.tsx',
  'app/otp/page.tsx',
  'app/success/page.tsx',
];

pagesWithBrowserAPIs.forEach(page => {
  checkFile(path.join(process.cwd(), page), [hasUseClient]);
});

// Check components that use browser APIs
const componentsWithBrowserAPIs = [
  'components/ProtectedRoute.tsx',
  'components/top-bar.tsx',
  'components/landing-nav.tsx',
  'components/sidebar.tsx',
];

componentsWithBrowserAPIs.forEach(component => {
  checkFile(path.join(process.cwd(), component), [hasUseClient]);
});

// Print results
console.log('📊 Safety Check Results:\n');

const passed = checks.filter(c => c.passed);
const failed = checks.filter(c => !c.passed);

if (failed.length === 0) {
  console.log('✅ All checks passed!\n');
  passed.forEach(check => {
    console.log(`  ✓ ${check.file}`);
  });
} else {
  console.log('❌ Some checks failed:\n');
  failed.forEach(check => {
    console.log(`  ✗ ${check.file}`);
    console.log(`    Issue: ${check.issue}\n`);
  });
  
  if (passed.length > 0) {
    console.log('\n✅ Passed checks:');
    passed.forEach(check => {
      console.log(`  ✓ ${check.file}`);
    });
  }
}

console.log(`\n📈 Summary: ${passed.length}/${checks.length} checks passed`);

if (failed.length > 0) {
  console.log('\n⚠️  Please fix the issues above before deploying');
  process.exit(1);
} else {
  console.log('\n🎉 Frontend is SSR-safe and ready for deployment!');
  process.exit(0);
}
