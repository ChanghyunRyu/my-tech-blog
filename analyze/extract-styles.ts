/**
 * 디자인 시스템 추출 CLI
 *
 * styles.json(원시 계산된 스타일)을 입력받아 구조화된 디자인 시스템으로 변환
 *
 * Usage:
 *   npx tsx scripts/analyze/extract-styles.ts --input "public/scraped/example-com/styles.json"
 */

import * as fs from 'fs';
import * as path from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

// ============================================================================
// Types
// ============================================================================

interface RawStyles {
  colors: {
    background: string[];
    text: string[];
    accent: string[];
    border: string[];
  };
  fonts: {
    families: string[];
    sizes: string[];
    weights: string[];
  };
  layout: {
    maxWidth: string | null;
    padding: string[];
    margin: string[];
    display: string[];
  };
  effects: {
    boxShadow: string[];
    borderRadius: string[];
  };
}

interface DesignSystem {
  colors: {
    primary: string | null;
    secondary: string | null;
    accent: string | null;
    background: string | null;
    text: string | null;
    muted: string | null;
    border: string | null;
  };
  typography: {
    fontFamily: string;
    scale: Record<string, string>;
    weights: string[];
  };
  spacing: {
    base: string;
    scale: string[];
  };
  borders: {
    radius: Record<string, string>;
  };
  shadows: Record<string, string>;
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
    description: 'styles.json 파일 경로',
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    description: '출력 파일 경로 (기본: 같은 폴더에 design-system.json)',
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
  .example('$0 --input public/scraped/example-com/styles.json', '기본 추출')
  .example('$0 -i styles.json -f md', '마크다운 형식으로 출력')
  .parseSync();

// ============================================================================
// Color Analysis
// ============================================================================

function hexToHsl(hex: string): { h: number; s: number; l: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return null;

  const r = parseInt(result[1], 16) / 255;
  const g = parseInt(result[2], 16) / 255;
  const b = parseInt(result[3], 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        break;
      case g:
        h = ((b - r) / d + 2) / 6;
        break;
      case b:
        h = ((r - g) / d + 4) / 6;
        break;
    }
  }

  return { h: h * 360, s: s * 100, l: l * 100 };
}

function analyzeColors(raw: RawStyles['colors']): DesignSystem['colors'] {
  const allColors = [
    ...raw.background,
    ...raw.text,
    ...raw.accent,
    ...raw.border,
  ].filter((c) => c && c !== 'transparent' && c.startsWith('#'));

  // 색상별 HSL 분석
  const colorData = allColors
    .map((hex) => ({ hex, hsl: hexToHsl(hex) }))
    .filter((c) => c.hsl !== null) as Array<{
    hex: string;
    hsl: { h: number; s: number; l: number };
  }>;

  // 배경색: 가장 밝은 색 (L > 90)
  const backgrounds = colorData.filter((c) => c.hsl.l > 90);
  const background = backgrounds[0]?.hex || '#FFFFFF';

  // 텍스트색: 가장 어두운 색 (L < 30)
  const texts = colorData.filter((c) => c.hsl.l < 30);
  const text = texts[0]?.hex || '#111827';

  // muted: 중간 밝기 + 낮은 채도 (40 < L < 70, S < 20)
  const muteds = colorData.filter(
    (c) => c.hsl.l > 40 && c.hsl.l < 70 && c.hsl.s < 20
  );
  const muted = muteds[0]?.hex || '#6B7280';

  // primary: 높은 채도 + 중간 밝기 (S > 50, 30 < L < 70)
  const primaries = colorData.filter(
    (c) => c.hsl.s > 50 && c.hsl.l > 30 && c.hsl.l < 70
  );
  const primary = primaries[0]?.hex || null;

  // secondary: primary 다음으로 채도 높은 색
  const secondary = primaries[1]?.hex || null;

  // accent: primary/secondary와 다른 hue의 높은 채도 색
  const primaryHue = primary ? hexToHsl(primary)?.h : null;
  const accents = colorData.filter((c) => {
    if (c.hsl.s < 50) return false;
    if (primaryHue !== null && Math.abs(c.hsl.h - primaryHue) < 30) return false;
    return true;
  });
  const accent = accents[0]?.hex || null;

  // border: 밝은 회색 (70 < L < 95, S < 10)
  const borders = colorData.filter(
    (c) => c.hsl.l > 70 && c.hsl.l < 95 && c.hsl.s < 10
  );
  const border = borders[0]?.hex || raw.border[0] || '#E5E7EB';

  return { primary, secondary, accent, background, text, muted, border };
}

