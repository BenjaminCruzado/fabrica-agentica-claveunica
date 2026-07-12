import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-22', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-22.component.html'})
export class Screen22Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#4338ca","actions":["Ver evidencia","Descargar bitacora"],"feature":"cases","fields":["Fecha","Evento","Resultado"],"layout":"case-timeline","moduleName":"Expedientes","route":"/expedientes/case-timeline","summary":"Linea de tiempo: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Linea de tiempo"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
