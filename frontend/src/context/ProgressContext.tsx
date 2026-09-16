import React, { createContext, useContext, useEffect, useState } from 'react';
import { CourseModule, UserProgress } from '../types/progress';
import { LessonContent } from '../types/lesson';
import { lessonApi } from '../api/lessonApi';
import { useAuth } from './AuthContext';

interface ProgressContextType {
  progress: UserProgress | null;
  modules: CourseModule[];
  activeLesson: LessonContent | null;
  isLoading: boolean;
  isGeneratingLesson: boolean;
  isSenateModalOpen: boolean;
  setIsSenateModalOpen: (open: boolean) => void;
  refreshProgress: () => Promise<void>;
  startNextLesson: () => Promise<LessonContent>;
  completeLesson: (score: number) => Promise<void>;
  clearActiveLesson: () => void;
}

const ProgressContext = createContext<ProgressContextType | undefined>(undefined);

export const ProgressProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { isAuthenticated } = useAuth();
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [modules, setModules] = useState<CourseModule[]>([]);
  const [activeLesson, setActiveLesson] = useState<LessonContent | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGeneratingLesson, setIsGeneratingLesson] = useState<boolean>(false);
  const [isSenateModalOpen, setIsSenateModalOpen] = useState<boolean>(false);

  const refreshProgress = async () => {
    if (!isAuthenticated) return;
    setIsLoading(true);
    try {
      const [progData, modsData] = await Promise.all([
        lessonApi.getProgress(),
        lessonApi.getModules(),
      ]);
      setProgress(progData);
      setModules(modsData);
    } catch (err) {
      console.error('Erro ao carregar progresso e módulos:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      refreshProgress();
    } else {
      setProgress(null);
      setModules([]);
      setActiveLesson(null);
      setIsSenateModalOpen(false);
    }
  }, [isAuthenticated]);

  const startNextLesson = async (): Promise<LessonContent> => {
    setIsGeneratingLesson(true);
    try {
      const lesson = await lessonApi.generateNextLesson();
      setActiveLesson(lesson);
      return lesson;
    } catch (err) {
      console.error('Erro ao gerar aula pelo Magister Latium:', err);
      throw err;
    } finally {
      setIsGeneratingLesson(false);
    }
  };

  const completeLesson = async (score: number = 100) => {
    if (!activeLesson) return;
    setIsLoading(true);
    try {
      const updatedProgress = await lessonApi.completeLesson(
        activeLesson.lesson_id,
        score
      );
      setProgress(updatedProgress);
      // Reload modules to update completion checkmarks
      const updatedModules = await lessonApi.getModules();
      setModules(updatedModules);
      setActiveLesson(null);
    } catch (err) {
      console.error('Erro ao registrar conclusão da lição:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clearActiveLesson = () => setActiveLesson(null);

  return (
    <ProgressContext.Provider
      value={{
        progress,
        modules,
        activeLesson,
        isLoading,
        isGeneratingLesson,
        isSenateModalOpen,
        setIsSenateModalOpen,
        refreshProgress,
        startNextLesson,
        completeLesson,
        clearActiveLesson,
      }}
    >
      {children}
    </ProgressContext.Provider>
  );
};

export const useProgress = () => {
  const context = useContext(ProgressContext);
  if (!context) {
    throw new Error('useProgress deve ser utilizado dentro de um ProgressProvider');
  }
  return context;
};
