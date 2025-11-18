interface GaonLogoProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'full' | 'symbol' | 'text';
  className?: string;
}

export default function GaonLogo({ 
  size = 'md', 
  variant = 'full',
  className = '' 
}: GaonLogoProps) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12', 
    lg: 'w-16 h-16'
  };

  if (variant === 'symbol') {
    return (
      <svg 
        viewBox="0 0 120 120" 
        className={`${sizeClasses[size]} ${className}`}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="warmGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{stopColor:'#E5664C', stopOpacity:1}} />
            <stop offset="100%" style={{stopColor:'#D95A42', stopOpacity:1}} />
          </linearGradient>
        </defs>
        <circle cx="60" cy="60" r="52" fill="none" stroke="url(#warmGradient)" strokeWidth="2" opacity="0.2"/>
        <path d="M 38 68 Q 60 42 82 68" fill="none" stroke="url(#warmGradient)" strokeWidth="4" strokeLinecap="round"/>
        <path d="M 34 52 Q 60 32 86 52" fill="none" stroke="url(#warmGradient)" strokeWidth="4" strokeLinecap="round" opacity="0.5"/>
        <circle cx="60" cy="60" r="7" fill="url(#warmGradient)"/>
      </svg>
    );
  }

  if (variant === 'text') {
    return (
      <div className={`flex items-center ${className}`}>
        <span className="text-2xl font-semibold text-[#D95A42] tracking-wider">GAON</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg 
        viewBox="0 0 120 120" 
        className={sizeClasses[size]}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="warmGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{stopColor:'#E5664C', stopOpacity:1}} />
            <stop offset="100%" style={{stopColor:'#D95A42', stopOpacity:1}} />
          </linearGradient>
        </defs>
        <circle cx="60" cy="60" r="52" fill="none" stroke="url(#warmGradient)" strokeWidth="2" opacity="0.2"/>
        <path d="M 38 68 Q 60 42 82 68" fill="none" stroke="url(#warmGradient)" strokeWidth="4" strokeLinecap="round"/>
        <path d="M 34 52 Q 60 32 86 52" fill="none" stroke="url(#warmGradient)" strokeWidth="4" strokeLinecap="round" opacity="0.5"/>
        <circle cx="60" cy="60" r="7" fill="url(#warmGradient)"/>
      </svg>
      <span className="text-xl font-semibold text-[#D95A42] tracking-wider">GAON</span>
    </div>
  );
}
