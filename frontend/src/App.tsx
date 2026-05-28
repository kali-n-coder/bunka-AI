import { useEffect, useMemo, useState } from 'react'
import type { Dispatch, FormEvent, SetStateAction } from 'react'
import { apiClient } from './api/client'
import type {
  AdminLog,
  AdminPin,
  ChatMessage,
  ItineraryResponse,
  ModelStatus,
  RagStatus,
  SourceChunk,
  StaffSession,
  WaitTime,
} from './api/client'
import './App.css'

type Mode = 'chat' | 'waits' | 'plan' | 'exhibitions' | 'admin' | 'staff'
type AdminTab = 'overview' | 'rag' | 'waits' | 'pins'
type WaitView = 'cards' | 'table'
type WaitSort = 'id' | 'name' | 'category' | 'waitAsc' | 'waitDesc'
type UiMessage = ChatMessage & { sources?: SourceChunk[] }

const CHAT_STORAGE_KEY = 'hakuryu_chat_history'
const visitorFriendlyError = 'ただいま案内機能の準備中です。しばらくしてからもう一度お試しください。'
const sampleWaitNotice = '最新情報の確認中です。いまはサンプルの待ち時間を表示しています。'
const samplePlanNotice = '行程作成機能の確認中です。いまはサンプルの行程を表示しています。'

const sampleWaitTimes: WaitTime[] = [
  {
    id: 1,
    exhibition_id: 1,
    exhibition_name: '白龍の舞',
    category: '展示',
    current_wait_minutes: 20,
    location_name: '体育館ステージ',
    duration_minutes: 15,
    recommended_for: '演出展示を見たい人・写真を撮りたい人',
    cautions: 'フラッシュ撮影は控えてください。',
    stage_start_time: '10:30',
    ticket_status: '整理券なし',
    capacity_status: '通常',
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    exhibition_id: 2,
    exhibition_name: '龍の巣カフェ',
    category: '飲食',
    current_wait_minutes: 5,
    location_name: '本館1階 多目的室',
    duration_minutes: 20,
    recommended_for: '休憩したい人・飲食を楽しみたい人',
    cautions: '売り切れ次第終了です。',
    ticket_status: '食券あり',
    capacity_status: '残りあり',
    updated_at: new Date().toISOString(),
  },
]

function waitLabel(minutes: number) {
  if (minutes <= 5) return '空いている'
  if (minutes <= 20) return 'やや混雑'
  if (minutes <= 45) return '混雑'
  return '満員に近い'
}

function waitTone(minutes: number) {
  if (minutes <= 5) return 'calm'
  if (minutes <= 20) return 'normal'
  if (minutes <= 45) return 'busy'
  return 'full'
}

function categoryClass(category?: string) {
  if (category === '飲食') return 'cat-food'
  if (category === 'ステージ' || category === '上映') return 'cat-stage'
  if (category === '体験') return 'cat-experience'
  if (category === '案内') return 'cat-guide'
  return 'cat-exhibit'
}

function sourceNames(sources?: SourceChunk[]) {
  const names = new Set<string>()
  for (const source of sources || []) {
    const metadata = source.metadata || {}
    const name = metadata.exhibition_name || metadata.source
    if (typeof name === 'string' && name.trim()) names.add(name.trim())
  }
  return Array.from(names).slice(0, 4)
}

