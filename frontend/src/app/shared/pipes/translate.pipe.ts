import { Pipe, PipeTransform, inject } from '@angular/core';

import { TranslationKey } from '../../core/i18n';
import { TranslationService } from '../../core/services/translation.service';

@Pipe({
  name: 'translate',
  pure: false,
})
export class TranslatePipe implements PipeTransform {
  private readonly i18n = inject(TranslationService);

  transform(key: TranslationKey, params?: Record<string, string | number>): string {
    // Read signal so impure pipe refreshes when language changes.
    this.i18n.lang();
    return this.i18n.t(key, params);
  }
}
