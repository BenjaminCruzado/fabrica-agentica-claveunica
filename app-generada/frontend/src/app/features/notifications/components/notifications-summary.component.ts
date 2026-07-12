import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({ selector: 'app-notifications-summary', standalone: true, imports: [CommonModule], template: `<section class="card"><h2>notifications</h2><p *ngFor="let item of items">{{item.primary}} - {{item.status}}</p></section>` })
export class NotificationsSummaryComponent {
  @Input() items: Array<{ primary: string; status: string }> = [];
}