function App() {
  const [mode, setMode] = useState<Mode>('chat')
  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<UiMessage[]>([])
  const [chatStatus, setChatStatus] = useState('')

  const [waitTimes, setWaitTimes] = useState<WaitTime[]>(sampleWaitTimes)
  const [waitStatus, setWaitStatus] = useState('サンプル表示中')
  const [waitView, setWaitView] = useState<WaitView>('cards')
  const [waitQuery, setWaitQuery] = useState('')
  const [waitSort, setWaitSort] = useState<WaitSort>('id')

  const [selectedPlanIds, setSelectedPlanIds] = useState<number[]>([1, 2])
  const [planCategory, setPlanCategory] = useState('すべて')
  const [startExhibitionId, setStartExhibitionId] = useState<number | ''>('')
  const [endExhibitionId, setEndExhibitionId] = useState<number | ''>('')
  const [availableMinutes, setAvailableMinutes] = useState(90)
  const [plan, setPlan] = useState<ItineraryResponse | null>(null)
  const [planStatus, setPlanStatus] = useState('')
  const [selectedDetailId, setSelectedDetailId] = useState<number | null>(null)

  const [adminTab, setAdminTab] = useState<AdminTab>('overview')
  const [adminPin, setAdminPin] = useState('')
  const [adminUnlocked, setAdminUnlocked] = useState(false)
  const [adminStatus, setAdminStatus] = useState('')
  const [adminLogs, setAdminLogs] = useState<AdminLog[]>([])
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [ragStatus, setRagStatus] = useState<RagStatus | null>(null)
  const [ragQuery, setRagQuery] = useState('白龍の舞について')
  const [ragResults, setRagResults] = useState<SourceChunk[]>([])
  const [adminPins, setAdminPins] = useState<AdminPin[]>([])
  const [adminWaitDrafts, setAdminWaitDrafts] = useState<Record<number, number>>({})
  const [adminPinDrafts, setAdminPinDrafts] = useState<Record<number, string>>({})

  const [staffPin, setStaffPin] = useState('')
  const [staffLoginExhibitionId, setStaffLoginExhibitionId] = useState(1)
  const [staffSession, setStaffSession] = useState<StaffSession | null>(null)
  const [staffWaitMinutes, setStaffWaitMinutes] = useState(10)
  const [staffStatus, setStaffStatus] = useState('')

  const latestWaitSummary = useMemo(() => {
    if (!waitTimes.length) return '待ち時間データなし'
    return `最短 ${Math.min(...waitTimes.map((item) => item.current_wait_minutes))}分`
  }, [waitTimes])

  const visibleWaitTimes = useMemo(() => {
    const query = waitQuery.trim().toLowerCase()
    const filtered = waitTimes.filter((item) => {
      if (!query) return true
      return [item.exhibition_name, item.category, item.location_name, item.recommended_for, item.cautions]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query))
    })
    return [...filtered].sort((a, b) => {
      if (waitSort === 'waitAsc') return a.current_wait_minutes - b.current_wait_minutes
      if (waitSort === 'waitDesc') return b.current_wait_minutes - a.current_wait_minutes
      if (waitSort === 'name') return (a.exhibition_name || '').localeCompare(b.exhibition_name || '', 'ja')
      if (waitSort === 'category') return (a.category || '').localeCompare(b.category || '', 'ja')
      return a.exhibition_id - b.exhibition_id
    })
  }, [waitQuery, waitSort, waitTimes])

  const categories = useMemo(() => ['すべて', ...Array.from(new Set(waitTimes.map((item) => item.category).filter(Boolean)))], [waitTimes])
  const planCandidates = useMemo(() => (planCategory === 'すべて' ? waitTimes : waitTimes.filter((item) => item.category === planCategory)), [planCategory, waitTimes])
  const selectedDetail = useMemo(() => waitTimes.find((item) => item.exhibition_id === selectedDetailId) || null, [selectedDetailId, waitTimes])
  const popularityRanking = useMemo(() => [...waitTimes].sort((a, b) => b.current_wait_minutes - a.current_wait_minutes).slice(0, 5), [waitTimes])
  const categoryCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const item of waitTimes) counts.set(item.category || '未分類', (counts.get(item.category || '未分類') || 0) + 1)
    return Array.from(counts.entries())
  }, [waitTimes])
  const planTotals = useMemo(() => {
    if (!plan) return null
    const travel = plan.total_travel_minutes ?? plan.stops.reduce((sum, stop) => sum + stop.travel_minutes_from_previous, 0)
    const wait = plan.total_wait_minutes ?? plan.stops.reduce((sum, stop) => sum + stop.wait_minutes, 0)
    const visit = plan.total_visit_minutes ?? plan.stops.reduce((sum, stop) => sum + stop.visit_minutes, 0)
    return { travel, wait, visit, total: plan.total_minutes }
  }, [plan])

  useEffect(() => {
    void loadWaitTimes()
    const timer = window.setInterval(() => void loadWaitTimes(), 30000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    const saved = window.localStorage.getItem(CHAT_STORAGE_KEY)
    if (!saved) return
    try {
      const parsed = JSON.parse(saved) as UiMessage[]
      if (Array.isArray(parsed)) setChatHistory(parsed)
    } catch {
      window.localStorage.removeItem(CHAT_STORAGE_KEY)
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(chatHistory))
  }, [chatHistory])

  async function loadWaitTimes() {
    setWaitStatus('更新中')
    try {
      const data = await apiClient.getWaitTimes()
      setWaitTimes(data.length ? data : sampleWaitTimes)
      setWaitStatus(data.length ? '最新データ' : 'サンプル表示中')
    } catch {
      setWaitTimes(sampleWaitTimes)
      setWaitStatus('サンプル表示中')
    }
  }

  async function submitChat(event?: FormEvent) {
    event?.preventDefault()
    const trimmed = message.trim()
    if (!trimmed) return
    const nextHistory: UiMessage[] = [...chatHistory, { role: 'user', content: trimmed }]
    setChatHistory([...nextHistory, { role: 'assistant', content: '', sources: [] }])
    setMessage('')
    setChatStatus('回答中')
    const assistantIndex = nextHistory.length
    try {
      await apiClient.streamChat(
        { message: trimmed, history: nextHistory.map(({ role, content }) => ({ role, content })) },
        (chunk) => {
          setChatHistory((current) => current.map((item, index) => (index === assistantIndex ? { ...item, content: `${item.content}${chunk}` } : item)))
        },
        (sources) => {
          setChatHistory((current) => current.map((item, index) => (index === assistantIndex ? { ...item, sources } : item)))
        },
      )
      setChatStatus('')
    } catch {
      setChatHistory([...nextHistory, { role: 'assistant', content: visitorFriendlyError }])
      setChatStatus('案内機能の準備中')
    }
  }

  async function submitPlan(event: FormEvent) {
    event.preventDefault()
    if (!selectedPlanIds.length) {
      setPlanStatus('見たい企画を選んでください')
      return
    }
    setPlanStatus('作成中')
    try {
      const result = await apiClient.planItinerary(
        selectedPlanIds,
        availableMinutes,
        typeof startExhibitionId === 'number' ? startExhibitionId : undefined,
        typeof endExhibitionId === 'number' ? endExhibitionId : undefined,
      )
      setPlan(result)
      setPlanStatus('')
    } catch {
      setPlan({
        stops: selectedPlanIds.map((id, index) => ({
          exhibition_id: id,
          exhibition_name: waitTimes.find((item) => item.exhibition_id === id)?.exhibition_name || `展示 ${id}`,
          wait_minutes: index === 0 ? 20 : 5,
          visit_minutes: 15,
          travel_minutes_from_previous: index === 0 ? 0 : 5,
          elapsed_minutes: (index + 1) * 25,
        })),
        total_minutes: selectedPlanIds.length * 25,
        skipped_exhibition_ids: [],
        note: samplePlanNotice,
      })
      setPlanStatus('サンプル表示中')
    }
  }

  async function loadAdminData(pinOverride = adminPin) {
    setAdminStatus('admin情報を確認中')
    try {
      const [logs, model, rag, pins] = await Promise.all([
        apiClient.getAdminLogs(),
        apiClient.getModelStatus(),
        apiClient.getRagStatus(),
        pinOverride ? apiClient.getAdminPins(pinOverride) : Promise.resolve({ pins: [] }),
      ])
      setAdminLogs(logs.logs)
      setModelStatus(model)
      setRagStatus(rag)
      setAdminPins(pins.pins)
      setAdminPinDrafts(Object.fromEntries(pins.pins.map((item) => [item.exhibition_id, item.pin])))
      setAdminStatus(pinOverride ? 'admin情報を更新しました' : 'admin PINを入力してください。')
    } catch (error) {
      setAdminStatus(error instanceof Error ? error.message : 'admin情報を取得できませんでした')
    }
  }

  async function submitAdminLogin(event: FormEvent) {
    event.preventDefault()
    if (!adminPin.trim()) {
      setAdminStatus('admin PINを入力してください')
      return
    }
    setAdminStatus('adminログイン中')
    try {
      await apiClient.getAdminPins(adminPin)
      setAdminUnlocked(true)
      await loadAdminData(adminPin)
    } catch {
      setAdminUnlocked(false)
      setAdminStatus('admin PINが違います')
    }
  }

  function adminLogout() {
    setAdminUnlocked(false)
    setAdminPin('')
    setAdminPins([])
    setAdminPinDrafts({})
    setAdminStatus('')
  }

  async function submitRagSearch(event: FormEvent) {
    event.preventDefault()
    const trimmed = ragQuery.trim()
    if (!trimmed) return
    setAdminStatus('検索候補を確認中')
    try {
      const response = await apiClient.searchRagDocuments(trimmed, 6)
      setRagResults(response.results)
      setAdminStatus(response.results.length ? '検索候補を表示しました' : '候補が見つかりませんでした')
    } catch {
      setAdminStatus('資料検索の確認に失敗しました')
    }
  }

  async function ingestRagDocuments(rebuild = false) {
    setAdminStatus(rebuild ? 'RAGデータを再構築中' : 'RAGデータを投入中')
    try {
      const result = rebuild ? await apiClient.rebuildRagDocuments() : await apiClient.ingestRagDocuments()
      setAdminStatus(`${result.loaded}件を読み込み、${result.upserted}件を投入しました`)
      await loadAdminData()
    } catch {
      setAdminStatus('資料の読み込みに失敗しました')
    }
  }

  async function updateAdminWait(exhibitionId: number) {
    if (!adminPin) {
      setAdminStatus('admin PINを入力してください')
      return
    }
    const minutes = adminWaitDrafts[exhibitionId] ?? waitTimes.find((item) => item.exhibition_id === exhibitionId)?.current_wait_minutes ?? 0
    try {
      await apiClient.updateAdminWaitTime(adminPin, exhibitionId, minutes)
      setAdminStatus(`企画ID ${exhibitionId} の待ち時間を ${minutes}分に更新しました`)
      await loadWaitTimes()
    } catch (error) {
      setAdminStatus(error instanceof Error ? error.message : '待ち時間を更新できませんでした')
    }
  }

  async function publishPublicWaitTimes() {
    if (!adminPin) {
      setAdminStatus('admin PINを入力してください')
      return
    }
    setAdminStatus('公開用の待ち時間を送信中')
    try {
      const result = await apiClient.publishPublicWaitTimes(adminPin)
      setAdminStatus(result.enabled ? `公開用の待ち時間を ${result.published}件送信しました` : 'Firebase公開設定が未設定です')
    } catch (error) {
      setAdminStatus(error instanceof Error ? error.message : '公開用の待ち時間を送信できませんでした')
    }
  }

  async function updateAdminPin(exhibitionId: number) {
    if (!adminPin) {
      setAdminStatus('admin PINを入力してください')
      return
    }
    const nextPin = (adminPinDrafts[exhibitionId] || '').trim()
    if (!nextPin) {
      setAdminStatus('新しいPINを入力してください')
      return
    }
    try {
      await apiClient.updateAdminPin(adminPin, exhibitionId, nextPin)
      setAdminStatus(`企画ID ${exhibitionId} のPINを更新しました`)
      await loadAdminData()
    } catch (error) {
      setAdminStatus(error instanceof Error ? error.message : 'PINを更新できませんでした')
    }
  }

  async function submitStaffLogin(event: FormEvent) {
    event.preventDefault()
    setStaffStatus('ログイン中')
    try {
      const session = await apiClient.staffLogin(staffLoginExhibitionId, staffPin)
      setStaffSession(session)
      setStaffStatus(`${session.exhibition_name || `展示 ${session.exhibition_id}`} にログインしました。`)
    } catch {
      setStaffSession(null)
      setStaffStatus('ログインできませんでした。企画IDとPINを確認してください。')
    }
  }

  async function submitStaffUpdate(event: FormEvent) {
    event.preventDefault()
    if (!staffSession) return
    setStaffStatus('更新中')
    try {
      await apiClient.updateWaitTime(staffSession.exhibition_id, staffWaitMinutes, staffPin)
      setStaffStatus(`${staffSession.exhibition_name || `展示 ${staffSession.exhibition_id}`} を${staffWaitMinutes}分に更新しました。`)
      await loadWaitTimes()
    } catch {
      setStaffStatus('更新できませんでした。企画ID・PINを確認してください。')
    }
  }

  function resetChatHistory() {
    setChatHistory([])
    setMessage('')
    setChatStatus('')
    window.localStorage.removeItem(CHAT_STORAGE_KEY)
  }

  function choosePrompt(text: string) {
    setMode('chat')
    setMessage(text)
  }

  function alternativeItems(item: WaitTime) {
    if (item.current_wait_minutes < 25) return []
    return waitTimes
      .filter((candidate) => candidate.exhibition_id !== item.exhibition_id && candidate.current_wait_minutes <= 15)
      .sort((a, b) => a.current_wait_minutes - b.current_wait_minutes)
      .slice(0, 2)
  }

  function togglePlanSelection(exhibitionId: number) {
    setSelectedPlanIds((current) => (current.includes(exhibitionId) ? current.filter((id) => id !== exhibitionId) : [...current, exhibitionId]))
  }

  return (
    <main className="app">
      <aside className="sidebar">
        <button className="compose-button" type="button" onClick={resetChatHistory}>新しいチャット</button>
        <nav className="history-list" aria-label="メニュー">
          <button className={mode === 'chat' ? 'active' : ''} type="button" onClick={() => setMode('chat')}>白龍に相談する</button>
          <button className={mode === 'waits' ? 'active' : ''} type="button" onClick={() => setMode('waits')}>待ち時間を見る</button>
          <button className={mode === 'plan' ? 'active' : ''} type="button" onClick={() => setMode('plan')}>行程を作る</button>
          <button className={mode === 'exhibitions' ? 'active' : ''} type="button" onClick={() => setMode('exhibitions')}>企画一覧</button>
        </nav>
        <div className="sidebar-status">
          <span>白龍祭ガイド</span>
          <small>{latestWaitSummary}</small>
          <button className="staff-link" type="button" onClick={() => setMode('admin')}>admin</button>
          <button className="staff-link" type="button" onClick={() => setMode('staff')}>スタッフ</button>
        </div>
      </aside>

      <section className="main-chat">
        <header className="topbar">
          <button className="model-button" type="button">白龍 AI</button>
          <div className="topbar-actions">
            {mode === 'chat' && chatHistory.length > 0 && <button type="button" onClick={resetChatHistory}>履歴リセット</button>}
            <span>{waitStatus}</span>
          </div>
        </header>

        {mode === 'chat' && (
          <>
            <div className={`conversation ${chatHistory.length === 0 ? 'empty' : ''}`}>
              {chatHistory.length === 0 ? (
                <section className="welcome">
                  <div className="logo-orb">白</div>
                  <h1>何を案内しましょう？</h1>
                  <p className="welcome-copy">展示案内、待ち時間、空いている企画、回り方を相談できます。</p>
                  <div className="prompt-grid">
                    {['白龍の舞について教えて', '今、空いている企画は？', 'おすすめの回り方は？', '整理券が必要な企画は？'].map((text) => (
                      <button key={text} type="button" onClick={() => choosePrompt(text)}>{text}</button>
                    ))}
                  </div>
                </section>
              ) : (
                chatHistory.map((item, index) => (
                  <article key={`${item.role}-${index}`} className={`message ${item.role}`}>
                    <div className="message-avatar">{item.role === 'user' ? 'U' : '白'}</div>
                    <div className="message-body">
                      <p>{item.content}</p>
                      {item.role === 'assistant' && sourceNames(item.sources).length > 0 && (
                        <div className="source-chips" aria-label="参照した資料">
                          <span>参照</span>
                          {sourceNames(item.sources).map((name) => <small key={name}>{name}</small>)}
                        </div>
                      )}
                    </div>
                  </article>
                ))
              )}
            </div>
            <footer className="composer-wrap">
              <form className="composer" onSubmit={submitChat}>
                <textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="白龍祭について質問する" rows={1} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void submitChat() } }} />
                <button type="submit" aria-label="送信">↑</button>
              </form>
              <p>{chatStatus === '回答中' ? <span className="thinking">白龍が資料を確認しています</span> : chatStatus || 'サンプルデータで試せます。'}</p>
            </footer>
          </>
        )}

        {mode === 'waits' && (
          <section className="tool-view">
            <div className="tool-heading">
              <div><h1>待ち時間</h1><p>現在の混雑状況を確認できます。</p></div>
              <div className="tool-actions">
                <div className="segmented-control" aria-label="待ち時間表示形式">
                  <button className={waitView === 'cards' ? 'active' : ''} type="button" onClick={() => setWaitView('cards')}>カード</button>
                  <button className={waitView === 'table' ? 'active' : ''} type="button" onClick={() => setWaitView('table')}>表</button>
                </div>
                <button type="button" onClick={loadWaitTimes}>更新</button>
              </div>
            </div>
            {waitStatus === 'サンプル表示中' && <p className="inline-status">{sampleWaitNotice}</p>}
            <div className="ranking-strip">
              <div><span>人気・混雑ランキング</span><strong>{popularityRanking[0]?.exhibition_name || 'データなし'}</strong></div>
              {popularityRanking.slice(0, 4).map((item, index) => <article key={item.exhibition_id}><span>{index + 1}</span><strong>{item.exhibition_name}</strong><small>{item.current_wait_minutes}分</small></article>)}
            </div>
            <div className="category-summary">
              {categoryCounts.map(([category, count]) => <span key={category} className={categoryClass(category)}>{category} {count}件</span>)}
            </div>
            <div className="wait-controls">
              <label>検索<input value={waitQuery} onChange={(event) => setWaitQuery(event.target.value)} placeholder="企画名・カテゴリ・場所で検索" /></label>
              <label>並び替え<select value={waitSort} onChange={(event) => setWaitSort(event.target.value as WaitSort)}><option value="id">展示ID順</option><option value="name">企画名順</option><option value="category">カテゴリ順</option><option value="waitAsc">待ち時間が短い順</option><option value="waitDesc">待ち時間が長い順</option></select></label>
            </div>
            {waitView === 'cards' ? (
              <div className="wait-grid">{visibleWaitTimes.map((item) => <WaitCard key={item.id} item={item} alternatives={alternativeItems(item)} />)}</div>
            ) : (
              <WaitTable items={visibleWaitTimes} />
            )}
          </section>
        )}

        {mode === 'plan' && (
          <section className="tool-view">
            <div className="tool-heading"><div><h1>行程プランナー</h1><p>企画名を選んで、待ち時間と移動時間を考慮した回り方を作ります。</p></div></div>
            <form className="planner-layout" onSubmit={submitPlan}>
              <label>カテゴリ<select value={planCategory} onChange={(event) => setPlanCategory(event.target.value)}>{categories.map((category) => <option key={category} value={category}>{category}</option>)}</select></label>
              <label>使える時間<input type="number" min="1" value={availableMinutes} onChange={(event) => setAvailableMinutes(Number(event.target.value))} /></label>
              <label>開始地点<select value={startExhibitionId} onChange={(event) => setStartExhibitionId(event.target.value ? Number(event.target.value) : '')}><option value="">指定なし</option>{waitTimes.map((item) => <option key={item.exhibition_id} value={item.exhibition_id}>{item.exhibition_name}</option>)}</select></label>
              <label>終了地点<select value={endExhibitionId} onChange={(event) => setEndExhibitionId(event.target.value ? Number(event.target.value) : '')}><option value="">指定なし</option>{waitTimes.map((item) => <option key={item.exhibition_id} value={item.exhibition_id}>{item.exhibition_name}</option>)}</select></label>
              <div className="planner-picks">
                {planCandidates.map((item) => <label key={item.exhibition_id} className="planner-pick"><input type="checkbox" checked={selectedPlanIds.includes(item.exhibition_id)} onChange={() => togglePlanSelection(item.exhibition_id)} /><span><strong>{item.exhibition_name}</strong><small>{item.location_name || item.category} / 待ち {item.current_wait_minutes}分</small></span></label>)}
              </div>
              <button type="submit">作成</button>
            </form>
            {planStatus && <p className="inline-status">{planStatus}</p>}
            {plan && <PlanResult plan={plan} totals={planTotals} />}
          </section>
        )}

        {mode === 'exhibitions' && (
          <section className="tool-view">
            <div className="tool-heading"><div><h1>企画一覧</h1><p>企画をクリックすると、場所・所要時間・注意事項を確認できます。</p></div></div>
            <div className="exhibition-layout">
              <div className="exhibition-list">
                {visibleWaitTimes.map((item) => <button key={item.exhibition_id} type="button" className={selectedDetailId === item.exhibition_id ? 'active' : ''} onClick={() => setSelectedDetailId(item.exhibition_id)}><strong>{item.exhibition_name}</strong><span>{item.category} / {item.location_name || '場所未設定'}</span></button>)}
              </div>
              <ExhibitionDetail item={selectedDetail} />
            </div>
          </section>
        )}

        {mode === 'admin' && (
          <section className="tool-view">
            <div className="tool-heading">
              <div><h1>admin</h1><p>RAG、運用状態、全企画の待ち時間、スタッフPINをまとめて管理します。</p></div>
              {adminUnlocked && <div className="tool-actions"><button type="button" onClick={() => loadAdminData()}>更新</button><button type="button" onClick={publishPublicWaitTimes}>公開待ち時間を送信</button><button type="button" onClick={adminLogout}>ログアウト</button></div>}
            </div>
            {!adminUnlocked ? (
              <form className="tool-form narrow" onSubmit={submitAdminLogin}>
                <label>admin PIN<input type="password" value={adminPin} onChange={(event) => setAdminPin(event.target.value)} placeholder="管理用PIN" /></label>
                <button type="submit">ログイン</button>
              </form>
            ) : (
              <>
                <div className="wait-controls">
                  <label>表示<select value={adminTab} onChange={(event) => setAdminTab(event.target.value as AdminTab)}><option value="overview">運用状態</option><option value="rag">RAG管理</option><option value="waits">全待ち時間</option><option value="pins">PIN管理</option></select></label>
                </div>
                {adminTab === 'overview' && <AdminOverview modelStatus={modelStatus} logs={adminLogs} />}
                {adminTab === 'rag' && <AdminRag ragStatus={ragStatus} ragQuery={ragQuery} setRagQuery={setRagQuery} ragResults={ragResults} submitRagSearch={submitRagSearch} ingestRagDocuments={ingestRagDocuments} />}
                {adminTab === 'waits' && <AdminWaits items={waitTimes} drafts={adminWaitDrafts} setDrafts={setAdminWaitDrafts} updateWait={updateAdminWait} />}
                {adminTab === 'pins' && <AdminPins pins={adminPins} drafts={adminPinDrafts} setDrafts={setAdminPinDrafts} updatePin={updateAdminPin} />}
              </>
            )}
            {adminStatus && <p className="inline-status">{adminStatus}</p>}
          </section>
        )}

        {mode === 'staff' && (
          <section className="tool-view">
            <div className="tool-heading"><div><h1>スタッフ</h1><p>企画IDと専用PINでログインすると、その企画の待ち時間だけ更新できます。</p></div></div>
            {!staffSession ? (
              <form className="tool-form narrow" onSubmit={submitStaffLogin}>
                <label>企画ID<input type="number" min="1" value={staffLoginExhibitionId} onChange={(event) => setStaffLoginExhibitionId(Number(event.target.value))} /></label>
                <label>企画専用PIN<input type="password" value={staffPin} onChange={(event) => setStaffPin(event.target.value)} /></label>
                <button type="submit">ログイン</button>
              </form>
            ) : (
              <>
                <div className="staff-session-card"><span>ログイン中</span><strong>{staffSession.exhibition_name || `展示 ${staffSession.exhibition_id}`}</strong><button type="button" onClick={() => { setStaffSession(null); setStaffStatus('') }}>ログアウト</button></div>
                <form className="tool-form narrow" onSubmit={submitStaffUpdate}>
                  <label>更新する企画<input value={staffSession.exhibition_name || `展示 ${staffSession.exhibition_id}`} disabled /></label>
                  <label>待ち時間<input type="number" min="0" max="240" value={staffWaitMinutes} onChange={(event) => setStaffWaitMinutes(Number(event.target.value))} /></label>
                  <div className="quick-wait-buttons">{[0, 5, 10, 20, 30, 45, 60].map((minutes) => <button key={minutes} type="button" onClick={() => setStaffWaitMinutes(minutes)}>{minutes}分</button>)}</div>
                  <button type="submit">更新</button>
                </form>
              </>
            )}
            {staffStatus && <p className="inline-status">{staffStatus}</p>}
          </section>
        )}
      </section>
    </main>
  )
}

