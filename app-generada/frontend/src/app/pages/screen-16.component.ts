import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-16', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-16.component.html'})
export class Screen16Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#0369a1","actions":["Guardar canal","Probar envio"],"feature":"notifications","fields":["Canal","Horario","Prioridad"],"layout":"notification-settings","moduleName":"Notificaciones","route":"/notificaciones/notification-settings","summary":"Preferencias de aviso: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Preferencias de aviso"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
