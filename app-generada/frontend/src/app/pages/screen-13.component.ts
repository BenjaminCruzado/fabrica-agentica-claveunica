import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';
import { FeatureApiService } from '../services/feature-api.service';

@Component({selector:'app-screen-13', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-13.component.html'})
export class Screen13Component {
  api = inject(PortalApiService);
  featureApi = inject(FeatureApiService);
  screen = {"accent":"#b45309","actions":["Comparar","Descargar historial"],"feature":"addresses","fields":["Fecha","Direccion","Origen"],"layout":"address-history","moduleName":"Domicilio Digital Unico","route":"/ddu/address-history","summary":"Historial de domicilio: informacion actualizada desde la base local y acciones del flujo ciudadano.","title":"Historial de domicilio"};
  state = this.api.state;
  form: Record<string, string> = Object.fromEntries(this.screen.fields.map((field: string) => [field, '']));
  rows() { return this.api.rowsForFeature(this.screen.feature); }
  statusMessage() { return this.api.statusMessageForFeature(this.screen.feature); }
  run(action: string) { this.featureApi.runFeatureAction(this.screen.feature, action, this.screen.route, this.form).subscribe(() => this.api.refresh().subscribe()); }
}