function WaitCard({ item, alternatives }: { item: WaitTime; alternatives: WaitTime[] }) {
  return (
    <article className={`wait-card ${waitTone(item.current_wait_minutes)} ${categoryClass(item.category)}`}>
      <div><h2>{item.exhibition_name || `展示 ${item.exhibition_id}`}</h2><p>{item.location_name || item.category || '場所未設定'}</p></div>
      <strong>{item.current_wait_minutes}分</strong>
      <span className="wait-badge">{waitLabel(item.current_wait_minutes)}</span>
      <dl className="wait-meta">
        <div><dt>カテゴリ</dt><dd>{item.category || '未設定'}</dd></div>
        <div><dt>所要時間</dt><dd>{item.duration_minutes ? `${item.duration_minutes}分` : '未設定'}</dd></div>
        <div><dt>開始時刻</dt><dd>{item.stage_start_time || '指定なし'}</dd></div>
        <div><dt>整理券</dt><dd>{item.ticket_status || 'なし'}</dd></div>
        <div><dt>定員</dt><dd>{item.capacity_status || '通常'}</dd></div>
        <div><dt>注意</dt><dd>{item.cautions || '未設定'}</dd></div>
      </dl>
      {alternatives.length > 0 && <div className="alternative-box"><span>混雑時の代替案</span>{alternatives.map((alternative) => <small key={alternative.exhibition_id}>{alternative.exhibition_name} ({alternative.current_wait_minutes}分)</small>)}</div>}
    </article>
  )
}

