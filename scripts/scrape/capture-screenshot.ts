/**
 * 단순 스크린샷 캡처 CLI
 *
 * Phase 5 검토 단계에서 로컬 프리뷰 서버의 스크린샷 촬영용
 *
 * Usage:
 *   npx tsx scripts/scrape/capture-screenshot.ts --url "http://localhost:3000" --output "preview.png"
 */

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import {
  launchBrowser,
  createPage,
  navigateToUrl,
  closeBrowser,
  registerShutdownHandler,
} from './lib/browser.js';
import { captureFullPage, captureViewport, captureSection } from './lib/screenshot.js';

interface CaptureOptions {
  url: string;
  output: string;
  width: number;
  height: number;
  wait: number;
  fullPage: boolean;
  maxHeight?: number;
  timeout: number;
}

const argv = yargs(hideBin(process.argv))
  .usage('Usage: $0 --url <url> --output <path> [options]')
  .option('url', {
    alias: 'u',
    type: 'string',
    demandOption: true,
    description: '캡처할 URL',
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    demandOption: true,
    description: '출력 파일 경로 (.png)',
  })
  .option('width', {
    type: 'number',
    default: 1920,
    description: '뷰포트 너비',
  })
  .option('height', {
    type: 'number',
    default: 1080,
    description: '뷰포트 높이',
  })
  .option('wait', {
    alias: 'w',
    type: 'number',
    default: 2000,
    description: '렌더링 대기 시간 (ms)',
  })
  .option('full-page', {
    type: 'boolean',
    default: true,
    description: '전체 페이지 캡처 여부',
  })
  .option('max-height', {
    type: 'number',
    description: '최대 캡처 높이 제한 (픽셀)',
  })
  .option('timeout', {
    alias: 't',
    type: 'number',
    default: 30000,
    description: '페이지 로드 타임아웃 (ms)',
  })
  .help()
  .alias('help', 'h')
  .example('$0 --url https://example.com --output screenshot.png', '기본 캡처')
  .example('$0 -u http://localhost:3000 -o preview.png --max-height 5000', '긴 페이지 상단만')
  .example('$0 -u https://example.com -o mobile.png --width 375 --no-full-page', '모바일 뷰포트')
  .parseSync();

const options: CaptureOptions = {
  url: argv.url,
  output: argv.output,
  width: argv.width,
  height: argv.height,
  wait: argv.wait,
  fullPage: argv['full-page'],
  maxHeight: argv['max-height'],
  timeout: argv.timeout,
};

async function main(): Promise<void> {
  registerShutdownHandler();

  console.log(`Capturing: ${options.url}`);
  console.log(`Output: ${options.output}`);
  console.log(`Viewport: ${options.width}x${options.height}`);

  const browser = await launchBrowser();
  const page = await createPage(browser, {
    width: options.width,
    height: options.height,
  });

  await navigateToUrl(page, options.url, {
    timeout: options.timeout,
    retries: 1,
  });

  // 렌더링 대기
  await page.waitForTimeout(options.wait);

  // 캡처 모드 결정
  if (options.maxHeight && options.maxHeight > 0) {
    // 높이 제한 모드: clip으로 상단 영역만
    console.log(`Capturing top ${options.maxHeight}px...`);
    await captureSection(
      page,
      { x: 0, y: 0, width: options.width, height: options.maxHeight },
      options.output
    );
  } else if (options.fullPage) {
    // 전체 페이지 캡처
    console.log('Capturing full page...');
    await captureFullPage(page, options.output);
  } else {
    // 뷰포트만 캡처
    console.log('Capturing viewport only...');
    await captureViewport(page, options.output);
  }

  console.log(`Screenshot saved: ${options.output}`);
  await closeBrowser();
}

main().catch(async (error) => {
  console.error('Capture failed:', error.message);
  await closeBrowser();
  process.exit(1);
});
