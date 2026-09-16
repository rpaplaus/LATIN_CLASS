import React from 'react';

interface ProgressBarProps {
  progress?: number; // 0 to 100
  value?: number;    // 0 to 100 alias
  label?: string;
  showPercentage?: boolean;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  value,
  label,
  showPercentage = true,
  className = '',
}) => {
  const currentVal = value !== undefined ? value : progress !== undefined ? progress : 0;
  const clamped = Math.min(100, Math.max(0, currentVal));

  return (
    <div className={`w-full space-y-1.5 ${className}`}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center text-xs text-stone-600 font-medium">
          {label && <span>{label}</span>}
          {showPercentage && <span>{Math.round(clamped)}%</span>}
        </div>
      )}
      <div className="h-2.5 w-full bg-stone-200/80 rounded-full overflow-hidden p-0.5">
        <div
          className="h-full bg-gradient-to-r from-amber-600 to-amber-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
};
