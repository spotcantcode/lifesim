import { describe, expect, it } from 'vitest';
import { dateLabel, interpretDecision, money } from './lib';
describe('explicit decision interpretation', () => {
  it('maps delegation, expense, travel and growth requests to real engine actions', () => {
    expect(interpretDecision('What if I hire an operator?')).toBe('hire_manager');
    expect(interpretDecision('Reduce monthly expenses')).toBe('reduce_expenses');
    expect(interpretDecision('Live internationally')).toBe('abroad');
    expect(interpretDecision('Aggressive growth')).toBe('expand_owner');
  });
  it('rejects unsupported actions instead of silently inventing a model', () => {
    expect(interpretDecision('Sell a business')).toBeNull();
    expect(interpretDecision('What happens next?')).toBeNull();
  });
});
describe('narrative units', () => {
  it('handles year boundaries without timezone shifts', () => {
    expect(dateLabel('2026-01-01', 12)).toBe('January 2027');
    expect(dateLabel('2026-11-01', 5)).toBe('April 2027');
  });
  it('labels real monetary units', () => expect(money(-2500)).toBe('-$2,500'));
});
