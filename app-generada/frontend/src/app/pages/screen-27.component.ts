import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-27', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-27.component.html'})
export class Screen27Component {
  api = inject(PortalApiService);
  screen = {"actions":["Comparar cambio","Ver actor"],"fields":["Dato","Antes","Despues"],"moduleName":"Auditoria","records":[["Correo","old@example.local","benjamin@example.local"],["Telefono","vacio","+56 9 0000 0000"]],"route":"/auditoria/data-changes","summary":"Cambios de datos: implementa campos Dato, Antes, Despues y acciones Comparar cambio, Ver actor.","title":"Cambios de datos"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