// ============================================================================
// Typography Analysis
// ============================================================================

function parsePixelValue(value: string): number | null {
  const match = value.match(/^(\d+(?:\.\d+)?)\s*px$/i);
  return match ? parseFloat(match[1]) : null;
}

function analyzeTypography(raw: RawStyles['fonts']): DesignSystem['typography'] {
  // 폰트 크기 파싱 및 정렬
  const sizes = raw.sizes
    .map((s) => ({ original: s, px: parsePixelValue(s) }))
    .filter((s) => s.px !== null)
    .sort((a, b) => a.px! - b.px!);

  const uniqueSizes = [...new Set(sizes.map((s) => s.px!))];

  // 스케일 매핑 (일반적인 타이포그래피 스케일)
  const scaleNames = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl'];
  const scale: Record<string, string> = {};

  // 16px를 base로 가정하고 스케일 구성
  const baseIndex = uniqueSizes.findIndex((s) => s === 16) ?? Math.floor(uniqueSizes.length / 2);

  uniqueSizes.forEach((size, i) => {
    const nameIndex = 2 + (i - baseIndex); // base = index 2
    const name = scaleNames[Math.max(0, Math.min(nameIndex, scaleNames.length - 1))];
    if (!scale[name]) {
      scale[name] = `${size}px`;
    }
  });

  // 폰트 패밀리
  const fontFamily = raw.families[0] || 'system-ui, sans-serif';

  // 폰트 웨이트 정렬
  const weights = [...new Set(raw.weights)].sort((a, b) => parseInt(a) - parseInt(b));

  return { fontFamily, scale, weights };
}

// ============================================================================
// Spacing Analysis
// ============================================================================

function analyzeSpacing(raw: RawStyles['layout']): DesignSystem['spacing'] {
  const allSpacing = [...raw.padding, ...raw.margin]
    .map(parsePixelValue)
    .filter((v) => v !== null && v > 0) as number[];

  const uniqueSpacing = [...new Set(allSpacing)].sort((a, b) => a - b);

  // 베이스 값 추론 (가장 작은 양수 값, 보통 4 또는 8)
  const base = uniqueSpacing[0] || 4;

  // 스케일 생성 (0 제외)
  const scale = uniqueSpacing.map((v) => String(v));

  return { base: `${base}px`, scale };
}

// ============================================================================
// Border Radius Analysis
// ============================================================================

function analyzeBorders(raw: RawStyles['effects']): DesignSystem['borders'] {
  const radii = raw.borderRadius
    .map((r) => {
      const px = parsePixelValue(r);
      return px !== null ? { original: r, px } : null;
    })
    .filter((r) => r !== null) as Array<{ original: string; px: number }>;

  const uniqueRadii = [...new Set(radii.map((r) => r.px))].sort((a, b) => a - b);

  const radius: Record<string, string> = { none: '0px' };

  uniqueRadii.forEach((r) => {
    if (r === 0) return;
    if (r <= 4) radius['sm'] = `${r}px`;
    else if (r <= 8) radius['md'] = `${r}px`;
    else if (r <= 16) radius['lg'] = `${r}px`;
    else if (r <= 24) radius['xl'] = `${r}px`;
    else radius['full'] = `${r}px`;
  });

  // full이 없으면 추가
  if (!radius['full']) {
    radius['full'] = '9999px';
  }

  return { radius };
}

// ============================================================================
// Shadow Analysis
// ============================================================================

