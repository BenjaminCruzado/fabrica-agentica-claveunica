import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-12', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-12.component.html'})
export class Screen12Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#b45309","actions":["Subir evidencia","Solicitar revision"],"feature":"addresses","fields":["Evidencia","Institucion","Resultado"],"layout":"address-verify","moduleName":"Domicilio Digital Unico","route":"/ddu/address-verify","summary":"Verificacion de domicilio: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Verificacion de domicilio"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
