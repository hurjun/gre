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
]

export const SUBGROUP_BY_KEY = Object.fromEntries(SUBGROUPS.map((s) => [s.key, s]))

export const MAX_LEVEL = 5
