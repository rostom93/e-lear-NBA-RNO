import { DOCUMENT } from '@angular/common';
import { Injectable, computed, effect, inject, signal } from '@angular/core';

import { AppLanguage, TRANSLATIONS, TranslationKey } from '../i18n';

const STORAGE_KEY = 'edulearn-lang';

@Injectable({ providedIn: 'root' })
export class TranslationService {
  private readonly document = inject(DOCUMENT);

  readonly lang = signal<AppLanguage>(this.readInitial());
  readonly direction = computed(() => (this.lang() === 'ar' ? 'rtl' : 'ltr'));
  readonly isRtl = computed(() => this.direction() === 'rtl');

  constructor() {
    effect(() => {
      const lang = this.lang();
      const dir = lang === 'ar' ? 'rtl' : 'ltr';
      const root = this.document.documentElement;
      root.lang = lang;
      root.dir = dir;
      localStorage.setItem(STORAGE_KEY, lang);
    });
  }

  setLanguage(lang: AppLanguage): void {
    this.lang.set(lang);
  }

  t(key: TranslationKey, params?: Record<string, string | number>): string {
    const dict = TRANSLATIONS[this.lang()];
    let value = dict[key] ?? TRANSLATIONS.fr[key] ?? key;
    if (params) {
      for (const [param, raw] of Object.entries(params)) {
        value = value.replace(`{{${param}}}`, String(raw));
      }
    }
    return value;
  }

  private readInitial(): AppLanguage {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'fr' || stored === 'en' || stored === 'ar') {
      return stored;
    }
    return 'fr';
  }
}
