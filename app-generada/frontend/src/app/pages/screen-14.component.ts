import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-14', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-14.component.html'})
export class Screen14Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#0369a1","actions":["Marcar leida","Responder"],"feature":"notifications","fields":["Asunto","Prioridad","Acuse"],"layout":"inbox","moduleName":"Notificaciones","route":"/notificaciones/inbox","summary":"Bandeja de notificaciones: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Bandeja de notificaciones"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
