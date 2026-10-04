import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, map, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  CreditPack,
  PurchaseResponse,
  Transaction,
  TransactionStatus,
} from '../models/payment.model';
import { AuthService } from './auth.service';

type ListResponse<T> = T[] | { results: T[] };

function asList<T>(payload: ListResponse<T>): T[] {
  return Array.isArray(payload) ? payload : (payload.results ?? []);
}

@Injectable({ providedIn: 'root' })
export class PaymentService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  readonly packs = signal<CreditPack[]>([]);
  readonly transactions = signal<Transaction[]>([]);
  readonly loading = signal(false);

  listPacks(): Observable<CreditPack[]> {
    this.loading.set(true);
    return this.http.get<ListResponse<CreditPack>>(`${environment.apiUrl}/credit-packs/`).pipe(
      map((payload) => asList(payload)),
      tap({
        next: (packs) => {
          this.packs.set(packs);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      }),
    );
  }

  listTransactions(): Observable<Transaction[]> {
    return this.http.get<ListResponse<Transaction>>(`${environment.apiUrl}/transactions/`).pipe(
      map((payload) => asList(payload)),
      tap((transactions) => this.transactions.set(transactions)),
    );
  }

  purchase(packId: number, simulateStatus?: TransactionStatus): Observable<PurchaseResponse> {
    const body: { pack_id: number; simulate_status?: TransactionStatus } = {
      pack_id: packId,
    };
    if (simulateStatus) {
      body.simulate_status = simulateStatus;
    }

    return this.http
      .post<PurchaseResponse>(`${environment.apiUrl}/transactions/purchase/`, body)
      .pipe(
        tap((response) => {
          this.auth.updateCreditBalance(response.credit_balance);
          this.transactions.update((list) => [response.transaction, ...list]);
        }),
      );
  }
}
