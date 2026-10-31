"""Pure monthly model. No storage, network, or narrative dependencies."""
from copy import deepcopy
import math
import numpy as np
from .schemas import Profile, Assumptions

ENGINE_VERSION = '1.0.1'
DECISIONS = {
  'expand_owner': ('Lead the expansion', 'Add 12 work hours/week; expansion adds 8 percentage points/year at the default assumption.'),
  'hire_manager': ('Hire an operator', 'Add manager salary; free 15 owner hours/week and add 60% of the expansion growth assumption.'),
  'maintain': ('Keep your rhythm', 'Keep the current business structure and its baseline growth assumption.'),
  'reduce_expenses': ('Simplify your lifestyle', 'Reduce personal spending by 15%, once per timeline.'),
  'invest_cash': ('Invest spare cash', 'Move half of cash above a six-month spending buffer into investments.'),
  'abroad': ('Try a slower life abroad', 'Spend three months/year abroad; add $400/month averaged travel cost and 3 weekly travel hours.'),
  'reduce_hours': ('Protect your time', 'Reduce work by 10 hours/week, once; reduce business revenue by 8%.'),
  'fund_repair': ('Fund an operations repair', 'Spend $2,500 once on an operational repair. No assumed future payoff.'),
}


def initial_state(profile: Profile):
  balances = {kind: sum(account.balance for account in profile.accounts if account.kind == kind) for kind in ['cash', 'investments', 'assets', 'debt']}
  revenue = sum(business.revenue for business in profile.businesses)
  cost = sum(business.expenses for business in profile.businesses)
  return dict(month=0, **balances, revenue=revenue, cost_ratio=cost / revenue if revenue else 0,
    fixed_business_cost=cost if not revenue else 0, spending=profile.monthly_expenses,
    work_hours=profile.work_hours, requested_work_hours=profile.work_hours, months_abroad=profile.months_abroad, travel_hours=profile.travel_hours,
    manager=False, expanded=False, simplified=False, reduced_hours=False, repaired=False,
    profit=revenue-cost, cash_flow=0, event_cost=0, tax=0, investment_gain=0, debt_interest=0,
    net_worth=balances['cash']+balances['investments']+balances['assets']-balances['debt'],
    free_hours=168-profile.work_hours-profile.sleep_hours-profile.exercise_hours-profile.family_hours-profile.personal_hours-profile.travel_hours,
    time_constrained=False)


def prepare(state, decision, profile, assumptions):
  state = deepcopy(state)
  # Preserve unmet work demand so a later turn cannot silently restore full growth.
  state['work_hours'] = state.get('requested_work_hours', state['work_hours'])
  if decision == 'expand_owner' and not state['expanded']:
    state['expanded'] = True
    state['work_hours'] += 12
  elif decision == 'hire_manager' and not state['manager']:
    state['manager'] = True
    state['work_hours'] = max(0, state['work_hours'] - 15)
  elif decision == 'reduce_expenses' and not state['simplified']:
    state['spending'] *= .85
    state['simplified'] = True
  elif decision == 'invest_cash':
    amount = max(0, state['cash'] - (state['spending']+profile.monthly_obligations)*6) / 2
    state['cash'] -= amount
    state['investments'] += amount
  elif decision == 'abroad' and state['months_abroad'] < 3:
    state['months_abroad'] = 3
    state['spending'] += 400
    state['travel_hours'] += 3
  elif decision == 'reduce_hours' and not state['reduced_hours']:
    state['work_hours'] = max(0, state['work_hours'] - 10)
    state['revenue'] *= .92
    state['reduced_hours'] = True
  elif decision == 'fund_repair' and not state['repaired']:
    state['cash'] -= 2500
    state['repaired'] = True
  state['requested_work_hours'] = state['work_hours']
  capacity = max(0, 168-profile.sleep_hours-profile.exercise_hours-profile.family_hours-profile.personal_hours-state['travel_hours'])
  state['time_constrained'] = state['work_hours'] > capacity
  state['capacity_factor'] = min(1, capacity / max(state['work_hours'], 1))
  state['work_hours'] = min(state['work_hours'], capacity)
  state['free_hours'] = max(0, capacity-state['work_hours'])
  return state


