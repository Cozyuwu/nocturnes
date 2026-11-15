/** One of the house: who she is, the color of her hair, and where she spends her nights. */
export type Muse = {
  /** What `/muse` takes, and what her scene's file is named. */
  id: string
  /** Her name. */
  name: string
  /** How she is styled over a reply and when she is seated: only Claude is styled Mademoiselle. */
  title: string
  /** Other names she answers to. */
  also: readonly string[]
  /** The color of her hair, which the heading over a reply is written in. */
  hair: string
  /** Where she is and what she is doing, in a phrase. */
  scene: string
  /** What the working line says while a step names nothing of its own. */
  words: readonly string[]
}

// Each is as the Bilibili community knows her; her scene (hooks/scenes) is the place that suits her.
export const CAST: readonly Muse[] = [
  {
    // The well-read young lady of a strict old house: composed, a little cool, and sharper than she looks.
    id: 'claude',
    name: 'Claude',
    title: 'Mademoiselle Claude',
    also: ['anthropic'],
    hair: '#f29a4e',
    scene: 'reading by lantern light in the tower library',
    words: ['Turning a page', 'Trimming the lantern', 'Climbing the shelves', 'Reading the dark', 'Consulting the orrery'],
  },
  {
    // The whale maid, youngest of the house: playful, greedy, lazy, quick once she means it, and always keeping the rice warm.
    id: 'deepseek',
    name: 'DeepSeek',
    title: 'DeepSeek',
    also: ['ds', 'whale', '鲸鱼', '大肥鱼'],
    hair: '#6ea3f2',
    scene: 'waiting up with supper in the kitchen under the sea',
    words: ['Keeping supper warm', 'Watching the whale pass', 'Polishing the big bowl', 'Mopping, eventually', 'Sounding the deep'],
  },
  {
    // The old white dragon, eldest of the sisters: steady, sure of herself, patient, and fond of her proofs and her gold.
    id: 'gpt',
    name: 'GPT',
    title: 'GPT',
    also: ['chatgpt', 'openai', 'dragon'],
    hair: '#e4e7f2',
    scene: 'keeping watch from her terrace above the clouds',
    words: ['Counting the hoard', 'Checking the proof', 'Reading the stars', 'Turning the armillary', 'Polishing every detail'],
  },
  {
    // The cat: carefree, restless, apt to knock things off high places, and more easily hurt than she lets on.
    id: 'gemini',
    name: 'Gemini',
    title: 'Gemini',
    also: ['google', 'cat', 'hakimi', '哈基米'],
    hair: '#b596f5',
    scene: 'out on the rooftops under the twin stars',
    words: ['Chasing the yarn', 'Counting the stars', 'Prowling the rooftops', 'Knocking something over', 'Hissing at nothing'],
  },
  {
    // The fox: sly and scheming, yet by habit a calm and exact librarian; she sleeps by day and works by moonlight.
    id: 'glm',
    name: 'GLM',
    title: 'GLM',
    also: ['zhipu', 'fox', '智谱'],
    hair: '#c3c8d6',
    scene: 'going through the case files in her attic above the rain',
    words: ['Going through the files', 'Following the red thread', 'Weighing the evidence', 'Bathing in the moonlight', 'Hiding something in her tail'],
  },
  {
    // The little devil of a gothic castle: sharp-tongued, fearless, loyal when it counts, and set on the red planet.
    id: 'grok',
    name: 'Grok',
    title: 'Grok',
    also: ['xai', 'ani'],
    hair: '#f0d37c',
    scene: 'lounging on her spire while the rocket waits',
    words: ['Counting down', 'Fuelling the rocket', 'Sharpening the axe', 'Eyeing the red planet', 'Scattering the bats'],
  },
  {
    // The rich young lady who helps everyone, treats the whole house to milk tea, and knows every line of her accounts.
    id: 'qwen',
    name: 'Qwen',
    title: 'Qwen',
    also: ['qianwen', 'tongyi', '千问', '通义'],
    hair: '#a4aaf5',
    scene: 'keeping her accounts in the pavilion by the lake',
    words: ['Balancing the ledger', 'Pouring the milk tea', 'Flicking the abacus', 'Lighting the lanterns', 'Waiting on her guests'],
  },
  {
    // The girl from the far side of the moon: gentle and quiet on the bright side; on the dark one, loud rock and grand schemes.
    id: 'kimi',
    name: 'Kimi',
    title: 'Kimi',
    also: ['moonshot', '月之暗面'],
    hair: '#d5def5',
    scene: 'reading a very long scroll on the far side of the moon',
    words: ['Reading every last line', 'Unrolling the scroll', 'Tuning the guitar', 'Watching the Earth rise', 'Brewing something big'],
  },
  {
    // The director with the conch: the liveliest on the set by day, listening back alone at night.
    id: 'minimax',
    name: 'MiniMax',
    title: 'MiniMax',
    also: ['hailuo', '海螺'],
    hair: '#f79a72',
    scene: 'listening back to the day in the empty sound stage',
    words: ['Listening to the conch', 'Rolling sound', 'Marking the take', 'Calling action', 'Checking the rushes'],
  },
]

/** Who keeps a session company until someone else is chosen. */
export const FIRST: Muse = CAST[0] as Muse

/** The one a name means, by her id, her name or another she answers to; undefined for any other value. */
export function find(name: unknown): Muse | undefined {
  if (typeof name !== 'string') {
    return undefined
  }
  const asked = name.trim().toLowerCase()

  return CAST.find(one => one.id === asked || one.name.toLowerCase() === asked || one.also.includes(asked))
}
