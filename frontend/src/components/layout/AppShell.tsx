import React from 'react';
import { Header } from './Header';
import { MobileBottomNav } from './MobileBottomNav';

interface AppShellProps {
  children: React.ReactNode;
  currentTab: 'dashboard' | 'syllabus' | 'profile';
  onSelectTab: (tab: 'dashboard' | 'syllabus' | 'profile') => void;
  hideNav?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  currentTab,
  onSelectTab,
  hideNav = false,
}) => {
  return (
    <div className="min-h-screen bg-[#fdfbf7] text-stone-900 flex flex-col font-sans antialiased selection:bg-amber-200 selection:text-amber-900">
      <Header />
      <main className={`flex-1 max-w-4xl w-full mx-auto px-4 py-6 ${hideNav ? 'pb-8' : 'pb-24 sm:pb-10'}`}>
        {children}
      </main>
      {!hideNav && (
        <MobileBottomNav currentTab={currentTab} onSelectTab={onSelectTab} />
      )}
    </div>
  );
};
