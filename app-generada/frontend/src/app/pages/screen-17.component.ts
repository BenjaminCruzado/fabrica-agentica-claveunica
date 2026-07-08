import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-17', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-17.component.html'})
export class Screen17Component {
  api = inject(PortalApiService);
  screen = {"actions":["Revocar","Renovar"],"fields":["Institucion","Dato","Vigencia"],"moduleName":"Autorizaciones","records":[["Registro Civil","Identidad","vigente"],["Municipalidad","Domicilio","por vencer"]],"route":"/autorizaciones/consent-list","summary":"Permisos de datos: implementa campos Institucion, Dato, Vigencia y acciones Revocar, Renovar.","title":"Permisos de datos"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
