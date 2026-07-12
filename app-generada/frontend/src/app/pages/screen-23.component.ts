import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-23', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-23.component.html'})
export class Screen23Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#525252","actions":["Buscar ayuda","Crear ticket"],"feature":"support","fields":["Tema","Canal","SLA"],"layout":"support-home","moduleName":"Ayuda","route":"/ayuda/support-home","summary":"Centro de ayuda: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Centro de ayuda"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
