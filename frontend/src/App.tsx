import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProgressProvider, useProgress } from './context/ProgressContext';
import { AppShell } from './components/layout/AppShell';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ClassroomPage } from './pages/ClassroomPage';
import { ProfilePage } from './pages/ProfilePage';

type MainTab = 'dashboard' | 'syllabus' | 'profile';

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
    return <LoginPage />;
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
        <ClassroomPage
          onBackToDashboard={() => {
            setIsClassroomOpen(false);
            clearActiveLesson();
          }}
        />
      </AppShell>
    );
  }

  // Authenticated Student Shell
  return (
    <AppShell currentTab={currentTab} onSelectTab={setCurrentTab}>
      {currentTab === 'dashboard' && (
        <DashboardPage onOpenClassroom={() => setIsClassroomOpen(true)} />
      )}
      {currentTab === 'syllabus' && (
        <DashboardPage onOpenClassroom={() => setIsClassroomOpen(true)} />
      )}
      {currentTab === 'profile' && <ProfilePage />}
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
