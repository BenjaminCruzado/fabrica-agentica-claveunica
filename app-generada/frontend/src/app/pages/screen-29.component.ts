import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-29', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-29.component.html'})
export class Screen29Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#0f766e","actions":["Reintentar","Ver detalle"],"feature":"procedures","fields":["Servicio","Estado","Latencia"],"layout":"integration-status","moduleName":"Portal ciudadano","route":"/portal/integration-status","summary":"Estado de integraciones: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Estado de integraciones"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
