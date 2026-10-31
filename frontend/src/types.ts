export type State = {
  month: number; cash: number; investments: number; assets: number; debt: number; revenue: number;
  spending: number; work_hours: number; net_worth: number; cash_flow: number; profit: number;
  event_cost: number; free_hours: number; months_abroad: number; manager: boolean; expanded: boolean;
};
export type Assumptions = Record<string, number>;
export type Profile = {
  id?: string; name: string; age: number; start_date: string; location: string; future_location: string;
  provenance: 'fictional' | 'user_assumption' | 'observed'; milestones: string; aspirations: string;
  businesses: { name: string; revenue: number; expenses: number; employees: number; contractors: number; dependency: string }[];
  accounts: { name: string; kind: string; balance: number }[]; goals: string[];
  monthly_expenses: number; monthly_obligations: number; other_income: number; work_hours: number;
  sleep_hours: number; exercise_hours: number; family_hours: number; personal_hours: number; travel_hours: number;
  months_abroad: number; relationship_commitments: string; lifestyle_preferences: string; target_work_hours: number;
  assumptions: Assumptions;
};
export type JournalEntry = { month: number; decision: string; title: string; run_id: string };
export type Scenario = {
  id: string; name: string; profile_id: string; parent_id: string | null; seed: number;
  assumptions: Assumptions; campaign: boolean; profile: Profile; state: State; starting_state: State;
  fork_month: number; journal: JournalEntry[]; latest_run: string | null;
};
export type Report = { title: string; subtitle: string; sections: { title: string; body: string }[]; calculated: Record<string, number> };
export type Trajectory = 'unfavorable' | 'central' | 'favorable';
export type Run = {
  reports: Record<Trajectory, Report>; trajectories: Record<Trajectory, State[]>;
  summary: { runs: number; seed: number; method: string; percentiles: Record<Trajectory, number>; minimum: number; maximum: number };
  sensitivity: { assumption: string; change: number; net_worth_delta: number }[];
};
export type Detail = { scenario: Scenario; history: State[]; run: Run | null };
export type Decision = { id: string; title: string; description: string };
export type Bootstrap = { profiles: Profile[]; scenarios: Scenario[]; decisions: Decision[]; engine_version: string };
export type Page = 'home' | 'profile' | 'studio' | 'future' | 'game' | 'timelines' | 'compare';
export type Act = (work: () => Promise<void>) => Promise<void>;
