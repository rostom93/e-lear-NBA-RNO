import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { PaymentService } from './payment.service';

describe('PaymentService', () => {
  let service: PaymentService;
  let http: HttpTestingController;
  let auth: AuthService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(PaymentService);
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
    auth.currentUser.set({
      id: 1,
      email: 'guest@gmail.com',
      username: 'guest',
      first_name: 'Gary',
      last_name: 'Guest',
      role: 'STUDENT',
      credit_balance: 0,
      is_active: true,
      date_joined: '2026-01-01T00:00:00Z',
    });
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('updates credit balance after successful purchase', () => {
    service.purchase(2).subscribe();

    const req = http.expectOne(`${environment.apiUrl}/transactions/purchase/`);
    expect(req.request.body).toEqual({ pack_id: 2 });
    req.flush({
      credit_balance: 300,
      transaction: {
        id: 10,
        user: 1,
        user_email: 'guest@gmail.com',
        pack: 2,
        pack_name: 'Pro',
        credits: 300,
        amount_euros: '24.99',
        status: 'SUCCESS',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    });

    expect(auth.creditBalance()).toBe(300);
    expect(service.transactions().length).toBe(1);
  });
});
