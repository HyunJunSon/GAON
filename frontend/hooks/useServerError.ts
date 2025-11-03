'use client';

import { getErrorMessage } from "@/utils/erros";
import { useCallback, useState } from "react";

export function useServerError(defaultMsg?: string) {
  const [serverError, setServerError] = useState<string | null>(null);
  const handleError = useCallback((e: unknown) => {
    setServerError(getErrorMessage(e, defaultMsg));
  }, [defaultMsg]);

  const clearError = useCallback(() => setServerError(null), [])
  
  return { serverError, setServerError, handleError, clearError};
}