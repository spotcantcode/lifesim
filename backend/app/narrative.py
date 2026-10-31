from typing import Protocol
from .engine import DECISIONS


class NarrativeProvider(Protocol):
  def generate(self, profile, start, end, assumptions, decisions: list[str]) -> dict: ...


def money(value):
  return f'${value:,.0f}'


def month_label(profile, month):
  year, initial_month, _ = map(int, profile.start_date.split('-'))
  absolute = initial_month - 1 + month
  from calendar import month_name
  return f'{month_name[absolute % 12 + 1]} {year + absolute // 12}'


class TemplateNarrativeProvider:
  def generate(self, profile, start, end, assumptions, decisions):
    hours = end['work_hours']
    short_day = hours <= 32
    positive = end['cash_flow'] >= 0
    spending = end['spending']+profile.monthly_obligations
    cover = end['investments']*assumptions.withdrawal_rate/12
    runway = end['cash']/max(spending, 1)
    location = f"{profile.location}, with {end['months_abroad']} months a year planned in {profile.future_location}" if end['months_abroad'] else profile.location
    generated = [
      ('Overview', f"By {month_label(profile, end['month'])}, your modeled life is anchored in {location}. You work {hours:.0f} hours a week and hold {money(end['net_worth'])} in net assets, excluding any business sale value. " + ('The schedule leaves room to choose how you spend your days.' if short_day else 'The business still takes a substantial share of your week.')),
      ('A typical day', f"With {hours:g} working hours across the week, " + ('your work can fit into a shorter daily block, leaving part of the day for life outside the business.' if short_day else 'a typical weekday includes a substantial block of business work, with personal commitments fitting around it.') + (f" An operator handles day-to-day decisions; you have {max(0, profile.work_hours-hours):g} fewer work hours than in your starting profile." if end['manager'] else '') + f" You have budgeted {profile.exercise_hours:g} hours of exercise and {profile.family_hours:g} hours with family each week. This routine is illustrative; the hours come from the model."),
      ('Business & career', f"Monthly business revenue reaches {money(end['revenue'])}; profit before personal tax is {money(end['profit'])}. " + ('An operator absorbs some day-to-day responsibilities, with a recurring salary of '+money(assumptions.manager_cost)+'.' if end['manager'] else 'Your business continues to depend on your direct involvement.') + (' Owner-led expansion increases both growth and demands on your time.' if end['expanded'] else ' Growth follows the assumptions shown below.')),
      ('Financial situation', f"Monthly cash flow after modeled tax, spending and debt interest is {money(end['cash_flow'])}. Cash is {money(end['cash'])}, investments {money(end['investments'])}, other assets {money(end['assets'])}, and debt {money(end['debt'])}. " + (f'Cash covers approximately {runway:.1f} months of current spending without income. ' if spending else 'No personal spending is configured. ') + f"At a {assumptions.withdrawal_rate:.1%} annual withdrawal assumption, investments support {money(cover)}/month against {money(spending)} spending. This is a planning comparison, not a guarantee."),
      ('Health & lifestyle', f"Your schedule reserves {profile.sleep_hours/7:.1f} hours of sleep a night and {profile.exercise_hours:g} hours of exercise a week. " + ('The shorter work schedule gives you more room to keep that routine.' if short_day else 'Keeping these routines will require protecting time alongside work.') + ' No medical outcome is predicted.'),
      ('Family & relationships', f"You reserve {profile.family_hours:g} hours a week for family and relationships. Your stated commitment: {profile.relationship_commitments} More available time creates an opportunity for connection; the model cannot infer how anyone else feels or behaves."),
      ('Location & travel', f"Your home base remains {profile.location}. " + (f"You plan {end['months_abroad']} months a year in {profile.future_location}. Travel cost is averaged into monthly spending; legal residence, visas and tax effects are not modeled." if end['months_abroad'] else f"Longer stays in {profile.future_location} remain a possibility rather than a scheduled change.")),
      ('Opportunities & challenges', ('Positive cash flow creates room to build reserves or reinvest. ' if positive else 'Spending exceeds current income; continued deficits draw down investments and then increase debt. ') + ('Delegation frees time but creates a fixed payroll commitment. ' if end['manager'] else 'Owner dependence remains a vulnerability. ') + ('The requested work schedule exceeded available time, so owner expansion growth was reduced. ' if end['time_constrained'] else '') + 'Revenue disruptions and market returns can materially change this path.'),
      ('Decisions that shaped this future', '; '.join(dict.fromkeys(DECISIONS[decision][0] for decision in decisions)) or 'Starting profile and baseline assumptions; no decision yet.'),
      ('Assumptions & uncertainties', f"Baseline annual revenue growth {assumptions.annual_growth:.1%}; investment return {assumptions.investment_return:.1%}; inflation {assumptions.inflation:.1%}; effective tax {assumptions.tax_rate:.0%}. Synthetic disruptions cost {assumptions.disruption_fraction:.0%} of revenue in months 6, 18, 30 and every 12 months thereafter. Narrative scenes illustrate computed constraints; they are not observations or forecasts of actual events."),
      ('What could change this future', 'Customer retention, manager execution, actual spending, market returns, and the time you choose to protect could change this outcome. Try another branch or adjust assumptions to see their modeled effects.'),
    ]
    return {'title': f"Your life in {month_label(profile, end['month'])}", 'subtitle': 'A calculated path. A possible life.', 'sections': [{'title': title, 'body': body} for title, body in generated],
      'calculated': {'net_worth': end['net_worth'], 'work_hours': hours, 'cash_flow': end['cash_flow'], 'monthly_spending': spending},
      'illustrative': ['Daily routine', 'Opportunities for connection', 'How free time might be used']}
