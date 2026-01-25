/**
 * DOM/CSS/HTML 추출
 */

import { Page } from 'puppeteer';
import { DOMNode, ComputedStyles, ElementStyle } from './types.js';

/**
 * 페이지 HTML 소스 추출
 */
export async function extractHtml(page: Page): Promise<string> {
  return await page.content();
}

/**
 * DOM 트리 구조 추출
 */
export async function extractDomTree(page: Page): Promise<DOMNode> {
  const domScript = `
    (() => {
      const buildTree = (element, depth = 0, maxDepth = 10) => {
        if (depth > maxDepth) return null;

        const attributes = {};
        for (const attr of element.attributes) {
          attributes[attr.name] = attr.value.length > 200
            ? attr.value.substring(0, 200) + '...'
            : attr.value;
        }

        const children = [];
        for (const child of element.children) {
          const childNode = buildTree(child, depth + 1, maxDepth);
          if (childNode) children.push(childNode);
        }

        let textContent;
        const directText = Array.from(element.childNodes)
          .filter(node => node.nodeType === Node.TEXT_NODE)
          .map(node => node.textContent?.trim())
          .filter(Boolean)
          .join(' ');

        if (directText && directText.length > 0) {
          textContent = directText.length > 500 ? directText.substring(0, 500) + '...' : directText;
        }

        return {
          tagName: element.tagName.toLowerCase(),
          id: element.id || undefined,
          className: element.className || undefined,
          attributes,
          children,
          textContent,
        };
      };

      return buildTree(document.documentElement);
    })()
  `;

  return await page.evaluate(domScript) as DOMNode;
}

/**
 * 페이지 전체 스타일 분석 및 추출
 */
export async function extractComputedStyles(page: Page): Promise<ComputedStyles> {
  // 문자열로 evaluate를 실행하여 esbuild 변환 문제 회피
  const styleScript = `
    (() => {
      const colors = {
        background: new Set(),
        text: new Set(),
        accent: new Set(),
        border: new Set(),
      };
      const fonts = {
        families: new Set(),
        sizes: new Set(),
        weights: new Set(),
      };
      const layout = {
        maxWidth: null,
        padding: new Set(),
        margin: new Set(),
        display: new Set(),
      };
      const effects = {
        boxShadow: new Set(),
        borderRadius: new Set(),
      };

      const selectors = [
        'body', 'header', 'nav', 'main', 'section', 'article', 'aside', 'footer',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'button',
        '.container', '[class*="wrapper"]', '[class*="content"]'
      ];

      const rgbToHex = (rgb) => {
        if (rgb.startsWith('#')) return rgb;
        if (rgb === 'transparent' || rgb === 'rgba(0, 0, 0, 0)') return 'transparent';
        const match = rgb.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
        if (!match) return rgb;
        const r = parseInt(match[1]);
        const g = parseInt(match[2]);
        const b = parseInt(match[3]);
        return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
      };

      for (const selector of selectors) {
        const elements = document.querySelectorAll(selector);
        elements.forEach((el) => {
          const style = window.getComputedStyle(el);
          const bgColor = rgbToHex(style.backgroundColor);
          if (bgColor !== 'transparent' && bgColor !== 'rgba(0, 0, 0, 0)') {
            colors.background.add(bgColor);
          }
          colors.text.add(rgbToHex(style.color));
          if (style.borderColor && style.borderColor !== 'transparent') {
            colors.border.add(rgbToHex(style.borderColor));
          }
          fonts.families.add(style.fontFamily.split(',')[0].trim().replace(/['"]/g, ''));
          fonts.sizes.add(style.fontSize);
          fonts.weights.add(style.fontWeight);
          if (style.maxWidth && style.maxWidth !== 'none') {
            layout.maxWidth = style.maxWidth;
          }
          if (style.padding !== '0px') layout.padding.add(style.padding);
          if (style.margin !== '0px') layout.margin.add(style.margin);
          layout.display.add(style.display);
          if (style.boxShadow && style.boxShadow !== 'none') effects.boxShadow.add(style.boxShadow);
          if (style.borderRadius && style.borderRadius !== '0px') effects.borderRadius.add(style.borderRadius);
        });
      }

      document.querySelectorAll('a, button, [role="button"]').forEach((el) => {
        const style = window.getComputedStyle(el);
        const bgColor = rgbToHex(style.backgroundColor);
        if (bgColor !== 'transparent' && bgColor !== '#ffffff' && bgColor !== '#000000') {
          colors.accent.add(bgColor);
        }
        const color = rgbToHex(style.color);
        if (color !== '#000000' && color !== '#ffffff') {
          colors.accent.add(color);
        }
      });

      return {
        colors: {
          background: [...colors.background].slice(0, 10),
          text: [...colors.text].slice(0, 10),
          accent: [...colors.accent].slice(0, 10),
          border: [...colors.border].slice(0, 10),
        },
        fonts: {
          families: [...fonts.families].slice(0, 10),
          sizes: [...fonts.sizes].slice(0, 10),
          weights: [...fonts.weights].slice(0, 5),
        },
        layout: {
          maxWidth: layout.maxWidth,
          padding: [...layout.padding].slice(0, 10),
          margin: [...layout.margin].slice(0, 10),
          display: [...layout.display].slice(0, 10),
        },
        effects: {
          boxShadow: [...effects.boxShadow].slice(0, 5),
          borderRadius: [...effects.borderRadius].slice(0, 5),
        },
      };
    })()
  `;

  return await page.evaluate(styleScript) as ComputedStyles;
}

/**
 * 특정 요소의 상세 스타일 추출
 */
export async function extractElementStyles(
  page: Page,
  selectors: string[]
): Promise<ElementStyle[]> {
  return await page.evaluate((sels) => {
    const results: ElementStyle[] = [];

    for (const selector of sels) {
      const element = document.querySelector(selector);
      if (!element) continue;

      const style = window.getComputedStyle(element);

      results.push({
        selector,
        tagName: element.tagName.toLowerCase(),
        styles: {
          color: style.color,
          backgroundColor: style.backgroundColor,
          fontFamily: style.fontFamily,
          fontSize: style.fontSize,
          fontWeight: style.fontWeight,
          lineHeight: style.lineHeight,
          padding: style.padding,
          margin: style.margin,
          display: style.display,
          position: style.position,
          width: style.width,
          height: style.height,
          boxShadow: style.boxShadow,
          borderRadius: style.borderRadius,
          borderColor: style.borderColor,
        },
      });
    }

    return results;
  }, selectors);
}
