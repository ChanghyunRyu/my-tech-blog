/**
 * 스크래핑 관련 타입 정의
 */

/** CLI 옵션 */
export interface ScrapeOptions {
  url: string;
  output?: string;
  wait: number;
  width: number;
  height: number;
  timeout: number;
  retries: number;
}

/** DOM 노드 구조 */
export interface DOMNode {
  tagName: string;
  id?: string;
  className?: string;
  attributes: Record<string, string>;
  children: DOMNode[];
  textContent?: string;
}

/** 요소 경계 */
export interface ElementBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** 섹션 정보 */
export interface SectionInfo {
  index: number;
  tagName: string;
  selector: string;
  bounds: ElementBounds;
  files: {
    screenshot: string;
    html: string;
  };
}

/** 계산된 스타일 */
export interface ComputedStyles {
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

/** 요소별 스타일 정보 */
export interface ElementStyle {
  selector: string;
  tagName: string;
  styles: {
    color: string;
    backgroundColor: string;
    fontFamily: string;
    fontSize: string;
    fontWeight: string;
    lineHeight: string;
    padding: string;
    margin: string;
    display: string;
    position: string;
    width: string;
    height: string;
    boxShadow: string;
    borderRadius: string;
    borderColor: string;
  };
}

/** 스크래핑 결과 */
export interface ScrapeResult {
  url: string;
  timestamp: string;
  outputDir: string;
  files: {
    screenshot: string;
    html: string;
    styles: string;
    domTree: string;
    sections: string;
  };
  sectionsCount: number;
  success: boolean;
  error?: string;
}

/** 스크래핑 진행 상태 */
export type ScrapePhase =
  | 'init'
  | 'launching-browser'
  | 'navigating'
  | 'waiting'
  | 'capturing-screenshot'
  | 'extracting-html'
  | 'extracting-styles'
  | 'extracting-dom'
  | 'parsing-sections'
  | 'capturing-sections'
  | 'saving'
  | 'done'
  | 'error';

/** 진행 콜백 */
export type ProgressCallback = (phase: ScrapePhase, message: string) => void;
