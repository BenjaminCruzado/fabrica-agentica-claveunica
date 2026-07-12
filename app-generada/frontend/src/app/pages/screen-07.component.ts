import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-07', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-07.component.html'})
export class Screen07Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#7c3aed","actions":["Verificar correo","Actualizar telefono"],"feature":"profile","fields":["Correo","Telefono","Canal preferente"],"layout":"contact","moduleName":"Perfil ciudadano","route":"/perfil/contact","summary":"Datos de contacto: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Datos de contacto"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
