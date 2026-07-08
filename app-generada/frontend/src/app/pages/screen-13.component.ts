import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-13', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-13.component.html'})
export class Screen13Component {
  api = inject(PortalApiService);
  screen = {"actions":["Comparar","Descargar historial"],"fields":["Fecha","Direccion","Origen"],"moduleName":"Domicilio Digital Unico","records":[["2026-01-10","Avenida Demo 123","ciudadano"],["2025-08-01","Calle Antigua 456","municipal"]],"route":"/ddu/address-history","summary":"Historial de domicilio: implementa campos Fecha, Direccion, Origen y acciones Comparar, Descargar historial.","title":"Historial de domicilio"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
