import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-18', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-18.component.html'})
export class Screen18Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#15803d","actions":["Autorizar","Rechazar"],"feature":"consents","fields":["Solicitante","Finalidad","Duracion"],"layout":"consent-request","moduleName":"Autorizaciones","route":"/autorizaciones/consent-request","summary":"Solicitud de autorizacion: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Solicitud de autorizacion"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
