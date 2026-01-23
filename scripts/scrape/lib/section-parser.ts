/**
 * 페이지 섹션 분할 및 분석
 */

import { Page } from 'puppeteer';
import { SectionInfo, ElementBounds } from './types.js';
import { captureElement } from './screenshot.js';
import { saveText, join } from '../utils/file-system.js';

/** 시맨틱 섹션 태그 */
const SEMANTIC_TAGS = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer'];

/** 섹션 후보 선택자 */
const SECTION_SELECTORS = [
  // 시맨틱 태그 (body 직계 자식 우선)
  'body > header',
  'body > nav',
  'body > main',
  'body > section',
  'body > article',
  'body > aside',
  'body > footer',
  // 중첩된 시맨틱 태그
  'main > section',
  'main > article',
  // 클래스 기반 섹션 (일반적인 패턴)
  '[class*="hero"]',
  '[class*="banner"]',
  '[class*="features"]',
  '[class*="pricing"]',
  '[class*="testimonial"]',
  '[class*="contact"]',
  '[class*="about"]',
  '[class*="services"]',
  '[class*="portfolio"]',
  '[class*="team"]',
  '[class*="cta"]',
  // ID 기반 섹션
  '[id*="hero"]',
  '[id*="features"]',
  '[id*="about"]',
  '[id*="contact"]',
];

/**
 * 페이지에서 섹션 감지
 */
export async function detectSections(page: Page): Promise<Array<{
  selector: string;
  tagName: string;
  bounds: ElementBounds;
}>> {
  const sectionScript = `
    ((selectors, semanticTags) => {
      const detected = [];
      const processedElements = new Set();

      const getUniqueSelector = (element) => {
        if (element.id) return '#' + element.id;

        const tagName = element.tagName.toLowerCase();
        const parent = element.parentElement;

        if (!parent || parent === document.body) {
          const siblings = parent
            ? Array.from(parent.children).filter(el => el.tagName === element.tagName)
            : [element];
          const index = siblings.indexOf(element);
          return index > 0 ? 'body > ' + tagName + ':nth-of-type(' + (index + 1) + ')' : 'body > ' + tagName;
        }

        const parentSelector = getUniqueSelector(parent);
        const siblings = Array.from(parent.children).filter(el => el.tagName === element.tagName);
        const index = siblings.indexOf(element);

        return index > 0
          ? parentSelector + ' > ' + tagName + ':nth-of-type(' + (index + 1) + ')'
          : parentSelector + ' > ' + tagName;
      };

      for (const tag of semanticTags) {
        const elements = document.querySelectorAll(tag);
        elements.forEach((el) => {
          if (processedElements.has(el)) return;
          const rect = el.getBoundingClientRect();
          if (rect.width < 100 || rect.height < 50) return;

          processedElements.add(el);
          detected.push({
            selector: getUniqueSelector(el),
            tagName: el.tagName.toLowerCase(),
            bounds: {
              x: Math.round(rect.x + window.scrollX),
              y: Math.round(rect.y + window.scrollY),
              width: Math.round(rect.width),
              height: Math.round(rect.height),
            },
          });
        });
      }

      for (const selector of selectors) {
        try {
          const elements = document.querySelectorAll(selector);
          elements.forEach((el) => {
            if (processedElements.has(el)) return;
            const rect = el.getBoundingClientRect();
            if (rect.width < 100 || rect.height < 50) return;

            processedElements.add(el);
            detected.push({
              selector: getUniqueSelector(el),
              tagName: el.tagName.toLowerCase(),
              bounds: {
                x: Math.round(rect.x + window.scrollX),
                y: Math.round(rect.y + window.scrollY),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
              },
            });
          });
        } catch (e) {
          // 잘못된 선택자 무시
        }
      }

      return detected.sort((a, b) => a.bounds.y - b.bounds.y);
    })(${JSON.stringify(SECTION_SELECTORS)}, ${JSON.stringify(SEMANTIC_TAGS)})
  `;

  return await page.evaluate(sectionScript) as Array<{
    selector: string;
    tagName: string;
    bounds: ElementBounds;
  }>;
}

/**
 * 섹션의 HTML 추출
 */
export async function extractSectionHtml(page: Page, selector: string): Promise<string> {
  return await page.evaluate((sel: string) => {
    const element = document.querySelector(sel);
    return element ? element.outerHTML : '';
  }, selector);
}

/**
 * 모든 섹션 처리 (스크린샷 + HTML 저장)
 */
export async function processSections(
  page: Page,
  outputDir: string
): Promise<SectionInfo[]> {
  const sections: SectionInfo[] = [];
  const detected = await detectSections(page);

  console.log(`Found ${detected.length} sections`);

  for (let i = 0; i < detected.length; i++) {
    const section = detected[i];
    const screenshotPath = join(outputDir, 'sections', `section-${i}.png`);
    const htmlPath = join(outputDir, 'sections', `section-${i}.html`);

    console.log(`  Processing section ${i}: ${section.tagName} (${section.selector})`);

    // 스크린샷 캡처
    const bounds = await captureElement(page, section.selector, screenshotPath);

    // HTML 추출 및 저장
    const html = await extractSectionHtml(page, section.selector);
    if (html) {
      await saveText(htmlPath, html);
    }

    sections.push({
      index: i,
      tagName: section.tagName,
      selector: section.selector,
      bounds: bounds || section.bounds,
      files: {
        screenshot: `sections/section-${i}.png`,
        html: `sections/section-${i}.html`,
      },
    });
  }

  return sections;
}
