import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';

import { PaymentService } from '../../../core/services/payment.service';
import { AuthService } from '../../../core/services/auth.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-credits',
  imports: [TranslatePipe],
  templateUrl: './credits.component.html',
  styleUrl: './credits.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreditsComponent implements OnInit {
  private readonly payments = inject(PaymentService);
  readonly auth = inject(AuthService);

  readonly packs = this.payments.packs;
  readonly transactions = this.payments.transactions;
  readonly loading = this.payments.loading;
  readonly purchasingId = signal<number | null>(null);
  readonly message = signal<'success' | 'error' | null>(null);

  ngOnInit(): void {
    this.payments.listPacks().subscribe();
    this.payments.listTransactions().subscribe();
  }

  buy(packId: number): void {
    this.purchasingId.set(packId);
    this.message.set(null);
    this.payments.purchase(packId).subscribe({
      next: () => {
        this.purchasingId.set(null);
        this.message.set('success');
      },
      error: () => {
        this.purchasingId.set(null);
        this.message.set('error');
      },
    });
  }
}
