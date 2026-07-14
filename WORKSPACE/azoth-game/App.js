// ════════════════════════════════════════════════════════════════════════════
//  SOVEREIGN — an AI-Dungeon-Master RPG set in the Mystery School.
//  Conceptual combat, living AI narration, the Athanor's forge.
//  Extended with: Codex (LAMAGUE reference), difficulty tiers, Π scoring.
// ════════════════════════════════════════════════════════════════════════════
import { useState, useRef, useEffect, useCallback } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, SafeAreaView,
  StatusBar, ScrollView, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SYMBOLS, DOMAINS } from './lib/lamague';
import { loadStats, saveStats, recordSessionEnd, updateStreak, piForSymbol, recordSymbolAnswer } from './lib/stats';
import { rollCheck, mod, levelFor, FLOORS, CLASSES } from './lib/content';
import { askDM } from './lib/ai';
import { canPrestige, executePrestige, titleForLevel, PRESTIGE_THRESHOLDS } from './lib/prestige';

const SAVE = '@sovereign_v1';
const PI_STORE = '@sovereign_pi';

// Map stat names to LAMAGUE symbols for Π scoring context
const STAT_SYMBOL_MAP = {
  might:   { glyph: '◆', name: 'VAEL' },
  insight: { glyph: 'Π', name: 'Truth Pressure' },
  will:    { glyph: '☿', name: 'Mercury' },
  luck:    { glyph: '◑', name: 'Observer' },
};

