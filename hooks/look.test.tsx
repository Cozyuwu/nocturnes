import { expect, mock, test } from 'claude-code/testing'

import { CAST } from './cast.js'
import { GLASS, lookFor, problems, sceneName } from './look.js'
import { SCENES } from './scenes/index.js'

const RUN = { origin: { kind: 'composer' }, presentation: { isFullscreen: true, columns: 120 } } as const

test('desktop paints the colors', async () => {
  // Any line that starts this way makes Desktop ignore the whole theme.
  expect(problems.filter(line => line.startsWith("Desktop won't paint"))).toEqual([])
})

test('a first session opens on Mademoiselle Claude, her look sent whole, once', async ($, on) => {
  const sent: unknown[] = []
  mock.store(on)
  on('command.register', () => ({ value: { command: 'muse' } }))
  on('theme.set', (_, e) => {
    sent.push(e)

    return { value: { isDrawn: true, requestId: 'backdrop' } }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  expect(sent).toEqual([lookFor('claude')])
})

test('every muse has a scene small enough for one drawing, built only of what the window allows', async () => {
  expect(CAST.map(one => one.id)).toEqual(['claude', 'deepseek', 'gpt', 'gemini', 'glm', 'grok', 'qwen', 'kimi', 'minimax'])

  for (const lady of CAST) {
    const scene = SCENES[lady.id] ?? ''

    expect(lookFor(lady.id).backdrop).toEqual({ scene: sceneName(lady.id), glass: GLASS })
    expect(scene.length).toBeLessThan(131072)
    expect(scene.startsWith('<svg')).toBe(true)
    // The window refuses a scene that holds a picture, a link out, or a script.
    expect(/<image|<script|<foreignObject|data:|https?:\/\/(?!www\.w3\.org)/.test(scene)).toBe(false)
  }
})

test("each one's scene is drawn for the desktop backdrop", async $ => {
  for (const lady of CAST) {
    const ui = await $.ui.mount({
      plugin: 'nocturnes',
      component: 'Backdrop',
      requestId: 'backdrop',
      surface: 'desktop',
      props: { scene: sceneName(lady.id), plugin: 'nocturnes', glass: GLASS },
    })

    expect((await ui.find({ type: 'Svg' })) !== undefined).toBe(true)
    await ui.unmount()
  }
})

test('a prompt of the person draws as a card around the engine row', async ($, on) => {
  // The hook here stands for the engine's own row.
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine row</Text>
  })

  const ui = await $.ui.mount({
    plugin: 'nocturnes',
    component: 'UserMessage',
    requestId: 'm1',
    surface: 'desktop',
    props: { text: 'hello', origin: { kind: 'composer' }, isExpanded: true },
  })

  expect((await ui.find({ type: 'Text', text: /VISITOR/ }))?.text).toContain('VISITOR')
  expect((await ui.find({ type: 'Text', text: /engine row/ }))?.text).toBe('engine row')
  await ui.unmount()
})

test('a reply opens under her name in the color of her hair, and a later block is left alone', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine reply</Text>
  })

  const first = await $.ui.mount({
    plugin: 'nocturnes',
    component: 'AssistantMessage',
    requestId: 'a1',
    surface: 'desktop',
    props: { text: 'hi', isFirstOfReply: true },
  })
  const heading = await first.find({ type: 'Text', text: /MADEMOISELLE CLAUDE/ })
  expect(heading?.text).toContain('MADEMOISELLE CLAUDE')
  expect(heading?.props.color).toBe('#f29a4e')
  await first.unmount()

  const later = await $.ui.mount({
    plugin: 'nocturnes',
    component: 'AssistantMessage',
    requestId: 'a2',
    surface: 'desktop',
    props: { text: 'hi', isFirstOfReply: false },
  })
  expect(await later.find({ type: 'Text', text: /MADEMOISELLE/ })).toBeUndefined()
  expect((await later.find({ type: 'Text', text: /engine reply/ }))?.text).toBe('engine reply')
  await later.unmount()
})

test('the one chosen in an earlier session is seated at the start of the next', async ($, on) => {
  const sent: unknown[] = []
  mock.store(on, { who: 'kimi' })
  on('command.register', () => ({ value: { command: 'muse' } }))
  on('theme.set', (_, e) => {
    sent.push(e)

    return { value: { isDrawn: true, requestId: 'backdrop' } }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine reply</Text>
  })

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  expect(sent).toEqual([lookFor('kimi')])

  const ui = await $.ui.mount({
    plugin: 'nocturnes',
    component: 'AssistantMessage',
    requestId: 'a1',
    surface: 'desktop',
    props: { text: 'hi', isFirstOfReply: true },
  })
  expect((await ui.find({ type: 'Text', text: /☾/ }))?.text).toBe('☾ KIMI')
  await ui.unmount()
})

test('/muse seats one by name, the next one when bare, and names the house for a stranger', async ($, on) => {
  const sent: unknown[] = []
  mock.store(on)
  on('command.register', () => ({ value: { command: 'muse' } }))
  on('theme.set', (_, e) => {
    sent.push(e)

    return { value: { isDrawn: true, requestId: 'backdrop' } }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  const named = await $.command.run({ command: 'muse', args: ' GPT ', ...RUN })
  expect(named.text).toContain('GPT takes the seat')
  expect(sent.at(-1)).toEqual(lookFor('gpt'))

  const next = await $.command.run({ command: 'muse', args: '', ...RUN })
  expect(next.text).toContain('Gemini takes the seat')
  expect(sent.at(-1)).toEqual(lookFor('gemini'))

  const stranger = await $.command.run({ command: 'muse', args: 'nobody', ...RUN })
  expect(stranger.text).toContain('claude, deepseek, gpt')
  expect(sent.length).toBe(3)

  // The choice is kept: the next session opens on her.
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  expect(sent.at(-1)).toEqual(lookFor('gemini'))
})

test('the small toggle beside the prompt names who is seated, and a click seats the next one', async ($, on) => {
  const sent: unknown[] = []
  mock.store(on)
  on('command.register', () => ({ value: { command: 'muse' } }))
  on('theme.set', (_, e) => {
    sent.push(e)

    return { value: { isDrawn: true, requestId: 'backdrop' } }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine modes</Text>
  })
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  const ui = await $.ui.mount({
    plugin: 'nocturnes',
    component: 'SessionMode',
    requestId: 'modes',
    surface: 'desktop',
    props: { modes: [] },
  })
  expect((await ui.find({ key: 'next-muse' }))?.text).toContain('Claude')
  expect((await ui.find({ type: 'Text', text: /engine modes/ }))?.text).toBe('engine modes')

  await ui.press({ key: 'next-muse' })
  expect(sent.at(-1)).toEqual(lookFor('deepseek'))
  expect((await ui.find({ key: 'next-muse' }))?.text).toContain('DeepSeek')
  await ui.unmount()
})