function WaitTable({ items }: { items: WaitTime[] }) {
  return (
    <div className="wait-table-wrap"><table className="wait-table"><thead><tr><th>ID</th><th>企画名</th><th>場所</th><th>カテゴリ</th><th>待ち</th><th>状態</th><th>整理券</th></tr></thead><tbody>
      {items.map((item) => <tr key={item.id} className={waitTone(item.current_wait_minutes)}><td>{item.exhibition_id}</td><td>{item.exhibition_name}</td><td>{item.location_name || '未設定'}</td><td>{item.category || '未設定'}</td><td>{item.current_wait_minutes}分</td><td><span className="wait-badge">{waitLabel(item.current_wait_minutes)}</span></td><td>{item.ticket_status || 'なし'}</td></tr>)}
    </tbody></table></div>
  )
}

function PlanResult({ plan, totals }: { plan: ItineraryResponse; totals: { travel: number; wait: number; visit: number; total: number } | null }) {
  return (
    <div className="timeline">
      {totals && <div className="plan-summary"><article><span>合計</span><strong>{totals.total}分</strong></article><article><span>移動</span><strong>{totals.travel}分</strong></article><article><span>待ち</span><strong>{totals.wait}分</strong></article><article><span>見学</span><strong>{totals.visit}分</strong></article></div>}
      {plan.stops.map((stop, index) => <article key={`${stop.exhibition_id}-${index}`} className="timeline-item"><span>{index + 1}</span><div><h2>{stop.exhibition_name}</h2><p>移動 {stop.travel_minutes_from_previous}分 / 待ち {stop.wait_minutes}分 / 見学 {stop.visit_minutes}分</p></div><strong>{stop.elapsed_minutes}分</strong></article>)}
      <p className="inline-status">{plan.note}</p>
    </div>
  )
}

