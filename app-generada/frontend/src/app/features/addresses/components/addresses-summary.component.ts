import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({ selector: 'app-addresses-summary', standalone: true, imports: [CommonModule], template: `<section class="card"><h2>addresses</h2><p *ngFor="let item of items">{{item.primary}} - {{item.status}}</p></section>` })
export class AddressesSummaryComponent {
  @Input() items: Array<{ primary: string; status: string }> = [];
}
