import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-11', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-11.component.html'})
export class Screen11Component {
  api = inject(PortalApiService);
  screen = {"actions":["Editar domicilio","Verificar"],"fields":["Direccion","Comuna","Estado"],"moduleName":"Domicilio Digital Unico","records":[["Avenida Demo 123","Santiago","vigente"],["Casilla digital","Web","activa"]],"route":"/ddu/address-current","summary":"Domicilio digital vigente: implementa campos Direccion, Comuna, Estado y acciones Editar domicilio, Verificar.","title":"Domicilio digital vigente"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
