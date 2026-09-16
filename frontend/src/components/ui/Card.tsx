import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'parchment' | 'gold';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default: 'bg-white border-stone-200/80 shadow-sm',
    parchment: 'bg-[#faf6ee] border-stone-300/80 shadow-md shadow-stone-900/5',
    gold: 'bg-gradient-to-br from-amber-50 to-orange-50/40 border-amber-200/80 shadow-md shadow-amber-500/10',
  };

  return (
    <div
      className={`rounded-2xl border p-5 sm:p-6 transition-all ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
