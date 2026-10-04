import { TestBed } from '@angular/core/testing';

import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.dataset['theme'] = '';
    TestBed.configureTestingModule({});
  });

  it('toggles theme and persists preference', () => {
    const service = TestBed.inject(ThemeService);
    TestBed.flushEffects();

    expect(service.theme()).toBe('light');
    service.toggle();
    TestBed.flushEffects();

    expect(service.theme()).toBe('dark');
    expect(localStorage.getItem('edulearn-theme')).toBe('dark');
    expect(document.documentElement.dataset['theme']).toBe('dark');
  });
});
