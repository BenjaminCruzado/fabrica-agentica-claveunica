import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-06', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-06.component.html'})
export class Screen06Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#7c3aed","actions":["Actualizar datos","Solicitar correccion"],"feature":"profile","fields":["Nombre","RUN","Fecha nacimiento","Nacionalidad"],"layout":"profile","moduleName":"Perfil ciudadano","route":"/perfil/profile","summary":"Datos personales: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Datos personales"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
