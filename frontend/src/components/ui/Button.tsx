import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'gold' | 'outline' | 'ghost' | 'danger' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] select-none';

  const sizeStyles = {
    sm: 'min-h-[38px] px-3.5 py-1.5 text-xs',
    md: 'min-h-[46px] px-5 py-2.5 text-sm',
    lg: 'min-h-[52px] px-6 py-3 text-base',
  };

  const variantStyles = {
    primary:
      'bg-slate-900 text-amber-50 hover:bg-slate-800 focus:ring-slate-900 shadow-md shadow-slate-900/10',
    gold:
      'bg-amber-600 text-white hover:bg-amber-700 focus:ring-amber-500 shadow-md shadow-amber-600/20 font-semibold',
    outline:
      'border-2 border-stone-300 text-stone-700 hover:bg-stone-100 focus:ring-stone-400 bg-white/80 backdrop-blur-sm',
    secondary:
      'border-2 border-stone-300 text-stone-700 hover:bg-stone-100 focus:ring-stone-400 bg-white/80 backdrop-blur-sm',
    ghost: 'text-stone-600 hover:bg-stone-200/60 focus:ring-stone-400',
    danger:
      'bg-rose-700 text-white hover:bg-rose-800 focus:ring-rose-600 shadow-sm',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${fullWidth ? 'w-full' : ''} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="inline-flex items-center gap-2">
          <svg
            className="animate-spin h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          Carregando...
        </span>
      ) : (
        children
      )}
    </button>
  );
};
