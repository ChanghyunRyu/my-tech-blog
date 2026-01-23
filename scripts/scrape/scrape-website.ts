#!/usr/bin/env node
/**
 * 웹사이트 스크래핑 메인 스크립트
 *
 * 사용법:
 *   npx tsx scripts/scrape/scrape-website.ts --url "https://example.com"
 *
 * 옵션:
 *   --url, -u      대상 URL (필수)
 *   --output, -o   출력 경로 (기본: public/scraped/{domain}-{date})
 *   --wait, -w     페이지 로드 후 대기 시간 ms (기본: 2000)
 *   --width        뷰포트 너비 (기본: 1920)
 *   --height       뷰포트 높이 (기본: 1080)
 *   --timeout, -t  페이지 로드 타임아웃 ms (기본: 30000)
 *   --retries, -r  재시도 횟수 (기본: 3)
 */

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { resolve } from 'path';

import { ScrapeOptions, ScrapeResult, ScrapePhase } from './lib/types.js';
import { isValidUrl, generateOutputDirName } from './utils/url-parser.js';
import { createOutputDirectory, saveJson, saveText, join } from './utils/file-system.js';
import {
  launchBrowser,
  createPage,
  navigateToUrl,
  waitForContent,
  closeBrowser,
  registerShutdownHandler,
} from './lib/browser.js';
import { captureFullPage } from './lib/screenshot.js';
import { extractHtml, extractDomTree, extractComputedStyles } from './lib/extractor.js';
import { processSections } from './lib/section-parser.js';

// 기본값
const DEFAULT_OPTIONS = {
  wait: 2000,
  width: 1920,
  height: 1080,
  timeout: 30000,
  retries: 3,
  outputBase: 'public/scraped',
};

// CLI 파싱
const argv = yargs(hideBin(process.argv))
  .usage('Usage: $0 --url <url> [options]')
  .option('url', {
    alias: 'u',
    type: 'string',
    description: 'Target URL to scrape',
    demandOption: true,
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    description: 'Output directory path',
  })
  .option('wait', {
    alias: 'w',
    type: 'number',
    default: DEFAULT_OPTIONS.wait,
    description: 'Wait time after page load (ms)',
  })
  .option('width', {
    type: 'number',
    default: DEFAULT_OPTIONS.width,
    description: 'Viewport width',
  })
  .option('height', {
    type: 'number',
    default: DEFAULT_OPTIONS.height,
    description: 'Viewport height',
  })
  .option('timeout', {
    alias: 't',
    type: 'number',
    default: DEFAULT_OPTIONS.timeout,
    description: 'Page load timeout (ms)',
  })
  .option('retries', {
    alias: 'r',
    type: 'number',
    default: DEFAULT_OPTIONS.retries,
    description: 'Number of retries on failure',
  })
  .help()
  .alias('help', 'h')
  .parseSync();

// 진행 상태 출력
function logProgress(phase: ScrapePhase, message: string): void {
  const timestamp = new Date().toISOString().substring(11, 19);
  console.log(`[${timestamp}] [${phase}] ${message}`);
}

// 메인 스크래핑 함수
async function scrapeWebsite(options: ScrapeOptions): Promise<ScrapeResult> {
  const startTime = Date.now();
  const timestamp = new Date().toISOString();

  // URL 검증
  if (!isValidUrl(options.url)) {
    throw new Error(`Invalid URL: ${options.url}`);
  }

  logProgress('init', `Starting scrape of ${options.url}`);

  // 출력 디렉토리 설정
  const outputDirName = generateOutputDirName(options.url);
  const outputBase = options.output || DEFAULT_OPTIONS.outputBase;
  const outputDir = resolve(process.cwd(), outputBase, outputDirName);

  logProgress('init', `Output directory: ${outputDir}`);

  // 디렉토리 생성
  await createOutputDirectory(outputBase, outputDirName);

  // Graceful shutdown 핸들러 등록
  registerShutdownHandler();

  try {
    // 브라우저 시작
    logProgress('launching-browser', 'Launching browser...');
    const browser = await launchBrowser();

    // 페이지 생성
    const page = await createPage(browser, {
      width: options.width,
      height: options.height,
    });

    // URL로 이동
    logProgress('navigating', `Navigating to ${options.url}...`);
    await navigateToUrl(page, options.url, {
      timeout: options.timeout,
      retries: options.retries,
    });

    // 추가 대기
    logProgress('waiting', `Waiting ${options.wait}ms for dynamic content...`);
    await waitForContent(page, options.wait);

    // 전체 페이지 스크린샷
    logProgress('capturing-screenshot', 'Capturing full page screenshot...');
    const screenshotPath = join(outputDir, 'full-page.png');
    await captureFullPage(page, screenshotPath);

    // HTML 추출
    logProgress('extracting-html', 'Extracting HTML...');
    const html = await extractHtml(page);
    const htmlPath = join(outputDir, 'page.html');
    await saveText(htmlPath, html);

    // 스타일 추출
    logProgress('extracting-styles', 'Extracting computed styles...');
    const styles = await extractComputedStyles(page);
    const stylesPath = join(outputDir, 'styles.json');
    await saveJson(stylesPath, styles);

    // DOM 트리 추출
    logProgress('extracting-dom', 'Extracting DOM tree...');
    const domTree = await extractDomTree(page);
    const domPath = join(outputDir, 'dom-tree.json');
    await saveJson(domPath, domTree);

    // 섹션 분할 및 처리
    logProgress('parsing-sections', 'Detecting and processing sections...');
    const sections = await processSections(page, outputDir);
    const sectionsPath = join(outputDir, 'sections.json');
    await saveJson(sectionsPath, sections);

    // 브라우저 종료
    logProgress('done', 'Closing browser...');
    await closeBrowser();

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    logProgress('done', `Scraping completed in ${duration}s`);

    return {
      url: options.url,
      timestamp,
      outputDir,
      files: {
        screenshot: 'full-page.png',
        html: 'page.html',
        styles: 'styles.json',
        domTree: 'dom-tree.json',
        sections: 'sections.json',
      },
      sectionsCount: sections.length,
      success: true,
    };
  } catch (error) {
    logProgress('error', `Error: ${(error as Error).message}`);
    await closeBrowser();

    return {
      url: options.url,
      timestamp,
      outputDir,
      files: {
        screenshot: '',
        html: '',
        styles: '',
        domTree: '',
        sections: '',
      },
      sectionsCount: 0,
      success: false,
      error: (error as Error).message,
    };
  }
}

// 메인 실행
async function main(): Promise<void> {
  const options: ScrapeOptions = {
    url: argv.url,
    output: argv.output,
    wait: argv.wait,
    width: argv.width,
    height: argv.height,
    timeout: argv.timeout,
    retries: argv.retries,
  };

  try {
    const result = await scrapeWebsite(options);

    if (result.success) {
      console.log('\n--- Scrape Result ---');
      console.log(`URL: ${result.url}`);
      console.log(`Output: ${result.outputDir}`);
      console.log(`Sections found: ${result.sectionsCount}`);
      console.log('\nGenerated files:');
      Object.entries(result.files).forEach(([key, value]) => {
        if (value) {
          console.log(`  - ${key}: ${value}`);
        }
      });
      process.exit(0);
    } else {
      console.error(`\nScraping failed: ${result.error}`);
      process.exit(1);
    }
  } catch (error) {
    console.error(`\nFatal error: ${(error as Error).message}`);
    process.exit(1);
  }
}

main();
