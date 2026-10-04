import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';

import { environment } from '../../../../environments/environment';
import { ChatbotWidgetComponent } from './chatbot-widget.component';

describe('ChatbotWidgetComponent', () => {
  let fixture: ComponentFixture<ChatbotWidgetComponent>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatbotWidgetComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatbotWidgetComponent);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    http.verify();
  });

  it('opens the panel and sends a message', () => {
    const toggle = fixture.debugElement.query(By.css('.chatbot__toggle'));
    toggle.triggerEventHandler('click');
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('#chatbot-panel')).toBeTruthy();

    const component = fixture.componentInstance;
    component.draft.set('crédits');
    component.send();
    fixture.detectChanges();

    const req = http.expectOne(`${environment.apiUrl}/chatbot/`);
    expect(req.request.body).toEqual({ message: 'crédits' });
    req.flush({
      reply: 'Pour acheter des crédits, ouvrez la section Paiements.',
      message_id: null,
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('crédits');
    expect(text.toLowerCase()).toContain('paiements');
  });
});