function ExhibitionDetail({ item }: { item: WaitTime | null }) {
  return (
    <article className="exhibition-detail">
      {item ? (
        <><p>{item.category}</p><h2>{item.exhibition_name}</h2><dl><div><dt>場所</dt><dd>{item.location_name || '未設定'}</dd></div><div><dt>所要時間</dt><dd>{item.duration_minutes || 15}分</dd></div><div><dt>現在の待ち時間</dt><dd>{item.current_wait_minutes}分</dd></div><div><dt>開始時刻</dt><dd>{item.stage_start_time || '指定なし'}</dd></div><div><dt>整理券</dt><dd>{item.ticket_status || 'なし'}</dd></div><div><dt>定員</dt><dd>{item.capacity_status || '通常'}</dd></div><div><dt>おすすめ</dt><dd>{item.recommended_for || '未設定'}</dd></div><div><dt>注意事項</dt><dd>{item.cautions || '未設定'}</dd></div></dl></>
      ) : (
        <><p>企画詳細</p><h2>左の一覧から企画を選択</h2></>
      )}
    </article>
  )
}

function AdminOverview({ modelStatus, logs }: { modelStatus: ModelStatus | null; logs: AdminLog[] }) {
  return (
    <div className="ops-grid">
      <section className="ops-panel"><h2>運用状態</h2>{modelStatus ? <div className="model-status-list"><article className={modelStatus.answer_model.ok ? 'ok' : 'ng'}><span>回答モデル</span><strong>{modelStatus.answer_model.matched_name || modelStatus.answer_model.name}</strong><small>{modelStatus.answer_model.ok ? '利用できます' : '確認が必要です'}</small></article><article className={modelStatus.embedding_model.ok ? 'ok' : 'ng'}><span>検索モデル</span><strong>{modelStatus.embedding_model.matched_name || modelStatus.embedding_model.name}</strong><small>{modelStatus.embedding_model.ok ? '利用できます' : '確認が必要です'}</small></article><article className={modelStatus.vector_store.ok ? 'ok' : 'ng'}><span>RAG投入</span><strong>{modelStatus.vector_store.collection_count}件</strong><small>{modelStatus.vector_store.ok ? '確認済み' : '確認が必要です'}</small></article></div> : <p className="inline-status">更新を押すと確認できます。</p>}</section>
      <section className="ops-panel"><h2>直近ログ</h2><div className="log-list">{logs.length ? logs.map((log, index) => <article key={`${log.time}-${index}`} className={log.level.toLowerCase()}><span>{log.time} / {log.level}</span><strong>{log.logger}</strong><p>{log.message}</p></article>) : <p className="inline-status">まだ表示できるログがありません。</p>}</div></section>
    </div>
  )
}

