import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  icon,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || props.name;

  return (
    <div className="w-full space-y-1.5 text-left">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-semibold uppercase tracking-wider text-stone-600 font-sans"
        >
          {label}
        </label>
      )}
      <div className="relative rounded-xl shadow-sm">
        {icon && (
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-stone-400">
            {icon}
          </div>
        )}
        <input
          id={inputId}
          className={`block w-full min-h-[46px] rounded-xl border-stone-200 bg-white/95 px-4 text-stone-900 placeholder:text-stone-400 focus:border-amber-600 focus:ring-2 focus:ring-amber-500/20 focus:outline-none transition-all sm:text-sm ${
            icon ? 'pl-10' : ''
          } ${error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/20' : 'border'} ${className}`}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-rose-600 pl-1 font-medium">{error}</p>}
    </div>
  );
};
