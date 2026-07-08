import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-23', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-23.component.html'})
export class Screen23Component {
  api = inject(PortalApiService);
  screen = {"actions":["Buscar ayuda","Crear ticket"],"fields":["Tema","Canal","SLA"],"moduleName":"Ayuda","records":[["Clave bloqueada","chat","4h"],["Domicilio","formulario","24h"]],"route":"/ayuda/support-home","summary":"Centro de ayuda: implementa campos Tema, Canal, SLA y acciones Buscar ayuda, Crear ticket.","title":"Centro de ayuda"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
