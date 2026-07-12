import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-03', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-03.component.html'})
export class Screen03Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#0f766e","actions":["Abrir tramite","Ver avisos"],"feature":"procedures","fields":["Tramites activos","Mensajes","Alertas"],"layout":"dashboard","moduleName":"Portal ciudadano","route":"/portal/dashboard","summary":"Dashboard ciudadano: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Dashboard ciudadano"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
