/**
 * 파일 시스템 유틸리티
 */

import { mkdir, writeFile, access } from 'fs/promises';
import { dirname, join } from 'path';

/**
 * 디렉토리 생성 (재귀적)
 */
export async function createDirectory(dirPath: string): Promise<void> {
  await mkdir(dirPath, { recursive: true });
}

/**
 * 출력 디렉토리 구조 생성
 * @returns 생성된 디렉토리 경로
 */
export async function createOutputDirectory(basePath: string, dirName: string): Promise<string> {
  const outputDir = join(basePath, dirName);
  const sectionsDir = join(outputDir, 'sections');

  await createDirectory(outputDir);
  await createDirectory(sectionsDir);

  return outputDir;
}

/**
 * JSON 파일 저장
 */
export async function saveJson(filePath: string, data: unknown): Promise<void> {
  await ensureDirectory(filePath);
  const content = JSON.stringify(data, null, 2);
  await writeFile(filePath, content, 'utf-8');
}

/**
 * 텍스트 파일 저장
 */
export async function saveText(filePath: string, content: string): Promise<void> {
  await ensureDirectory(filePath);
  await writeFile(filePath, content, 'utf-8');
}

/**
 * 바이너리 파일 저장
 */
export async function saveBinary(filePath: string, data: Buffer): Promise<void> {
  await ensureDirectory(filePath);
  await writeFile(filePath, data);
}

/**
 * 파일 경로의 디렉토리가 존재하는지 확인하고 없으면 생성
 */
async function ensureDirectory(filePath: string): Promise<void> {
  const dir = dirname(filePath);
  await createDirectory(dir);
}

/**
 * 파일/디렉토리 존재 여부 확인
 */
export async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

/**
 * 경로 조합 (re-export for convenience)
 */
export { join } from 'path';
