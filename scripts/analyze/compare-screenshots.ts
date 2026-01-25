/**
 * 스크린샷 비교 CLI
 *
 * 원본과 구현 스크린샷을 비교하여 차이점 리포트 생성
 * - 메타데이터 비교 (해상도, 파일 크기)
 * - 픽셀 레벨 비교 (pixelmatch 사용)
 *
 * Usage:
 *   npx tsx scripts/analyze/compare-screenshots.ts \
 *     --original "public/scraped/example-com/full-page.png" \
 *     --current "public/preview.png"
 *
 * Options:
 *   --threshold  픽셀 비교 임계값 0-1 (기본: 0.1)
 *   --diff       diff 이미지 생성 경로 (선택)
 */

import * as fs from 'fs';
import * as path from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

// ============================================================================
// Types
// ============================================================================

interface ImageMetadata {
  filePath: string;
  width: number;
  height: number;
  fileSize: number;
  format: string;
}

interface Differences {
  widthMatch: boolean;
  widthDiff: number;
  widthDiffPercent: number;
  heightMatch: boolean;
  heightDiff: number;
  heightDiffPercent: number;
  fileSizeDiff: number;
  fileSizeDiffPercent: number;
}

interface PixelDiff {
  enabled: boolean;
  totalPixels: number;
  diffPixels: number;
  diffPercent: number;
  diffImagePath: string | null;
  threshold: number;
}

type ComparisonStatus = 'match' | 'minor_diff' | 'major_diff' | 'error';

interface ComparisonResult {
  original: ImageMetadata;
  current: ImageMetadata;
  differences: Differences;
  pixelDiff: PixelDiff;
  status: ComparisonStatus;
}

interface DiffReport {
  version: string;
  timestamp: string;
  files: {
    original: string;
    current: string;
  };
  comparison: ComparisonResult;
  recommendations: string[];
}

// ============================================================================
// CLI
// ============================================================================

const argv = yargs(hideBin(process.argv))
  .usage('Usage: $0 --original <path> --current <path> [options]')
  .option('original', {
    type: 'string',
    demandOption: true,
    description: '원본 스크린샷 경로',
  })
  .option('current', {
    type: 'string',
    demandOption: true,
    description: '현재 구현 스크린샷 경로',
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    description: '출력 경로 (기본: diff-report.json)',
  })
  .option('format', {
    alias: 'f',
    type: 'string',
    choices: ['json', 'md'] as const,
    default: 'json',
    description: '출력 형식',
  })
  .option('threshold', {
    type: 'number',
    default: 0.1,
    description: '픽셀 비교 임계값 0-1 (기본: 0.1)',
  })
  .option('diff', {
    alias: 'd',
    type: 'string',
    description: 'diff 이미지 출력 경로 (선택)',
  })
  .option('skip-pixel', {
    type: 'boolean',
    default: false,
    description: '픽셀 비교 건너뛰기 (메타데이터만 비교)',
  })
  .help()
  .alias('help', 'h')
  .example(
    '$0 --original original.png --current preview.png',
    '기본 비교'
  )
  .example(
    '$0 --original a.png --current b.png --format md',
    '마크다운 형식'
  )
  .parseSync();

// ============================================================================
// PNG Metadata Extraction
// ============================================================================

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function isPngFile(buffer: Buffer): boolean {
  if (buffer.length < 8) return false;
  return buffer.subarray(0, 8).equals(PNG_SIGNATURE);
}

function extractPngMetadata(filePath: string): ImageMetadata {
  const absolutePath = path.resolve(filePath);

  if (!fs.existsSync(absolutePath)) {
    throw new Error(`File not found: ${absolutePath}`);
  }

  const stats = fs.statSync(absolutePath);
  const buffer = fs.readFileSync(absolutePath);

  if (!isPngFile(buffer)) {
    throw new Error(`Not a valid PNG file: ${absolutePath}`);
  }

  // PNG IHDR chunk: offset 16 = width, offset 20 = height (big-endian)
  const width = buffer.readUInt32BE(16);
  const height = buffer.readUInt32BE(20);

  return {
    filePath: absolutePath,
    width,
    height,
    fileSize: stats.size,
    format: 'PNG',
  };
}

// ============================================================================
// Pixel Comparison (pixelmatch)
// ============================================================================

function loadPng(filePath: string): PNG {
  const buffer = fs.readFileSync(filePath);
  return PNG.sync.read(buffer);
}

