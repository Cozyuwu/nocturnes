import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import { CAST, FIRST, find, type Muse } from './cast.js'
import { DUSK, LAMP, lookFor, problems, sceneOwner } from './look.js'
import { SCENES } from './scenes/index.js'

/** The slash command that changes who keeps the session company. */
const COMMAND = 'muse'

/** The key her name is kept under between sessions. */
const KEPT = 'who'

/** Who keeps this session company: her `id`. Drawings read it, so a change redraws them. */
const who = atom({ plugin: 'nocturnes', key: 'who' } as const, FIRST.id)

function pick(list: readonly string[], seed: string): string {
  let sum = 0

  for (let i = 0; i < seed.length; i += 1) {
    sum += seed.charCodeAt(i)
  }

  return list[sum % list.length] ?? list[0] ?? ''
}

/** The cast as a line of names, for the command's answers. */
function roll(): string {
  return CAST.map(one => one.id).join(', ')
}

/** Who follows `lady` in the cast, round to the first again. */
function after(lady: Muse): Muse {
  return CAST[(CAST.indexOf(lady) + 1) % CAST.length] ?? FIRST
}

export const register: Register = on => {
  // The look is set once; its scene moves by itself, by CSS inside the SVG.
  on('session.start', async ($, e, next) => {
    // Desktop ignores a whole theme when any text falls under 3:1, so say so.
    const unpainted = problems.find(line => line.startsWith("Desktop won't paint"))

    if (unpainted !== undefined) {
      $.ui.toast(unpainted)
    }
    // Whoever was chosen last, in any session; Mademoiselle Claude until someone is.
    const lady = find(await $.store.get(KEPT)) ?? FIRST
    await update($, who, () => lady.id)
    await $.command.register({
      name: COMMAND,
      description: 'Choose who keeps you company behind the chat',
      argumentHint: `[${roll()}]`,
    })
    const set = await $.theme.set(lookFor(lady.id))

    if (!set.isDrawn) {
      // The look still stands, and is drawn once the app attaches.
      $.ui.status(set.reason)
    }

    return next(e)
  })

  // `/muse gpt` seats her by name; bare, it seats whoever is next.
  on('command.run', { command: COMMAND }, async ($, e) => {
    const asked = e.args.trim()
    const now = find(await read($, who)) ?? FIRST
    const lady = asked === '' ? after(now) : find(asked)

    if (lady === undefined) {
      return { text: `No one here answers to "${asked}". The house keeps: ${roll()}.` }
    }
    await $.store.set(KEPT, lady.id)
    await update($, who, () => lady.id)
    await $.theme.set(lookFor(lady.id))

    return { text: `${lady.title} takes the seat: ${lady.scene}.` }
  })

  // The scene behind the chat: her traced painting, drawn by the desktop and mobile apps.
  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    const lady = find(sceneOwner(e.props.scene))
    const scene = lady === undefined ? undefined : SCENES[lady.id]

    if ((e.surface !== 'desktop' && e.surface !== 'mobile') || lady === undefined || scene === undefined) {
      return next(e)
    }

    const { Svg } = $.ui.resolve(e)

    return <Svg source={scene} alt={`${lady.title}: ${lady.scene}`} />
  })

  // The person's own prompt: a card under a small lamp-colored heading.
  on('ui.render', { component: 'UserMessage' }, async ($, e, next) => {
    const isOwn = e.props.task === undefined && e.props.from === undefined && e.props.origin.kind !== 'task-notification'

    if (e.surface !== 'desktop' || !isOwn) {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="column" borderStyle="round" borderColor={DUSK} paddingX={1} gap="xs">
        <Text size="caption" mono color={LAMP}>
          ✦ VISITOR
        </Text>
        {await next(e)}
      </Box>
    )
  })

  // Each reply opens under her name, in the color of her hair. The engine's own row takes
  // no size from a Box around it, so the reply keeps the column's width.
  on('ui.render', { component: 'AssistantMessage' }, async ($, e, next) => {
    if (e.surface !== 'desktop' || !e.props.isFirstOfReply || e.props.isSummary === true) {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)
    const lady = find(await read($, who)) ?? FIRST

    return (
      <Box flexDirection="column" gap="xs">
        <Text size="caption" mono color={lady.hair}>
          ☾ {lady.title.toUpperCase()}
        </Text>
        {await next(e)}
      </Box>
    )
  })

  // A small toggle at the right of the prompt's footer, beside the engine's own mode labels:
  // it names who is seated, and a click seats whoever is next.
  on('ui.render', { component: 'SessionMode' }, async ($, e, next) => {
    if (e.surface !== 'desktop') {
      return next(e)
    }

    const { Box, Button } = $.ui.resolve(e)
    const lady = find(await read($, who)) ?? FIRST

    return (
      <Box flexDirection="row" gap="sm">
        {await next(e)}
        <Button
          key="next-muse"
          plain
          dimColor
          onPress={() => {
            // Read afresh: the drawing's own `lady` may be a press behind.
            void (async () => {
              const coming = after(find(await read($, who)) ?? FIRST)
              await $.store.set(KEPT, coming.id)
              await update($, who, () => coming.id)
              await $.theme.set(lookFor(coming.id))
            })()
          }}
        >
          ☾ {lady.name}
        </Button>
      </Box>
    )
  })

  // The working line: her scene's words where the engine has only "Working".
  on('ui.render', { component: 'Spinner' }, async ($, e, next) => {
    if (e.props.message !== null || e.props.word !== 'Working') {
      return next(e)
    }

    const lady = find(await read($, who)) ?? FIRST

    return next({ ...e, props: { ...e.props, word: pick(lady.words, e.requestId + e.props.mode) } })
  })
}
