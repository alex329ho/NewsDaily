import { BASE_URL } from './config';

export type Headline = {
  title: string;
  url: string;
  source_domain: string;
  seendate: string;
};

export type SummaryResponse = {
  topics: string[];
  hours: number;
  region?: string | null;
  language?: string | null;
  fetched_count: number;
  summary: string;
  headlines: Headline[];
};

function buildQuery(params: Record<string, string | number | undefined | null>): string {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');
  return query;
}

export async function fetchSummary(options: {
  topics: string[];
  hours: number;
  region?: string;
  language?: string;
}): Promise<SummaryResponse> {
  const query = buildQuery({
    topics: options.topics.join(','),
    hours: options.hours,
    region: options.region,
    language: options.language,
  });

  const response = await fetch(`${BASE_URL}/summary?${query}`);
  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }

  const data = await response.json();
  const topics = Array.isArray(data.topics)
    ? data.topics.map((value: unknown) => String(value))
    : String(data.topics ?? '').split(',').map((value) => value.trim()).filter(Boolean);

  return {
    topics,
    hours: Number(data.hours ?? 0),
    region: data.region ?? null,
    language: data.language ?? null,
    fetched_count: Number(data.fetched_count ?? 0),
    summary: String(data.summary ?? 'No news available.'),
    headlines: Array.isArray(data.headlines) ? data.headlines : [],
  };
}
