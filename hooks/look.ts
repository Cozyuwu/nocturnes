import type { ThemeSetArgs } from 'claude-code'

import { makeColors } from './make-colors.js'

// Night, wherever she is: blue-black surfaces a few steps apart, text the color of
// moonlight, and cool blues for the accents. One mode, since every scene is a night.
export const { theme, problems } = makeColors({
  label: 'Nocturnes',
  only: 'dark',
  roles: {
    accent: '#8fa8dc',
    danger: '#c8616e',
    success: '#6fa58a',
    warning: '#c9a45a',
    pro: '#a590d6',
  },
  dark: {
    gray: {
      anchors: {
        'surface-0': '#0b0e17',
        'surface-1': '#10141f',
        'surface-2': '#151a27',
        'surface-3': '#191f2e',
        'text-primary': '#e3e9f5',
        'text-secondary': '#bcc6da',
        'text-muted': '#97a4be',
      },
    },
  },
})

/** Raw colors for the pieces the mod draws itself. */
export const DUSK = '#5c6b90'
export const LAMP = '#ffe6b0'

/** What the panels over the scene are tinted with: not blurred, so the drawing stays sharp. */
export const GLASS = { blur: 0, tint: '#0b0e17', opacity: 0.38 } as const

const SCENE_PREFIX = 'nocturne-'

/** The name a muse's scene goes by, which the hook that draws it reads back. */
export function sceneName(id: string): string {
  return SCENE_PREFIX + id
}

/** Whose scene a name is, or undefined when the name is no scene of this mod. */
export function sceneOwner(name: string): string | undefined {
  return name.startsWith(SCENE_PREFIX) ? name.slice(SCENE_PREFIX.length) : undefined
}

/**
 * The look with one muse's scene behind it. The desktop window draws no picture file
 * as a background, only shapes, so each painting is traced into an SVG scene (hooks/scenes).
 */
export function lookFor(id: string): ThemeSetArgs {
  return { colors: theme, backdrop: { scene: sceneName(id), glass: GLASS } }
}
