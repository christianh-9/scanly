import {type ClassValue, clsx} from "clsx";
import {twMerge} from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export const generateUUID = () => crypto.randomUUID();


export type ScoreTone = 'pass' | 'warn' | 'fail';

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

export const verdict = (score: number): string =>
  score >= 85 ? 'Ready to send.'
  : score >= 70 ? 'Solid. Fix the flagged items first.'
  : score >= 50 ? 'Needs work before you apply.'
  : 'Not ready to send.';