function resizePngToMatch(source: PNG, targetWidth: number, targetHeight: number): PNG {
  // 크기가 다르면 작은 쪽에 맞춰 새 이미지 생성 (빈 영역은 투명)
  const result = new PNG({ width: targetWidth, height: targetHeight });

  // 원본 데이터 복사 (겹치는 영역만)
  const copyWidth = Math.min(source.width, targetWidth);
  const copyHeight = Math.min(source.height, targetHeight);

  for (let y = 0; y < copyHeight; y++) {
    for (let x = 0; x < copyWidth; x++) {
      const srcIdx = (source.width * y + x) << 2;
      const dstIdx = (targetWidth * y + x) << 2;
      result.data[dstIdx] = source.data[srcIdx];
      result.data[dstIdx + 1] = source.data[srcIdx + 1];
      result.data[dstIdx + 2] = source.data[srcIdx + 2];
      result.data[dstIdx + 3] = source.data[srcIdx + 3];
    }
  }

  return result;
}

function comparePixels(
  originalPath: string,
  currentPath: string,
  options: { threshold: number; diffOutputPath?: string }
): PixelDiff {
  const original = loadPng(originalPath);
  const current = loadPng(currentPath);

  // 크기가 다르면 더 큰 쪽에 맞춤
  const width = Math.max(original.width, current.width);
  const height = Math.max(original.height, current.height);

  let img1 = original;
  let img2 = current;

  if (original.width !== width || original.height !== height) {
    img1 = resizePngToMatch(original, width, height);
  }
  if (current.width !== width || current.height !== height) {
    img2 = resizePngToMatch(current, width, height);
  }

  const diff = new PNG({ width, height });

  const diffPixels = pixelmatch(
    img1.data,
    img2.data,
    diff.data,
    width,
    height,
    { threshold: options.threshold }
  );

  const totalPixels = width * height;
  const diffPercent = (diffPixels / totalPixels) * 100;

  let diffImagePath: string | null = null;

  if (options.diffOutputPath) {
    const diffBuffer = PNG.sync.write(diff);
    fs.writeFileSync(options.diffOutputPath, diffBuffer);
    diffImagePath = path.resolve(options.diffOutputPath);
  }

  return {
    enabled: true,
    totalPixels,
    diffPixels,
    diffPercent: Math.round(diffPercent * 100) / 100,
    diffImagePath,
    threshold: options.threshold,
  };
}

// ============================================================================
// Comparison Logic
// ============================================================================

function calculateDiffPercent(original: number, current: number): number {
  if (original === 0) return current === 0 ? 0 : 100;
  return ((current - original) / original) * 100;
}

interface CompareOptions {
  skipPixel?: boolean;
  threshold?: number;
  diffOutputPath?: string;
}

function compareImages(
  original: ImageMetadata,
  current: ImageMetadata,
  options: CompareOptions = {}
): ComparisonResult {
  const widthDiff = current.width - original.width;
  const heightDiff = current.height - original.height;
  const fileSizeDiff = current.fileSize - original.fileSize;

  const widthDiffPercent = calculateDiffPercent(original.width, current.width);
  const heightDiffPercent = calculateDiffPercent(original.height, current.height);
  const fileSizeDiffPercent = calculateDiffPercent(
    original.fileSize,
    current.fileSize
  );

  const differences: Differences = {
    widthMatch: widthDiff === 0,
    widthDiff,
    widthDiffPercent: Math.round(widthDiffPercent * 100) / 100,
    heightMatch: heightDiff === 0,
    heightDiff,
    heightDiffPercent: Math.round(heightDiffPercent * 100) / 100,
    fileSizeDiff,
    fileSizeDiffPercent: Math.round(fileSizeDiffPercent * 100) / 100,
  };

  // Pixel comparison
  let pixelDiff: PixelDiff;

  if (options.skipPixel) {
    pixelDiff = {
      enabled: false,
      totalPixels: 0,
      diffPixels: 0,
      diffPercent: 0,
      diffImagePath: null,
      threshold: options.threshold || 0.1,
    };
  } else {
    pixelDiff = comparePixels(original.filePath, current.filePath, {
      threshold: options.threshold || 0.1,
      diffOutputPath: options.diffOutputPath,
    });
  }

  // Determine status (now considering pixel diff)
  let status: ComparisonStatus;

  const absWidthDiffPercent = Math.abs(widthDiffPercent);
  const absHeightDiffPercent = Math.abs(heightDiffPercent);
  const absFileSizeDiffPercent = Math.abs(fileSizeDiffPercent);

  // 픽셀 비교가 활성화된 경우 픽셀 차이도 고려
  const pixelDiffThreshold = pixelDiff.enabled ? pixelDiff.diffPercent : 0;

  if (
    differences.widthMatch &&
    differences.heightMatch &&
    absFileSizeDiffPercent < 5 &&
    pixelDiffThreshold < 1
  ) {
    status = 'match';
  } else if (
    absWidthDiffPercent > 5 ||
    absHeightDiffPercent > 5 ||
    absFileSizeDiffPercent > 20 ||
    pixelDiffThreshold > 10
  ) {
    status = 'major_diff';
  } else {
    status = 'minor_diff';
  }

  return {
    original,
    current,
    differences,
    pixelDiff,
    status,
  };
}

