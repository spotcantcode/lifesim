import time
import pytest
from backend.app.schemas import Profile, Assumptions
from backend.app.engine import initial_state, simulate, prepare, DECISIONS
from backend.app.narrative import TemplateNarrativeProvider


def run(profile=None, decision='maintain', months=12, runs=1, seed=42):
  profile = profile or Profile()
  return simulate(profile, initial_state(profile), profile.assumptions, decision, months, runs, seed)


def test_financial_ledger_reconciles_every_month():
  profile = Profile()
  previous = initial_state(profile)
  for snapshot in run()['trajectories']['central']:
    assert snapshot['net_worth'] == pytest.approx(snapshot['cash']+snapshot['investments']+snapshot['assets']-snapshot['debt'], abs=.001)
    expected_delta = snapshot['profit']-snapshot['tax']+profile.other_income-snapshot['spending']-profile.monthly_obligations-snapshot['debt_interest']+snapshot['investment_gain']
    assert snapshot['net_worth']-previous['net_worth'] == pytest.approx(expected_delta, abs=.001)
    previous = snapshot


def test_actions_change_actual_workload_costs_and_revenue():
  baseline = run()['trajectories']['central'][-1]
  owner = run(decision='expand_owner')['trajectories']['central'][-1]
  manager = run(decision='hire_manager')['trajectories']['central'][-1]
  assert owner['work_hours'] == 57
  assert manager['work_hours'] == 30
  assert owner['revenue'] > manager['revenue'] > baseline['revenue']
  assert manager['profit'] < owner['profit']
  assert owner['net_worth'] != manager['net_worth']


def test_hiring_not_double_charged_and_deterministic_split_matches():
  profile = Profile()
  starting = initial_state(profile)
  first = simulate(profile, starting, profile.assumptions, 'hire_manager', 6, 1, 42)['trajectories']['central'][-1]
  split = simulate(profile, first, profile.assumptions, 'hire_manager', 6, 1, 42)['trajectories']['central'][-1]
  continuous = run(decision='hire_manager')['trajectories']['central'][-1]
  assert split['work_hours'] == 30
  assert split['net_worth'] == pytest.approx(continuous['net_worth'], abs=.001)
  assert starting['manager'] is False


def test_deficit_liquidates_then_adds_debt_without_inventing_money():
  profile = Profile(monthly_expenses=1000000)
  result = run(profile=profile, months=1)['trajectories']['central'][0]
  assert result['cash'] == 0
  assert result['investments'] == 0
  assert result['debt'] > 500000
  starting = initial_state(profile)
  expected = starting['net_worth']+result['cash_flow']+result['investment_gain']
  assert result['net_worth'] == pytest.approx(expected, abs=.001)


def test_time_feasibility_and_capacity_reduce_growth():
  profile = Profile(work_hours=74)
  starting = initial_state(profile)
  adjusted = prepare(starting, 'expand_owner', profile, profile.assumptions)
  assert adjusted['time_constrained']
  assert adjusted['capacity_factor'] < 1
  total = adjusted['work_hours']+profile.sleep_hours+profile.exercise_hours+profile.family_hours+profile.personal_hours+adjusted['travel_hours']
  assert total <= 168
  with pytest.raises(ValueError): Profile(work_hours=100)
  first = simulate(profile, starting, profile.assumptions, 'expand_owner', 6, 1, 42)['trajectories']['central'][-1]
  split = simulate(profile, first, profile.assumptions, 'maintain', 6, 1, 42)['trajectories']['central'][-1]
  full = simulate(profile, starting, profile.assumptions, 'expand_owner', 12, 1, 42)['trajectories']['central'][-1]
  assert split['time_constrained']
  assert split['net_worth'] == pytest.approx(full['net_worth'], abs=.001)


def test_seeded_ensemble_reproducibility_and_common_draws():
  first = run(runs=100)
  assert first == run(runs=100)
  assert first != run(runs=100, seed=43)
  assert first['summary']['percentiles']['unfavorable'] <= first['summary']['percentiles']['central'] <= first['summary']['percentiles']['favorable']
  profile = Profile()
  fixed = profile.model_copy(deep=True)
  fixed.assumptions.expansion_growth = 0
  owner = run(profile=fixed, decision='expand_owner', runs=100)
  unchanged = run(profile=fixed, runs=100)
  assert owner['summary'] == unchanged['summary']
  for label in first['trajectories']:
    assert len(first['trajectories'][label]) == 12


def test_maximum_ensemble_performance_and_finite_values():
  started = time.perf_counter()
  result = run(months=240, runs=10000)
  assert time.perf_counter()-started < 20
  assert result['summary']['runs'] == 10000
  assert all(abs(value) < float('inf') for value in result['summary']['percentiles'].values())


@pytest.mark.parametrize('decision', list(DECISIONS))
def test_each_supported_decision_has_valid_results(decision):
  result = run(decision=decision)
  assert result['trajectories']['central'][-1]['free_hours'] >= 0


def test_narratives_grounded_in_metrics_and_cover_required_domains():
  profile = Profile()
  end = run(decision='hire_manager')['trajectories']['central'][-1]
  report = TemplateNarrativeProvider().generate(profile, initial_state(profile), end, profile.assumptions, ['hire_manager'])
  assert len(report['sections']) == 11
  assert report['calculated']['net_worth'] == end['net_worth']
  assert '30 hours a week' in report['sections'][0]['body']
  assert 'shorter daily block' in report['sections'][1]['body']
  assert '15 fewer work hours' in report['sections'][1]['body']
  assert '$3,000' in report['sections'][2]['body']
  assert 'No medical outcome' in report['sections'][4]['body']
