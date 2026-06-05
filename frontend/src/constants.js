// Display metadata for the three adaptive subgroups and the writing group.

export const SUBGROUPS = [
  {
    key: 'se_tc',
    group: 'Verbal',
    label: 'Sentence Equivalence & Text Completion',
    short: 'SE / TC',
  },
  {
    key: 'reading_reasoning',
    group: 'Verbal',
    label: 'Reading Comprehension & Critical Reasoning',
    short: 'Reading / Reasoning',
  },
  {
    key: 'quant',
    group: 'Math',
    label: 'Quantitative Reasoning',
    short: 'Quant',
  },
  {
    key: 'vocabulary',
    group: 'Vocabulary',
    label: 'GRE Word Test',
    short: 'Words',
  },
]

export const SUBGROUP_BY_KEY = Object.fromEntries(SUBGROUPS.map((s) => [s.key, s]))

// Default level ceiling; individual sections report their own max_level from the
// API (verbal/math climb to 5, the vocabulary Word Test climbs to 10).
export const DEFAULT_MAX_LEVEL = 5
