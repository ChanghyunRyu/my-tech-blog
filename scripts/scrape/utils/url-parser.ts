/**
 * URL 파싱 유틸리티
 */

/**
 * URL에서 도메인 추출
 * @example extractDomain('https://www.example.com/path') => 'example-com'
 */
export function extractDomain(url: string): string {
  try {
    const parsed = new URL(url);
    // www. 제거 후 특수문자를 하이픈으로 변환
    return parsed.hostname
      .replace(/^www\./, '')
      .replace(/[^a-zA-Z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  } catch {
    throw new Error(`Invalid URL: ${url}`);
  }
}

/**
 * 오늘 날짜 문자열 반환
 * @example getDateString() => '2026-01-23'
 */
export function getDateString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * URL 유효성 검사
 */
export function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

/**
 * URL 정규화 (https 강제, 후행 슬래시 제거)
 */
export function normalizeUrl(url: string): string {
  try {
    const parsed = new URL(url);
    // http를 https로 변환
    if (parsed.protocol === 'http:') {
      parsed.protocol = 'https:';
    }
    // 후행 슬래시 제거 (루트 경로 제외)
    let normalized = parsed.toString();
    if (normalized.endsWith('/') && parsed.pathname !== '/') {
      normalized = normalized.slice(0, -1);
    }
    return normalized;
  } catch {
    throw new Error(`Invalid URL: ${url}`);
  }
}

/**
 * 출력 디렉토리 이름 생성
 * @example generateOutputDirName('https://example.com') => 'example-com-2026-01-23'
 */
export function generateOutputDirName(url: string): string {
  const domain = extractDomain(url);
  const date = getDateString();
  return `${domain}-${date}`;
}
