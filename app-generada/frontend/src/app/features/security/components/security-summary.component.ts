import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({ selector: 'app-security-summary', standalone: true, imports: [CommonModule], template: `<section class="card"><h2>security</h2><p *ngFor="let item of items">{{item.primary}} - {{item.status}}</p></section>` })
export class SecuritySummaryComponent {
  @Input() items: Array<{ primary: string; status: string }> = [];
}
