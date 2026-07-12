import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-21', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-21.component.html'})
export class Screen21Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#4338ca","actions":["Adjuntar documento","Enviar comentario"],"feature":"cases","fields":["Folio","Hito","Documento"],"layout":"case-detail","moduleName":"Expedientes","route":"/expedientes/case-detail","summary":"Detalle de expediente: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Detalle de expediente"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