function AdminRag({ ragStatus, ragQuery, setRagQuery, ragResults, submitRagSearch, ingestRagDocuments }: { ragStatus: RagStatus | null; ragQuery: string; setRagQuery: (value: string) => void; ragResults: SourceChunk[]; submitRagSearch: (event: FormEvent) => void; ingestRagDocuments: (rebuild?: boolean) => void }) {
  return (
    <div className="rag-admin-grid">
      <section className="rag-panel"><h2>投入状態</h2><div className="tool-actions"><button type="button" onClick={() => ingestRagDocuments(false)}>データ投入</button><button type="button" onClick={() => ingestRagDocuments(true)}>再構築</button></div>{ragStatus ? <><div className="rag-stats"><article><span>資料ファイル</span><strong>{ragStatus.file_count}</strong></article><article><span>読み込み候補</span><strong>{ragStatus.chunk_count}</strong></article><article><span>投入済み</span><strong>{ragStatus.collection_count}</strong></article></div><p className="rag-path">{ragStatus.data_dir}</p><div className="rag-source-list">{ragStatus.sources.map((source) => <article key={source.path}><strong>{source.path.split(/[\\/]/).pop() || source.path}</strong><span>{source.type} / {source.chunk_count}件</span></article>)}</div></> : <p className="inline-status">更新を押すと状態を確認できます。</p>}</section>
      <section className="rag-panel"><h2>検索候補チェック</h2><form className="rag-search-form" onSubmit={submitRagSearch}><textarea value={ragQuery} onChange={(event) => setRagQuery(event.target.value)} rows={3} placeholder="例: 今空いている企画は？" /><button type="submit">検索候補を見る</button></form><div className="rag-result-list">{ragResults.map((result, index) => <article key={`${result.metadata.source || 'source'}-${index}`}><div><strong>{String(result.metadata.exhibition_name || result.metadata.source || `候補${index + 1}`)}</strong>{typeof result.distance === 'number' && <span>距離 {result.distance.toFixed(3)}</span>}</div><p>{result.content}</p></article>)}</div></section>
    </div>
  )
}

