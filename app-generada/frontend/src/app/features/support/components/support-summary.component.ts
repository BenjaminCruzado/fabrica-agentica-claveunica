import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({ selector: 'app-support-summary', standalone: true, imports: [CommonModule], template: `<section class="card"><h2>support</h2><p *ngFor="let item of items">{{item.primary}} - {{item.status}}</p></section>` })
export class SupportSummaryComponent {
  @Input() items: Array<{ primary: string; status: string }> = [];
}
