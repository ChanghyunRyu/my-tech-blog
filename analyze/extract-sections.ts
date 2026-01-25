/**
 * 섹션 레이아웃 분석 CLI
 *
 * sections.json과 섹션별 HTML을 분석하여 레이아웃 구조와 역할을 추론
 *
 * Usage:
 *   npx tsx scripts/analyze/extract-sections.ts --input "public/scraped/example-com/sections.json"
 */

import * as fs from 'fs';
import * as path from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

// ============================================================================
// Types
// ============================================================================

interface ElementBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface SectionInfo {
  index: number;
  tagName: string;
  selector: string;
  bounds: ElementBounds;
  files: {
    screenshot: string;
    html: string;
  };
}

interface ComponentInfo {
  type: string;
  count: number;
}

interface LayoutPattern {
  pattern: 'flex' | 'grid' | 'stack' | 'unknown';
  direction?: 'row' | 'column';
  childCount: number;
}

interface SectionRole {
  type: string;
  confidence: number;
  reasoning: string;
}

interface SectionAnalysis {
  index: number;
  name: string;
  tagName: string;
  role: SectionRole;
  layout: LayoutPattern;
  components: ComponentInfo[];
  bounds: ElementBounds;
  files: {
    screenshot: string;
    html: string;
  };
}

interface LayoutAnalysisResult {
  version: string;
  timestamp: string;
  sourceFile: string;
  sections: SectionAnalysis[];
  summary: {
    totalSections: number;
    roles: Record<string, number>;
  };
}

// ============================================================================
// CLI
// ============================================================================

const argv = yargs(hideBin(process.argv))
  .usage('Usage: $0 --input <path> [options]')
  .option('input', {
    alias: 'i',
    type: 'string',
    demandOption: true,
    description: 'sections.json 파일 경로',
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    description: '출력 경로 (기본: 같은 폴더에 layout-analysis.json)',
  })
  .option('format', {
    alias: 'f',
    type: 'string',
    choices: ['json', 'md'] as const,
    default: 'json',
    description: '출력 형식',
  })
  .help()
  .alias('help', 'h')
  .example('$0 --input public/scraped/example-com/sections.json', '기본 분석')
  .example('$0 -i sections.json -f md', '마크다운 형식으로 출력')
  .parseSync();

// ============================================================================
// HTML Parsing (regex-based, no external dependencies)
// ============================================================================

function countTags(html: string, tagName: string): number {
  const regex = new RegExp(`<${tagName}[\\s>]`, 'gi');
  return (html.match(regex) || []).length;
}

function hasTag(html: string, tagName: string): boolean {
  return countTags(html, tagName) > 0;
}

function extractTextContent(html: string, maxLength: number = 200): string {
  // Remove all tags
  const text = html
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return text.substring(0, maxLength);
}

function countDirectChildren(html: string): number {
  // Simplified: count immediate children of root element
  // This is approximate since we don't have a full DOM parser
  const match = html.match(/<(\w+)[^>]*>([\s\S]*)<\/\1>/);
  if (!match) return 0;

  const innerHtml = match[2];
  // Count top-level opening tags (simplified heuristic)
  const topLevelTags = innerHtml.match(/<(\w+)[^>]*>/g) || [];
  // Filter to likely direct children (div, section, article, etc.)
  const directChildPatterns = ['div', 'section', 'article', 'li', 'a', 'button', 'span', 'p', 'img'];
  let count = 0;

  for (const tag of topLevelTags) {
    const tagMatch = tag.match(/<(\w+)/);
    if (tagMatch && directChildPatterns.includes(tagMatch[1].toLowerCase())) {
      count++;
    }
  }

  return Math.min(count, 20); // Cap at reasonable number
}

// ============================================================================
// Section Role Inference
// ============================================================================