function analyzeShadows(raw: RawStyles['effects']): DesignSystem['shadows'] {
  const shadows = raw.boxShadow.filter(
    (s) => s && s !== 'none' && s !== 'initial'
  );

  if (shadows.length === 0) {
    return {
      sm: '0 1px 2px rgba(0,0,0,0.05)',
      md: '0 4px 6px rgba(0,0,0,0.1)',
      lg: '0 10px 15px rgba(0,0,0,0.15)',
    };
  }

  // blur 크기로 분류
  const classified: Record<string, string> = {};

  shadows.forEach((shadow) => {
    // 간단한 blur 추출 (첫 번째 숫자 3개 중 3번째가 blur)
    const parts = shadow.split(/\s+/);
    const blurMatch = parts[2]?.match(/(\d+)/);
    const blur = blurMatch ? parseInt(blurMatch[1]) : 0;

    if (blur <= 3 && !classified['sm']) classified['sm'] = shadow;
    else if (blur <= 8 && !classified['md']) classified['md'] = shadow;
    else if (!classified['lg']) classified['lg'] = shadow;
  });

  return {
    sm: classified['sm'] || shadows[0] || '0 1px 2px rgba(0,0,0,0.05)',
    md: classified['md'] || shadows[1] || shadows[0] || '0 4px 6px rgba(0,0,0,0.1)',
    lg: classified['lg'] || shadows[2] || shadows[0] || '0 10px 15px rgba(0,0,0,0.15)',
  };
}

// ============================================================================
// Output Formatting
// ============================================================================

function toMarkdown(design: DesignSystem): string {
  const lines: string[] = [
    '# Design System Report',
    '',
    '## Colors',
    '',
    `- **Primary**: ${design.colors.primary || 'N/A'}`,
    `- **Secondary**: ${design.colors.secondary || 'N/A'}`,
    `- **Accent**: ${design.colors.accent || 'N/A'}`,
    `- **Background**: ${design.colors.background}`,
    `- **Text**: ${design.colors.text}`,
    `- **Muted**: ${design.colors.muted}`,
    `- **Border**: ${design.colors.border}`,
    '',
    '## Typography',
    '',
    `**Font Family**: ${design.typography.fontFamily}`,
    '',
    '### Scale',
    '',
  ];

  Object.entries(design.typography.scale).forEach(([name, value]) => {
    lines.push(`- ${name}: ${value}`);
  });

  lines.push('', '### Weights', '');
  lines.push(design.typography.weights.join(', '));

  lines.push('', '## Spacing', '');
  lines.push(`**Base**: ${design.spacing.base}`);
  lines.push('', `**Scale**: ${design.spacing.scale.join(', ')}`);

  lines.push('', '## Border Radius', '');
  Object.entries(design.borders.radius).forEach(([name, value]) => {
    lines.push(`- ${name}: ${value}`);
  });

  lines.push('', '## Shadows', '');
  Object.entries(design.shadows).forEach(([name, value]) => {
    lines.push(`- ${name}: \`${value}\``);
  });

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
  const raw: RawStyles = JSON.parse(rawContent);

  console.log('Analyzing styles...');

  const designSystem: DesignSystem = {
    colors: analyzeColors(raw.colors),
    typography: analyzeTypography(raw.fonts),
    spacing: analyzeSpacing(raw.layout),
    borders: analyzeBorders(raw.effects),
    shadows: analyzeShadows(raw.effects),
  };

  // 출력 경로 결정
  const outputDir = path.dirname(inputPath);
  const defaultOutputName =
    argv.format === 'md' ? 'design-system.md' : 'design-system.json';
  const outputPath = argv.output
    ? path.resolve(argv.output)
    : path.join(outputDir, defaultOutputName);

  // 저장
  const content =
    argv.format === 'md'
      ? toMarkdown(designSystem)
      : JSON.stringify(designSystem, null, 2);

  fs.writeFileSync(outputPath, content, 'utf-8');

  console.log(`Design system saved: ${outputPath}`);

  // 요약 출력
  console.log('\n--- Summary ---');
  console.log(`Colors: ${Object.values(designSystem.colors).filter(Boolean).length} defined`);
  console.log(`Typography: ${Object.keys(designSystem.typography.scale).length} sizes`);
  console.log(`Spacing: ${designSystem.spacing.scale.length} values`);
  console.log(`Border Radius: ${Object.keys(designSystem.borders.radius).length} variants`);
  console.log(`Shadows: ${Object.keys(designSystem.shadows).length} variants`);
}

main().catch((error) => {
  console.error('Error:', error.message);
  process.exit(1);
});
