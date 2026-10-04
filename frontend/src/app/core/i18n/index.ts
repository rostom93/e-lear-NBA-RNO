import { AR } from './ar';
import { EN } from './en';
import { FR, TranslationKey } from './fr';

export type AppLanguage = 'fr' | 'en' | 'ar';

export const TRANSLATIONS: Record<AppLanguage, Record<TranslationKey, string>> = {
  fr: FR,
  en: EN,
  ar: AR,
};

export type { TranslationKey };
