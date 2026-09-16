import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'gold' | 'green' | 'stone' | 'navy' | 'warning' | 'success' | 'default' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'stone',
  size = 'md',
  className = '',
}) => {
  const styles: Record<string, string> = {
    gold: 'bg-amber-100 text-amber-900 border-amber-300',
    warning: 'bg-amber-100 text-amber-900 border-amber-300',
    green: 'bg-emerald-100 text-emerald-900 border-emerald-300',
    success: 'bg-emerald-100 text-emerald-900 border-emerald-300',
    stone: 'bg-stone-100 text-stone-700 border-stone-300',
    neutral: 'bg-stone-100 text-stone-700 border-stone-300',
    default: 'bg-stone-100 text-stone-700 border-stone-300',
    navy: 'bg-slate-900 text-amber-100 border-slate-700',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-0.5 text-xs',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-semibold tracking-wide border ${styles[variant] || styles.stone} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};
