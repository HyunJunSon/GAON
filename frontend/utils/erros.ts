export function getErrorMessage(
  e: unknown,
  fallback = "문제가 발생했습니다. 잠시 후 다시 시도해주세요."
) {
  if (e instanceof Error) {
    if (e.message.startsWith("HTTP 409")) {
      return "이미 가입된 이메일입니다.";
    }
    return e.message;
  }
  return fallback;
}
