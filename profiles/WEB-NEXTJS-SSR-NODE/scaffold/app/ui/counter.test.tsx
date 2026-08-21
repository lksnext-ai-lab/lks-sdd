import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import Counter from './counter';

describe('Counter', () => {
  it('hydrates local interaction state', () => {
    render(<Counter />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('button')).toHaveTextContent('1');
  });
});
