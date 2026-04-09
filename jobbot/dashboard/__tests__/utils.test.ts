import { describe, it, expect } from 'vitest';
import { cn } from '../src/components/ui/button';

describe('cn utility', () => {
  it('should merge class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('should handle conditional classes', () => {
    expect(cn('foo', true && 'bar', false && 'baz')).toBe('foo bar');
  });

  it('should handle tailwind conflicts', () => {
    expect(cn('px-2 py-1', 'p-4')).toBe('p-4');
  });

  it('should handle undefined and null', () => {
    expect(cn('foo', undefined, null, 'bar')).toBe('foo bar');
  });
});
