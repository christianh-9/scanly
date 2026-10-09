import {type ClassValue, clsx} from "clsx";
import {twMerge} from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  // Determine the appropriate unit by calculating the log
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  // Format with 2 decimal places and round
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export const generateUUID = () => crypto.randomUUID();


export type ScoreTone = 'pass' | 'warn' | 'fail';

// One source of truth for score bands; pass/warn/fail colors mean nothing else in the UI.
export const scoreTone = (score: number): ScoreTone =>
  score >= 70 ? 'pass' : score >= 50 ? 'warn' : 'fail';

export const toneText: Record<ScoreTone, string> = {
  pass: 'text-pass',
  warn: 'text-warn',
  fail: 'text-fail',
};

export const toneBg: Record<ScoreTone, string> = {
  pass: 'bg-pass',
  warn: 'bg-warn',
  fail: 'bg-fail',
};

// Blunt by design: the verdict says what to do next.
export const verdict = (score: number): string =>
  score >= 85 ? 'Ready to send.'
  : score >= 70 ? 'Solid. Fix the flagged items first.'
  : score >= 50 ? 'Needs work before you apply.'
  : 'Not ready to send.';
