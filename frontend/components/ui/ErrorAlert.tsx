'use client';

type Props = { message?: string | null; className?: string };

export default function ErrorAlert({ message, className = '' }: Props) {
  if (!message) return null;
  return (
    <div
      role="alert"
      aria-live="polite"
      className={`mb-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 ${className}`}
    >
      {message}
    </div>
  )
}