import { describe, expect, it } from 'vitest';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  it('keeps deterministic local state', () => {
    const component = new AppComponent();
    component.increment();
    expect(component.count).toBe(1);
    expect(component.title).toContain('Angular');
  });
});
