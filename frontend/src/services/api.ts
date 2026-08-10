import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 120000,
});

export async function analyzeDeck(
  decklist: string,
  commander: string,
  useAI: boolean,
  budget?: string
) {
  const { data } = await api.post('/analyze', {
    decklist,
    commander,
    use_ai: useAI,
    budget: budget || undefined,
  });
  return data;
}

export async function getMulliganAdvice(
  decklist: string,
  commander: string,
  hand: string[],
  useAI: boolean
) {
  const { data } = await api.post('/mulligan', { decklist, commander, hand, use_ai: useAI });
  return data;
}

export async function healthCheck() {
  const { data } = await api.get('/health');
  return data;
}
