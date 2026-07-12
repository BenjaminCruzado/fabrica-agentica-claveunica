import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-17', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-17.component.html'})
export class Screen17Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#15803d","actions":["Revocar","Renovar"],"feature":"consents","fields":["Institucion","Dato","Vigencia"],"layout":"consent-list","moduleName":"Autorizaciones","route":"/autorizaciones/consent-list","summary":"Permisos de datos: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Permisos de datos"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
