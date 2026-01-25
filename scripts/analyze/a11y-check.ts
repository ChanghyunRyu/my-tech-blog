#!/usr/bin/env node
/**
 * 접근성 검사 CLI
 *
 * @axe-core/puppeteer를 사용하여 WCAG 2.1 AA 기준 접근성 검사 수행
 *
 * Usage:
 *   npx tsx scripts/analyze/a11y-check.ts --url "http://localhost:3000"
 *   npx tsx scripts/analyze/a11y-check.ts --file "path/to/page.html"
 *
 * Options:
 *   --url, -u      검사할 URL
 *   --file, -f     검사할 로컬 HTML 파일
 *   --output, -o   결과 출력 경로 (기본: a11y-report.json)
 *   --format       출력 형식: json, md (기본: json)
 *   --standard     검사 기준: wcag2a, wcag2aa, wcag21aa, best-practice (기본: wcag21aa)
 */

import * as fs from 'fs';
import * as path from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import puppeteer, { Browser, Page } from 'puppeteer';
import AxePuppeteer from '@axe-core/puppeteer';

// ============================================================================
// Types
// ============================================================================

type Severity = 'critical' | 'serious' | 'moderate' | 'minor';
type Standard = 'wcag2a' | 'wcag2aa' | 'wcag21aa' | 'best-practice';

interface ViolationNode {
  html: string;
  target: string[];
  failureSummary?: string;
}

interface Violation {
  id: string;
  impact: Severity;
  description: string;
  help: string;
  helpUrl: string;
  tags: string[];
  nodes: ViolationNode[];
}

interface A11yResult {
  url: string;
  timestamp: string;
  standard: Standard;
  summary: {
    violations: number;
    passes: number;
    incomplete: number;
    inapplicable: number;
    bySeverity: {
      critical: number;
      serious: number;
      moderate: number;
      minor: number;
    };
  };
  violations: Violation[];
  passes: { id: string; description: string }[];
  incomplete: { id: string; description: string }[];
}

// ============================================================================
// CLI
// ============================================================================

const argv = yargs(hideBin(process.argv))
  .usage('Usage: $0 --url <url> OR --file <path> [options]')
  .option('url', {
    alias: 'u',
    type: 'string',
    description: '검사할 URL',
  })
  .option('file', {
    alias: 'f',
    type: 'string',
    description: '검사할 로컬 HTML 파일',
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    description: '결과 출력 경로',
  })
  .option('format', {
    type: 'string',
    choices: ['json', 'md'] as const,
    default: 'json',
    description: '출력 형식',
  })
  .option('standard', {
    type: 'string',
    choices: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'] as const,
    default: 'wcag21aa' as Standard,
    description: '검사 기준',
  })
  .check((argv) => {
    if (!argv.url && !argv.file) {
      throw new Error('--url 또는 --file 중 하나는 필수입니다');
    }
    return true;
  })
  .help()
  .alias('help', 'h')
  .example('$0 --url http://localhost:3000', 'URL 검사')
  .example('$0 --file ./public/index.html', '로컬 파일 검사')
  .example('$0 --url http://localhost:3000 --format md', '마크다운 출력')
  .parseSync();

// ============================================================================
// Axe Configuration
// ============================================================================

function getAxeTags(standard: Standard): string[] {
  switch (standard) {
    case 'wcag2a':
      return ['wcag2a'];
    case 'wcag2aa':
      return ['wcag2a', 'wcag2aa'];
    case 'wcag21aa':
      return ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];
    case 'best-practice':
      return ['best-practice'];
    default:
      return ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];
  }
}

// ============================================================================
// Core Logic
// ============================================================================

