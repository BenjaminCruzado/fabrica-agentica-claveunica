import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-27', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-27.component.html'})
export class Screen27Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#334155","actions":["Comparar cambio","Ver actor"],"feature":"audit","fields":["Dato","Antes","Despues"],"layout":"data-changes","moduleName":"Auditoria","route":"/auditoria/data-changes","summary":"Cambios de datos: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Cambios de datos"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