function inferSectionRole(section: SectionInfo, html: string): SectionRole {
  const tagName = section.tagName.toLowerCase();
  const selector = section.selector.toLowerCase();
  const bounds = section.bounds;
  const text = extractTextContent(html).toLowerCase();

  // Check for semantic tags first
  if (tagName === 'header') {
    return {
      type: 'header',
      confidence: 0.95,
      reasoning: '시맨틱 <header> 태그',
    };
  }

  if (tagName === 'footer') {
    return {
      type: 'footer',
      confidence: 0.95,
      reasoning: '시맨틱 <footer> 태그',
    };
  }

  if (tagName === 'nav') {
    return {
      type: 'navigation',
      confidence: 0.95,
      reasoning: '시맨틱 <nav> 태그',
    };
  }

  // Check selector patterns
  const heroPatterns = ['hero', 'banner', 'jumbotron', 'masthead'];
  const featurePatterns = ['feature', 'service', 'benefit', 'card'];
  const pricingPatterns = ['pricing', 'plan', 'tier'];
  const testimonialPatterns = ['testimonial', 'review', 'quote'];
  const teamPatterns = ['team', 'member', 'staff', 'about'];
  const contactPatterns = ['contact', 'form', 'cta', 'newsletter'];

  for (const pattern of heroPatterns) {
    if (selector.includes(pattern) || text.includes(pattern)) {
      return {
        type: 'hero',
        confidence: 0.85,
        reasoning: `선택자/내용에 "${pattern}" 포함`,
      };
    }
  }

  for (const pattern of featurePatterns) {
    if (selector.includes(pattern)) {
      return {
        type: 'features',
        confidence: 0.8,
        reasoning: `선택자에 "${pattern}" 포함`,
      };
    }
  }

  for (const pattern of pricingPatterns) {
    if (selector.includes(pattern) || text.includes(pattern)) {
      return {
        type: 'pricing',
        confidence: 0.8,
        reasoning: `선택자/내용에 "${pattern}" 포함`,
      };
    }
  }

  for (const pattern of testimonialPatterns) {
    if (selector.includes(pattern) || text.includes(pattern)) {
      return {
        type: 'testimonial',
        confidence: 0.75,
        reasoning: `선택자/내용에 "${pattern}" 포함`,
      };
    }
  }

  for (const pattern of teamPatterns) {
    if (selector.includes(pattern)) {
      return {
        type: 'team',
        confidence: 0.7,
        reasoning: `선택자에 "${pattern}" 포함`,
      };
    }
  }

  for (const pattern of contactPatterns) {
    if (selector.includes(pattern)) {
      return {
        type: 'contact',
        confidence: 0.75,
        reasoning: `선택자에 "${pattern}" 포함`,
      };
    }
  }

  // Position-based inference
  if (bounds.y < 100 && bounds.height < 150) {
    return {
      type: 'header',
      confidence: 0.6,
      reasoning: '상단 위치 + 낮은 높이',
    };
  }

  if (bounds.y < 200 && bounds.height > 400 && hasTag(html, 'h1')) {
    return {
      type: 'hero',
      confidence: 0.7,
      reasoning: '상단 위치 + 큰 높이 + h1 포함',
    };
  }

  // Check for form elements
  if (hasTag(html, 'form') || hasTag(html, 'input')) {
    return {
      type: 'contact',
      confidence: 0.65,
      reasoning: '폼 요소 포함',
    };
  }

  // Check for repeated structures (features/cards)
  const childCount = countDirectChildren(html);
  if (childCount >= 3) {
    return {
      type: 'features',
      confidence: 0.5,
      reasoning: `반복 구조 감지 (${childCount}개 자식)`,
    };
  }

  return {
    type: 'content',
    confidence: 0.3,
    reasoning: '기본 콘텐츠 섹션',
  };
}

// ============================================================================
// Layout Analysis
// ============================================================================

function analyzeLayout(html: string, selector: string): LayoutPattern {
  const childCount = countDirectChildren(html);

  // Check selector for layout hints
  const selectorLower = selector.toLowerCase();

  if (selectorLower.includes('grid') || selectorLower.includes('row')) {
    return {
      pattern: 'grid',
      direction: 'row',
      childCount,
    };
  }

  if (selectorLower.includes('flex') || selectorLower.includes('column')) {
    return {
      pattern: 'flex',
      direction: 'column',
      childCount,
    };
  }

  // Infer from child count
  if (childCount >= 3 && childCount <= 6) {
    return {
      pattern: 'grid',
      direction: 'row',
      childCount,
    };
  }

  if (childCount > 0) {
    return {
      pattern: 'stack',
      direction: 'column',
      childCount,
    };
  }

  return {
    pattern: 'unknown',
    childCount,
  };
}

// ============================================================================
// Component Extraction
// ============================================================================

function extractComponents(html: string): ComponentInfo[] {
  const components: ComponentInfo[] = [];

  const tagCounts: Record<string, string> = {
    img: 'image',
    button: 'button',
    a: 'link',
    input: 'input',
    form: 'form',
    video: 'video',
    svg: 'icon',
    h1: 'heading',
    h2: 'heading',
    h3: 'heading',
    ul: 'list',
    ol: 'list',
  };

  const counts: Record<string, number> = {};

  for (const [tag, type] of Object.entries(tagCounts)) {
    const count = countTags(html, tag);
    if (count > 0) {
      counts[type] = (counts[type] || 0) + count;
    }
  }

  for (const [type, count] of Object.entries(counts)) {
    components.push({ type, count });
  }

  // Sort by count descending
  components.sort((a, b) => b.count - a.count);

  return components;
}