async function runA11yCheck(
  targetUrl: string,
  standard: Standard
): Promise<A11yResult> {
  let browser: Browser | null = null;

  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page: Page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    console.log(`Navigating to: ${targetUrl}`);
    await page.goto(targetUrl, {
      waitUntil: 'networkidle0',
      timeout: 30000,
    });

    console.log(`Running axe-core analysis (${standard})...`);
    const axeBuilder = new AxePuppeteer(page).withTags(getAxeTags(standard));
    const results = await axeBuilder.analyze();

    // 결과 정리
    const bySeverity = {
      critical: 0,
      serious: 0,
      moderate: 0,
      minor: 0,
    };

    const violations: Violation[] = results.violations.map((v) => {
      const impact = (v.impact as Severity) || 'minor';
      bySeverity[impact]++;

      return {
        id: v.id,
        impact,
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        tags: v.tags,
        nodes: v.nodes.map((n) => ({
          html: n.html,
          target: n.target as string[],
          failureSummary: n.failureSummary,
        })),
      };
    });

    // 심각도순 정렬
    const severityOrder: Severity[] = ['critical', 'serious', 'moderate', 'minor'];
    violations.sort(
      (a, b) => severityOrder.indexOf(a.impact) - severityOrder.indexOf(b.impact)
    );

    return {
      url: targetUrl,
      timestamp: new Date().toISOString(),
      standard,
      summary: {
        violations: results.violations.length,
        passes: results.passes.length,
        incomplete: results.incomplete.length,
        inapplicable: results.inapplicable.length,
        bySeverity,
      },
      violations,
      passes: results.passes.map((p) => ({
        id: p.id,
        description: p.description,
      })),
      incomplete: results.incomplete.map((i) => ({
        id: i.id,
        description: i.description,
      })),
    };
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// ============================================================================
// Output Formatting
// ============================================================================

function getSeverityEmoji(severity: Severity): string {
  switch (severity) {
    case 'critical':
      return '\u{1F6A8}'; // 🚨
    case 'serious':
      return '\u{26A0}\u{FE0F}'; // ⚠️
    case 'moderate':
      return '\u{1F536}'; // 🔶
    case 'minor':
      return '\u{1F539}'; // 🔹
    default:
      return '\u{2753}'; // ❓
  }
}

function toMarkdown(result: A11yResult): string {
  const lines: string[] = [
    '# Accessibility Report',
    '',
    `**URL**: ${result.url}`,
    `**Generated**: ${result.timestamp}`,
    `**Standard**: ${result.standard.toUpperCase()}`,
    '',
    '## Summary',
    '',
    '| Category | Count |',
    '|----------|-------|',
    `| Violations | ${result.summary.violations} |`,
    `| Passes | ${result.summary.passes} |`,
    `| Incomplete | ${result.summary.incomplete} |`,
    '',
    '### Violations by Severity',
    '',
    '| Severity | Count |',
    '|----------|-------|',
    `| ${getSeverityEmoji('critical')} Critical | ${result.summary.bySeverity.critical} |`,
    `| ${getSeverityEmoji('serious')} Serious | ${result.summary.bySeverity.serious} |`,
    `| ${getSeverityEmoji('moderate')} Moderate | ${result.summary.bySeverity.moderate} |`,
    `| ${getSeverityEmoji('minor')} Minor | ${result.summary.bySeverity.minor} |`,
    '',
  ];

  if (result.violations.length > 0) {
    lines.push('## Violations');
    lines.push('');

    for (const v of result.violations) {
      lines.push(`### ${getSeverityEmoji(v.impact)} [${v.impact.toUpperCase()}] ${v.help}`);
      lines.push('');
      lines.push(`**ID**: \`${v.id}\``);
      lines.push(`**Description**: ${v.description}`);
      lines.push(`**Learn more**: [${v.id}](${v.helpUrl})`);
      lines.push('');
      lines.push('**Affected Elements**:');
      lines.push('');

      for (const node of v.nodes.slice(0, 5)) {
        // 최대 5개만 표시
        lines.push(`- \`${node.target.join(' > ')}\``);
        if (node.failureSummary) {
          lines.push(`  - ${node.failureSummary.split('\n')[0]}`);
        }
      }

      if (v.nodes.length > 5) {
        lines.push(`- ... and ${v.nodes.length - 5} more`);
      }

      lines.push('');
    }
  } else {
    lines.push('## Violations');
    lines.push('');
    lines.push('\u{2705} No violations found!');
    lines.push('');
  }

  if (result.incomplete.length > 0) {
    lines.push('## Needs Review');
    lines.push('');
    lines.push('The following items need manual review:');
    lines.push('');

    for (const item of result.incomplete.slice(0, 10)) {
      lines.push(`- \`${item.id}\`: ${item.description}`);
    }

    if (result.incomplete.length > 10) {
      lines.push(`- ... and ${result.incomplete.length - 10} more`);
    }

    lines.push('');
  }

  lines.push('---');
  lines.push('');
  lines.push('*Generated by axe-core via a11y-check.ts*');

  return lines.join('\n');
}

// ============================================================================
// Main
// ============================================================================

async function main(): Promise<void> {
  let targetUrl: string;

  if (argv.url) {
    targetUrl = argv.url;
  } else if (argv.file) {
    const filePath = path.resolve(argv.file);
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }
    targetUrl = `file://${filePath}`;
  } else {
    throw new Error('--url or --file is required');
  }

  console.log('Starting accessibility check...');
  console.log(`  Target: ${targetUrl}`);
  console.log(`  Standard: ${argv.standard}`);

  const result = await runA11yCheck(targetUrl, argv.standard as Standard);

  // 결과 요약 출력
  console.log('\n--- Summary ---');
  console.log(`Violations: ${result.summary.violations}`);
  console.log(`  - Critical: ${result.summary.bySeverity.critical}`);
  console.log(`  - Serious: ${result.summary.bySeverity.serious}`);
  console.log(`  - Moderate: ${result.summary.bySeverity.moderate}`);
  console.log(`  - Minor: ${result.summary.bySeverity.minor}`);
  console.log(`Passes: ${result.summary.passes}`);
  console.log(`Needs Review: ${result.summary.incomplete}`);

  // 파일 저장
  const defaultOutputName =
    argv.format === 'md' ? 'a11y-report.md' : 'a11y-report.json';
  const outputPath = argv.output
    ? path.resolve(argv.output)
    : path.join(process.cwd(), defaultOutputName);

  const content =
    argv.format === 'md' ? toMarkdown(result) : JSON.stringify(result, null, 2);

  fs.writeFileSync(outputPath, content, 'utf-8');
  console.log(`\nReport saved: ${outputPath}`);

  // 위반 사항이 있으면 종료 코드 1
  if (result.summary.bySeverity.critical > 0 || result.summary.bySeverity.serious > 0) {
    console.log('\n\u{26A0}\u{FE0F} Critical or serious violations found!');
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Error:', error.message);
  process.exit(1);
});
