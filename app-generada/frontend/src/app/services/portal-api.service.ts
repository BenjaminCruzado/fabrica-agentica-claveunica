import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class PortalApiService {
  state = signal<any>({ portalMetrics: [], db: {} });
  constructor(private http: HttpClient) { this.refresh().subscribe(); }
  refresh() { return this.http.get<any>('/api/v1/app-state').pipe(tap(data => this.state.set(data))); }

  rowsForFeature(feature: string): string[][] {
    const db = this.state().db || {};
    const pick = (items: any[], map: (item: any) => string[]) => (items || []).slice(0, 8).map(map);
    if (feature === 'procedures') return pick(db.procedures, item => [item.name, item.owner, item.status]);
    if (feature === 'notifications') return pick(db.notifications, item => [item.subject, item.channel, item.read_at ? 'leida' : 'pendiente']);
    if (feature === 'consents') return pick(db.consents, item => [item.grantee, item.purpose, item.status]);
    if (feature === 'addresses') return pick(db.addresses, item => [item.address_line, item.comuna, item.verified_at ? 'verificado' : 'por verificar']);
    if (feature === 'cases') return pick(db.cases, item => [item.subject, item.assigned_to, item.status]);
    if (feature === 'support') return pick(db.tickets, item => [item.topic, item.channel, item.status]);
    if (feature === 'audit') return pick(db.events, item => [item.event_type, item.detail, item.created_at]);
    if (feature === 'security') return pick(db.sessions, item => [item.device, item.ip, item.active ? 'activa' : 'cerrada']);
    if (feature === 'profile') return pick(db.profileChanges, item => [item.field_name, item.new_value, item.changed_at]);
    return pick(db.services, item => [item.name, item.institution, item.category]);
  }

  statusMessageForFeature(feature: string): string {
    const rows = this.rowsForFeature(feature).length;
    return rows ? `${rows} registros sincronizados desde la base de datos local.` : 'Sin registros disponibles para este modulo.';
  }
}
