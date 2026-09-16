import React, { Suspense, useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProgressProvider, useProgress } from './context/ProgressContext';
import { AppShell } from './components/layout/AppShell';

// Code-splitting via React.lazy for optimized bundle size
const LoginPage = React.lazy(() =>
  import('./pages/LoginPage').then((m) => ({ default: m.LoginPage }))
);
const DashboardPage = React.lazy(() =>
  import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage }))
);
const ClassroomPage = React.lazy(() =>
  import('./pages/ClassroomPage').then((m) => ({ default: m.ClassroomPage }))
);
const ProfilePage = React.lazy(() =>
  import('./pages/ProfilePage').then((m) => ({ default: m.ProfilePage }))
);

type MainTab = 'dashboard' | 'syllabus' | 'profile';

const PageFallback: React.FC = () => (
  <div className="flex-1 flex flex-col items-center justify-center p-12 min-h-[300px]">
    <div className="w-10 h-10 rounded-xl bg-amber-100/70 border border-amber-300 flex items-center justify-center text-xl shadow-sm animate-pulse">
      🏛️
    </div>
    <span className="text-xs text-stone-500 font-serif mt-3 tracking-wide">
      Carregando pergaminhos do Senado...
    </span>
  </div>
);

const MainApp: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { activeLesson, clearActiveLesson } = useProgress();
  const [currentTab, setCurrentTab] = useState<MainTab>('dashboard');
  const [isClassroomOpen, setIsClassroomOpen] = useState<boolean>(false);

  // Splash / Loading Screen during session restoration
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#fdfbf7] flex flex-col items-center justify-center space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-amber-100/80 border border-amber-300 flex items-center justify-center text-3xl shadow-md animate-bounce">
          🏛️
        </div>
        <div className="text-center">
          <h2 className="font-serif font-bold text-xl text-slate-800 tracking-wider">
            LATIUM AI
          </h2>
          <p className="text-xs text-stone-500 font-sans mt-1">
            Restaurando sessão e conectando com o Magister...
          </p>
        </div>
      </div>
    );
  }

  // Unauthenticated -> Login & Register Screen
  if (!isAuthenticated) {
    return (
      <Suspense fallback={<PageFallback />}>
        <LoginPage />
      </Suspense>
    );
  }

  // Active Classroom Screen (when lesson is active or opened)
  if (isClassroomOpen || activeLesson) {
    return (
      <AppShell
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setIsClassroomOpen(false);
          setCurrentTab(tab);
        }}
        hideNav={true}
      >
        <Suspense fallback={<PageFallback />}>
          <ClassroomPage
            onBackToDashboard={() => {
              setIsClassroomOpen(false);
              clearActiveLesson();
            }}
          />
        </Suspense>
      </AppShell>
    );
  }

  // Authenticated Student Shell
  return (
    <AppShell currentTab={currentTab} onSelectTab={setCurrentTab}>
      <Suspense fallback={<PageFallback />}>
        {currentTab === 'dashboard' && (
          <DashboardPage onOpenClassroom={() => setIsClassroomOpen(true)} />
        )}
        {currentTab === 'syllabus' && (
          <DashboardPage onOpenClassroom={() => setIsClassroomOpen(true)} />
        )}
        {currentTab === 'profile' && <ProfilePage />}
      </Suspense>
    </AppShell>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <ProgressProvider>
        <MainApp />
      </ProgressProvider>
    </AuthProvider>
  );
};

export default App;
