import React from 'react';
import { Cpu } from 'lucide-react';
import { Badge } from '../ui/Badge';

/**
 * Strict presentation typing for the Exercise Header.
 * Enforces strict separation of state: target_answer is omitted from header display properties
 * to guarantee that the expected answer cannot be injected or rendered in the title before completion.
 */
export interface SafeExerciseHeaderProps {
  instruction: string;
  question_prompt: string; // Exclusively the question prompt or context sentence (NEVER the expected answer)
  isAiEvaluated?: boolean;
}

/**
 * Sanitizes question prompts to protect against accidental answer leaks:
 * 1. If the prompt is literally identical to the target answer (e.g. "SUNT"), masks it with a neutral prompt.
 * 2. If it is a fill_blank sentence where the answer was inadvertently left unmasked and lacks '____', masks the answer with '____'.
 * 3. Never renders target_answer before the exercise is checked.
 */
export function getSafeQuestionPrompt(
  prompt: string,
  targetAnswer?: string,
  isAnswerChecked: boolean = false
): string {
  if (!prompt) return '';
  if (isAnswerChecked) return prompt;

  const trimmedPrompt = prompt.trim();
  const trimmedTarget = (targetAnswer || '').trim();

  // If prompt is just the answer itself (leak):
  if (trimmedTarget && trimmedPrompt.toLowerCase() === trimmedTarget.toLowerCase()) {
    return 'Complete a lacuna na oração com a forma clássica correta:';
  }

  // If prompt contains target answer without any blank marker (unmasked leak):
  if (trimmedTarget && !trimmedPrompt.includes('____') && !trimmedPrompt.includes('__')) {
    const escaped = trimmedTarget.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const wordRegex = new RegExp(`\\b${escaped}\\b`, 'gi');
    if (wordRegex.test(trimmedPrompt)) {
      return trimmedPrompt.replace(wordRegex, '____');
    }
  }

  return prompt;
}

/**
 * Sanitizes exercise instructions to ensure the target answer is not revealed in hints or labels.
 */
export function getSafeInstruction(
  instruction?: string,
  targetAnswer?: string,
  isAnswerChecked: boolean = false
): string {
  if (!instruction) return 'Responda a pergunta';
  if (isAnswerChecked) return instruction;

  const trimmedTarget = (targetAnswer || '').trim();
  if (trimmedTarget) {
    const escaped = trimmedTarget.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const wordRegex = new RegExp(`\\b${escaped}\\b`, 'gi');
    if (wordRegex.test(instruction)) {
      return instruction.replace(wordRegex, '[...]');
    }
  }
  return instruction;
}

/**
 * ExerciseHeader Component
 * Renders the question instruction badge and question prompt safely without leaking target answers.
 */
export const ExerciseHeader: React.FC<SafeExerciseHeaderProps> = ({
  instruction,
  question_prompt,
  isAiEvaluated = false,
}) => {
  return (
    <div>
      <div className="flex items-center gap-2">
        <Badge variant="neutral" size="sm">
          {instruction || 'Responda a pergunta'}
        </Badge>
        {isAiEvaluated && (
          <span className="inline-flex items-center gap-1 text-[11px] text-amber-800 font-semibold bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
            <Cpu className="w-3 h-3 text-amber-600" />
            Correção com IA (Censor Latium)
          </span>
        )}
      </div>
      <h3 className="font-serif text-lg sm:text-xl font-bold text-slate-900 mt-2">
        {question_prompt}
      </h3>
    </div>
  );
};