// ============================================================================
// Report Generation
// ============================================================================

function generateRecommendations(result: ComparisonResult): string[] {
  const recommendations: string[] = [];
  const { differences, pixelDiff } = result;

  if (!differences.widthMatch) {
    recommendations.push(
      `너비 차이 ${differences.widthDiff}px (${differences.widthDiffPercent}%) 확인 필요`
    );
  }

  if (!differences.heightMatch) {
    recommendations.push(
      `높이 차이 ${differences.heightDiff}px (${differences.heightDiffPercent}%) 확인 필요`
    );
  }

  if (Math.abs(differences.fileSizeDiffPercent) > 10) {
    const direction = differences.fileSizeDiff > 0 ? '증가' : '감소';
    recommendations.push(
      `파일 크기 ${Math.abs(differences.fileSizeDiffPercent)}% ${direction} - 콘텐츠 변화 가능성`
    );
  }

  // 픽셀 비교 결과 권장사항
  if (pixelDiff.enabled) {
    if (pixelDiff.diffPercent > 10) {
      recommendations.push(
        `픽셀 차이 ${pixelDiff.diffPercent}% (${pixelDiff.diffPixels}/${pixelDiff.totalPixels} 픽셀) - 주요 시각적 차이 존재`
      );
    } else if (pixelDiff.diffPercent > 5) {
      recommendations.push(
        `픽셀 차이 ${pixelDiff.diffPercent}% - 중간 수준의 시각적 차이`
      );
    } else if (pixelDiff.diffPercent > 1) {
      recommendations.push(
        `픽셀 차이 ${pixelDiff.diffPercent}% - 미세한 시각적 차이`
      );
    }

    if (pixelDiff.diffImagePath) {
      recommendations.push(`diff 이미지 확인: ${pixelDiff.diffImagePath}`);
    }
  }

  if (recommendations.length === 0) {
    if (pixelDiff.enabled) {
      recommendations.push(`픽셀 비교 결과 거의 동일함 (차이 ${pixelDiff.diffPercent}%)`);
    } else {
      recommendations.push('메타데이터 기준 유사함. 시각적 검토 권장.');
    }
  }

  return recommendations;
}

function generateReport(result: ComparisonResult): DiffReport {
  return {
    version: '1.0',
    timestamp: new Date().toISOString(),
    files: {
      original: result.original.filePath,
      current: result.current.filePath,
    },
    comparison: result,
    recommendations: generateRecommendations(result),
  };
}

// ============================================================================
// Output Formatting
// ============================================================================

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getStatusEmoji(status: ComparisonStatus): string {
  switch (status) {
    case 'match':
      return '✅';
    case 'minor_diff':
      return '⚠️';
    case 'major_diff':
      return '❌';
    default:
      return '❓';
  }
}

function getStatusText(status: ComparisonStatus): string {
  switch (status) {
    case 'match':
      return 'Match';
    case 'minor_diff':
      return 'Minor Differences';
    case 'major_diff':
      return 'Major Differences';
    default:
      return 'Error';
  }
}