// ============================================================================
// Output Formatting
// ============================================================================

function toMarkdown(result: LayoutAnalysisResult): string {
  const lines: string[] = [
    '# Layout Analysis Report',
    '',
    `Generated: ${result.timestamp}`,
    `Source: ${result.sourceFile}`,
    '',
    '## Summary',
    '',
    `Total Sections: ${result.summary.totalSections}`,
    '',
    '### Roles Distribution',
    '',
  ];

  for (const [role, count] of Object.entries(result.summary.roles)) {
    lines.push(`- ${role}: ${count}`);
  }

  lines.push('', '---', '', '## Sections', '');

  for (const section of result.sections) {
    lines.push(`### ${section.index + 1}. ${section.name}`);
    lines.push('');
    lines.push(`- **Tag**: \`<${section.tagName}>\``);
    lines.push(`- **Role**: ${section.role.type} (${Math.round(section.role.confidence * 100)}%)`);
    lines.push(`- **Reasoning**: ${section.role.reasoning}`);
    lines.push(`- **Layout**: ${section.layout.pattern} (${section.layout.childCount} children)`);
    lines.push(`- **Size**: ${section.bounds.width}x${section.bounds.height}px`);
    lines.push('');

    if (section.components.length > 0) {
      lines.push('**Components**:');
      for (const comp of section.components) {
        lines.push(`- ${comp.type}: ${comp.count}`);
      }
      lines.push('');
    }

    lines.push('---', '');
  }

  return lines.join('\n');
}

// ============================================================================
// Main
// ============================================================================

async function main(): Promise<void> {
  const inputPath = path.resolve(argv.input);

  if (!fs.existsSync(inputPath)) {
    console.error(`Error: File not found: ${inputPath}`);
    process.exit(1);
  }

  console.log(`Reading: ${inputPath}`);

  const rawContent = fs.readFileSync(inputPath, 'utf-8');
  const sections: SectionInfo[] = JSON.parse(rawContent);

  const inputDir = path.dirname(inputPath);

  console.log(`Analyzing ${sections.length} sections...`);

  const analyzedSections: SectionAnalysis[] = [];
  const roleCounts: Record<string, number> = {};

  for (const section of sections) {
    // Read HTML file
    const htmlPath = path.join(inputDir, section.files.html);
    let html = '';

    if (fs.existsSync(htmlPath)) {
      html = fs.readFileSync(htmlPath, 'utf-8');
    } else {
      console.warn(`Warning: HTML file not found: ${htmlPath}`);
    }

    // Analyze
    const role = inferSectionRole(section, html);
    const layout = analyzeLayout(html, section.selector);
    const components = extractComponents(html);

    // Generate name
    const name =
      role.type === 'content'
        ? `Section ${section.index + 1}`
        : role.type.charAt(0).toUpperCase() + role.type.slice(1);

    analyzedSections.push({
      index: section.index,
      name,
      tagName: section.tagName,
      role,
      layout,
      components,
      bounds: section.bounds,
      files: section.files,
    });

    // Count roles
    roleCounts[role.type] = (roleCounts[role.type] || 0) + 1;
  }

  const result: LayoutAnalysisResult = {
    version: '1.0',
    timestamp: new Date().toISOString(),
    sourceFile: path.basename(inputPath),
    sections: analyzedSections,
    summary: {
      totalSections: sections.length,
      roles: roleCounts,
    },
  };

  // Output path
  const defaultOutputName =
    argv.format === 'md' ? 'layout-analysis.md' : 'layout-analysis.json';
  const outputPath = argv.output
    ? path.resolve(argv.output)
    : path.join(inputDir, defaultOutputName);

  // Save
  const content =
    argv.format === 'md'
      ? toMarkdown(result)
      : JSON.stringify(result, null, 2);

  fs.writeFileSync(outputPath, content, 'utf-8');

  console.log(`Layout analysis saved: ${outputPath}`);

  // Summary
  console.log('\n--- Summary ---');
  console.log(`Total sections: ${result.summary.totalSections}`);
  console.log('Roles:');
  for (const [role, count] of Object.entries(roleCounts)) {
    console.log(`  ${role}: ${count}`);
  }
}

main().catch((error) => {
  console.error('Error:', error.message);
  process.exit(1);
});
