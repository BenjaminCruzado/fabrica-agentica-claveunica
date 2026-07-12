import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-09', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-09.component.html'})
export class Screen09Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#1d4ed8","actions":["Cerrar sesion","Confiar dispositivo"],"feature":"security","fields":["Dispositivo","Ubicacion","Ultimo acceso"],"layout":"sessions","moduleName":"Seguridad","route":"/seguridad/sessions","summary":"Sesiones activas: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Sesiones activas"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