export default function App() {
  const [screen, setScreen]     = useState('title'); // title | create | play | codex | records
  const [hero, setHero]         = useState(null);
  const [log, setLog]           = useState([]);
  const [input, setInput]       = useState('');
  const [busy, setBusy]         = useState(false);
  const [stats, setStats]       = useState(null);
  const [piScores, setPiScores] = useState({}); // { symbolName: { correct, total } }
  const [rollResult, setRollResult] = useState(null); // { stat, verdict, pi } for Π display
  const [showPrestige, setShowPrestige] = useState(false); // prestige confirmation modal
  const scroll = useRef(null);
  // ── Codex state ──
  const [codexFilter, setCodexFilter] = useState('All');
  // load saved hero + pi scores + stats
  useEffect(() => {
  // load saved hero + pi scores + stats
  useEffect(() => {
    AsyncStorage.getItem(SAVE).then((r) => r && setHero(JSON.parse(r))).catch(() => {});
    AsyncStorage.getItem(PI_STORE).then((r) => r && setPiScores(JSON.parse(r))).catch(() => {});
    loadStats(AsyncStorage).then(setStats).catch(() => {});
  }, []);
  useEffect(() => {
    if (scroll.current) setTimeout(() => scroll.current.scrollToEnd({ animated: true }), 50);
  }, [log, busy]);

  const save = (h) => { setHero(h); AsyncStorage.setItem(SAVE, JSON.stringify(h)).catch(() => {}); };
  const savePi = (p) => { setPiScores(p); AsyncStorage.setItem(PI_STORE, JSON.stringify(p)).catch(() => {}); };

  // ── send a player action to the AI Dungeon Master ──
  const act = useCallback(async (action) => {
    if (busy || !hero) return;
    setBusy(true);
    setLog((L) => [...L, { who: 'me', text: action }]);
    const floor = FLOORS[0];
    const history = log.filter((l) => l.who !== 'sys')
      .map((l) => ({ role: l.who === 'dm' ? 'assistant' : 'user', content: l.text }));
    const r = await askDM({ floor, character: hero, history, playerAction: action });

    let h = { ...hero }; const sys = [];
    if (r.dmg)  { h.hp = Math.max(0, h.hp - r.dmg); sys.push(`⚔ −${r.dmg} HP`); }
    if (r.xp)   { const lv = h.level; h.xp += r.xp; h.light += r.xp; h.totalPiEver = (h.totalPiEver || 0) + r.xp; h.level = levelFor(h.xp);
                  sys.push(`✦ +${r.xp} XP`); if (h.level > lv) { h.maxHp += 4; h.hp = h.maxHp; sys.push(`★ LEVEL ${h.level}!`); }
                  sys.push(`✦ +${r.xp} XP`); if (h.level > lv) { h.maxHp += 4; h.hp = h.maxHp; sys.push(`★ LEVEL ${h.level}!`); }
                  // When XP is awarded (DM confirms a correct action), try to detect
                  // which symbol was involved from the DM's narration or action context
                  const symbolMatch = action.match(/\b(Sol|Luna|VAEL|Mercury|Observer|Athanor|Solve|Coagula|Compression|Truth\s*Pressure|Summation|Threshold|Container|Recursion|Tensor|Cascade|Composite|Subtraction|Paradox|Triangulation)\b/i);
                  if (symbolMatch) {
                    const symName = symbolMatch[1].replace(/\s+/g, ' ');
                    // Normalize to match SYMBOLS names
                    const normalized = { 'Truth Pressure': 'Truth Pressure', 'Truth pressure': 'Truth Pressure' }[symName] || symName;
                    const newStats = recordSymbolAnswer(stats, normalized, true);
                    setStats(newStats);
                    saveStats(AsyncStorage, newStats).catch(() => {});
                    sys.push(`Π:${normalized} +1 correct`);
                  } }
    if (r.loot) { h.loot = [...(h.loot || []), r.loot]; sys.push(`◈ ${r.loot}`); }
    if (h.hp <= 0) { h.hp = Math.ceil(h.maxHp / 2); sys.push('☠ You fall — the School returns you to the threshold.'); }

    setLog((L) => [...L, { who: 'dm', text: r.text }, ...sys.map((s) => ({ who: 'sys', text: s }))]);
    if (r.roll) setLog((L) => [...L, { who: 'sys', text: `🎲 roll needed: ${r.roll.stat} vs DC ${r.roll.dc} — type "roll"`, roll: r.roll }]);
    h._roll = r.roll || null;
    save(h);
    setBusy(false);
  }, [busy, hero, log, stats]);

  // ── handle the player's typed input ──
  const submit = useCallback(() => {
    const t = input.trim(); if (!t) return; setInput('');
    if (t.toLowerCase() === 'roll' && hero?._roll) {
      const stat = hero._roll.stat;
      const res = rollCheck(mod(hero.stats[stat] || 0), hero._roll.dc);
      const verdict = res.crit ? 'CRIT!' : res.fumble ? 'FUMBLE!' : res.success ? 'success' : 'failure';
      const succeeded = res.success || res.crit;
      // Record the answer in stats for Π scoring
      const symbolInfo = STAT_SYMBOL_MAP[stat];
      if (symbolInfo) {
        const newStats = recordSymbolAnswer(stats, symbolInfo.name, succeeded);
        setStats(newStats);
        saveStats(AsyncStorage, newStats).catch(() => {});
        const pi = piForSymbol(newStats, symbolInfo.name);
        setRollResult({ stat, verdict, pi, glyph: symbolInfo?.glyph || '✦' });
      } else {
        setRollResult({ stat, verdict, pi: null, glyph: '✦' });
      }
      setTimeout(() => setRollResult(null), 3000);
      return;
    }
    act(t);
  }, [input, hero, act, stats]);
  const createHero = useCallback((cls) => {
    const c = CLASSES.find((x) => x.id === cls);
    const h = {
      id: Date.now().toString(36), name: 'Seeker', classId: cls, className: c.name,
      level: 1, xp: 0, light: 0, hp: 18, maxHp: 18, stats: { ...c.stats }, loot: [], _roll: null,
    };
    save(h); setScreen('play');
  }, []);

  // ── render functions ──

  const TitleScreen = () => (
    <View style={styles.center}>
      <Text style={styles.title}>SOVEREIGN</Text>
      <Text style={styles.subtitle}>The Mystery School</Text>
      <TouchableOpacity style={styles.btn} onPress={() => setScreen('create')}>
        <Text style={styles.btnText}>{hero ? '⟫ Continue' : '⟫ Begin'}</Text>
      </TouchableOpacity>
      <TouchableOpacity style={[styles.btn, styles.btnSecondary]} onPress={() => setScreen('codex')}>
        <Text style={styles.btnText}>◈ Codex</Text>
      </TouchableOpacity>
      <TouchableOpacity style={[styles.btn, styles.btnSecondary]} onPress={() => setScreen('records')}>
        <Text style={styles.btnText}>◈ Records</Text>
      </TouchableOpacity>
      {hero && (
        <TouchableOpacity style={[styles.btn, styles.btnDanger]} onPress={() => { AsyncStorage.removeItem(SAVE); setHero(null); }}>
          <Text style={styles.btnText}>⟲ New Game</Text>
        </TouchableOpacity>
      )}

  const CreateScreen = () => (
    <View style={styles.center}>
      <Text style={styles.heading}>Choose your Path</Text>
      {CLASSES.map((c) => (
        <TouchableOpacity key={c.id} style={styles.classCard} onPress={() => createHero(c.id)}>
          <Text style={styles.classGlyph}>{c.glyph}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.className}>{c.name}</Text>
            <Text style={styles.classDesc}>{c.desc}</Text>
            <Text style={styles.classStats}>
              M{'\u2605'.repeat(c.stats.might)}{'\u2606'.repeat(Math.max(0, 3 - c.stats.might))}  ·
              I{'\u2605'.repeat(c.stats.insight)}{'\u2606'.repeat(Math.max(0, 3 - c.stats.insight))}  ·
              W{'\u2605'.repeat(c.stats.will)}{'\u2606'.repeat(Math.max(0, 3 - c.stats.will))}  ·
              L{'\u2605'.repeat(c.stats.luck)}{'\u2606'.repeat(Math.max(0, 3 - c.stats.luck))}
            </Text>
          </View>
        </TouchableOpacity>
      ))}
      <TouchableOpacity style={[styles.btn, styles.btnSecondary]} onPress={() => setScreen('title')}>
        <Text style={styles.btnText}>← Back</Text>
      </TouchableOpacity>
    </View>
  );

  const CodexScreen = () => (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.heading}>◈ Codex of Glyphs</Text>
        <TouchableOpacity onPress={() => setScreen(hero ? 'play' : 'title')}>
          <Text style={styles.closeBtn}>✕</Text>
        </TouchableOpacity>
      </View>
      <ScrollView horizontal style={styles.filterRow} showsHorizontalScrollIndicator={false}>
        {DOMAINS.map((d) => (
          <TouchableOpacity
            key={d}
            style={[styles.filterChip, codexFilter === d && styles.filterChipActive]}
            onPress={() => setCodexFilter(d)}
          >
            <Text style={[styles.filterText, codexFilter === d && styles.filterTextActive]}>{d}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      <ScrollView style={styles.codexList}>
        {SYMBOLS.filter((s) => codexFilter === 'All' || s.domain === codexFilter).map((s, i) => {
          const sd = stats?.symbolsStudied?.[s.name];
          const piLabel = !sd || sd.total === 0 ? '' : sd.correct / sd.total > 0.8 ? 'HIGH' : sd.correct / sd.total > 0.5 ? 'MED' : 'LOW';
          return (
            <View key={i} style={styles.codexEntry}>
              <Text style={styles.codexGlyph}>{s.glyph}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.codexName}>{s.name}</Text>
                <Text style={styles.codexMeaning}>{s.meaning}</Text>
                <Text style={styles.codexDomain}>{s.domain}</Text>
              </View>
              {piLabel ? (
                <Text style={[styles.piBadge, piLabel === 'HIGH' && styles.piHigh, piLabel === 'MED' && styles.piMed]}>
                  Π:{piLabel}
                </Text>
              ) : null}
            </View>
          );
        })}
      </ScrollView>
    </SafeAreaView>
  );
  const RecordsScreen = () => {
    const s = stats || { totalSessions: 0, totalXpEarned: 0, highestLevel: 1, bestStreak: 0, totalDeaths: 0, sessions: [] };
    return (
      <SafeAreaView style={styles.screen}>
        <View style={styles.header}>
          <Text style={styles.heading}>◈ Hall of Records</Text>
          <TouchableOpacity onPress={() => setScreen('title')}>
            <Text style={styles.closeBtn}>✕</Text>
          </TouchableOpacity>
        </View>
        <ScrollView style={styles.codexList}>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Sessions</Text>
            <Text style={styles.statValue}>{s.totalSessions}</Text>
          </View>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Total XP</Text>
            <Text style={styles.statValue}>{s.totalXpEarned}</Text>
          </View>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Highest Level</Text>
            <Text style={styles.statValue}>{s.highestLevel}</Text>
          </View>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Best Streak</Text>
            <Text style={styles.statValue}>{s.bestStreak}</Text>
          </View>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Deaths</Text>
            <Text style={styles.statValue}>{s.totalDeaths}</Text>
          </View>
          <Text style={[styles.codexName, { marginTop: 20, marginBottom: 10 }]}>Recent Sessions</Text>
          {s.sessions.length === 0 && <Text style={styles.classDesc}>No sessions yet. Descend into the School.</Text>}
          {s.sessions.map((ses, i) => (
            <View key={i} style={styles.statRow}>
              <Text style={styles.statLabel}>{ses.date}</Text>
              <Text style={styles.statValue}>Lv {ses.level} · {ses.xp} XP</Text>
            </View>
          ))}
          {/* ── Prestige Section ── */}
          <Text style={[styles.codexName, { marginTop: 24, marginBottom: 10 }]}>☿ Prestige</Text>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Current Level</Text>
            <Text style={styles.statValue}>{titleForLevel(hero?.prestigeLevel || 0) || 'Seeker'} (Lv {hero?.prestigeLevel || 0})</Text>
          </View>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Total Π (lifetime)</Text>
            <Text style={styles.statValue}>{hero?.totalPiEver || 0}</Text>
          </View>
          {canPrestige(hero).eligible ? (
            <TouchableOpacity style={styles.prestigeBtn} onPress={() => setShowPrestige(true)}>
              <Text style={styles.prestigeBtnText}>☿ PRESTIGE — {canPrestige(hero).nextTitle}</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.statRow}>
              <Text style={styles.statLabel}>Next Prestige</Text>
              <Text style={styles.statValue}>{canPrestige(hero).nextTitle || '—'} ({canPrestige(hero).piNeeded || 0} Π needed)</Text>
            </View>
          )}
        </ScrollView>
        {/* ── Prestige Confirmation Modal ── */}
        {showPrestige && (
          <View style={styles.modalOverlay}>
            <View style={styles.modalBox}>
              <Text style={styles.modalTitle}>☿ Dissolve and Rebirth?</Text>
              <Text style={styles.modalBody}>
                Prestige to {canPrestige(hero).nextTitle}?{'\n'}
                Bonus: {canPrestige(hero).nextBonus}{'\n\n'}
                Your stats will reset to base + prestige bonus.{'\n'}
                Mastered symbols and discoveries carry over.
              </Text>
              <View style={styles.modalBtns}>
                <TouchableOpacity style={styles.modalCancel} onPress={() => setShowPrestige(false)}>
                  <Text style={styles.modalCancelText}>Remain</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.modalConfirm} onPress={() => {
                  const newHero = executePrestige(hero);
                  save(newHero);
                  setHero(newHero);
                  setShowPrestige(false);
                  setLog([]);
                  setScreen('play');
                }}>
                  <Text style={styles.modalConfirmText}>☿ Prestige</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}
        </ScrollView>
      </SafeAreaView>
    );
  };

  const PlayScreen = () => (
    <SafeAreaView style={styles.screen}>
        <Text style={styles.heroName}>
          {hero?.className} · Lv{hero?.level} · ❤️ {hero?.hp}/{hero?.maxHp}
          {hero?.light ? ` · ✦ ${hero.light}` : ''}
          {hero?.prestigeLevel ? ` · ☿${hero.prestigeLevel}` : ''}
        </Text>
        <TouchableOpacity onPress={() => setScreen('title')}>
          <Text style={styles.closeBtn}>✕</Text>
      <ScrollView style={styles.log} ref={scroll}>
        {log.map((l, i) => (
          <Text key={i} style={[
            styles.logLine,
            l.who === 'dm' && styles.dmText,
            l.who === 'sys' && styles.sysText,
            l.who === 'me' && styles.meText,
          ]}>
            {l.who === 'dm' ? '' : l.who === 'sys' ? '⚙ ' : '▸ '}{l.text}
          </Text>
        ))}
        {busy && <ActivityIndicator style={{ margin: 16 }} />}
      </ScrollView>
      {rollResult && (
        <View style={styles.piToast}>
          <Text style={styles.piToastGlyph}>{rollResult.glyph}</Text>
          <Text style={styles.piToastText}>
            {rollResult.stat.toUpperCase()} · {rollResult.verdict}
          </Text>
          {rollResult.pi ? (
            <Text style={[
              styles.piToastBadge,
              rollResult.pi === 'HIGH' && styles.piHigh,
              rollResult.pi === 'MED' && styles.piMed,
            ]}>
              Π:{rollResult.pi}
            </Text>
          ) : (
            <Text style={styles.piToastBadge}>Π:—</Text>
          )}
        </View>
      )}
        {busy && <ActivityIndicator style={{ margin: 16 }} />}
      </ScrollView>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder={hero?._roll ? 'Type "roll" or act...' : 'What do you do?'}
            placeholderTextColor="#666"
            onSubmitEditing={submit}
            editable={!busy}
          />
          <TouchableOpacity style={styles.sendBtn} onPress={submit} disabled={busy}>
            <Text style={styles.sendText}>⟫</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );

  if (screen === 'codex') return <CodexScreen />;
  if (screen === 'create') return <CreateScreen />;
  if (screen === 'play') return <PlayScreen />;
  if (screen === 'records') return <RecordsScreen />;
  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar barStyle="light-content" />
      <TitleScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#0a0a12' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  title: { fontSize: 42, fontWeight: '800', color: '#c9a84c', letterSpacing: 6 },
  subtitle: { fontSize: 20, color: '#7bdcb5', marginTop: 4, letterSpacing: 3 },
  tagline: { fontSize: 12, color: '#555', marginTop: 8, marginBottom: 40, letterSpacing: 1 },
  btn: { backgroundColor: '#c9a84c', paddingVertical: 14, paddingHorizontal: 48, borderRadius: 8, marginTop: 12, minWidth: 200, alignItems: 'center' },
  btnSecondary: { backgroundColor: '#1a1a2e', borderWidth: 1, borderColor: '#c9a84c' },
  btnDanger: { backgroundColor: '#2e1a1a', borderWidth: 1, borderColor: '#a84c4c' },
  btnText: { color: '#0a0a12', fontSize: 16, fontWeight: '700', letterSpacing: 1 },
  heading: { fontSize: 24, fontWeight: '700', color: '#c9a84c', marginBottom: 20, letterSpacing: 2 },
  classCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#12121e', borderRadius: 12, padding: 16, marginBottom: 10, width: '100%', borderWidth: 1, borderColor: '#1a1a2e' },
  classGlyph: { fontSize: 32, marginRight: 16, color: '#c9a84c' },
  className: { fontSize: 18, fontWeight: '700', color: '#eee' },
  classDesc: { fontSize: 13, color: '#888', marginTop: 2 },
  classStats: { fontSize: 11, color: '#666', marginTop: 4, letterSpacing: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, paddingTop: 8, borderBottomWidth: 1, borderBottomColor: '#1a1a2e' },
  heroName: { fontSize: 14, color: '#7bdcb5', fontWeight: '600' },
  closeBtn: { fontSize: 20, color: '#666', padding: 4 },
  log: { flex: 1, padding: 16 },
  logLine: { fontSize: 15, lineHeight: 22, marginBottom: 8, color: '#ccc' },
  dmText: { color: '#c9a84c', fontStyle: 'italic' },
  sysText: { color: '#7bdcb5', fontSize: 13 },
  meText: { color: '#eee' },
  inputRow: { flexDirection: 'row', padding: 8, borderTopWidth: 1, borderTopColor: '#1a1a2e' },
  input: { flex: 1, backgroundColor: '#12121e', borderRadius: 8, padding: 12, color: '#eee', fontSize: 15 },
  sendBtn: { backgroundColor: '#c9a84c', borderRadius: 8, padding: 12, marginLeft: 8, justifyContent: 'center' },
  sendText: { fontSize: 18, color: '#0a0a12', fontWeight: '700' },
  // Codex styles
  filterRow: { paddingHorizontal: 12, paddingVertical: 8, maxHeight: 44 },
  filterChip: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16, backgroundColor: '#1a1a2e', marginRight: 8 },
  filterChipActive: { backgroundColor: '#c9a84c' },
  filterText: { fontSize: 13, color: '#888' },
  filterTextActive: { color: '#0a0a12', fontWeight: '700' },
  codexList: { flex: 1, paddingHorizontal: 16 },
  codexEntry: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#1a1a2e' },
  codexGlyph: { fontSize: 28, width: 44, textAlign: 'center', color: '#c9a84c' },
  codexName: { fontSize: 16, fontWeight: '700', color: '#eee' },
  codexMeaning: { fontSize: 13, color: '#888', marginTop: 2, lineHeight: 18 },
  codexDomain: { fontSize: 11, color: '#555', marginTop: 2, letterSpacing: 1 },
  piBadge: { fontSize: 10, fontWeight: '700', color: '#a84c4c', backgroundColor: '#1a0a0a', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, marginLeft: 8 },
  piHigh: { color: '#4ca84c', backgroundColor: '#0a1a0a' },
  piMed: { color: '#c9a84c', backgroundColor: '#1a1a0a' },
  // Records screen
  statRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#1a1a2e' },
  statValue: { fontSize: 18, fontWeight: '700', color: '#c9a84c' },
  // Π toast overlay — shown after successful roll
  piToast: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#12121e', borderWidth: 1, borderColor: '#c9a84c', borderRadius: 12, paddingVertical: 8, paddingHorizontal: 16, marginHorizontal: 16, marginBottom: 8 },
  piToastGlyph: { fontSize: 20, marginRight: 8, color: '#c9a84c' },
  piToastBadge: { fontSize: 11, fontWeight: '700', color: '#a84c4c', backgroundColor: '#1a0a0a', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, marginLeft: 8 },
  // ── Prestige ──
  prestigeBtn: { backgroundColor: '#2a1a0a', borderWidth: 1, borderColor: '#c9a84c', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 8, marginTop: 16, marginBottom: 8, alignItems: 'center' },
  prestigeBtnText: { color: '#c9a84c', fontSize: 16, fontWeight: '700', letterSpacing: 1 },
  modalOverlay: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.8)', justifyContent: 'center', alignItems: 'center', padding: 32 },
  modalBox: { backgroundColor: '#1a1a2e', borderRadius: 16, padding: 24, width: '100%', maxWidth: 360, borderWidth: 1, borderColor: '#c9a84c' },
  modalTitle: { fontSize: 20, fontWeight: '700', color: '#c9a84c', textAlign: 'center', marginBottom: 12 },
  modalBody: { fontSize: 14, color: '#aaa', lineHeight: 20, textAlign: 'center', marginBottom: 20 },
  modalBtns: { flexDirection: 'row', justifyContent: 'space-around' },
  modalCancel: { backgroundColor: '#2a2a3e', paddingVertical: 10, paddingHorizontal: 24, borderRadius: 8 },
  modalCancelText: { color: '#888', fontSize: 14, fontWeight: '600' },
  modalConfirm: { backgroundColor: '#c9a84c', paddingVertical: 10, paddingHorizontal: 24, borderRadius: 8 },
  modalConfirmText: { color: '#0a0a12', fontSize: 14, fontWeight: '700' },
});
