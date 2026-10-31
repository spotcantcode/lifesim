from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
  model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Business(StrictModel):
  name: str = Field(default='Northstar Studio', min_length=1, max_length=100)
  revenue: float = Field(default=24000, ge=0, le=1e8)
  expenses: float = Field(default=14000, ge=0, le=1e8)
  employees: int = Field(default=2, ge=0, le=10000)
  contractors: int = Field(default=1, ge=0, le=10000)
  dependency: str = Field(default='Owner handles sales and delivery', max_length=500)


class Account(StrictModel):
  name: str = Field(min_length=1, max_length=100)
  kind: Literal['cash', 'investments', 'assets', 'debt']
  balance: float = Field(ge=0, le=1e10)


class Assumptions(StrictModel):
  annual_growth: float = Field(default=.03, ge=-.3, le=.3)
  investment_return: float = Field(default=.05, ge=-.3, le=.3)
  revenue_volatility: float = Field(default=.12, ge=0, le=1)
  investment_volatility: float = Field(default=.16, ge=0, le=1)
  inflation: float = Field(default=.025, ge=0, le=.2)
  tax_rate: float = Field(default=.25, ge=0, le=.6)
  investment_allocation: float = Field(default=.6, ge=0, le=1)
  withdrawal_rate: float = Field(default=.04, ge=.01, le=.1)
  debt_interest: float = Field(default=.06, ge=0, le=.4)
  manager_cost: float = Field(default=3000, ge=0, le=1e6)
  expansion_growth: float = Field(default=.08, ge=0, le=.3)
  disruption_fraction: float = Field(default=.12, ge=0, le=1)


class Profile(StrictModel):
  name: str = Field(default='Alex Morgan', min_length=1, max_length=100)
  age: int = Field(default=45, ge=18, le=100)
  start_date: str = Field(default='2026-01-01', pattern=r'^\d{4}-\d{2}-01$')
  location: str = Field(default='Austin, Texas', min_length=1, max_length=100)
  future_location: str = Field(default='Lisbon, Portugal', min_length=1, max_length=100)
  milestones: str = Field(default='Built a small creative services business over ten years.', max_length=2000)
  aspirations: str = Field(default='More ownership of my time, meaningful work, and longer stays abroad.', max_length=2000)
  provenance: Literal['fictional', 'user_assumption', 'observed'] = 'fictional'
  businesses: list[Business] = Field(default_factory=lambda: [Business()], min_length=1, max_length=20)
  accounts: list[Account] = Field(default_factory=lambda: [Account(name='Cash reserve', kind='cash', balance=60000), Account(name='Index portfolio', kind='investments', balance=220000), Account(name='Other assets', kind='assets', balance=80000), Account(name='Debt', kind='debt', balance=20000)], max_length=50)
  goals: list[str] = Field(default_factory=lambda: ['Financial independence by 50', 'Work 25 hours a week', 'Spend three months a year abroad'], max_length=20)
  monthly_expenses: float = Field(default=4500, ge=0, le=1e7)
  monthly_obligations: float = Field(default=500, ge=0, le=1e7)
  other_income: float = Field(default=0, ge=0, le=1e7)
  work_hours: float = Field(default=45, ge=0, le=100)
  sleep_hours: float = Field(default=56, ge=35, le=84)
  exercise_hours: float = Field(default=4, ge=0, le=30)
  family_hours: float = Field(default=20, ge=0, le=100)
  personal_hours: float = Field(default=12, ge=0, le=100)
  travel_hours: float = Field(default=2, ge=0, le=50)
  months_abroad: int = Field(default=0, ge=0, le=12)
  relationship_commitments: str = Field(default='Protect evenings and a weekly family day.', max_length=2000)
  lifestyle_preferences: str = Field(default='Regular exercise, a stable home base, and unhurried travel.', max_length=2000)
  target_work_hours: float = Field(default=25, ge=0, le=100)
  assumptions: Assumptions = Field(default_factory=Assumptions)

  @model_validator(mode='after')
  def check_time(self):
    from datetime import date
    date.fromisoformat(self.start_date)
    if sum([self.work_hours, self.sleep_hours, self.exercise_hours, self.family_hours, self.personal_hours, self.travel_hours]) > 168:
      raise ValueError('Weekly allocations exceed 168 hours. Reduce one or more commitments.')
    if any(len(goal) > 500 for goal in self.goals):
      raise ValueError('Goals must be 500 characters or fewer.')
    return self


DecisionKey = Literal['expand_owner', 'hire_manager', 'maintain', 'reduce_expenses', 'invest_cash', 'abroad', 'reduce_hours', 'fund_repair']


class ScenarioInput(StrictModel):
  profile_id: str
  name: str = Field(default='A different kind of future', min_length=1, max_length=100)
  seed: int = Field(default=42, ge=0, le=2**31 - 1)
  assumptions: Assumptions | None = None
  campaign: bool = True


class AdvanceInput(StrictModel):
  decision: DecisionKey = 'maintain'
  months: int = Field(default=1, ge=1, le=240)
  runs: Literal[1, 100, 1000, 10000] = 1


class BranchInput(StrictModel):
  month: int = Field(ge=0, le=240)
  name: str = Field(default='An alternate path', min_length=1, max_length=100)


class ObservationInput(StrictModel):
  profile_id: str
  month: str = Field(pattern=r'^\d{4}-\d{2}$')
  note: str = Field(min_length=1, max_length=2000)


class ImportInput(StrictModel):
  format: Literal['json', 'csv']
  content: str = Field(max_length=500000)
