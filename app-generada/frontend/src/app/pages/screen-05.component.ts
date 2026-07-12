import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-05', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-05.component.html'})
export class Screen05Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#0f766e","actions":["Continuar solicitud","Descargar requisitos"],"feature":"procedures","fields":["Requisitos","Costo","Tiempo estimado"],"layout":"service-detail","moduleName":"Portal ciudadano","route":"/portal/service-detail","summary":"Detalle de tramite: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Detalle de tramite"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
