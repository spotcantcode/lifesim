import { lazy, Suspense, useEffect, useState } from 'react';
import { api, download } from './lib';
import { Badge, Button, Icon } from './components/ui';
import Home from './pages/Home';
import Game from './pages/Game';
import Studio from './pages/Studio';
import ProfileEditor from './pages/ProfileEditor';
import type { Assumptions, Bootstrap, Detail, Page, Profile, Scenario } from './types';
const Future = lazy(() => import('./pages/Future'));
const Timelines = lazy(() => import('./pages/Timelines'));
const Compare = lazy(() => import('./pages/Compare'));

const navigation: { page: Page; label: string }[] = [
  { page: 'home', label: 'Command center' }, { page: 'profile', label: 'My digital twin' },
  { page: 'studio', label: 'Simulation studio' }, { page: 'future', label: 'Future explorer' },
  { page: 'game', label: 'Strategy game' }, { page: 'timelines', label: 'Timelines' }, { page: 'compare', label: 'Compare futures' },
];

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [data, setData] = useState<Bootstrap | null>(null);
  const [profileId, setProfileId] = useState('');
  const [scenarioId, setScenarioId] = useState(() => localStorage.getItem('lifesim.scenario.v1') || '');
  const [detail, setDetail] = useState<Detail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [deleteOpen, setDeleteOpen] = useState(false);

  async function refresh() {
    const next = await api<Bootstrap>('/bootstrap');
    setData(next);
    setProfileId(current => next.profiles.some(profile => profile.id === current) ? current : next.profiles[0]?.id || '');
  }
  async function act(work: () => Promise<void>) {
    setBusy(true); setError('');
    try { await work(); } catch (reason) { setError(reason instanceof Error ? reason.message : 'The action could not be completed.'); }
    finally { setBusy(false); }
  }
  useEffect(() => { void act(refresh); }, []);
  useEffect(() => { window.scrollTo(0, 0); }, [page, scenarioId]);
  useEffect(() => {
    if (!scenarioId) { setDetail(null); localStorage.removeItem('lifesim.scenario.v1'); return; }
    let current = true;
    setDetail(null);
    localStorage.setItem('lifesim.scenario.v1', scenarioId);
    void (async () => { try { const next = await api<Detail>(`/scenarios/${scenarioId}`); if (current) setDetail(next); } catch (reason) { if (current) { setError(String(reason)); setScenarioId(''); } } })();
    return () => { current = false; };
  }, [scenarioId]);

  function open(id: string, destination: Page = 'game') { setScenarioId(id); setPage(destination); }
  const profile = data?.profiles.find(item => item.id === profileId) || data?.profiles[0];
  async function enterCampaign() {
    await act(async () => {
      const campaigns = data?.scenarios.filter(item => item.campaign && item.profile_id === profile?.id && item.state.month < 60) || [];
      const existing = campaigns.find(item => item.id === scenarioId) || campaigns.at(-1);
      if (existing) { open(existing.id); return; }
      const scenario = await api<Scenario>('/scenarios', 'POST', { profile_id: profile?.id, name: profile?.provenance === 'fictional' ? 'Freedom by 50' : `${profile?.name} · My campaign`, seed: 42, campaign: true });
      await refresh(); open(scenario.id);
    });
  }
  async function advance(decision: string, months: number) {
    await act(async () => { const next = await api<Detail>(`/scenarios/${scenarioId}/advance`, 'POST', { decision, months, runs: 1 }); setDetail(next); await refresh(); if (months === 12) setPage('future'); });
  }
  async function simulate(input: { name: string; seed: number; assumptions: Assumptions; months: number; runs: number; decision: string }) {
    await act(async () => {
      const scenario = await api<Scenario>('/scenarios','POST',{ profile_id: profile!.id, name: input.name, seed: input.seed, assumptions: input.assumptions, campaign: false });
      await api<Detail>(`/scenarios/${scenario.id}/advance`,'POST',{ decision: input.decision, months: input.months, runs: input.runs });
      await refresh(); open(scenario.id, 'future');
    });
  }
  async function saveProfile(next: Profile, create: boolean) {
    const { id: ignored, ...payload } = next;
    void ignored;
    const saved = await api<Profile>(create ? '/profiles' : `/profiles/${profile!.id}`, create ? 'POST' : 'PUT', payload);
    await refresh(); setProfileId(saved.id!);
  }

  return <div className="app-shell"><aside className="sidebar"><button className="brand" aria-label="LifeSim home" onClick={() => setPage('home')}><span className="brand-mark"><Icon name="leaf" size={24}/></span>LifeSim<span className="brand-beta">LOCAL</span></button><div className="sidebar-label">YOUR POSSIBLE FUTURES</div><nav aria-label="Main navigation">{navigation.map(item => <button key={item.page} aria-label={item.label} className={page === item.page ? 'nav-item active' : 'nav-item'} onClick={() => setPage(item.page)}><Icon name={item.page}/><span>{item.label}</span>{page === item.page && <span className="nav-dot"/>}</button>)}</nav><div className="sidebar-quote"><Icon name="leaf" size={24}/><p>“The best way to predict your future is to explore it.”</p><span>A LITTLE CURIOSITY GOES A LONG WAY.</span></div><div className="local-status"><span className="status-dot"/><div>Local workspace<small>No AI connection required</small></div></div></aside><div className="main-shell"><header className="topbar"><div><span className="breadcrumb">Your world</span><span className="breadcrumb-separator">/</span><span>{navigation.find(item => item.page === page)?.label}</span></div><div className="topbar-right"><Badge muted>{profile?.provenance === 'fictional' ? 'FICTIONAL DEMO' : 'MANUAL PROFILE'}</Badge><span className="avatar">{profile?.name.split(' ').map(word => word[0]).slice(0,2).join('') || 'LS'}</span></div></header><main><div className="workspace-controls">{data && data.profiles.length > 1 && ['home','profile','studio'].includes(page) && <label>Profile<select aria-label="Active profile" value={profileId} onChange={event => setProfileId(event.target.value)}>{data.profiles.map(item => <option key={item.id} value={item.id}>{item.name} · {item.provenance.replaceAll('_',' ')}</option>)}</select></label>}{data && data.scenarios.length > 0 && page !== 'home' && page !== 'profile' && page !== 'studio' && <label>Active timeline<select aria-label="Active timeline" value={scenarioId} onChange={event => setScenarioId(event.target.value)}><option value="">Choose a future</option>{data.scenarios.map(item => <option key={item.id} value={item.id}>{item.name} · month {item.state.month}</option>)}</select></label>}</div>{busy && <div className="working-status" role="status">Calculating and saving locally…</div>}{error && <div className="error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>}{!data ? <section className="panel empty"><h2>Opening your world…</h2><p>If this takes longer than expected, check that the backend is running.</p><Button variant="secondary" onClick={() => act(refresh)}>Retry connection</Button></section> : !profile ? <section className="panel empty"><h2>A fresh start.</h2><p>All local data has been deleted. Create a fictional profile to begin again.</p><Button onClick={() => act(async () => { await api('/profiles','POST',{}); await refresh(); })}>Create fictional demo</Button></section> : <Suspense fallback={<div className="panel empty">Opening this chapter…</div>}>
      {page === 'home' && <Home data={data} profile={profile} navigate={setPage} enter={enterCampaign} open={open}/>}
      {page === 'game' && <Game detail={detail} decisions={data.decisions} busy={busy} advance={advance} rewind={month => act(async () => { const branch = await api<Scenario>(`/scenarios/${scenarioId}/branch`,'POST',{ month, name: `${detail!.scenario.name.slice(0,65)} · branch at ${month}` }); await refresh(); open(branch.id); })} future={() => setPage('future')} start={enterCampaign}/>}
      {page === 'studio' && <Studio key={profile.id} profile={profile} decisions={data.decisions} busy={busy} simulate={simulate}/>}
      {page === 'future' && <Future detail={detail} studio={() => setPage('studio')} game={() => setPage('game')} compare={() => setPage('compare')}/>}
      {page === 'profile' && <ProfileEditor key={profile.id} profile={profile} busy={busy} act={act} save={saveProfile} refresh={refresh}/>}
      {page === 'timelines' && <Timelines scenarios={data.scenarios} open={open} compare={() => setPage('compare')} studio={() => setPage('studio')}/>}
      {page === 'compare' && <Compare key={data.scenarios.map(item => item.latest_run).join()} scenarios={data.scenarios} studio={() => setPage('studio')}/>}
    </Suspense>}<footer><span>LifeSim <span className="footer-dot">·</span> A little clarity for the road ahead.</span><div><button onClick={() => act(async () => download('lifesim-workspace.json',JSON.stringify(await api('/export'),null,2)))}>Export workspace</button><button onClick={() => setDeleteOpen(true)}>Delete local data</button></div></footer></main></div>{deleteOpen && <div className="modal-backdrop"><section className="modal panel" role="dialog" aria-modal="true" aria-labelledby="delete-title"><h2 id="delete-title">Delete all local data?</h2><p>This removes every profile, observation, saved run and timeline in this workspace. Export a backup first if you want to keep them.</p><div className="actions"><Button variant="secondary" autoFocus onClick={() => setDeleteOpen(false)}>Keep my data</Button><Button variant="danger" disabled={busy} onClick={() => act(async () => { await api('/data','DELETE'); setScenarioId(''); setDetail(null); await refresh(); setDeleteOpen(false); setPage('home'); })}>Delete everything</Button></div></section></div>}</div>;
}
