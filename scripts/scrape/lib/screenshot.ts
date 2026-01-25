/**
 * 스크린샷 캡처 유틸리티
 */

import { Page, ElementHandle } from 'puppeteer';
import { ElementBounds } from './types.js';
import { saveBinary } from '../utils/file-system.js';

/**
 * 전체 페이지 스크린샷 캡처
 */
export async function captureFullPage(page: Page, outputPath: string): Promise<void> {
  const screenshot = await page.screenshot({
    fullPage: true,
    type: 'png',
  });

  await saveBinary(outputPath, screenshot as Buffer);
}

/**
 * 특정 요소 스크린샷 캡처
 */
export async function captureElement(
  page: Page,
  selector: string,
  outputPath: string
): Promise<ElementBounds | null> {
  try {
    const element = await page.$(selector);
    if (!element) {
      console.warn(`Element not found: ${selector}`);
      return null;
    }

    const bounds = await getElementBounds(element);
    if (!bounds || bounds.width === 0 || bounds.height === 0) {
      console.warn(`Element has no dimensions: ${selector}`);
      return null;
    }

    const screenshot = await element.screenshot({
      type: 'png',
    });

    await saveBinary(outputPath, screenshot as Buffer);

    return bounds;
  } catch (error) {
    console.warn(`Failed to capture element ${selector}: ${(error as Error).message}`);
    return null;
  }
}

/**
 * 섹션 스크린샷 캡처 (클립 영역 지정)
 */
export async function captureSection(
  page: Page,
  bounds: ElementBounds,
  outputPath: string
): Promise<void> {
  const screenshot = await page.screenshot({
    type: 'png',
    clip: {
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
    },
  });

  await saveBinary(outputPath, screenshot as Buffer);
}

/**
 * 요소의 경계(bounds) 정보 추출
 */
export async function getElementBounds(
  element: ElementHandle
): Promise<ElementBounds | null> {
  const boundingBox = await element.boundingBox();
  if (!boundingBox) {
    return null;
  }

  return {
    x: Math.round(boundingBox.x),
    y: Math.round(boundingBox.y),
    width: Math.round(boundingBox.width),
    height: Math.round(boundingBox.height),
  };
}

/**
 * 페이지에서 모든 섹션의 bounds 추출
 */
export async function getAllSectionBounds(
  page: Page,
  selectors: string[]
): Promise<Map<string, ElementBounds>> {
  const boundsMap = new Map<string, ElementBounds>();

  for (const selector of selectors) {
    const element = await page.$(selector);
    if (element) {
      const bounds = await getElementBounds(element);
      if (bounds && bounds.width > 0 && bounds.height > 0) {
        boundsMap.set(selector, bounds);
      }
    }
  }

  return boundsMap;
}

/**
 * 뷰포트 스크린샷 (현재 보이는 영역만)
 */
export async function captureViewport(page: Page, outputPath: string): Promise<void> {
  const screenshot = await page.screenshot({
    fullPage: false,
    type: 'png',
  });

  await saveBinary(outputPath, screenshot as Buffer);
}