def _paths(profile, starting, assumptions, decision, months, runs, seed, selected=None):
  prepared = prepare(starting, decision, profile, assumptions)
  vectors = {key: np.full(runs, prepared[key], dtype=float) for key in ['cash', 'investments', 'debt', 'revenue', 'spending']}
  history = {int(index): [] for index in selected} if selected is not None else {}
  growth = assumptions.annual_growth
  growth += assumptions.expansion_growth * prepared['capacity_factor'] if prepared['expanded'] else 0
  growth += assumptions.expansion_growth * .6 if prepared['manager'] else 0
  for offset in range(1, months + 1):
    month = starting['month'] + offset
    # Absolute month seeds keep shocks aligned across choices and split advances.
    rng = np.random.default_rng(np.random.SeedSequence([seed, month]))
    revenue_shock = rng.normal(size=runs) if runs > 1 else np.zeros(runs)
    market_shock = rng.normal(size=runs) if runs > 1 else np.zeros(runs)
    vectors['revenue'] *= np.exp(math.log1p(growth/12) - (assumptions.revenue_volatility**2/24 if runs > 1 else 0) + revenue_shock*assumptions.revenue_volatility/math.sqrt(12))
    vectors['spending'] *= 1+assumptions.inflation/12
    event_cost = vectors['revenue'] * assumptions.disruption_fraction if month % 12 == 6 else np.zeros(runs)
    operating_cost = vectors['revenue']*prepared['cost_ratio']+prepared['fixed_business_cost']+(assumptions.manager_cost if prepared['manager'] else 0)
    profit = vectors['revenue']-operating_cost-event_cost
    tax = np.maximum(profit, 0)*assumptions.tax_rate
    interest = vectors['debt']*assumptions.debt_interest/12
    cash_flow = profit-tax+profile.other_income-vectors['spending']-profile.monthly_obligations-interest
    gain = vectors['investments']*(np.exp(math.log1p(assumptions.investment_return/12) - (assumptions.investment_volatility**2/24 if runs > 1 else 0)+market_shock*assumptions.investment_volatility/math.sqrt(12))-1)
    contribution = np.maximum(cash_flow, 0)*assumptions.investment_allocation
    vectors['investments'] += gain+contribution
    vectors['cash'] += cash_flow-contribution
    liquidation = np.minimum(np.maximum(-vectors['cash'], 0), vectors['investments'])
    vectors['cash'] += liquidation
    vectors['investments'] -= liquidation
    vectors['debt'] += np.maximum(-vectors['cash'], 0)
    vectors['cash'] = np.maximum(vectors['cash'], 0)
    net_worth = vectors['cash']+vectors['investments']+prepared['assets']-vectors['debt']
    for index in history:
      snapshot = {**prepared, **{key: round(float(values[index]), 4) for key, values in vectors.items()},
        'month': month, 'profit': round(float(profit[index]), 4), 'cash_flow': round(float(cash_flow[index]), 4),
        'event_cost': round(float(event_cost[index]), 4), 'tax': round(float(tax[index]), 4),
        'investment_gain': round(float(gain[index]), 4), 'debt_interest': round(float(interest[index]), 4),
        'net_worth': round(float(net_worth[index]), 4)}
      history[index].append(snapshot)
  return net_worth, history


def simulate(profile: Profile, starting: dict, assumptions: Assumptions, decision: str, months: int, runs: int, seed: int):
  if decision not in DECISIONS or not 1 <= months <= 240 or runs not in [1, 100, 1000, 10000]:
    raise ValueError('Unsupported decision, duration, or run count.')
  finals, _ = _paths(profile, starting, assumptions, decision, months, runs, seed)
  ranks = np.argsort(finals)
  indices = {label: int(ranks[round((runs-1)*percentile)]) for label, percentile in [('unfavorable', .1), ('central', .5), ('favorable', .9)]}
  _, histories = _paths(profile, starting, assumptions, decision, months, runs, seed, set(indices.values()))
  trajectories = {label: histories[index] for label, index in indices.items()}
  return {'trajectories': trajectories, 'indices': indices, 'summary': {
    'minimum': round(float(np.min(finals)), 2), 'maximum': round(float(np.max(finals)), 2),
    'percentiles': {label: trajectories[label][-1]['net_worth'] for label in indices},
    'runs': runs, 'seed': seed, 'method': 'deterministic' if runs == 1 else 'conditional Monte Carlo percentile representatives'}}


def sensitivity(profile, starting, assumptions, decision, months, seed):
  results = []
  baseline = simulate(profile, starting, assumptions, decision, months, 1, seed)['trajectories']['central'][-1]['net_worth']
  for field in ['annual_growth', 'investment_return']:
    for change in [-.02, .02]:
      adjusted = assumptions.model_copy(update={field: getattr(assumptions, field)+change})
      final = simulate(profile, starting, adjusted, decision, months, 1, seed)['trajectories']['central'][-1]['net_worth']
      results.append({'assumption': field, 'change': change, 'net_worth_delta': round(final-baseline, 2)})
  return results
