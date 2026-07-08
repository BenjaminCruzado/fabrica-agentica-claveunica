import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class PortalApiService {
  state = signal<any>({ portalMetrics: [], db: {} });
  constructor(private http: HttpClient) { this.refresh().subscribe(); }
  refresh() { return this.http.get<any>('/api/v1/app-state').pipe(tap(data => this.state.set(data))); }
  runAction(screenRoute: string, action: string) { return this.http.post<any>('/api/v1/actions', { screenRoute, action }).pipe(tap(() => this.refresh().subscribe())); }
}
