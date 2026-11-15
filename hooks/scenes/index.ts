import { SCENE as claude } from './claude.js'
import { SCENE as deepseek } from './deepseek.js'
import { SCENE as gpt } from './gpt.js'
import { SCENE as gemini } from './gemini.js'
import { SCENE as glm } from './glm.js'
import { SCENE as grok } from './grok.js'
import { SCENE as qwen } from './qwen.js'
import { SCENE as kimi } from './kimi.js'
import { SCENE as minimax } from './minimax.js'

/** Each muse's scene, by her id in the cast. */
export const SCENES: Readonly<Record<string, string>> = { claude, deepseek, gpt, gemini, glm, grok, qwen, kimi, minimax }
