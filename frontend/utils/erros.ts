export function getErrorMessage(e: unknown, fallback = '문제가 발생했습니다. 잠시 후 다시 시도해주세요.') {
  if (e instanceof Error) return e.message;
  if (typeof e === 'object' && e && 'message' in e) {
    return String((e as {message?: string}).message);
  }
  return fallback;
}