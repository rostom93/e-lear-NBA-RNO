import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ChatBubble, ChatReply } from '../models/chat.model';

@Injectable({ providedIn: 'root' })
export class ChatbotService {
  private readonly http = inject(HttpClient);
  private seq = 0;

  readonly open = signal(false);
  readonly sending = signal(false);
  readonly messages = signal<ChatBubble[]>([]);

  toggle(): void {
    this.open.update((value) => !value);
  }

  openPanel(): void {
    this.open.set(true);
  }

  closePanel(): void {
    this.open.set(false);
  }

  send(message: string): Observable<ChatReply> {
    const text = message.trim();
    this.messages.update((list) => [
      ...list,
      { id: this.nextId('user'), sender: 'user', content: text },
    ]);
    this.sending.set(true);

    return this.http
      .post<ChatReply>(`${environment.apiUrl}/chatbot/`, { message: text })
      .pipe(
        tap({
          next: (response) => {
            this.messages.update((list) => [
              ...list,
              {
                id: this.nextId('bot'),
                sender: 'bot',
                content: response.reply,
              },
            ]);
            this.sending.set(false);
          },
          error: () => {
            this.messages.update((list) => [
              ...list,
              {
                id: this.nextId('bot'),
                sender: 'bot',
                content: 'ERROR',
              },
            ]);
            this.sending.set(false);
          },
        }),
      );
  }

  private nextId(prefix: string): string {
    this.seq += 1;
    return `${prefix}-${this.seq}`;
  }
}
