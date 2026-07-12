import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-15', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-15.component.html'})
export class Screen15Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#0369a1","actions":["Descargar adjunto","Acusar recibo"],"feature":"notifications","fields":["Remitente","Folio","Adjuntos"],"layout":"message-detail","moduleName":"Notificaciones","route":"/notificaciones/message-detail","summary":"Detalle de mensaje: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Detalle de mensaje"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