function toMarkdown(report: DiffReport): string {
  const { comparison } = report;
  const { original, current, differences, pixelDiff, status } = comparison;

  const lines: string[] = [
    '# Screenshot Comparison Report',
    '',
    `**Generated**: ${report.timestamp}`,
    `**Status**: ${getStatusEmoji(status)} ${getStatusText(status)}`,
    '',
    '## Files',
    '',
    `- **Original**: ${path.basename(original.filePath)}`,
    `- **Current**: ${path.basename(current.filePath)}`,
    '',
    '## Image Metadata',
    '',
    '| Property | Original | Current | Difference |',
    '|----------|----------|---------|------------|',
    `| Width | ${original.width}px | ${current.width}px | ${differences.widthMatch ? '✅ Match' : `${differences.widthDiff}px (${differences.widthDiffPercent}%)`} |`,
    `| Height | ${original.height}px | ${current.height}px | ${differences.heightMatch ? '✅ Match' : `${differences.heightDiff}px (${differences.heightDiffPercent}%)`} |`,
    `| File Size | ${formatFileSize(original.fileSize)} | ${formatFileSize(current.fileSize)} | ${differences.fileSizeDiffPercent}% |`,
    '',
  ];

  // 픽셀 비교 결과
  if (pixelDiff.enabled) {
    lines.push('## Pixel Comparison');
    lines.push('');
    lines.push('| Metric | Value |');
    lines.push('|--------|-------|');
    lines.push(`| Total Pixels | ${pixelDiff.totalPixels.toLocaleString()} |`);
    lines.push(`| Different Pixels | ${pixelDiff.diffPixels.toLocaleString()} |`);
    lines.push(`| Difference | ${pixelDiff.diffPercent}% |`);
    lines.push(`| Threshold | ${pixelDiff.threshold} |`);
    if (pixelDiff.diffImagePath) {
      lines.push(`| Diff Image | [View](${path.basename(pixelDiff.diffImagePath)}) |`);
    }
    lines.push('');
  }

  lines.push('## Recommendations');
  lines.push('');

  for (const rec of report.recommendations) {
    lines.push(`- ${rec}`);
  }

  lines.push('', '---', '');
  if (pixelDiff.enabled) {
    lines.push('*Comparison includes both metadata and pixel-level analysis.*');
  } else {
    lines.push('*Note: This comparison is metadata-based only. Visual inspection recommended.*');
  }

  return lines.join('\n');
}

// ============================================================================
// Main
// ============================================================================

async function main(): Promise<void> {
  const originalPath = path.resolve(argv.original);
  const currentPath = path.resolve(argv.current);
  const skipPixel = argv['skip-pixel'] as boolean;
  const threshold = argv.threshold as number;
  const diffOutputPath = argv.diff ? path.resolve(argv.diff as string) : undefined;

  console.log('Comparing screenshots...');
  console.log(`  Original: ${originalPath}`);
  console.log(`  Current: ${currentPath}`);
  console.log(`  Pixel comparison: ${skipPixel ? 'disabled' : 'enabled'}`);
  if (!skipPixel) {
    console.log(`  Threshold: ${threshold}`);
  }

  // Extract metadata
  const originalMeta = extractPngMetadata(originalPath);
  const currentMeta = extractPngMetadata(currentPath);

  console.log(`\nOriginal: ${originalMeta.width}x${originalMeta.height} (${formatFileSize(originalMeta.fileSize)})`);
  console.log(`Current: ${currentMeta.width}x${currentMeta.height} (${formatFileSize(currentMeta.fileSize)})`);

  // Compare with pixel comparison
  console.log('\nRunning comparison...');
  const result = compareImages(originalMeta, currentMeta, {
    skipPixel,
    threshold,
    diffOutputPath,
  });
  const report = generateReport(result);

  console.log(`\nStatus: ${getStatusEmoji(result.status)} ${getStatusText(result.status)}`);

  // 픽셀 비교 결과 출력
  if (result.pixelDiff.enabled) {
    console.log(`\nPixel Diff: ${result.pixelDiff.diffPercent}% (${result.pixelDiff.diffPixels.toLocaleString()} / ${result.pixelDiff.totalPixels.toLocaleString()} pixels)`);
    if (result.pixelDiff.diffImagePath) {
      console.log(`Diff image: ${result.pixelDiff.diffImagePath}`);
    }
  }

  // Output path
  const defaultOutputName =
    argv.format === 'md' ? 'diff-report.md' : 'diff-report.json';
  const outputPath = argv.output
    ? path.resolve(argv.output as string)
    : path.join(process.cwd(), defaultOutputName);

  // Save
  const content =
    argv.format === 'md'
      ? toMarkdown(report)
      : JSON.stringify(report, null, 2);

  fs.writeFileSync(outputPath, content, 'utf-8');

  console.log(`\nReport saved: ${outputPath}`);

  // Print recommendations
  console.log('\n--- Recommendations ---');
  for (const rec of report.recommendations) {
    console.log(`  • ${rec}`);
  }
}

main().catch((error) => {
  console.error('Error:', error.message);
  process.exit(1);
});
