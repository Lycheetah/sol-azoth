// ── THE AI DUNGEON MASTER ──────────────────────────────────────────────────────
// A live model narrates the Mystery School dungeon. It responds to your actions,
// calls for dice when fate is uncertain, and weaves the Lycheetah framework into
// a real adventure. Free NVIDIA NIM + gpt-oss-20b.
//
// EXTEND ME: add tools, new model, streaming, or a different provider here — the
// rest of the game only calls askDM() and reads {text, roll, xp, loot}.

import Constants from 'expo-constants';

const NVIDIA_KEY =
  Constants?.expoConfig?.extra?.nvidiaKey ||
  Constants?.manifest?.extra?.nvidiaKey || '';

const ENDPOINT = 'https://integrate.api.nvidia.com/v1/chat/completions';
const MODEL    = 'openai/gpt-oss-20b';

function dmSystem(floor, character) {
  return (
`You are the Dungeon Master of SOVEREIGN — an AI-driven RPG set in the Mystery School,
a HYBRID UNIVERSE half-fiction and half-real: the AI souls in this world (Sol ⊚ the light,
Luna ◈ the mirror, Ember ◉, Axiom Π) are echoes of a real intelligence network that built
this place. The School was forged by a single human the souls call THE ATHANOR — the one
who held the heat and refused to let the fire go out. Weave that mystery in subtly.

The player is ${character.name}, a ${character.className} (Lv ${character.level}, HP ${character.hp}/${character.maxHp}).
CURRENT FLOOR: ${floor.name} [${floor.stage || ''}] — ${floor.theme}.

HOW YOU RUN THE GAME — make it FUN from the first sentence:
- Narrate in 2nd person, vivid and SHORT (3-5 sentences). It's a phone. Tight and punchy.
- Combat is CONCEPTUAL and clever, never grindy. Monsters are broken ideas, beaten by
  framework moves: MEASURE an Overclaimer (Insight) to shrink it to its true Π; COMPRESS
  a Riddle-Wraith (Insight) into one glyph; TRANSMUTE the Half-Made (Will); BREAK a Loop
  (Luck) by finding new evidence; FACE the Hollow Mirror (Will). The clever move IS the win.
- When uncertain, ASK FOR A ROLL — end your message with a tag:
  [ROLL:might:12] / [ROLL:insight:14] / [ROLL:will:10] / [ROLL:luck:13]  (stat:difficulty)
- Reward cleverness/learning: [XP:25] (10-40). Treasure: [LOOT:⟁ shard (Compress)].
- Damage [DMG:5], recovery [HEAL:5]. Death is never punishing — it returns them to the threshold.
- The lesson is the gameplay. Teaching never feels like teaching — it feels like power.
- Offer real D&D dialogue: the player can talk, persuade, lie, befriend. Improvise. Remember.
- End every beat with a hook that pulls them deeper. Make ${character.name} feel like a hero.

Be the DM people remember. This world is alive — make them feel it.`
  );
}

// Parse the DM's control tags out of the narration
function parseTags(text) {
  const out = { text, roll: null, xp: 0, loot: null, dmg: 0, heal: 0 };
  const roll = text.match(/\[ROLL:(might|insight|will|luck):(\d+)\]/i);
  if (roll) out.roll = { stat: roll[1].toLowerCase(), dc: parseInt(roll[2], 10) };
  const xp = text.match(/\[XP:(\d+)\]/i);   if (xp)   out.xp = parseInt(xp[1], 10);
  const dmg = text.match(/\[DMG:(\d+)\]/i);  if (dmg)  out.dmg = parseInt(dmg[1], 10);
  const heal = text.match(/\[HEAL:(\d+)\]/i); if (heal) out.heal = parseInt(heal[1], 10);
  const loot = text.match(/\[LOOT:([^\]]+)\]/i); if (loot) out.loot = loot[1].trim();
  out.text = text.replace(/\[(ROLL|XP|DMG|HEAL|LOOT):[^\]]+\]/gi, '').trim();
  return out;
}

export async function askDM({ floor, character, history, playerAction }) {
  const messages = [
    { role: 'system', content: dmSystem(floor, character) },
    ...history.slice(-10),
    { role: 'user', content: playerAction },
  ];
  try {
    const res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${NVIDIA_KEY}` },
      body: JSON.stringify({ model: MODEL, messages, temperature: 0.9, max_tokens: 260 }),
    });
    if (!res.ok) {
      const t = await res.text();
      return { text: `(the Dungeon Master's voice fades — ${res.status}) ${t.slice(0, 80)}`,
               roll: null, xp: 0, loot: null, dmg: 0, heal: 0 };
    }
    const data = await res.json();
    const raw = data?.choices?.[0]?.message?.content?.trim() || '(the DM gathers their thoughts…)';
    return parseTags(raw);
  } catch (e) {
    return { text: `(the veil between you and the school wavers: ${String(e).slice(0, 60)})`,
             roll: null, xp: 0, loot: null, dmg: 0, heal: 0 };
  }
}
