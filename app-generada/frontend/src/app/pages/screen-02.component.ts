import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-02', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-02.component.html'})
export class Screen02Component {
  api = inject(PortalApiService);
  screen = {"actions":["Enviar enlace","Validar identidad"],"fields":["Correo","RUN","Canal"],"moduleName":"Seguridad","records":[["Correo","benjamin@example.local","verificado"],["Canal","email","activo"]],"route":"/seguridad/auth-recovery","summary":"Recuperacion de acceso: implementa campos Correo, RUN, Canal y acciones Enviar enlace, Validar identidad.","title":"Recuperacion de acceso"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
