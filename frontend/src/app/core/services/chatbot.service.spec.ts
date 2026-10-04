import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { environment } from '../../../environments/environment';
import { ChatbotService } from './chatbot.service';

describe('ChatbotService', () => {
  let service: ChatbotService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ChatbotService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('stores user and bot messages after a successful reply', () => {
    service.send('bonjour').subscribe();

    const req = http.expectOne(`${environment.apiUrl}/chatbot/`);
    expect(req.request.body).toEqual({ message: 'bonjour' });
    req.flush({ reply: 'Bonjour !', message_id: null });

    expect(service.messages().length).toBe(2);
    expect(service.messages()[0].sender).toBe('user');
    expect(service.messages()[1].content).toBe('Bonjour !');
    expect(service.sending()).toBe(false);
  });

  it('records an error bubble when the API fails', () => {
    service.send('help').subscribe({ error: () => undefined });

    const req = http.expectOne(`${environment.apiUrl}/chatbot/`);
    req.flush({ detail: 'down' }, { status: 500, statusText: 'Server Error' });

    expect(service.messages().at(-1)?.content).toBe('ERROR');
    expect(service.sending()).toBe(false);
  });
});
