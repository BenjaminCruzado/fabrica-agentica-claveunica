import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-12', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-12.component.html'})
export class Screen12Component {
  api = inject(PortalApiService);
  screen = {"actions":["Subir evidencia","Solicitar revision"],"fields":["Evidencia","Institucion","Resultado"],"moduleName":"Domicilio Digital Unico","records":[["Cuenta servicios","CGEDemo","aceptada"],["Georreferencia","Sistema","pendiente"]],"route":"/ddu/address-verify","summary":"Verificacion de domicilio: implementa campos Evidencia, Institucion, Resultado y acciones Subir evidencia, Solicitar revision.","title":"Verificacion de domicilio"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