function AdminWaits({ items, drafts, setDrafts, updateWait }: { items: WaitTime[]; drafts: Record<number, number>; setDrafts: Dispatch<SetStateAction<Record<number, number>>>; updateWait: (exhibitionId: number) => void }) {
  return <div className="rag-result-list">{items.map((item) => <article key={item.exhibition_id}><div><strong>{item.exhibition_name}</strong><span>現在 {item.current_wait_minutes}分</span></div><div className="admin-row"><input type="number" min="0" max="240" value={drafts[item.exhibition_id] ?? item.current_wait_minutes} onChange={(event) => setDrafts((current) => ({ ...current, [item.exhibition_id]: Number(event.target.value) }))} /><button type="button" onClick={() => updateWait(item.exhibition_id)}>更新</button></div></article>)}</div>
}

function AdminPins({ pins, drafts, setDrafts, updatePin }: { pins: AdminPin[]; drafts: Record<number, string>; setDrafts: Dispatch<SetStateAction<Record<number, string>>>; updatePin: (exhibitionId: number) => void }) {
  return <div className="rag-result-list">{pins.length ? pins.map((item) => <article key={item.exhibition_id}><div><strong>{item.name}</strong><span>ID {item.exhibition_id}</span></div><div className="admin-row"><input value={drafts[item.exhibition_id] ?? item.pin} onChange={(event) => setDrafts((current) => ({ ...current, [item.exhibition_id]: event.target.value }))} /><button type="button" onClick={() => updatePin(item.exhibition_id)}>PIN更新</button></div></article>) : <p className="inline-status">admin PINを入力して更新を押すとPIN一覧を表示します。</p>}</div>
}

export default App
