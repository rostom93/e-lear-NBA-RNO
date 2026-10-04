import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ChatbotService } from '../../../core/services/chatbot.service';
import { TranslationService } from '../../../core/services/translation.service';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-chatbot-widget',
  imports: [FormsModule, TranslatePipe],
  templateUrl: './chatbot-widget.component.html',
  styleUrl: './chatbot-widget.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatbotWidgetComponent {
  readonly chat = inject(ChatbotService);
  private readonly i18n = inject(TranslationService);

  private readonly panel = viewChild<ElementRef<HTMLElement>>('panel');
  private readonly inputEl = viewChild<ElementRef<HTMLTextAreaElement>>('inputEl');
  private readonly toggleBtn = viewChild<ElementRef<HTMLButtonElement>>('toggleBtn');
  private readonly threadEl = viewChild<ElementRef<HTMLElement>>('thread');

  readonly draft = signal('');
  readonly localError = signal(false);

  constructor() {
    effect(() => {
      if (!this.chat.open()) {
        return;
      }
      queueMicrotask(() => {
        this.inputEl()?.nativeElement.focus();
        this.scrollThread();
      });
    });

    effect(() => {
      this.chat.messages();
      queueMicrotask(() => this.scrollThread());
    });
  }

  toggle(): void {
    this.localError.set(false);
    this.chat.toggle();
    if (!this.chat.open()) {
      queueMicrotask(() => this.toggleBtn()?.nativeElement.focus());
    }
  }

  close(): void {
    this.chat.closePanel();
    queueMicrotask(() => this.toggleBtn()?.nativeElement.focus());
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape' && this.chat.open()) {
      event.preventDefault();
      this.close();
    }
  }

  send(): void {
    const text = this.draft().trim();
    if (!text || this.chat.sending()) {
      return;
    }
    this.localError.set(false);
    this.draft.set('');
    this.chat.send(text).subscribe({
      error: () => this.localError.set(true),
    });
  }

  displayContent(content: string): string {
    if (content === 'ERROR') {
      return this.i18n.t('chat.error');
    }
    return content;
  }

  private scrollThread(): void {
    const el = this.threadEl()?.nativeElement;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }
}
