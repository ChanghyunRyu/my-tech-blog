/**
 * Puppeteer 브라우저 관리
 */

import puppeteer, { Browser, Page, PuppeteerLaunchOptions } from 'puppeteer';

let browserInstance: Browser | null = null;

/** 브라우저 실행 옵션 */
const DEFAULT_LAUNCH_OPTIONS: PuppeteerLaunchOptions = {
  headless: 'new',
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--disable-gpu',
    '--window-size=1920,1080',
  ],
};

/**
 * 브라우저 인스턴스 시작
 */
export async function launchBrowser(options?: Partial<PuppeteerLaunchOptions>): Promise<Browser> {
  if (browserInstance) {
    return browserInstance;
  }

  browserInstance = await puppeteer.launch({
    ...DEFAULT_LAUNCH_OPTIONS,
    ...options,
  });

  return browserInstance;
}

/**
 * 새 페이지 생성 및 설정
 */
export async function createPage(
  browser: Browser,
  viewport: { width: number; height: number }
): Promise<Page> {
  const page = await browser.newPage();

  // 뷰포트 설정
  await page.setViewport({
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
  });

  // User-Agent 설정 (봇 탐지 회피)
  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  );

  // 불필요한 리소스 차단 (성능 향상)
  await page.setRequestInterception(true);
  page.on('request', (request) => {
    const resourceType = request.resourceType();
    // 폰트와 미디어는 차단 (이미지, CSS, JS는 필요)
    if (['font', 'media'].includes(resourceType)) {
      request.abort();
    } else {
      request.continue();
    }
  });

  return page;
}

/**
 * URL로 네비게이션 (재시도 로직 포함)
 */
export async function navigateToUrl(
  page: Page,
  url: string,
  options: {
    timeout?: number;
    waitUntil?: 'load' | 'domcontentloaded' | 'networkidle0' | 'networkidle2';
    retries?: number;
  } = {}
): Promise<void> {
  const { timeout = 30000, waitUntil = 'networkidle2', retries = 3 } = options;

  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await page.goto(url, {
        timeout,
        waitUntil,
      });
      return; // 성공시 리턴
    } catch (error) {
      lastError = error as Error;
      console.warn(`Navigation attempt ${attempt}/${retries} failed: ${lastError.message}`);

      if (attempt < retries) {
        // 지수 백오프 대기
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`Retrying in ${delay}ms...`);
        await sleep(delay);
      }
    }
  }

  throw new Error(`Failed to navigate to ${url} after ${retries} attempts: ${lastError?.message}`);
}

/**
 * 페이지 로드 후 추가 대기
 */
export async function waitForContent(page: Page, waitMs: number): Promise<void> {
  if (waitMs > 0) {
    await sleep(waitMs);
  }
}

/**
 * 브라우저 종료
 */
export async function closeBrowser(): Promise<void> {
  if (browserInstance) {
    await browserInstance.close();
    browserInstance = null;
  }
}

/**
 * 현재 브라우저 인스턴스 반환
 */
export function getBrowser(): Browser | null {
  return browserInstance;
}

/**
 * Graceful shutdown 핸들러 등록
 */
export function registerShutdownHandler(): void {
  const shutdown = async (signal: string) => {
    console.log(`\nReceived ${signal}, closing browser...`);
    await closeBrowser();
    process.exit(0);
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
}

/** sleep 유틸리티 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
