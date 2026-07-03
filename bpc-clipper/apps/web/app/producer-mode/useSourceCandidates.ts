'use client';

import { useCallback, useState } from 'react';
import { Candidate, listSourceCandidates } from '../../lib/api';

export function useSourceCandidates(projectId?: string) {
  const [isLoadingSourceCandidates, setIsLoadingSourceCandidates] = useState(false);
  const [sourceCandidateError, setSourceCandidateError] = useState('');

  const loadSourceCandidates = useCallback(async (sourceId: string): Promise<Candidate[]> => {
    if (!projectId || !sourceId) return [];
    setIsLoadingSourceCandidates(true);
    setSourceCandidateError('');
    try {
      const result = await listSourceCandidates(projectId, sourceId);
      return result.candidates;
    } catch (caught) {
      setSourceCandidateError(caught instanceof Error ? caught.message : 'Unable to load source candidates.');
      throw caught;
    } finally {
      setIsLoadingSourceCandidates(false);
    }
  }, [projectId]);

  return { isLoadingSourceCandidates, sourceCandidateError, loadSourceCandidates };
}
