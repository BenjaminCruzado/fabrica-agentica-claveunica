import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-26', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-26.component.html'})
export class Screen26Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#334155","actions":["Filtrar","Exportar"],"feature":"audit","fields":["Fecha","IP","Resultado"],"layout":"access-log","moduleName":"Auditoria","route":"/auditoria/access-log","summary":"Bitacora de accesos: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Bitacora de accesos"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
