import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-28', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-28.component.html'})
export class Screen28Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#334155","actions":["Generar CSV","Generar PDF"],"feature":"audit","fields":["Rango","Formato","Estado"],"layout":"audit-export","moduleName":"Auditoria","route":"/auditoria/audit-export","summary":"Exportacion de auditoria: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Exportacion de auditoria"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
