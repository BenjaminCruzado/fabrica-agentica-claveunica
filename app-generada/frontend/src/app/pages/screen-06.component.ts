import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-06', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-06.component.html'})
export class Screen06Component {
  api = inject(PortalApiService);
  screen = {"actions":["Actualizar datos","Solicitar correccion"],"fields":["Nombre","RUN","Fecha nacimiento","Nacionalidad"],"moduleName":"Perfil ciudadano","records":[["Nombre","Benjamin Cruzado","validado"],["RUN","12.345.678-9","bloqueado"]],"route":"/perfil/profile","summary":"Datos personales: implementa campos Nombre, RUN, Fecha nacimiento, Nacionalidad y acciones Actualizar datos, Solicitar correccion.","title":"Datos personales"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
